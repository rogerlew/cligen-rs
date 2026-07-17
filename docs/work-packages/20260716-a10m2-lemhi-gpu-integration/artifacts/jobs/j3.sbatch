#!/bin/bash
#SBATCH --job-name=a10m2-j3
#SBATCH --partition=gpu-icrews
#SBATCH --gres=gpu:l40:2
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

set -euo pipefail
test -x runtime/pytorch/bin/torchrun
result_dir="results/j3/${SLURM_JOB_ID}"
mkdir -p "$result_dir"
export OMP_NUM_THREADS=4
export NCCL_DEBUG=WARN
runtime/pytorch/bin/torchrun --standalone --nproc-per-node=2 jobs/j3_ddp_smoke.py |
    tee "$result_dir/ddp-smoke.json"
sha256sum "$result_dir/ddp-smoke.json" |
    sed 's#  .*/#  #' >"$result_dir/sha256.txt"
