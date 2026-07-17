#!/bin/bash
#SBATCH --job-name=a10m2-j2
#SBATCH --partition=gpu-icrews
#SBATCH --gres=gpu:l40:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:10:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

set -euo pipefail
module purge
module use /opt/modules/modulefiles
module load python/3.11.11

rm -rf runtime/pytorch
python -m venv runtime/pytorch
runtime/pytorch/bin/python -m pip install \
    --disable-pip-version-check --no-index --find-links=wheelhouse \
    --require-hashes -r environment/requirements.lock
runtime/pytorch/bin/python -m pip check

result_dir="results/j2/${SLURM_JOB_ID}"
mkdir -p "$result_dir" checkpoints
export A10M2_CHECKPOINT="checkpoints/j2-smoke.pt"
runtime/pytorch/bin/python jobs/j2_pytorch_smoke.py | tee "$result_dir/pytorch-smoke.json"
sha256sum "$A10M2_CHECKPOINT" "$result_dir/pytorch-smoke.json" |
    sed 's#  .*/#  #' >"$result_dir/sha256.txt"
printf 'j2_offline_reconstruction=pass\n'
