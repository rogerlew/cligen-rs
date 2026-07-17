#!/bin/bash
#SBATCH --job-name=a10m2-j1
#SBATCH --partition=gpu-icrews
#SBATCH --gres=gpu:l40:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:10:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

set -euo pipefail
cuda_root=/usr/local/cuda-12.8
test -x "$cuda_root/bin/nvcc"
export PATH="$cuda_root/bin:$PATH"
export LD_LIBRARY_PATH="$cuda_root/lib64:${LD_LIBRARY_PATH:-}"

result_dir="results/j1/${SLURM_JOB_ID}"
mkdir -p "$result_dir"
local_root=${SLURM_TMPDIR:-${TMPDIR:-/tmp}}
local_dir="${local_root}/a10m2-j1-${SLURM_JOB_ID}"
mkdir -p "$local_dir"
trap 'rm -rf "$local_dir"' EXIT

printf 'job=J1\n'
printf 'cuda_visible_device_count=%s\n' "$(nvidia-smi --query-gpu=name --format=csv,noheader | wc -l | tr -d ' ')"
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
nvcc --version | tail -1
printf 'durable_fs_type=%s\n' "$(df -PT . | awk 'NR==2 {print $2}')"
if [ -n "${SLURM_TMPDIR:-}" ]; then
    printf 'local_root_source=SLURM_TMPDIR\n'
elif [ -n "${TMPDIR:-}" ]; then
    printf 'local_root_source=TMPDIR\n'
else
    printf 'local_root_source=/tmp-fallback\n'
fi
printf 'local_fs_type=%s\n' "$(df -PT "$local_root" | awk 'NR==2 {print $2}')"

nvcc -O2 -std=c++17 jobs/j1_cuda_smoke.cu -o "$local_dir/j1_cuda_smoke"
"$local_dir/j1_cuda_smoke" | tee "$result_dir/cuda-smoke.txt"

dd if=/dev/zero of="$local_dir/local.bin" bs=1024 count=1024 status=none
cp "$local_dir/local.bin" "$result_dir/durable.bin"
cmp "$local_dir/local.bin" "$result_dir/durable.bin"
sha256sum "$result_dir/cuda-smoke.txt" "$result_dir/durable.bin" |
    sed 's#  .*/#  #' >"$result_dir/sha256.txt"
printf 'storage_copy=pass\n'
printf 'j1=pass\n'
