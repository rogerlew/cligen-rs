#!/bin/sh
#SBATCH --export=NONE
set -eu
umask 077

run_root=$PWD
runtime_root=$run_root/runtime/cpython
environment=$run_root/runtime/environment
job_local=${TMPDIR:-/tmp}/a10m4-qualification-$SLURM_JOB_ID
evidence_partial=$run_root/evidence.json.part
evidence_final=$run_root/evidence.json

write_failure_receipt() {
  status=$?
  trap - EXIT
  if [ "$status" -ne 0 ] && [ -x "$runtime_root/bin/python3" ]; then
    "$runtime_root/bin/python3" - "$evidence_partial" "$evidence_final" "$status" <<'PY' || true
import json, os, sys
partial, final, status = sys.argv[1:]
if os.path.exists(partial):
    with open(partial, encoding="utf-8") as stream:
        value = json.load(stream)
else:
    value = {"classification": "development-only-implementation-qualification", "gates": {"job_completed": False}}
value["exit_code"] = int(status)
value["verdict"] = "FAIL"
temporary = final + ".failure"
with open(temporary, "w", encoding="utf-8") as stream:
    json.dump(value, stream, indent=2, sort_keys=True); stream.write("\n")
os.replace(temporary, final)
if os.path.exists(partial): os.unlink(partial)
root = os.path.dirname(final)
for name in ("benchmark.json", "checkpoint.json", "resource.json"):
    destination = os.path.join(root, name)
    if not os.path.exists(destination):
        temporary = destination + ".failure"
        with open(temporary, "w", encoding="utf-8") as stream:
            json.dump({"status": "unavailable_due_to_failed_attempt"}, stream, sort_keys=True)
            stream.write("\n")
        os.replace(temporary, destination)
PY
  fi
  exit "$status"
}
trap write_failure_receipt EXIT

unset PYTHONPATH PYTHONHOME LD_LIBRARY_PATH
export PYTHONNOUSERSITE=1 PIP_NO_INDEX=1
export PATH=/usr/bin:/bin
export CC=/usr/bin/gcc CXX=/usr/bin/g++
export CARGO_NET_OFFLINE=true

rm -rf -- "$run_root/runtime"
mkdir -p -- "$runtime_root" "$job_local" "$run_root/checkpoint"
tar -xzf "$run_root/runtime.tar.gz" --strip-components=1 -C "$runtime_root"
test "$($runtime_root/bin/python3 --version 2>&1)" = "Python 3.11.15"
"$runtime_root/bin/python3" -m venv --copies "$environment"
tar -xf "$run_root/wheelhouse.tar" -C "$job_local"
"$environment/bin/python" -m pip install --disable-pip-version-check --no-index --require-hashes \
  --find-links "$job_local/wheelhouse" -r "$run_root/requirements.lock" >"$job_local/pip-install.log" 2>&1
"$environment/bin/python" -m pip check >"$job_local/pip-check.log" 2>&1

mkdir -p "$job_local/corpus" "$job_local/source" "$job_local/vendor" "$job_local/parameters"
tar -xf "$run_root/corpus.tar" -C "$job_local"
tar -xzf "$run_root/source.tar.gz" -C "$job_local"
tar -xzf "$run_root/cargo-vendor.tar.gz" -C "$job_local"
tar -xzf "$run_root/selected-parameters-v1.tar.gz" -C "$job_local/parameters"
tar -xJf "$run_root/cargo-1.92.0-x86_64-unknown-linux-gnu.tar.xz" -C "$job_local"
mkdir -p "$job_local/source/.cargo"
printf '%s\n' '[source.crates-io]' 'replace-with = "vendored-sources"' '' \
  '[source.vendored-sources]' 'directory = "../../vendor"' >"$job_local/source/.cargo/config.toml"
export PATH="$job_local/cargo-1.92.0-x86_64-unknown-linux-gnu/cargo/bin:/usr/bin:/bin"
(cd "$job_local/source" && cargo build --release --locked --offline -p cligen --bin cligen)
faithful_binary=$job_local/source/target/release/cligen
test -x "$faithful_binary"

common_args="--corpus $job_local/corpus --checkpoint $run_root/checkpoint/qualification.pt --expected $run_root/checkpoint/expected.pt --train-result $run_root/train.json"
# shellcheck disable=SC2086
"$environment/bin/python" "$run_root/qualify.py" train $common_args

# A distinct process restores on the same L40 and reproduces update 2 exactly.
# shellcheck disable=SC2086
"$environment/bin/python" "$run_root/qualify.py" restart $common_args \
  --checkpoint-result "$run_root/checkpoint.json" \
  --resumed-state "$run_root/checkpoint/resumed.pt"

export CUDA_VISIBLE_DEVICES=""
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
# shellcheck disable=SC2086
"$environment/bin/python" "$run_root/qualify.py" benchmark $common_args \
  --checkpoint-result "$run_root/checkpoint.json" \
  --resumed-state "$run_root/checkpoint/resumed.pt" \
  --benchmark "$run_root/benchmark.json" \
  --resource-result "$run_root/resource.json" \
  --evidence "$evidence_partial" \
  --export "$run_root/model-export.pt" \
  --faithful-binary "$faithful_binary" \
  --parameters "$job_local/parameters/station-parameters" \
  --work "$job_local/benchmark"

rm -rf -- "$job_local"
test ! -e "$job_local"
"$environment/bin/python" - "$evidence_partial" "$evidence_final" <<'PY'
import json, os, sys
partial, final = sys.argv[1:]
with open(partial, encoding="utf-8") as stream: value = json.load(stream)
value["gates"]["job_local_cleanup"] = True
value["gates"]["offline_hash_install"] = True
value["gates"]["job_completed"] = True
value["verdict"] = "PASS" if all(value["gates"].values()) else "FAIL"
temporary = final + ".promote"
with open(temporary, "w", encoding="utf-8") as stream:
    json.dump(value, stream, indent=2, sort_keys=True); stream.write("\n")
os.replace(temporary, final); os.unlink(partial)
if value["verdict"] != "PASS": raise SystemExit("final gate failed")
PY
printf '%s\n' A10M4-QUALIFICATION-PASS
