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
printf '%s\n' A10M5R10R1R3-CONTROLS-MATERIALIZED
