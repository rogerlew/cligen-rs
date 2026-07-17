#!/bin/bash
#SBATCH --job-name=a10m2c-c1
#SBATCH --partition=gpu-icrews
#SBATCH --gres=gpu:l40:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:15:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

set -euo pipefail
python_root=/opt/modules/devel/python/3.11.11
cuda_root=/usr/local/cuda-12.8
python="$python_root/bin/python"
test -x "$python"
test -x "$cuda_root/bin/nvcc"
test -x /usr/bin/g++
export PATH="$cuda_root/bin:$python_root/bin:/usr/bin:/bin"
export LD_LIBRARY_PATH="$cuda_root/lib64:$python_root/lib:${LD_LIBRARY_PATH:-}"

result_dir="results/c1/${SLURM_JOB_ID}"
local_root=${SLURM_TMPDIR:-${TMPDIR:-/tmp}}
local_root=${local_root%/}
local_dir="$local_root/a10m2c-c1-${SLURM_JOB_ID}"
test "$local_dir" = "$local_root/a10m2c-c1-${SLURM_JOB_ID}"
test ! -e "$local_dir"
mkdir -p "$result_dir" checkpoints/stage2 inputs/a10m1 "$local_dir"
cleanup() {
    test "$local_dir" = "$local_root/a10m2c-c1-${SLURM_JOB_ID}"
    rm -rf "$local_dir"
    test ! -e "$local_dir"
    printf 'job_local_cleanup=pass\n'
}
trap cleanup EXIT

printf 'job=C1\n'
printf 'visible_gpu_count=%s\n' "$(nvidia-smi --query-gpu=name --format=csv,noheader | wc -l | tr -d ' ')"
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
"$cuda_root/bin/nvcc" --version | tail -n 1
/usr/bin/g++ --version | head -n 1
printf 'durable_fs_type=%s\n' "$(df -PT . | awk 'NR==2 {print $2}')"
printf 'local_fs_type=%s\n' "$(df -PT "$local_root" | awk 'NR==2 {print $2}')"
df -Pk . "$local_root" | awk 'NR == 1 || NR == 2 || NR == 4 {print}'

"$cuda_root/bin/nvcc" -ccbin=/usr/bin/g++ -O2 -std=c++17 \
    jobs/cuda_smoke.cu -o "$local_dir/cuda_smoke"
"$local_dir/cuda_smoke" | tee "$result_dir/cuda-smoke.txt"

corpus_sha=$("$python" -c 'import json,sys; print(json.load(open(sys.argv[1]))["a10m1-corpus.tar"]["sha256"])' environment/asset-manifest.json)
wheel_sha=$("$python" -c 'import json,sys; print(json.load(open(sys.argv[1]))["wheelhouse.tar"]["sha256"])' environment/asset-manifest.json)
printf '%s  %s\n' "$corpus_sha" assets/a10m1-corpus.tar | sha256sum -c -
printf '%s  %s\n' "$wheel_sha" assets/wheelhouse.tar | sha256sum -c -

tar -xf assets/a10m1-corpus.tar -C inputs/a10m1
cp assets/wheelhouse.tar "$local_dir/wheelhouse.tar"
tar -xf "$local_dir/wheelhouse.tar" -C "$local_dir"
"$python" jobs/verify_wheelhouse.py \
    environment/wheelhouse-manifest.json "$local_dir/wheelhouse"

runtime_part="runtime/pytorch-${SLURM_JOB_ID}"
test ! -e runtime/pytorch
test ! -e "$runtime_part"
"$python" -m venv "$runtime_part"
"$runtime_part/bin/python" -m pip install \
    --disable-pip-version-check --no-index \
    --find-links="$local_dir/wheelhouse" --require-hashes \
    -r environment/requirements.lock
"$runtime_part/bin/python" -m pip check
mv "$runtime_part" runtime/pytorch

export A10M2_CHECKPOINT="checkpoints/c1-framework.pt"
runtime/pytorch/bin/python jobs/one_gpu_smoke.py | tee "$result_dir/framework.json"

"$python" jobs/stage2.py \
    --durable-root inputs/a10m1 \
    --manifest environment/a10m1-transfer-manifest.json \
    --archive assets/a10m1-corpus.tar \
    --archive-sha256 "$corpus_sha" \
    --local-dir "$local_dir/stage2" \
    --result "$result_dir/stage2.json" \
    --checkpoint checkpoints/stage2/copyback-64m.bin

sha256sum "$A10M2_CHECKPOINT" checkpoints/stage2/copyback-64m.bin \
    "$result_dir/cuda-smoke.txt" "$result_dir/framework.json" \
    "$result_dir/stage2.json" >"$result_dir/sha256.txt"
printf 'c1=pass\n'
