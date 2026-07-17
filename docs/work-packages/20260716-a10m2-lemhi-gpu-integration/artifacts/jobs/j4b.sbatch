#!/bin/bash
#SBATCH --job-name=a10m2-j4b
#SBATCH --partition=gpu-icrews
#SBATCH --gres=gpu:l40:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

set -euo pipefail
module purge
module use /opt/modules/modulefiles
module load python/3.11.11
test -s checkpoints/j4-state.json
result_dir="results/j4b/${SLURM_JOB_ID}"
mkdir -p "$result_dir"
nvidia-smi --query-gpu=name --format=csv,noheader
python jobs/j4_state_machine.py resume checkpoints/j4-state.json |
    tee "$result_dir/resume.json"
sha256sum checkpoints/j4-state.json "$result_dir/resume.json" |
    sed 's#  .*/#  #' >"$result_dir/sha256.txt"
