#!/bin/sh
set -eu
umask 077

job_local=${1:?supervised job-local root required}
role=${2:?role required}
candidate=${3:?candidate required}
capacity=${4:?capacity required}
run_root=$PWD
output=$run_root/results/$role
controls=$run_root/results/control-materialization
runtime_root=$job_local/runtime/cpython
environment=$job_local/runtime/environment

test -f "$controls/control-summary.json"
mkdir -p -- "$runtime_root" "$output" "$job_local/wheels" "$job_local/corpus"
unset PYTHONPATH PYTHONHOME LD_LIBRARY_PATH
export PYTHONNOUSERSITE=1 PIP_NO_INDEX=1 CUBLAS_WORKSPACE_CONFIG=:4096:8
export PATH=/usr/bin:/bin CC=/usr/bin/gcc CXX=/usr/bin/g++
tar -xzf "$run_root/runtime.tar.gz" --strip-components=1 -C "$runtime_root"
test "$("$runtime_root/bin/python3" --version 2>&1)" = "Python 3.11.15"
"$runtime_root/bin/python3" -m venv --copies "$environment"
tar -xf "$run_root/wheelhouse.tar" -C "$job_local/wheels"
"$environment/bin/python" -m pip install --disable-pip-version-check --no-index \
  --require-hashes --find-links "$job_local/wheels/wheelhouse" \
  -r "$run_root/requirements.lock" >"$job_local/pip-install.log" 2>&1
"$environment/bin/python" -m pip check >"$job_local/pip-check.log" 2>&1
tar -xf "$run_root/corpus.tar" -C "$job_local"

stderr=$output/candidate-experiment.stderr.part
if ! "$environment/bin/python" "$run_root/candidate_experiment.py" \
  --run-root "$run_root" --corpus "$job_local/corpus" --controls "$controls" \
  --candidate "$candidate" --capacity "$capacity" --output "$output" \
  2>"$stderr"; then
  sed "s|$run_root|[REMOTE_RUN_ROOT]|g; s|$job_local|[JOB_LOCAL]|g" \
    "$stderr" >&2 || true
  exit 1
fi
rm -f -- "$stderr"
printf '%s\n' "A10M5R10-CANDIDATE-COMPLETE role=$role"
