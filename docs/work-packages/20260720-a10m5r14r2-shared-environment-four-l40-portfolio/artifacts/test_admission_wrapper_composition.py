#!/usr/bin/env python3
"""Exercise the wrapper with the inherited materializer's exact CLI shape."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
WRAPPER = PACKAGE / "artifacts/jobs/admission_checker.py"
spec = importlib.util.spec_from_file_location("r14r2_admission_checker", WRAPPER)
assert spec and spec.loader
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


with tempfile.TemporaryDirectory(prefix="a10m5r14r2-admission-composition-") as raw:
    root = Path(raw)
    inherited = root / "inherited_admission_checker.py"
    marker = root / "inherited-executed"
    output = root / "admissions/control-materialization.json"
    source = f'''import hashlib, json, os, sys
from pathlib import Path
Path({str(marker)!r}).write_text("executed")
def main():
    target = Path(sys.argv[sys.argv.index("--output") + 1])
    target.parent.mkdir(parents=True, exist_ok=True)
    value = {{"role": sys.argv[sys.argv.index("--role") + 1], "valid": True}}
    value["record_sha256"] = hashlib.sha256(json.dumps(value, separators=(",", ":"), sort_keys=True).encode()).hexdigest()
    target.write_text(json.dumps(value))
'''
    inherited.write_text(source)
    manifest = {
        "assets": {
            "inherited_admission_checker.py": {
                "bytes": inherited.stat().st_size,
                "sha256": hashlib.sha256(inherited.read_bytes()).hexdigest(),
            }
        }
    }
    (root / "asset-manifest.json").write_text(json.dumps(manifest))
    checker.SOURCE = inherited
    sys.argv = [
        str(WRAPPER),
        "--contract", str(root / "job-local-capacity-contract.json"),
        "--asset-manifest", str(root / "asset-manifest.json"),
        "--toolkit-state", str(root / "admission-input/state.json"),
        "--publication-dir", str(root / "admission-input/publication"),
        "--remote-run-root", str(root),
        "--role", "control-materialization",
        "--output", str(output),
    ]
    checker.main()
    assert marker.read_text() == "executed"
    assert checker.authenticated(json.loads(output.read_text()))
    assert json.loads(output.read_text())["role"] == "control-materialization"

    marker.unlink()
    inherited.write_text(source + "# identity drift\n")
    try:
        checker.main()
    except RuntimeError as error:
        assert "asset identity drift" in str(error)
    else:
        raise AssertionError("tampered inherited checker was executed")
    assert not marker.exists()

print("A10M5R14R2-ADMISSION-WRAPPER-COMPOSITION-PASS")
