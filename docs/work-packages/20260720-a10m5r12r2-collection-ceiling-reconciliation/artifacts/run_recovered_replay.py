#!/usr/bin/env python3
"""Replay the frozen A10M5R12 selector from R2-recovered evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any


HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent
REPO = PACKAGE.parents[2]
IDENTITIES = HERE / "frozen-parent-identities.json"
PARENT_PACKAGE = REPO / "docs/work-packages/20260719-a10m5r12r1-admission-materialization-remedy"
PREDECESSOR_COMMIT = "b3d4e81e5305d584dfe6609f418bc976e64165e0"
PREDECESSOR_RESULT = (
    "docs/work-packages/20260719-a10m5r11r2-comparator-burn-contract-remedy/"
    "artifacts/temporal-result.json"
)
PREDECESSOR_SHA256 = "656f23ce7b8ec64a96aa7eff98a162f12c57c8d51497fd4285d5eb7594d68a41"
BINARY = {"bytes": 57_004_072, "sha256": "615aba134dcb8878046640d9672d42f470982afd26df7e1b5f0ee4c2a1835e79"}
CORPUS = {"bytes": 224_040_960, "sha256": "8770e127f8413eedd47d50670c359e450988444a8c4d8d43ca5645619a1b0a17"}
SELECTOR_SOURCES = (
    "artifacts/jobs/temporal_select.py",
    "artifacts/jobs/temporal_metrics.py",
    "artifacts/temporal-contract.json",
    "artifacts/portfolio-contract.json",
    "artifacts/sites.json",
    "artifacts/calendar-control-expectation.json",
)
ALLOWED_TERMINALS = {
    "A10M5R12-TEMPORAL-READY",
    "HOLD-A10M5R12-NO-TEMPORALLY-ELIGIBLE-CANDIDATE",
}


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"), sort_keys=True).encode()


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON record is not an object: {path}")
    return value


def authenticated(value: dict[str, Any]) -> bool:
    semantic = dict(value)
    recorded = semantic.pop("record_sha256", None)
    return isinstance(recorded, str) and recorded == hashlib.sha256(canonical(semantic)).hexdigest()


def signed(value: dict[str, Any]) -> dict[str, Any]:
    output = dict(value)
    output["record_sha256"] = hashlib.sha256(canonical(value)).hexdigest()
    return output


def file_identity(path: Path) -> dict[str, Any]:
    if not path.is_absolute() or not path.is_file() or path.is_symlink() or path.stat().st_nlink != 1:
        raise RuntimeError(f"invalid input file: {path}")
    return {"bytes": path.stat().st_size, "sha256": digest(path)}


def git_bytes(commit: str, relative: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{commit}:{relative}"], cwd=REPO, check=True, capture_output=True
    ).stdout


def tree_identity(root: Path) -> dict[str, Any]:
    rows = [
        {"bytes": path.stat().st_size, "path": path.relative_to(root).as_posix(), "sha256": digest(path)}
        for path in sorted(item for item in root.rglob("*") if item.is_file())
    ]
    return {"file_count": len(rows), "semantic_sha256": hashlib.sha256(canonical(rows)).hexdigest()}


def published_source(parent_commit: str) -> str:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO, check=True, capture_output=True, text=True
    ).stdout.strip()
    upstream = subprocess.run(
        ["git", "rev-parse", "origin/main"], cwd=REPO, check=True, capture_output=True, text=True
    ).stdout.strip()
    if head != upstream:
        raise RuntimeError("replay source is not exact published main")
    if subprocess.run(["git", "merge-base", "--is-ancestor", parent_commit, head], cwd=REPO).returncode:
        raise RuntimeError("parent source is not an ancestor of published replay source")
    for path in (Path(__file__).resolve(), IDENTITIES):
        committed = git_bytes(head, path.relative_to(REPO).as_posix())
        if path.read_bytes() != committed:
            raise RuntimeError(f"replay source differs from published main: {path.name}")
    return head


def validate_recovery(config: dict[str, Any]) -> tuple[Path, dict[str, Any], str]:
    root = Path(config["recovery"]["output_root"])
    receipt_path = root / "collection-recovery.json"
    receipt = read(receipt_path)
    parent = config["parent"]
    if not (
        authenticated(receipt)
        and receipt.get("record_type") == "collection_recovery_receipt"
        and receipt.get("package_id") == config["recovery"]["package_id"]
        and receipt.get("source_commit") == parent["source_commit"]
        and receipt.get("parent_plan_id") == parent["plan_id"]
        and receipt.get("parent_run_id") == parent["run_id"]
        and receipt.get("state") == "RAW_COLLECTED_EQUIVALENT"
        and receipt.get("actual_gpu_minutes") == 0
        and receipt.get("parent_actual_gpu_minutes") == 99
        and receipt.get("remote_cleanup_performed") is False
    ):
        raise RuntimeError("collection recovery receipt identity failed")
    rows = receipt.get("files")
    if not isinstance(rows, list) or len(rows) != config["caps"]["archive_members"]:
        raise RuntimeError("recovered evidence manifest shape failed")
    logical_names: set[str] = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"bytes", "logical_name", "sha256"}:
            raise RuntimeError("recovered evidence manifest row failed")
        logical = row["logical_name"]
        path = PurePosixPath(logical)
        if path.is_absolute() or ".." in path.parts or logical in logical_names:
            raise RuntimeError("recovered evidence path failed")
        logical_names.add(logical)
        evidence = root / "evidence" / Path(*path.parts)
        if file_identity(evidence) != {"bytes": row["bytes"], "sha256": row["sha256"]}:
            raise RuntimeError(f"recovered evidence identity failed: {logical}")
    manifest_sha = hashlib.sha256(canonical(sorted(rows, key=lambda row: row["logical_name"]))).hexdigest()
    if receipt.get("recovered_evidence_manifest_sha256") != manifest_sha:
        raise RuntimeError("recovered evidence manifest semantic identity failed")
    return root, receipt, digest(receipt_path)


def extract_observations(corpus: Path, destination: Path, sites: list[dict[str, Any]]) -> dict[str, Any]:
    expected = {site["daymet_shard"]: site["daymet_shard_sha256"] for site in sites}
    members = {
        f"corpus/docs/work-packages/20260717-a10m1-corpus-role-freeze/raw/training/daymet-v2/{name}": name
        for name in expected
    }
    destination.mkdir(mode=0o700)
    found: set[str] = set()
    with tarfile.open(corpus, "r:") as archive:
        for member in archive:
            name = members.get(member.name)
            if name is None:
                continue
            if not member.isfile() or member.uid != 0 or member.gid != 0 or member.mode & 0o6000:
                raise RuntimeError(f"unsafe observation member: {member.name}")
            source = archive.extractfile(member)
            if source is None:
                raise RuntimeError(f"unreadable observation member: {member.name}")
            target = destination / name
            with source, target.open("xb") as output:
                shutil.copyfileobj(source, output)
            os.chmod(target, 0o600)
            if digest(target) != expected[name]:
                raise RuntimeError(f"observation identity failed: {name}")
            found.add(name)
    if found != set(expected):
        raise RuntimeError("observation shard set incomplete")
    rows = [{"name": name, **file_identity(destination / name)} for name in sorted(expected)]
    return {"files": rows, "semantic_sha256": hashlib.sha256(canonical(rows)).hexdigest()}


def verify_inputs(options: argparse.Namespace) -> tuple[dict[str, Any], Path, dict[str, Any]]:
    config = read(IDENTITIES)
    parent = config["parent"]
    published = published_source(parent["source_commit"])
    recovery_root, recovery, recovery_sha = validate_recovery(config)
    binary = file_identity(options.binary)
    corpus = file_identity(options.corpus)
    if binary != BINARY or corpus != CORPUS:
        raise RuntimeError("binary or corpus identity drift")
    runtime = json.loads(subprocess.run(
        [str(options.python), "-c", "import json,numpy,sys; print(json.dumps({'numpy':numpy.__version__,'python':sys.version.split()[0]}))"],
        check=True, capture_output=True, text=True,
    ).stdout)
    if runtime != {"numpy": "2.2.6", "python": "3.10.14"}:
        raise RuntimeError("evaluation runtime drift")
    predecessor = git_bytes(PREDECESSOR_COMMIT, PREDECESSOR_RESULT)
    if hashlib.sha256(predecessor).hexdigest() != PREDECESSOR_SHA256 or (REPO / PREDECESSOR_RESULT).read_bytes() != predecessor:
        raise RuntimeError("predecessor result identity drift")
    sources: dict[str, Any] = {}
    for relative in SELECTOR_SOURCES:
        path = PARENT_PACKAGE / relative
        committed = git_bytes(parent["source_commit"], path.relative_to(REPO).as_posix())
        if path.read_bytes() != committed:
            raise RuntimeError(f"selector source drift: {relative}")
        sources[relative] = {"bytes": len(committed), "sha256": hashlib.sha256(committed).hexdigest()}
    sites = read(PARENT_PACKAGE / "artifacts/sites.json")["sites"]
    observations = extract_observations(options.corpus, options.output_root / "observations", sites)
    inputs = {
        "binary": binary,
        "collection_recovery_record_sha256": recovery["record_sha256"],
        "collection_recovery_sha256": recovery_sha,
        "corpus": corpus,
        "data_root": tree_identity(options.data_root),
        "evaluation_runtime": {**runtime, "executable": file_identity(options.python.resolve())},
        "observations": observations,
        "predecessor_temporal_result": {"commit": PREDECESSOR_COMMIT, "sha256": PREDECESSOR_SHA256},
        "recovered_evidence_manifest_sha256": recovery["recovered_evidence_manifest_sha256"],
        "selector_sources": sources,
    }
    return config, recovery_root / "evidence", {"published_main_head": published, **inputs}


def selector_command(options: argparse.Namespace, neural_root: Path, scratch: Path, output: Path) -> list[str]:
    return [
        str(options.python), str(PARENT_PACKAGE / "artifacts/jobs/temporal_select.py"),
        "--binary", str(options.binary), "--data-root", str(options.data_root),
        "--observation-shards", str(options.output_root / "observations"),
        "--neural-root", str(neural_root), "--scratch", str(scratch), "--output", str(output),
        "--contract", str(PARENT_PACKAGE / "artifacts/temporal-contract.json"),
        "--portfolio-contract", str(PARENT_PACKAGE / "artifacts/portfolio-contract.json"),
        "--calendar-control-expectation", str(PARENT_PACKAGE / "artifacts/calendar-control-expectation.json"),
        "--sites", str(PARENT_PACKAGE / "artifacts/sites.json"),
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    options = parser.parse_args()
    config = read(IDENTITIES)
    options.output_root = Path(config["recovery"]["replay_receipt"]).parent
    if options.output_root.exists():
        raise RuntimeError("replay output root must be fresh")
    options.output_root.mkdir(parents=True, mode=0o700)
    try:
        config, neural_root, inputs = verify_inputs(options)
        outputs = []
        for name in ("pass-a", "pass-b"):
            root = options.output_root / name
            root.mkdir(mode=0o700)
            result = root / "temporal-result.json"
            subprocess.run(selector_command(options, neural_root, root / "scratch", result), check=True)
            outputs.append(result)
        if outputs[0].read_bytes() != outputs[1].read_bytes():
            raise RuntimeError("isolated selector replays differ")
        result = read(outputs[0])
        predecessor = read(REPO / PREDECESSOR_RESULT)
        terminal = result.get("terminal")
        if terminal not in ALLOWED_TERMINALS or result.get("protected_roles_opened") != []:
            raise RuntimeError("selector terminal or protected-role gate failed")
        if result.get("prism_provenance") != predecessor.get("prism_provenance"):
            raise RuntimeError("inherited comparator provenance drift")
        final = options.output_root / "temporal-result.json"
        shutil.copyfile(outputs[0], final)
        parent = config["parent"]
        identity = signed({
            "byte_identical": True,
            "inputs": inputs,
            "package_id": config["recovery"]["package_id"],
            "parent_package_id": parent["package_id"],
            "parent_plan_id": parent["plan_id"],
            "parent_run_id": parent["run_id"],
            "pass_a_result_sha256": digest(outputs[0]),
            "pass_b_result_sha256": digest(outputs[1]),
            "protected_roles_opened": [],
            "record_type": "a10m5r12r2_replay_identity",
            "replay_source_commit": inputs["published_main_head"],
            "result_bytes": final.stat().st_size,
            "schema_version": "a10m5r12r2-replay-identity-1",
            "source_commit": parent["source_commit"],
            "temporal_result_sha256": digest(final),
            "terminal": terminal,
        })
        Path(config["recovery"]["replay_receipt"]).write_bytes(json.dumps(identity, indent=2, sort_keys=True).encode() + b"\n")
        print(terminal)
    except BaseException:
        if options.output_root.exists():
            shutil.rmtree(options.output_root)
        raise


if __name__ == "__main__":
    main()
