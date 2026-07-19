#!/bin/sh
set -eu
umask 077

row_id=${1:?row ID required}
capacity=${2:?capacity required}
seed=${3:?training seed required}
job_local=${4:?supervised job-local root required}
run_root=$PWD
output=$run_root/results/$row_id
runtime_root=$job_local/runtime/cpython
environment=$job_local/runtime/environment

printf '%s\n' 'recovery not invoked' >"$run_root/slurm/toolkit-recovery.0.out"
printf '%s\n' 'recovery not invoked' >"$run_root/slurm/toolkit-recovery.0.err"

unset PYTHONPATH PYTHONHOME LD_LIBRARY_PATH
export PYTHONNOUSERSITE=1 PIP_NO_INDEX=1 CUBLAS_WORKSPACE_CONFIG=:4096:8
export PATH=/usr/bin:/bin CC=/usr/bin/gcc CXX=/usr/bin/g++
mkdir -p -- "$runtime_root" "$output" "$job_local/wheels" "$job_local/corpus"
tar -xzf "$run_root/runtime.tar.gz" --strip-components=1 -C "$runtime_root"
test "$("$runtime_root/bin/python3" --version 2>&1)" = "Python 3.11.15"
"$runtime_root/bin/python3" -m venv --copies "$environment"
tar -xf "$run_root/wheelhouse.tar" -C "$job_local/wheels"
"$environment/bin/python" -m pip install --disable-pip-version-check --no-index \
  --require-hashes --find-links "$job_local/wheels/wheelhouse" \
  -r "$run_root/requirements.lock" >"$job_local/pip-install.log" 2>&1
"$environment/bin/python" -m pip check >"$job_local/pip-check.log" 2>&1
tar -xf "$run_root/corpus.tar" -C "$job_local"

trainer_stderr=$output/trainer.stderr.part
if ! "$environment/bin/python" "$run_root/train.py" \
  --row-id "$row_id" --family lognormal_wet_v2 --capacity "$capacity" \
  --seed "$seed" --corpus "$job_local/corpus" --output "$output" \
  2>"$trainer_stderr"; then
  sed "s|$run_root|[REMOTE_RUN_ROOT]|g; s|$job_local|[JOB_LOCAL]|g" "$trainer_stderr" >&2 || true
  exit 1
fi
rm -f -- "$trainer_stderr"
printf '%s\n' "trainer-exited $row_id" >"$output/trainer-exited.marker"

generator_stderr=$output/generator.stderr.part
if ! env CUDA_VISIBLE_DEVICES= NVIDIA_VISIBLE_DEVICES=void \
  OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  NUMEXPR_NUM_THREADS=1 "$environment/bin/python" "$run_root/generate.py" \
  --row-id "$row_id" --contract "$run_root/temporal-contract.json" \
  --reconstruction-contract "$run_root/reconstruction-contract.json" \
  --sites "$run_root/sites.json" --output "$output" 2>"$generator_stderr"; then
  sed "s|$run_root|[REMOTE_RUN_ROOT]|g; s|$job_local|[JOB_LOCAL]|g" "$generator_stderr" >&2 || true
  exit 1
fi
rm -f -- "$generator_stderr"
printf '%s\n' "A10M5R4R2R1-MODEL-PASS $row_id $capacity $seed"
