#!/bin/sh
set -eu
umask 077

attempt_root=$1
run_root=$2
runtime_root=$run_root/runtime/cpython
environment=$run_root/runtime/environment
app_evidence=$run_root/app-evidence.json

unset PYTHONPATH PYTHONHOME LD_LIBRARY_PATH
export PYTHONNOUSERSITE=1 PIP_NO_INDEX=1 CARGO_NET_OFFLINE=true
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export CC=/usr/bin/gcc CXX=/usr/bin/g++

rm -rf -- "$run_root/runtime"
mkdir -p -- "$runtime_root" "$attempt_root/wheelhouse" "$attempt_root/source" "$attempt_root/vendor"
tar -xzf "$run_root/runtime.tar.gz" --strip-components=1 -C "$runtime_root"
test "$($runtime_root/bin/python3 --version 2>&1)" = "Python 3.11.15"
"$runtime_root/bin/python3" -m venv --copies "$environment"
tar -xf "$run_root/wheelhouse.tar" -C "$attempt_root/wheelhouse"
"$environment/bin/python" -m pip install --disable-pip-version-check --no-index --require-hashes \
  --find-links "$attempt_root/wheelhouse/wheelhouse" -r "$run_root/requirements.lock" >/dev/null
"$environment/bin/python" -m pip check >/dev/null

tar -xzf "$run_root/source.tar.gz" -C "$attempt_root"
tar -xzf "$run_root/cargo-vendor.tar.gz" -C "$attempt_root"
tar -xJf "$run_root/rust-1.92.0-x86_64-unknown-linux-gnu.tar.xz" -C "$attempt_root"
"$attempt_root/rust-1.92.0-x86_64-unknown-linux-gnu/install.sh" \
  --prefix="$attempt_root/toolchain" --disable-ldconfig >/dev/null
export PATH="$runtime_root/bin:$attempt_root/toolchain/bin:/usr/bin:/bin"

case "$(rustc --version)" in "rustc 1.92.0 "*) ;; *) exit 101 ;; esac
case "$(cargo --version)" in "cargo 1.92.0 "*) ;; *) exit 101 ;; esac
test -d "$attempt_root/toolchain/lib/rustlib/x86_64-unknown-linux-gnu/lib"
/usr/bin/g++ --version >/dev/null
mkdir -p "$attempt_root/source/.cargo"
printf '%s\n' '[source.crates-io]' 'replace-with = "vendored-sources"' '' \
  '[source.vendored-sources]' 'directory = "../vendor"' >"$attempt_root/source/.cargo/config.toml"
(cd "$attempt_root/source" && cargo metadata --locked --offline --format-version 1 >/dev/null)
(cd "$attempt_root/source" && cargo build --release --locked --offline -p cligen --bin cligen >/dev/null)
test -x "$attempt_root/source/target/release/cligen"

/usr/bin/ldd "$runtime_root/bin/python3" | grep -qv 'not found'
torch_extension=$(find "$environment/lib" -type f -path '*/torch/_C*.so' -print | head -n 1)
test -n "$torch_extension"
/usr/bin/ldd "$torch_extension" | grep -qv 'not found'

"$environment/bin/python" "$run_root/smoke.py" \
  --output "$app_evidence" \
  --configuration-sha256 5addee9c5db3592ee247eab2b5266ed5567fd9aaf24ed78dcb321ecbb001e22d

"$environment/bin/python" - "$app_evidence" <<'PY'
import json, os, sys
path = sys.argv[1]
with open(path, encoding="utf-8") as stream:
    value = json.load(stream)
value["gates"].update({
    "cargo_1_92_0": True,
    "rustc_1_92_0": True,
    "target_stdlib": True,
    "host_gxx": True,
    "loader_resolution": True,
    "cargo_metadata_locked_offline": True,
    "cargo_build_locked_offline": True,
    "source_vendor_relationship": True,
})
temporary = path + ".part"
with open(temporary, "w", encoding="utf-8") as stream:
    json.dump(value, stream, sort_keys=True); stream.write("\n")
os.replace(temporary, path)
PY
