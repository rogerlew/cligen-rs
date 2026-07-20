#!/usr/bin/env python3
"""Authenticate collected R14 evidence and replay the selector twice pre-cleanup."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tarfile
from pathlib import Path, PurePosixPath

PACKAGE_ID = "20260720-a10m5r14-continuous-distribution-head-factorial"
RUN_ID = "a10m5r14-continuous-distribution-head-factorial-r0"
TERMINALS = {"A10M5R14-TEMPORAL-READY", "HOLD-A10M5R14-NO-TEMPORALLY-ELIGIBLE-CANDIDATE"}
COMPARATOR = {"bytes": 57004072, "sha256": "615aba134dcb8878046640d9672d42f470982afd26df7e1b5f0ee4c2a1835e79"}
SELECTOR_ASSETS = (
    "temporal_select.py", "temporal_metrics.py", "temporal-contract.json",
    "portfolio-contract.json", "sites.json", "calendar-control-expectation.json",
)
PREDECESSOR_PIN = Path(__file__).resolve().parent / "replay-predecessor-pin.json"


def _utf16_key(value: str) -> bytes:
    return value.encode("utf-16-be", "surrogatepass")


def _jcs_text(value: object) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        if abs(value) > 9_007_199_254_740_991:
            raise RuntimeError("unsafe JSON integer")
        return str(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, list):
        return "[" + ",".join(_jcs_text(item) for item in value) + "]"
    if isinstance(value, dict):
        items = sorted(value.items(), key=lambda item: _utf16_key(item[0]))
        return "{" + ",".join(
            f"{_jcs_text(key)}:{_jcs_text(item)}" for key, item in items
        ) + "}"
    raise RuntimeError(f"unsupported toolkit JSON type: {type(value).__name__}")


def canonical(value: object) -> bytes:
    """Return RFC-8785 bytes for the integer-only toolkit record subset."""
    return _jcs_text(value).encode("utf-8")


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


def read_toolkit_object(path: Path) -> dict:
    def unique(pairs: list[tuple[str, object]]) -> dict:
        value = {}
        for key, item in pairs:
            if key in value:
                raise RuntimeError(f"duplicate JSON key: {key!r}")
            value[key] = item
        return value

    def reject_float(value: str) -> None:
        raise RuntimeError(f"floating toolkit JSON number prohibited: {value}")

    def reject_constant(value: str) -> None:
        raise RuntimeError(f"toolkit JSON constant prohibited: {value}")

    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=unique,
        parse_float=reject_float,
        parse_constant=reject_constant,
    )
    if not isinstance(value, dict):
        raise RuntimeError(f"toolkit JSON object required: {path}")
    canonical(value)
    return value


def authenticated(value: dict) -> bool:
    semantic = dict(value)
    recorded = semantic.pop("record_sha256", None)
    return isinstance(recorded, str) and recorded == hashlib.sha256(canonical(semantic)).hexdigest()


def reconstruct_semantic_plan(raw_plan: dict, plan_receipt: dict) -> dict:
    """Reproduce LemhiToolkit._semantic_plan exactly."""
    cluster_profile = plan_receipt.get("cluster_profile_sha256")
    provider_stack = plan_receipt.get("provider_stack")
    if not (
        isinstance(cluster_profile, str)
        and len(cluster_profile) == 64
        and all(character in "0123456789abcdef" for character in cluster_profile)
        and isinstance(provider_stack, list)
        and provider_stack
        and all(isinstance(provider, dict) for provider in provider_stack)
    ):
        raise RuntimeError("plan receipt omits toolkit semantic additions")
    semantic = dict(raw_plan)
    semantic.pop("created_at", None)
    semantic["cluster_profile_sha256"] = cluster_profile
    semantic["provider_stack"] = provider_stack
    return semantic


def validate_allowlist(value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise RuntimeError("authenticated semantic evidence allowlist is empty")
    paths = []
    for item in value:
        if not isinstance(item, str) or not item or "\\" in item:
            raise RuntimeError("invalid authenticated evidence allowlist path")
        path = PurePosixPath(item)
        if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
            raise RuntimeError("unsafe authenticated evidence allowlist path")
        paths.append(item)
    if len(paths) != len(set(paths)):
        raise RuntimeError("duplicate authenticated evidence allowlist path")
    return tuple(paths)


def authenticate_plan(
    raw_plan: dict, plan_receipt: dict, source_commit: str
) -> dict:
    if not (
        authenticated(plan_receipt)
        and plan_receipt.get("record_type") == "run_plan_receipt"
        and plan_receipt.get("package_id") == PACKAGE_ID
        and plan_receipt.get("run_id") == RUN_ID
        and plan_receipt.get("source_commit") == source_commit
        and raw_plan.get("package_id") == PACKAGE_ID
        and raw_plan.get("run_id") == RUN_ID
        and raw_plan.get("source_commit") == source_commit
    ):
        raise RuntimeError("R14 raw plan or publication receipt authentication failed")
    semantic = reconstruct_semantic_plan(raw_plan, plan_receipt)
    semantic_id = hashlib.sha256(canonical(semantic)).hexdigest()
    if semantic_id != plan_receipt.get("plan_id"):
        raise RuntimeError("R14 semantic plan does not match authenticated plan_id")
    validate_allowlist(semantic.get("evidence_allowlist"))
    return semantic


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
    parser.add_argument("--semantic-plan", type=Path, required=True)
    parser.add_argument("--plan-receipt", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    options = parser.parse_args()
    if options.output_root.exists():
        raise RuntimeError("fresh replay output required")
    collection = read_toolkit_object(options.collection)
    raw_plan = read_toolkit_object(options.semantic_plan)
    plan_receipt = read_toolkit_object(options.plan_receipt)
    predecessor = read(PREDECESSOR_PIN)
    manifest = read(options.asset_root / "asset-manifest.json")
    head = subprocess.run(
        ("git", "rev-parse", "HEAD"), check=True, capture_output=True, text=True
    ).stdout.strip()
    upstream = subprocess.run(
        ("git", "rev-parse", "origin/main"), check=True, capture_output=True, text=True
    ).stdout.strip()
    plan = authenticate_plan(raw_plan, plan_receipt, head)
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
        and collection.get("plan_id") == plan_receipt.get("plan_id")
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
            "continuous-location-ou-k2",
            "continuous-location-ou-smooth-climatology-k2",
            "continuous-location-scale-ou-k2",
            "continuous-location-scale-ou-smooth-climatology-k2",
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
            "plan_receipt_record_sha256": plan_receipt["record_sha256"],
            "protected_roles_opened": [],
            "record_type": "a10m5r14-precleanup-replay",
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
