#!/bin/sh
set -eu
umask 077

job_local=${1:?supervised job-local root required}
run_root=$PWD
output=$run_root/results/memory-attribution
runtime_root=$job_local/runtime/cpython
environment=$job_local/runtime/environment
work=$job_local/diagnostic

unset PYTHONPATH PYTHONHOME LD_LIBRARY_PATH
export PYTHONNOUSERSITE=1 PIP_NO_INDEX=1 CUDA_VISIBLE_DEVICES=""
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export PATH=/usr/bin:/bin

mkdir -p -- "$runtime_root" "$output" "$job_local/wheels" "$work"
tar -xzf "$run_root/runtime.tar.gz" --strip-components=1 -C "$runtime_root"
test "$("$runtime_root/bin/python3" --version 2>&1)" = "Python 3.11.15"
"$runtime_root/bin/python3" -m venv --copies "$environment"
tar -xf "$run_root/wheelhouse.tar" -C "$job_local/wheels"
"$environment/bin/python" -m pip install --disable-pip-version-check --no-index --require-hashes \
  --find-links "$job_local/wheels/wheelhouse" -r "$run_root/requirements.lock" \
  >"$job_local/pip-install.log" 2>&1
"$environment/bin/python" -m pip check >"$job_local/pip-check.log" 2>&1

/usr/bin/time -v -o "$work/build.time-v.txt" \
  "$environment/bin/python" "$run_root/diagnose.py" build --work "$work"
for variant in import-only load-only eager jit-default jit-unoptimized jit-mkldnn-off jit-frozen; do
  /usr/bin/time -v -o "$work/$variant.time-v.txt" \
    "$environment/bin/python" "$run_root/diagnose.py" worker \
      --work "$work" --variant "$variant" --result "$work/$variant.json"
done
"$environment/bin/python" "$run_root/diagnose.py" aggregate \
  --work "$work" --output "$output/evidence.json.part"
printf '%s\n' A10M5R1-DIAGNOSTIC-COMPLETE
