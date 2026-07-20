#!/bin/sh
set -eu
umask 077

job_local=${1:?supervised job-local root required}
role=${2:?role required}
run_id=${3:?run identity required}
job_id=${4:?job identity required}
node=${5:?node identity required}
marker_sha=${6:?owner marker identity required}
admission_receipt=${7:?submission admission receipt required}
run_root=$PWD
output=$run_root/results/control-materialization
environment=$job_local/runtime/environment

mkdir -p -- "$run_root/slurm" "$output" "$job_local/corpus"
printf '%s\n' 'recovery not invoked' >"$run_root/slurm/toolkit-recovery.0.out"
printf '%s\n' 'recovery not invoked' >"$run_root/slurm/toolkit-recovery.0.err"

./bootstrap_environment.sh "$job_local" "$output" "$run_id" "$role" \
  "$job_id" "$node" "$marker_sha" "$admission_receipt"

unset PYTHONPATH PYTHONHOME LD_LIBRARY_PATH
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export PATH=$environment/bin:/usr/bin:/bin
export PIP_CACHE_DIR=$job_local/pip-cache
export PYTHONNOUSERSITE=1
export TMPDIR=$job_local/tmp
export TORCH_HOME=$job_local/torch-cache
export XDG_CACHE_HOME=$job_local/cache
[ "$CUBLAS_WORKSPACE_CONFIG" = :4096:8 ]
[ "$PATH" = "$environment/bin:/usr/bin:/bin" ]
[ "$PIP_CACHE_DIR" = "$job_local/pip-cache" ]
[ "$PYTHONNOUSERSITE" = 1 ]
[ "$TMPDIR" = "$job_local/tmp" ]
[ "$TORCH_HOME" = "$job_local/torch-cache" ]
[ "$XDG_CACHE_HOME" = "$job_local/cache" ]
[ -z "${PYTHONPATH+x}" ] && [ -z "${PYTHONHOME+x}" ] && \
  [ -z "${LD_LIBRARY_PATH+x}" ]

tar -xf "$run_root/corpus.tar" -C "$job_local"

stderr=$output/materialize-controls.stderr.part
if ! "$environment/bin/python" "$run_root/materialize_controls.py" \
  --run-root "$run_root" --corpus "$job_local/corpus" --output "$output" \
  2>"$stderr"; then
  sed "s|$run_root|[REMOTE_RUN_ROOT]|g; s|$job_local|[JOB_LOCAL]|g" \
    "$stderr" >&2 || true
  exit 1
fi
rm -f -- "$stderr"
"$environment/bin/python" - "$output/calendar-preflight.json" \
  "$run_root/calendar-control-expectation.json" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as stream:
    actual = json.load(stream)
with open(sys.argv[2], encoding="utf-8") as stream:
    expected = json.load(stream)
if actual != expected:
    raise SystemExit("control calendar preflight differs from inherited expectation")
PY
printf '%s\n' A10M5R12-CONTROLS-MATERIALIZED
