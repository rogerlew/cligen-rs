#!/usr/bin/python3.11
"""R14R2R1 outer admission checker with composed-chain authentication."""

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
SLOTS = ["admission_checker.py", "inherited_admission_checker.py"]
PROTOCOL = "ordered-plan-assets-v1"
SOURCE = Path(__file__).resolve().with_name(SLOTS[1])


def canonical(value: object) -> bytes:
    return json.dumps(value, separators=(",", ":"), sort_keys=True).encode()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
        return sys.argv[sys.argv.index(name) + 1]
    except (ValueError, IndexError) as error:
        raise RuntimeError(f"missing admission option: {name}") from error


def current_plan(state: dict) -> tuple[str, dict]:
    current = state.get("current_plan_id")
    matches = [
        revision.get("semantic")
        for revision in state.get("plan_revisions", [])
        if isinstance(revision, dict) and revision.get("plan_id") == current
    ]
    if not (isinstance(current, str) and len(matches) == 1 and isinstance(matches[0], dict)):
        raise RuntimeError("current semantic plan missing, stale, or ambiguous")
    if hashlib.sha256(canonical(matches[0])).hexdigest() != current:
        raise RuntimeError("current semantic plan identity mismatch")
    return current, matches[0]


def checker_projection(
    state: dict,
    manifest: dict,
    remote_root: Path,
    own_file: Path,
    delegate_file: Path | None = None,
) -> dict:
    """Authenticate exact ordered slot 0/1 against plan, manifest, and bytes."""
    _, plan = current_plan(state)
    contract = plan.get("admission_materialization", {}).get("checker_assets")
    if contract != {"logical_names": SLOTS, "protocol": PROTOCOL}:
        raise RuntimeError("composed checker contract drift")
    root = remote_root.resolve()
    delegate = SOURCE if delegate_file is None else delegate_file
    try:
        own_name = own_file.resolve().relative_to(root).as_posix()
        delegate_name = delegate.resolve().relative_to(root).as_posix()
    except ValueError as error:
        raise RuntimeError("checker chain escapes exact remote root") from error
    if (
        own_file.is_symlink()
        or delegate.is_symlink()
        or own_file.stat().st_nlink != 1
        or delegate.stat().st_nlink != 1
        or [own_name, delegate_name] != SLOTS
    ):
        raise RuntimeError("checker chain slot or path identity drift")
    plan_assets = {
        item.get("logical_name"): item
        for item in plan.get("assets", [])
        if isinstance(item, dict) and isinstance(item.get("logical_name"), str)
    }
    manifest_assets = manifest.get("assets", {})
    projected = []
    for logical_name, path in zip(SLOTS, (own_file, delegate), strict=True):
        actual = {"bytes": path.stat().st_size, "sha256": digest(path)}
        planned = {key: plan_assets.get(logical_name, {}).get(key) for key in ("bytes", "sha256")}
        staged = {key: manifest_assets.get(logical_name, {}).get(key) for key in ("bytes", "sha256")}
        if actual != planned or actual != staged:
            raise RuntimeError(f"checker chain identity drift: {logical_name}")
        projected.append({"logical_name": logical_name, **actual})
    return {"assets": projected, "protocol": PROTOCOL}


def capture_occupancy(output: Path) -> dict:
    started = dt.datetime.now(dt.timezone.utc)
    sinfo = subprocess.run(("sinfo", "--Node", "--noheader", "--nodes=node03", "--format=%N|%T|%G"), check=True, capture_output=True, text=True, timeout=10).stdout.strip().splitlines()
    active = subprocess.run(("squeue", "--noheader", "--all", "--nodelist=node03", "--states=RUNNING,COMPLETING,CONFIGURING", "--format=%i|%T|%u|%b|%R"), check=True, capture_output=True, text=True, timeout=10).stdout.strip().splitlines()
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
        "record_type": "a10m5r14r2r1-immediate-pre-submit-occupancy",
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
    state = json.loads(Path(option("--toolkit-state")).read_text())
    manifest = json.loads((remote_root / "asset-manifest.json").read_text())
    projection = checker_projection(state, manifest, remote_root, Path(__file__))
    # Only authenticated slot 1 is imported; __file__ is never aliased.
    spec = importlib.util.spec_from_file_location("r14r2r1_inherited_admission_checker", SOURCE)
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
    receipt.setdefault("gates", {})["composed_checker_chain_authenticated"] = True
    receipt.setdefault("input_identities", {})["checker_assets"] = projection
    if target == PORTFOLIO_ROLE:
        control = state.get("attempts", {}).get("control-materialization.0", {})
        control_result = control.get("result", {})
        control_gate_sha = control_result.get("gate_receipt_sha256")
        if not (control.get("state") == "RESULT_VALIDATED" and control.get("passed") is True and isinstance(control_gate_sha, str) and len(control_gate_sha) == 64):
            raise RuntimeError("portfolio admission lacks authenticated control gate identity")
        receipt["gates"]["immediate_node03_four_l40_idle"] = True
        receipt["gates"]["control_gate_receipt_bound"] = True
        receipt["input_identities"]["control_gate_receipt_sha256"] = control_gate_sha
        receipt["input_identities"]["occupancy_receipt"] = {
            "bytes": occupancy_path.stat().st_size,
            "record_sha256": occupancy["record_sha256"],
            "sha256": digest(occupancy_path),
        }
        receipt["occupancy_captured_at"] = occupancy["captured_at"]
        receipt["occupancy_node"] = "node03"
    receipt["valid"] = bool(receipt["gates"]) and all(receipt["gates"].values())
    receipt["decision"] = "PASS" if receipt["valid"] else "FAIL"
    atomic_replace(output, receipt)


if __name__ == "__main__":
    main()
