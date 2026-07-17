#!/bin/bash
#SBATCH --job-name=a10m2c-c2
#SBATCH --partition=gpu-icrews
#SBATCH --gres=gpu:l40:2
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

set -euo pipefail
python_root=/opt/modules/devel/python/3.8.11
test -x "$python_root/bin/python3.8"
test -x runtime/pytorch/bin/torchrun
export PATH="$python_root/bin:/usr/bin:/bin"
export LD_LIBRARY_PATH="$python_root/lib:${LD_LIBRARY_PATH:-}"
export OMP_NUM_THREADS=4
export NCCL_DEBUG=WARN
result_dir="results/c2/${SLURM_JOB_ID}"
mkdir -p "$result_dir"
printf 'visible_gpu_count=%s\n' "$(nvidia-smi --query-gpu=name --format=csv,noheader | wc -l | tr -d ' ')"
nvidia-smi --query-gpu=index,uuid,name,driver_version --format=csv,noheader
runtime/pytorch/bin/torchrun --standalone --nproc-per-node=2 jobs/ddp_smoke.py |
    tee "$result_dir/ddp.json"
sha256sum "$result_dir/ddp.json" >"$result_dir/sha256.txt"
printf 'c2=pass\n'
