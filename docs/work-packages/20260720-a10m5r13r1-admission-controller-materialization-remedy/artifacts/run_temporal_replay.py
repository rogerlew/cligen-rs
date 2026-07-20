#!/usr/bin/env python3
"""Authenticate collected R13 evidence and replay the selector twice pre-cleanup."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tarfile
from pathlib import Path

PACKAGE_ID = "20260720-a10m5r13r1-admission-controller-materialization-remedy"
RUN_ID = "a10m5r13r1-admission-controller-materialization-remedy-r0"
TERMINALS = {"A10M5R13-TEMPORAL-READY", "HOLD-A10M5R13-NO-TEMPORALLY-ELIGIBLE-CANDIDATE"}
COMPARATOR = {"bytes": 57004072, "sha256": "615aba134dcb8878046640d9672d42f470982afd26df7e1b5f0ee4c2a1835e79"}
SELECTOR_ASSETS = (
    "temporal_select.py", "temporal_metrics.py", "temporal-contract.json",
    "portfolio-contract.json", "sites.json", "calendar-control-expectation.json",
)
PREDECESSOR_PIN = Path(__file__).resolve().parent / "replay-predecessor-pin.json"


def canonical(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def selector_asset_identity(path: Path, manifest_entry: dict, name: str) -> dict:
    """Authenticate selector bytes while ignoring manifest location metadata."""
    identity = {"bytes": path.stat().st_size, "sha256": digest(path)}
    try:
        expected = {
            "bytes": manifest_entry["bytes"],
            "sha256": manifest_entry["sha256"],
        }
    except (KeyError, TypeError) as error:
        raise RuntimeError(f"selector asset manifest identity incomplete: {name}") from error
    if identity != expected:
        raise RuntimeError(f"selector asset identity drift: {name}")
    return identity


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def authenticated(value: dict) -> bool:
    semantic = dict(value)
    recorded = semantic.pop("record_sha256", None)
    return isinstance(recorded, str) and recorded == hashlib.sha256(canonical(semantic)).hexdigest()


def tree_identity(root: Path) -> dict:
    rows = [
        {
            "bytes": path.stat().st_size,
            "path": path.relative_to(root).as_posix(),
            "sha256": digest(path),
        }
        for path in sorted(item for item in root.rglob("*") if item.is_file())
    ]
    return {
        "file_count": len(rows),
        "semantic_sha256": hashlib.sha256(canonical(rows)).hexdigest(),
    }


def extract_observations(corpus: Path, output: Path, sites: list[dict]) -> None:
    wanted = {site["daymet_shard"]: site["daymet_shard_sha256"] for site in sites}
    output.mkdir(mode=0o700)
    with tarfile.open(corpus, "r:") as archive:
        for member in archive:
            name = Path(member.name).name
            if name not in wanted:
                continue
            if not member.isfile() or member.uid != 0 or member.gid != 0:
                raise RuntimeError("unsafe observation archive member")
            stream = archive.extractfile(member)
            if stream is None:
                raise RuntimeError("unreadable observation archive member")
            target = output / name
            with stream, target.open("xb") as destination:
                shutil.copyfileobj(stream, destination)
            if digest(target) != wanted[name]:
                raise RuntimeError("observation shard identity drift")
    if {path.name for path in output.iterdir()} != set(wanted):
        raise RuntimeError("observation shard roster incomplete")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--collection", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    options = parser.parse_args()
    if options.output_root.exists():
        raise RuntimeError("fresh replay output required")
    collection, plan = read(options.collection), read(options.plan)
    predecessor = read(PREDECESSOR_PIN)
    manifest = read(options.asset_root / "asset-manifest.json")
    head = subprocess.run(
        ("git", "rev-parse", "HEAD"), check=True, capture_output=True, text=True
    ).stdout.strip()
    upstream = subprocess.run(
        ("git", "rev-parse", "origin/main"), check=True, capture_output=True, text=True
    ).stdout.strip()
    repo = Path(__file__).resolve().parents[4]
    for published_path in (Path(__file__).resolve(), PREDECESSOR_PIN):
        payload = subprocess.run(
            ("git", "show", f"{head}:{published_path.relative_to(repo).as_posix()}"),
            cwd=repo, check=True, capture_output=True,
        ).stdout
        if payload != published_path.read_bytes():
            raise RuntimeError(f"replay source differs from published main: {published_path.name}")
    if not (
        head == upstream == manifest.get("source_commit") == plan.get("source_commit")
        and authenticated(collection)
        and collection.get("record_type") == "collection_receipt"
        and collection.get("package_id") == PACKAGE_ID
        and collection.get("run_id") == RUN_ID
        and collection.get("source_commit") == head
        and collection.get("plan_id") == plan.get("plan_id")
        and collection.get("download_promoted") is True
        and collection.get("remote_cleanup_performed") is not True
        and plan.get("package_id") == PACKAGE_ID
        and plan.get("run_id") == RUN_ID
    ):
        raise RuntimeError("published source/collection/plan authentication failed")
    comparator = {"bytes": options.binary.stat().st_size, "sha256": digest(options.binary)}
    corpus = {"bytes": options.corpus.stat().st_size, "sha256": digest(options.corpus)}
    runtime = json.loads(subprocess.run(
        [str(options.python), "-c", "import json,numpy,sys; print(json.dumps({'numpy':numpy.__version__,'python':sys.version.split()[0]}))"],
        check=True, capture_output=True, text=True,
    ).stdout)
    if comparator != COMPARATOR or corpus != manifest["assets"]["corpus.tar"]:
        raise RuntimeError("comparator or corpus identity drift")
    if runtime != {"numpy": "2.2.6", "python": "3.10.14"}:
        raise RuntimeError("evaluation runtime drift")
    data_root = tree_identity(options.data_root)
    if data_root != predecessor["data_root_tree"]:
        raise RuntimeError("comparator data-root identity drift")
    selector_identities = {}
    for name in SELECTOR_ASSETS:
        path = options.asset_root / name
        selector_identities[name] = selector_asset_identity(
            path, manifest["assets"][name], name
        )
    allowlist = set(plan["evidence_allowlist"])
    rows = collection.get("sanitized_files", [])
    if {row["logical_name"] for row in rows} != set(collection.get("present", [])):
        raise RuntimeError("collection present/identity roster drift")
    for row in rows:
        logical = row["logical_name"]
        path = options.evidence_root / logical
        if logical not in allowlist or path.is_symlink() or not path.is_file():
            raise RuntimeError(f"collected evidence outside allowlist: {logical}")
        if {"bytes": path.stat().st_size, "sha256": digest(path)} != {
            "bytes": row["bytes"], "sha256": row["sha256"]
        }:
            raise RuntimeError(f"collected evidence identity drift: {logical}")
    required = {
        f"results/{role}/streams.npz"
        for role in (
            "selector-aligned-continuous-hierarchy-k2",
            "selector-aligned-shared-slow-climate-state-k2",
        )
    }
    if not required <= set(collection["present"]):
        raise RuntimeError("candidate stream evidence incomplete")

    options.output_root.mkdir(mode=0o700)
    observations = options.output_root / "observations"
    sites = read(options.asset_root / "sites.json")["sites"]
    extract_observations(options.corpus, observations, sites)
    results = []
    try:
        for name in ("pass-a", "pass-b"):
            root = options.output_root / name
            root.mkdir(mode=0o700)
            result = root / "temporal-result.json"
            subprocess.run([
                str(options.python), str(options.asset_root / "temporal_select.py"),
                "--binary", str(options.binary), "--data-root", str(options.data_root),
                "--observation-shards", str(observations),
                "--neural-root", str(options.evidence_root),
                "--scratch", str(root / "scratch"), "--output", str(result),
                "--contract", str(options.asset_root / "temporal-contract.json"),
                "--portfolio-contract", str(options.asset_root / "portfolio-contract.json"),
                "--calendar-control-expectation", str(options.asset_root / "calendar-control-expectation.json"),
                "--sites", str(options.asset_root / "sites.json"),
            ], check=True)
            results.append(result)
        if results[0].read_bytes() != results[1].read_bytes():
            raise RuntimeError("isolated selector passes differ")
        result = read(results[0])
        if result.get("terminal") not in TERMINALS or result.get("protected_roles_opened") != []:
            raise RuntimeError("selector terminal/firewall drift")
        if result.get("prism_provenance") != predecessor["prism_provenance"]:
            raise RuntimeError("inherited PRISM comparator provenance drift")
        shutil.copy2(results[0], options.output_root / "temporal-result.json")
        record = {
            "byte_identical_passes": True,
            "collection_record_sha256": collection["record_sha256"],
            "asset_manifest_sha256": digest(options.asset_root / "asset-manifest.json"),
            "comparator_binary": comparator,
            "corpus": corpus,
            "data_root_tree": data_root,
            "evaluation_runtime": runtime,
            "package_id": PACKAGE_ID,
            "plan_id": collection["plan_id"],
            "protected_roles_opened": [],
            "record_type": "a10m5r13-precleanup-replay",
            "run_id": RUN_ID,
            "source_commit": head,
            "selector_assets": selector_identities,
            "predecessor_replay_record_sha256": predecessor["replay_record_sha256"],
            "prism_provenance": result["prism_provenance"],
            "temporal_result_sha256": digest(results[0]),
            "terminal": result["terminal"],
        }
        record["record_sha256"] = hashlib.sha256(canonical(record)).hexdigest()
        (options.output_root / "replay-identity.json").write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(result["terminal"])
    except BaseException:
        shutil.rmtree(options.output_root)
        raise


if __name__ == "__main__":
    main()
