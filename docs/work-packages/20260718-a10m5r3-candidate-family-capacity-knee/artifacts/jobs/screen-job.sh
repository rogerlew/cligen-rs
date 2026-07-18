#!/bin/sh
set -eu
umask 077

row_id=${1:?row ID required}
phase=${2:?phase required}
family=${3:?family or AUTO required}
capacity=${4:?capacity or slot required}
seed=${5:?seed required}
job_local=${6:?supervised job-local root required}
run_root=$PWD
output=$run_root/results/$row_id
runtime_root=$job_local/runtime/cpython
environment=$job_local/runtime/environment

if [ "$family" = AUTO ]; then
  set -- $(/usr/bin/python3 "$run_root/resolve.py" --phase "$phase" --slot "$capacity" --seed "$seed" --results "$run_root/results")
  family=$1
  capacity=$2
fi

unset PYTHONPATH PYTHONHOME LD_LIBRARY_PATH
export PYTHONNOUSERSITE=1 PIP_NO_INDEX=1 CUBLAS_WORKSPACE_CONFIG=:4096:8
export PATH=/usr/bin:/bin CC=/usr/bin/gcc CXX=/usr/bin/g++ CARGO_NET_OFFLINE=true
mkdir -p -- "$runtime_root" "$output" "$job_local/wheels" "$job_local/corpus" "$job_local/source" "$job_local/vendor" "$job_local/parameters"
tar -xzf "$run_root/runtime.tar.gz" --strip-components=1 -C "$runtime_root"
test "$("$runtime_root/bin/python3" --version 2>&1)" = "Python 3.11.15"
"$runtime_root/bin/python3" -m venv --copies "$environment"
tar -xf "$run_root/wheelhouse.tar" -C "$job_local/wheels"
"$environment/bin/python" -m pip install --disable-pip-version-check --no-index --require-hashes --find-links "$job_local/wheels/wheelhouse" -r "$run_root/requirements.lock" >"$job_local/pip-install.log" 2>&1
"$environment/bin/python" -m pip check >"$job_local/pip-check.log" 2>&1
tar -xf "$run_root/corpus.tar" -C "$job_local"
tar -xzf "$run_root/source.tar.gz" -C "$job_local"
tar -xzf "$run_root/cargo-vendor.tar.gz" -C "$job_local"
tar -xzf "$run_root/selected-parameters-v1.tar.gz" -C "$job_local/parameters"
tar -xJf "$run_root/rust-1.92.0-x86_64-unknown-linux-gnu.tar.xz" -C "$job_local"
"$job_local/rust-1.92.0-x86_64-unknown-linux-gnu/install.sh" --prefix="$job_local/rust-toolchain" --disable-ldconfig >/dev/null
mkdir -p "$job_local/source/.cargo"
printf '%s\n' '[source.crates-io]' 'replace-with = "vendored-sources"' '' '[source.vendored-sources]' 'directory = "../vendor"' >"$job_local/source/.cargo/config.toml"
export PATH="$job_local/rust-toolchain/bin:/usr/bin:/bin"
(cd "$job_local/source" && cargo build --release --locked --offline -p cligen --bin cligen)

trainer_stderr=$output/trainer.stderr.part
if ! "$environment/bin/python" "$run_root/train.py" --row-id "$row_id" --family "$family" --capacity "$capacity" --seed "$seed" --corpus "$job_local/corpus" --output "$output" 2>"$trainer_stderr"; then
  sed "s|$run_root|[REMOTE_RUN_ROOT]|g; s|$job_local|[JOB_LOCAL]|g" "$trainer_stderr" >&2 || true
  exit 1
fi
rm -f -- "$trainer_stderr"
printf '%s\n' "trainer-exited $row_id" >"$output/trainer-exited.marker"
worker_stderr=$output/cpu-worker.stderr.part
time_v=$output/cpu.time-v.txt
if ! env CUDA_VISIBLE_DEVICES= NVIDIA_VISIBLE_DEVICES=void OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 /usr/bin/time -v -o "$time_v" "$environment/bin/python" "$run_root/cpu_worker.py" --row-id "$row_id" --phase "$phase" --output "$output" --faithful-binary "$job_local/source/target/release/cligen" --parameters "$job_local/parameters/station-parameters" --trainer-exited-marker "$output/trainer-exited.marker" 2>"$worker_stderr"; then
  sed "s|$run_root|[REMOTE_RUN_ROOT]|g; s|$job_local|[JOB_LOCAL]|g" "$worker_stderr" >&2 || true
  exit 1
fi
rm -f -- "$worker_stderr"
"$environment/bin/python" "$run_root/finalize.py" --row-id "$row_id" --phase "$phase" --output "$output" --time-v "$time_v"
printf '%s\n' "A10M5R3-ROW-PASS $row_id $family $capacity $seed"
