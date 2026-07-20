#!/usr/bin/python3.11
"""R14R2 admission wrapper with an immediate node03 four-L40 idle gate."""

from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

PORTFOLIO_ROLE = "continuous-distribution-head-factorial-portfolio"
SOURCE = Path(__file__).resolve().with_name("inherited_admission_checker.py")


def canonical(value: object) -> bytes:
    return json.dumps(value, separators=(",", ":"), sort_keys=True).encode()


def authenticated(value: dict) -> bool:
    semantic = dict(value)
    recorded = semantic.pop("record_sha256", None)
    return recorded == hashlib.sha256(canonical(semantic)).hexdigest()


def atomic_replace(path: Path, value: dict) -> None:
    semantic = dict(value)
    semantic.pop("record_sha256", None)
    semantic["record_sha256"] = hashlib.sha256(canonical(semantic)).hexdigest()
    temporary = path.with_name(path.name + f".promote.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as stream:
        json.dump(semantic, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def option(name: str) -> str:
    try:
        index = sys.argv.index(name)
        return sys.argv[index + 1]
    except (ValueError, IndexError) as error:
        raise RuntimeError(f"missing admission option: {name}") from error


def capture_occupancy(output: Path) -> dict:
    started = dt.datetime.now(dt.timezone.utc)
    sinfo = subprocess.run(
        ("sinfo", "--Node", "--noheader", "--nodes=node03", "--format=%N|%T|%G"),
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    ).stdout.strip().splitlines()
    active = subprocess.run(
        (
            "squeue",
            "--noheader",
            "--all",
            "--nodelist=node03",
            "--states=RUNNING,COMPLETING,CONFIGURING",
            "--format=%i|%T|%u|%b|%R",
        ),
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    ).stdout.strip().splitlines()
    finished = dt.datetime.now(dt.timezone.utc)
    gates = {
        "all_partition_active_allocation_absent": active == [],
        "capture_bounded_seconds": (finished - started).total_seconds() <= 15,
        "exact_node": len(sinfo) == 1 and sinfo[0].split("|", 1)[0] == "node03",
        "four_l40_inventory": len(sinfo) == 1 and "gpu:l40:4" in sinfo[0].lower(),
        "node_idle": len(sinfo) == 1 and sinfo[0].split("|")[1].lower().rstrip("~*+") == "idle",
    }
    record = {
        "active_allocations": active,
        "captured_at": finished.isoformat().replace("+00:00", "Z"),
        "gates": gates,
        "node": "node03",
        "record_type": "a10m5r14r2-immediate-pre-submit-occupancy",
        "schema_version": 1,
        "sinfo": sinfo,
        "valid": bool(gates) and all(gates.values()),
    }
    atomic_replace(output, record)
    return json.loads(output.read_text())


def main() -> None:
    target = option("--role")
    output = Path(option("--output"))
    remote_root = Path(option("--remote-run-root"))
    manifest = json.loads((remote_root / "asset-manifest.json").read_text())
    source_identity = {"bytes": SOURCE.stat().st_size, "sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest()}
    if source_identity != {
        key: manifest.get("assets", {}).get("inherited_admission_checker.py", {}).get(key)
        for key in ("bytes", "sha256")
    }:
        raise RuntimeError("inherited admission checker asset identity drift")
    spec = importlib.util.spec_from_file_location("r14r1_admission_checker", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load authenticated inherited admission checker")
    parent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parent)
    occupancy = None
    occupancy_path = output.with_name(f"{target}-occupancy.json")
    if target == PORTFOLIO_ROLE:
        occupancy = capture_occupancy(occupancy_path)
        if occupancy.get("valid") is not True or not authenticated(occupancy):
            raise RuntimeError("node03 immediate four-L40 occupancy gate failed")
    parent.main()
    receipt = json.loads(output.read_text())
    if not authenticated(receipt):
        raise RuntimeError("inherited admission receipt authentication failed")
    if target == PORTFOLIO_ROLE:
        state = json.loads(Path(option("--toolkit-state")).read_text())
        control = state.get("attempts", {}).get("control-materialization.0", {})
        control_result = control.get("result", {})
        control_gate_sha = control_result.get("gate_receipt_sha256")
        if not (
            control.get("state") == "RESULT_VALIDATED"
            and control.get("passed") is True
            and isinstance(control_gate_sha, str)
            and len(control_gate_sha) == 64
        ):
            raise RuntimeError("portfolio admission lacks authenticated control gate identity")
        receipt.setdefault("gates", {})["immediate_node03_four_l40_idle"] = True
        receipt["gates"]["control_gate_receipt_bound"] = True
        receipt.setdefault("input_identities", {})[
            "control_gate_receipt_sha256"
        ] = control_gate_sha
        receipt.setdefault("input_identities", {})["occupancy_receipt"] = {
            "bytes": occupancy_path.stat().st_size,
            "record_sha256": occupancy["record_sha256"],
            "sha256": hashlib.sha256(occupancy_path.read_bytes()).hexdigest(),
        }
        receipt["occupancy_captured_at"] = occupancy["captured_at"]
        receipt["occupancy_node"] = "node03"
        receipt["valid"] = bool(receipt["gates"]) and all(receipt["gates"].values())
        receipt["decision"] = "PASS" if receipt["valid"] else "FAIL"
        atomic_replace(output, receipt)


if __name__ == "__main__":
    main()
