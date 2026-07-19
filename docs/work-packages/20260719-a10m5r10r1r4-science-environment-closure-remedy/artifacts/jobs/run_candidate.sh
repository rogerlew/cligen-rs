#!/bin/sh
set -eu
umask 077

job_local=${1:?supervised job-local root required}
role=${2:?role required}
candidate=${3:?candidate required}
capacity=${4:?capacity required}
run_id=${5:?run identity required}
job_id=${6:?job identity required}
node=${7:?node identity required}
marker_sha=${8:?owner marker identity required}
admission_receipt=${9:?submission admission receipt required}
run_root=$PWD
output=$run_root/results/$role
controls=$run_root/results/control-materialization
environment=$job_local/runtime/environment

test -f "$controls/control-summary.json"
test -f "$controls/evidence.json"
mkdir -p -- "$output" "$job_local/corpus"
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

"$environment/bin/python" -c \
  'import json,sys; assert json.load(open(sys.argv[1], encoding="utf-8")).get("valid") is True' \
  "$controls/evidence.json"
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
printf '%s\n' "A10M5R10R1R4-CANDIDATE-COMPLETE role=$role"
