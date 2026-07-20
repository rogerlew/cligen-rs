#!/bin/sh
set -eu
umask 077

job_local=${1:?supervised job-local root required}
run_id=${2:?run identity required}
job_id=${3:?job identity required}
node=${4:?node identity required}
marker_sha=${5:?owner marker identity required}
admission_receipt=${6:?submission admission receipt required}
run_root=$PWD
role=continuous-distribution-head-factorial-portfolio
output=$run_root/results/$role
environment=$job_local/runtime/environment
shared_corpus=$job_local/shared-corpus

test "$SLURMD_NODENAME" = node03
test -f "$run_root/results/control-materialization/evidence.json"
test -f "$run_root/portfolio-role-map.json"
mkdir -p -- "$output" "$job_local/storage-preflight" "$shared_corpus"

# Fail before expanding any asset unless the frozen shared-storage formula is
# satisfied on the exact filesystem that will hold the environment and corpus.
available_kb=$(df -Pk "$job_local" | awk 'NR==2 {print $4}')
available_inodes=$(df -Pi "$job_local" | awk 'NR==2 {print $4}')
test "$available_kb" -ge 16777216
test "$available_inodes" -ge 16000
printf '{"available_bytes":%s,"available_inodes":%s,"minimum_bytes":17179869184,"minimum_inodes":16000,"valid":true}\n' \
  "$((available_kb * 1024))" "$available_inodes" >"$output/storage-preflight.json"

./bootstrap_environment.sh "$job_local" "$output" "$run_id" "$role" \
  "$job_id" "$node" "$marker_sha" "$admission_receipt"

unset PYTHONPATH PYTHONHOME LD_LIBRARY_PATH
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export PATH=$environment/bin:/usr/bin:/bin
export PYTHONDONTWRITEBYTECODE=1
export PYTHONNOUSERSITE=1
tar -xf "$run_root/corpus.tar" -C "$shared_corpus"
test -d "$shared_corpus/corpus"
chmod -R a-w -- "$environment" "$shared_corpus"

restore_cleanup_permissions() {
  chmod -R u+w -- "$environment" "$shared_corpus"
  environment_writable=false
  corpus_writable=false
  [ -w "$environment" ] && environment_writable=true
  [ -w "$shared_corpus" ] && corpus_writable=true
  if [ "$environment_writable" = true ] && [ "$corpus_writable" = true ]; then
    printf '%s\n' '{"corpus_owner_writable":true,"environment_owner_writable":true,"restored_after_launcher":true,"schema_version":1,"valid":true}' \
      >"$output/cleanup-permissions.json"
  else
    printf '%s\n' '{"corpus_owner_writable":false,"environment_owner_writable":false,"restored_after_launcher":true,"schema_version":1,"valid":false}' \
      >"$output/cleanup-permissions.json"
  fi
}
trap restore_cleanup_permissions EXIT
set +e
"$environment/bin/python" "$run_root/portfolio_launcher.py" \
  --run-root "$run_root" --job-local "$job_local" \
  --environment "$environment" --shared-corpus "$shared_corpus/corpus" \
  --role-map "$run_root/portfolio-role-map.json"
launcher_status=$?
set -e
restore_cleanup_permissions
trap - EXIT
"$environment/bin/python" -c \
  'import json,sys; assert json.load(open(sys.argv[1], encoding="utf-8"))["valid"] is True' \
  "$output/cleanup-permissions.json"
exit "$launcher_status"
