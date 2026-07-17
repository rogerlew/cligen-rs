#!/bin/bash
#SBATCH --job-name=a10m2d1-d1
#SBATCH --partition=gpu-icrews
#SBATCH --nodelist=node03
#SBATCH --gres=gpu:l40:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

set -u
set -o pipefail
umask 077
ulimit -c 0

cuda_root=/usr/local/cuda-12.8
result_dir="results/d1/${SLURM_JOB_ID}"
local_root=${SLURM_TMPDIR:-${TMPDIR:-/tmp}}
build_dir="${local_root}/a10m2d1-${SLURM_JOB_ID}"
matrix="$result_dir/matrix.tsv"
mkdir -p "$result_dir" "$build_dir"
trap 'rm -rf "$build_dir"' EXIT
printf 'test\tstatus\tdetail\n' >"$matrix"
test -x "$cuda_root/bin/nvcc" || exit 3

record() {
    printf '%s\t%s\t%s\n' "$1" "$2" "$3" >>"$matrix"
}

printf '=== bounded node inventory ===\n'
lscpu | grep -E '^(Architecture|Vendor ID|CPU family|Model:|Model name|Socket|Core|Thread)'
cpu_flags=$(awk -F: '/^flags/{print $2; exit}' /proc/cpuinfo)
for feature in avx avx2 avx512f avx512dq avx512bw avx512vl; do
    if printf '%s\n' "$cpu_flags" | grep -qw "$feature"; then
        record "cpu-${feature}" 0 present
    else
        record "cpu-${feature}" 1 absent
    fi
done
uname -sr
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
"$cuda_root/bin/nvcc" --version
device_count=$(nvidia-smi --query-gpu=name --format=csv,noheader | wc -l)
device_name=$(nvidia-smi --query-gpu=name --format=csv,noheader)
if [ "$device_count" -ne 1 ] || ! printf '%s\n' "$device_name" | grep -q L40; then
    record gpu-allocation 1 wrong-count-or-type
    exit 4
fi
record gpu-allocation 0 one-L40

printf '=== module visibility ===\n'
if [ -d /opt/modules/modulefiles ]; then
    record M0-directory 0 present
else
    record M0-directory 1 absent
fi
(
    module purge
    module use /opt/modules/modulefiles
    module --ignore_cache is-avail cuda/12.8
)
record M0-is-avail $? cache-bypassed
(
    module purge
    module use /opt/modules/modulefiles
    module --ignore_cache load cuda/12.8
)
record M0-load $? cache-bypassed

probe_compiler() {
    label=$1
    compiler=$2
    if [ ! -x "$compiler" ]; then
        record "${label}-driver" 127 missing
        return
    fi
    "$compiler" --version >"$result_dir/${label}-version.log" 2>&1
    record "${label}-driver" $? "$compiler"
    "$compiler" -dM -E - </dev/null >"$result_dir/${label}-preprocess.log" 2>&1
    record "${label}-preprocess" $? macros
    cc1=$("$compiler" -print-prog-name=cc1 2>/dev/null)
    if [ -x "$cc1" ]; then
        timeout 20 "$cc1" --help >"$result_dir/${label}-cc1.log" 2>&1
        record "${label}-cc1" $? executable
        ldd "$cc1" >"$result_dir/${label}-cc1-ldd.log" 2>&1
    else
        record "${label}-cc1" 127 missing
    fi
}

ambient_gxx=$(command -v g++ || true)
probe_compiler ambient "$ambient_gxx"
probe_compiler system /usr/bin/g++
probe_compiler advertised /opt/modules/devel/gcc/11.2.0/bin/g++

compile_and_run() {
    label=$1
    compiler=$2
    binary="$build_dir/${label}"
    compile_log="$result_dir/${label}-compile.log"
    run_log="$result_dir/${label}-run.log"
    if [ "$compiler" = ambient ]; then
        timeout 90 "$cuda_root/bin/nvcc" -O2 -std=c++17 \
            jobs/cuda_smoke.cu -o "$binary" >"$compile_log" 2>&1
    elif [ -x "$compiler" ]; then
        timeout 90 "$cuda_root/bin/nvcc" -ccbin="$compiler" -O2 -std=c++17 \
            jobs/cuda_smoke.cu -o "$binary" >"$compile_log" 2>&1
    else
        record "${label}-compile" 127 compiler-missing
        return
    fi
    compile_status=$?
    record "${label}-compile" "$compile_status" node03
    if [ "$compile_status" -eq 0 ] && [ -x "$binary" ]; then
        sha256sum "$binary" >"$result_dir/${label}-binary.sha256"
        timeout 60 "$binary" >"$run_log" 2>&1
        run_status=$?
        record "${label}-run" "$run_status" node-built
    fi
}

set +e
compile_and_run C0-node ambient
compile_and_run C1-node /usr/bin/g++
compile_and_run C2-node /opt/modules/devel/gcc/11.2.0/bin/g++

for binary in prestaged/C?-login; do
    [ -x "$binary" ] || continue
    label=${binary##*/}
    timeout 60 "$binary" >"$result_dir/${label}-run.log" 2>&1
    record "${label}-run" $? prestaged
done
set -e

sha256sum jobs/cuda_smoke.cu "$matrix" >"$result_dir/result-manifest.sha256"
find "$result_dir" -maxdepth 1 -type f ! -name result-manifest.sha256 -print0 |
    sort -z | xargs -0 -r sha256sum >>"$result_dir/result-manifest.sha256"
cat "$matrix"
printf 'd1=complete\n'
