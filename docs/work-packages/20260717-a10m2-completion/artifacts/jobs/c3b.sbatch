#!/bin/bash
#SBATCH --job-name=a10m2c-c3b
#SBATCH --partition=gpu-icrews
#SBATCH --gres=gpu:l40:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:02:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

set -euo pipefail
python=/opt/modules/devel/python/3.8.11/bin/python3.8
test -x "$python"
unset PYTHONPATH PYTHONHOME
export PYTHONNOUSERSITE=1
export LD_LIBRARY_PATH=/opt/modules/devel/python/3.8.11/lib
test -s checkpoints/c3-state.json
result_dir="results/c3b/${SLURM_JOB_ID}"
mkdir -p "$result_dir"
nvidia-smi --query-gpu=name --format=csv,noheader
"$python" jobs/restart_state.py resume checkpoints/c3-state.json |
    tee "$result_dir/resume.json"
sha256sum checkpoints/c3-state.json "$result_dir/resume.json" \
    >"$result_dir/sha256.txt"
printf 'c3b=pass\n'
