#!/bin/sh
set -eu
umask 077

job_local=${1:?job-local root required}
output=${2:?output required}
role=${3:?role required}
world=${4:?world required}
mode=${5:?mode required}
run_root=$PWD
runtime_root=$job_local/runtime/cpython
environment=$job_local/runtime/environment

unset PYTHONPATH PYTHONHOME LD_LIBRARY_PATH
export PYTHONNOUSERSITE=1 PIP_NO_INDEX=1 CUBLAS_WORKSPACE_CONFIG=:4096:8
export PATH=/usr/bin:/bin CC=/usr/bin/gcc CXX=/usr/bin/g++
export NCCL_DEBUG=WARN TORCH_NCCL_ASYNC_ERROR_HANDLING=1
mkdir -p -- "$runtime_root" "$environment" "$job_local/wheels" "$output"
tar -xzf "$run_root/runtime.tar.gz" --strip-components=1 -C "$runtime_root"
test "$("$runtime_root/bin/python3" --version 2>&1)" = "Python 3.11.15"
"$runtime_root/bin/python3" -m venv --copies "$environment"
tar -xf "$run_root/wheelhouse.tar" -C "$job_local/wheels"
"$environment/bin/python" -m pip install --disable-pip-version-check --no-index \
  --require-hashes --find-links "$job_local/wheels/wheelhouse" \
  -r "$run_root/requirements.lock" >"$job_local/pip-install.log" 2>&1
"$environment/bin/python" -m pip check >"$job_local/pip-check.log" 2>&1

if [ "$mode" = success ]; then
  exec "$environment/bin/torchrun" --standalone --nnodes=1 \
    --nproc-per-node="$world" "$run_root/qualify.py" \
    --expected-world "$world" --output "$output" --role "$role"
fi
exec "$environment/bin/torchrun" --standalone --nnodes=1 \
  --nproc-per-node=2 "$run_root/rank_failure.py" --output "$output"
