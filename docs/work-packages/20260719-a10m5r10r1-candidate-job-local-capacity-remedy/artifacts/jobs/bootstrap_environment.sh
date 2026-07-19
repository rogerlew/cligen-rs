#!/bin/sh
set -eu

job_local=${1:?supervised job-local root required}
output=${2:?durable output root required}
run_id=${3:?run identity required}
role=${4:?role required}
job_id=${5:?job identity required}
node=${6:?node identity required}
marker_sha=${7:?owner marker identity required}
admission_receipt=${8:?submission admission receipt required}
run_root=$PWD
runtime_root=$job_local/runtime/cpython
environment=$job_local/runtime/environment
setup_json=$output/setup.json
setup_log=$output/setup.log
step_log=$job_local/setup-step.log
runtime_version_exit=125
pip_install_exit=125
pip_check_exit=125

mkdir -p -- "$runtime_root" "$output" "$job_local/wheels" \
  "$job_local/tmp" "$job_local/pip-cache" "$job_local/cache" \
  "$job_local/torch-cache"
: >"$setup_log"

unset PYTHONPATH PYTHONHOME LD_LIBRARY_PATH
export PYTHONNOUSERSITE=1 PIP_NO_INDEX=1 PIP_NO_CACHE_DIR=1
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export PATH=/usr/bin:/bin CC=/usr/bin/gcc CXX=/usr/bin/g++
export TMPDIR=$job_local/tmp
export PIP_CACHE_DIR=$job_local/pip-cache
export XDG_CACHE_HOME=$job_local/cache
export TORCH_HOME=$job_local/torch-cache

record_setup() {
  stage=$1
  ready=${2:-false}
  ready_option=
  [ "$ready" = true ] && ready_option=--ready-for-science
  /usr/bin/python3 "$run_root/setup_diagnostics.py" record \
    --output "$setup_json" --stage "$stage" --run-root "$run_root" \
    --job-local "$job_local" --wheel-archive "$run_root/wheelhouse.tar" \
    --runtime-archive "$run_root/runtime.tar.gz" \
    --requirements "$run_root/requirements.lock" \
    --asset-manifest "$run_root/asset-manifest.json" \
    --admission-receipt "$admission_receipt" --run-id "$run_id" \
    --role "$role" --job-id "$job_id" --node "$node" \
    --owner-marker-sha256 "$marker_sha" \
    --runtime-version-exit "$runtime_version_exit" \
    --pip-install-exit "$pip_install_exit" \
    --pip-check-exit "$pip_check_exit" $ready_option
}

run_logged() {
  label=$1
  shift
  set +e
  "$@" >"$step_log" 2>&1
  step_status=$?
  set -e
  /usr/bin/python3 "$run_root/setup_diagnostics.py" log \
    --output "$setup_log" --source "$step_log" --label "$label" \
    --run-root "$run_root" --job-local "$job_local"
  rm -f -- "$step_log"
  return "$step_status"
}

record_setup initialized false
/usr/bin/python3 -c \
  'import json,sys; value=json.load(open(sys.argv[1], encoding="utf-8")); assert value.get("authentication") and all(value["authentication"].values())' \
  "$setup_json"

if run_logged runtime-extract tar -xzf "$run_root/runtime.tar.gz" \
  --strip-components=1 -C "$runtime_root"; then
  :
else
  status=$?
  record_setup runtime-extract-failed false
  exit "$status"
fi

if run_logged runtime-version "$runtime_root/bin/python3" --version; then
  version=$("$runtime_root/bin/python3" --version 2>&1 || true)
  if [ "$version" = "Python 3.11.15" ]; then
    runtime_version_exit=0
  else
    runtime_version_exit=65
  fi
else
  runtime_version_exit=$?
fi
if [ "$runtime_version_exit" -ne 0 ]; then
  record_setup runtime-version-failed false
  exit "$runtime_version_exit"
fi

if run_logged environment-create "$runtime_root/bin/python3" -m venv \
  --copies "$environment"; then
  :
else
  status=$?
  record_setup environment-create-failed false
  exit "$status"
fi

if run_logged wheelhouse-extract tar -xf "$run_root/wheelhouse.tar" \
  -C "$job_local/wheels"; then
  :
else
  status=$?
  record_setup wheelhouse-extract-failed false
  exit "$status"
fi

if run_logged pip-install "$environment/bin/python" -m pip install \
  --disable-pip-version-check --no-index --no-cache-dir --require-hashes \
  --find-links "$job_local/wheels/wheelhouse" \
  -r "$run_root/requirements.lock"; then
  pip_install_exit=0
else
  pip_install_exit=$?
  record_setup pip-install-failed false
  exit "$pip_install_exit"
fi

if run_logged pip-check "$environment/bin/python" -m pip check; then
  pip_check_exit=0
else
  pip_check_exit=$?
  record_setup pip-check-failed false
  exit "$pip_check_exit"
fi

record_setup verified-install false
rm -rf -- "$job_local/wheels" "$job_local/pip-cache"
if [ -e "$job_local/wheels" ] || [ -e "$job_local/pip-cache" ]; then
  record_setup setup-payload-deletion-failed false
  exit 73
fi
record_setup ready-for-science true
test -s "$setup_json"
test -f "$setup_log"

printf '%s\n' A10M5R10R1-ENVIRONMENT-READY
