#!/bin/bash
#SBATCH --job-name=a10m2c-c3a
#SBATCH --partition=gpu-icrews
#SBATCH --gres=gpu:l40:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:02:00
#SBATCH --signal=B:USR1@90
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

set -euo pipefail
python=/opt/modules/devel/python/3.8.11/bin/python3.8
test -x "$python"
unset PYTHONPATH PYTHONHOME
export PYTHONNOUSERSITE=1
export LD_LIBRARY_PATH=/opt/modules/devel/python/3.8.11/lib
mkdir -p checkpoints results/c3a
nvidia-smi --query-gpu=name --format=csv,noheader

"$python" jobs/restart_state.py interrupt checkpoints/c3-state.json &
child=$!
forward_usr1() {
    kill -USR1 "$child"
}
trap forward_usr1 USR1
set +e
while kill -0 "$child" 2>/dev/null; do
    wait "$child"
    status=$?
done
set -e
if [ "${status:-0}" -ne 75 ]; then
    printf 'unexpected_child_status=%s\n' "${status:-0}" >&2
    exit 1
fi
cp checkpoints/c3-state.json results/c3a/checkpoint.json
sha256sum checkpoints/c3-state.json >results/c3a/sha256.txt
printf 'c3a_expected_interruption=pass\n'
exit 75
