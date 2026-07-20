#!/usr/bin/env python3
"""Run two isolated, identity-bound A10M5R12 temporal selector replays."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]
PACKAGE_ID = "20260719-a10m5r12-continuous-latent-temporal-process"
RUN_ID = "a10m5r12-continuous-latent-temporal-process-r0"
PREDECESSOR_COMMIT = "b3d4e81e5305d584dfe6609f418bc976e64165e0"
PREDECESSOR_RESULT_RELATIVE = (
    "docs/work-packages/20260719-a10m5r11r2-comparator-burn-contract-remedy/"
    "artifacts/temporal-result.json"
)
PREDECESSOR_RESULT_SHA256 = (
    "656f23ce7b8ec64a96aa7eff98a162f12c57c8d51497fd4285d5eb7594d68a41"
)
COMPARATOR_BINARY = {
    "bytes": 57004072,
    "sha256": "615aba134dcb8878046640d9672d42f470982afd26df7e1b5f0ee4c2a1835e79",
}
SOURCES = (
    "artifacts/run_temporal_replay.py",
    "artifacts/jobs/temporal_select.py",
    "artifacts/jobs/temporal_metrics.py",
    "artifacts/temporal-contract.json",
    "artifacts/portfolio-contract.json",
    "artifacts/sites.json",
    "artifacts/calendar-control-expectation.json",
)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def authenticated(value: dict[str, Any]) -> bool:
    recorded = value.get("record_sha256")
    semantic = dict(value)
    semantic.pop("record_sha256", None)
    return isinstance(recorded, str) and recorded == hashlib.sha256(
        canonical(semantic)
    ).hexdigest()


def git_bytes(commit: str, relative: str) -> bytes:
    return subprocess.run(
        ("git", "show", f"{commit}:{relative}"),
        cwd=REPO,
        check=True,
        capture_output=True,
    ).stdout


def tree_identity(root: Path) -> dict[str, Any]:
    rows = []
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        rows.append(
            {
                "bytes": path.stat().st_size,
                "path": path.relative_to(root).as_posix(),
                "sha256": digest(path),
            }
        )
    return {
        "file_count": len(rows),
        "semantic_sha256": hashlib.sha256(canonical(rows)).hexdigest(),
    }


def verify_inputs(options: argparse.Namespace) -> dict[str, Any]:
    head = subprocess.run(
        ("git", "rev-parse", "HEAD"), cwd=REPO, check=True, capture_output=True, text=True
    ).stdout.strip()
    upstream = subprocess.run(
        ("git", "rev-parse", "origin/main"), cwd=REPO, check=True, capture_output=True, text=True
    ).stdout.strip()
    if head != options.source_commit or upstream != options.source_commit:
        raise RuntimeError("selector source commit is not exact published main")
    actual_binary = {
        "bytes": options.binary.stat().st_size,
        "sha256": digest(options.binary),
    }
    if actual_binary != COMPARATOR_BINARY:
        raise RuntimeError("inherited comparator binary identity drift")
    predecessor_payload = git_bytes(PREDECESSOR_COMMIT, PREDECESSOR_RESULT_RELATIVE)
    predecessor_result_path = REPO / PREDECESSOR_RESULT_RELATIVE
    if (
        hashlib.sha256(predecessor_payload).hexdigest()
        != PREDECESSOR_RESULT_SHA256
        or predecessor_result_path.read_bytes() != predecessor_payload
    ):
        raise RuntimeError("inherited comparator result/provenance identity drift")
    runtime = json.loads(
        subprocess.run(
            (
                str(options.python),
                "-c",
                "import json,numpy,sys; print(json.dumps({'numpy':numpy.__version__,'python':sys.version.split()[0]}))",
            ),
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    )
    if runtime != {"numpy": "2.2.6", "python": "3.10.14"}:
        raise RuntimeError("local evaluation runtime version drift")
    sources = {}
    for package_relative in SOURCES:
        path = PACKAGE / package_relative
        repository_relative = path.relative_to(REPO).as_posix()
        committed = git_bytes(options.source_commit, repository_relative)
        if path.read_bytes() != committed:
            raise RuntimeError(f"selector source differs from commit: {package_relative}")
        sources[package_relative] = {
            "bytes": len(committed),
            "sha256": hashlib.sha256(committed).hexdigest(),
        }
    collection = read(options.collection)
    cleanup = read(options.cleanup)
    terminal = read(options.terminal)
    sanitized = collection.get("sanitized_files", [])
    sanitized_by_name = {
        row.get("logical_name"): row for row in sanitized if isinstance(row, dict)
    }
    collection_files_valid = (
        len(sanitized_by_name) == len(sanitized)
        and set(collection.get("present", [])) == set(sanitized_by_name)
    )
    for logical_name, expected in sanitized_by_name.items():
        path = options.neural_root / logical_name
        collection_files_valid = collection_files_valid and (
            path.is_file()
            and path.stat().st_size == expected.get("bytes")
            and digest(path) == expected.get("sha256")
        )
    if not (
        authenticated(collection)
        and collection.get("record_type") == "collection_receipt"
        and collection.get("package_id") == PACKAGE_ID
        and collection.get("run_id") == RUN_ID
        and collection.get("source_commit") == options.source_commit
        and collection.get("absent") == []
        and collection.get("download_promoted") is True
        and collection_files_valid
        and authenticated(cleanup)
        and cleanup.get("package_id") == PACKAGE_ID
        and cleanup.get("run_id") == RUN_ID
        and cleanup.get("source_commit") == options.source_commit
        and cleanup.get("remote_absent") is True
        and cleanup.get("job_local_cleanup") == "verified_absent"
        and authenticated(terminal)
        and terminal.get("package_id") == PACKAGE_ID
        and terminal.get("run_id") == RUN_ID
        and terminal.get("source_commit") == options.source_commit
        and terminal.get("terminal") == "LEMHI-TOOLKIT-RUN-CLOSED"
    ):
        raise RuntimeError("collection/cleanup/terminal receipt identity failed")
    temporal = read(PACKAGE / "artifacts/temporal-contract.json")
    for role in temporal["roles"]:
        admission = read(options.neural_root / "admissions" / f"{role['role_id']}.json")
        if admission.get("source_commit") != options.source_commit:
            raise RuntimeError("candidate evidence source commit mismatch")
    return {
        "binary": actual_binary,
        "cleanup_sha256": digest(options.cleanup),
        "collection_sha256": digest(options.collection),
        "data_root": tree_identity(options.data_root),
        "evaluation_runtime": {
            **runtime,
            "executable": {
                "bytes": options.python.stat().st_size,
                "sha256": digest(options.python),
            },
        },
        "predecessor_temporal_result": {
            "record_commit": PREDECESSOR_COMMIT,
            "sha256": PREDECESSOR_RESULT_SHA256,
        },
        "sources": sources,
        "terminal_sha256": digest(options.terminal),
    }


def selector_command(
    options: argparse.Namespace, scratch: Path, output: Path
) -> list[str]:
    return [
        str(options.python),
        str(PACKAGE / "artifacts/jobs/temporal_select.py"),
        "--binary",
        str(options.binary),
        "--data-root",
        str(options.data_root),
        "--observation-shards",
        str(options.observation_shards),
        "--neural-root",
        str(options.neural_root),
        "--scratch",
        str(scratch),
        "--output",
        str(output),
        "--contract",
        str(PACKAGE / "artifacts/temporal-contract.json"),
        "--portfolio-contract",
        str(PACKAGE / "artifacts/portfolio-contract.json"),
        "--calendar-control-expectation",
        str(PACKAGE / "artifacts/calendar-control-expectation.json"),
        "--sites",
        str(PACKAGE / "artifacts/sites.json"),
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--observation-shards", type=Path, required=True)
    parser.add_argument("--neural-root", type=Path, required=True)
    parser.add_argument("--collection", type=Path, required=True)
    parser.add_argument("--cleanup", type=Path, required=True)
    parser.add_argument("--terminal", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    options = parser.parse_args()
    if options.output_root.exists():
        raise RuntimeError("replay output root must be fresh")
    options.output_root.mkdir(parents=True)
    inputs = verify_inputs(options)
    outputs = []
    for name in ("pass-a", "pass-b"):
        root = options.output_root / name
        root.mkdir()
        result = root / "temporal-result.json"
        subprocess.run(
            selector_command(options, root / "scratch", result), check=True
        )
        outputs.append(result)
    if outputs[0].read_bytes() != outputs[1].read_bytes():
        raise RuntimeError("isolated temporal selector replays differ")
    result = read(outputs[0])
    predecessor_result = read(REPO / PREDECESSOR_RESULT_RELATIVE)
    if result.get("prism_provenance") != predecessor_result.get("prism_provenance"):
        raise RuntimeError("inherited comparator data/provenance drift")
    if result.get("protected_roles_opened") != []:
        raise RuntimeError("selector replay opened a protected role")
    final_result = options.output_root / "temporal-result.json"
    shutil.copyfile(outputs[0], final_result)
    identity = {
        "bootstrap_replicates": result["bootstrap"]["replicates"],
        "bootstrap_seed": result["bootstrap"]["seed"],
        "byte_identical": True,
        "inputs": inputs,
        "pass_a_result_sha256": digest(outputs[0]),
        "pass_b_result_sha256": digest(outputs[1]),
        "protected_roles_opened": [],
        "result_bytes": final_result.stat().st_size,
        "schema_version": 1,
        "source_commit": options.source_commit,
        "terminal": result["terminal"],
    }
    (options.output_root / "replay-identity.json").write_text(
        json.dumps(identity, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(result["terminal"])


if __name__ == "__main__":
    main()
