#!/bin/bash

set -u
set -o pipefail
umask 077
ulimit -c 0

root=${1:-.}
cuda_root=/usr/local/cuda-12.8
source_file="$root/jobs/cuda_smoke.cu"
output_dir="$root/prestaged"
log_dir="$root/logs/prestage"
matrix="$root/prestage-matrix.tsv"

test -f "$source_file" || exit 2
test -x "$cuda_root/bin/nvcc" || exit 3
mkdir -p "$output_dir" "$log_dir"
printf 'configuration\tcompiler\tcompile_status\tbinary_sha256\n' >"$matrix"

compile_one() {
    label=$1
    compiler=$2
    binary="$output_dir/${label}"
    log="$log_dir/${label}.log"
    if [ "$compiler" = ambient ]; then
        compiler_identity=$(command -v g++ || true)
        timeout 90 "$cuda_root/bin/nvcc" -O2 -std=c++17 \
            "$source_file" -o "$binary" >"$log" 2>&1
    elif [ -x "$compiler" ]; then
        compiler_identity=$compiler
        timeout 90 "$cuda_root/bin/nvcc" -ccbin="$compiler" -O2 -std=c++17 \
            "$source_file" -o "$binary" >"$log" 2>&1
    else
        printf '%s\t%s\tmissing\t-\n' "$label" "$compiler" >>"$matrix"
        return
    fi
    status=$?
    if [ "$status" -eq 0 ] && [ -x "$binary" ]; then
        digest=$(sha256sum "$binary" | awk '{print $1}')
    else
        digest=-
    fi
    printf '%s\t%s\t%s\t%s\n' \
        "$label" "$compiler_identity" "$status" "$digest" >>"$matrix"
}

set +e
compile_one C0-login ambient
compile_one C1-login /usr/bin/g++
compile_one C2-login /opt/modules/devel/gcc/11.2.0/bin/g++
set -e
(
    cd "$root" || exit 1
    sha256sum jobs/cuda_smoke.cu prestage-matrix.tsv
    find prestaged -maxdepth 1 -type f -perm -100 -print0 |
        sort -z | xargs -0 -r sha256sum
) >"$root/prestage-manifest.sha256"
printf 'prestage=complete\n'
