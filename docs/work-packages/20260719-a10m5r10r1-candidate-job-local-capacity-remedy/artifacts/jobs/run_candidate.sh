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
/usr/bin/python3 -c \
  'import json,sys; assert json.load(open(sys.argv[1], encoding="utf-8")).get("valid") is True' \
  "$controls/evidence.json"
mkdir -p -- "$output" "$job_local/corpus"
./bootstrap_environment.sh "$job_local" "$output" "$run_id" "$role" \
  "$job_id" "$node" "$marker_sha" "$admission_receipt"
tar -xf "$run_root/corpus.tar" -C "$job_local/corpus"

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
printf '%s\n' "A10M5R10R1-CANDIDATE-COMPLETE role=$role"
