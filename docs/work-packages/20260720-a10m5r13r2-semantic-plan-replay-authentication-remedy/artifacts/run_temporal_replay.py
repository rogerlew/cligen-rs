#!/usr/bin/env python3
"""Authenticate the R13R1 semantic plan and replay its selector pre-cleanup."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tarfile
from pathlib import Path, PurePosixPath

REPO_ROOT = Path(__file__).resolve().parents[4]
SAFE_INTEGER = 9_007_199_254_740_991

INPUT_PACKAGE_ID = "20260720-a10m5r13r1-admission-controller-materialization-remedy"
INPUT_RUN_ID = "a10m5r13r1-admission-controller-materialization-remedy-r0"
INPUT_SOURCE_COMMIT = "927c6147f879ed3a9a56ff1218ffaa3953bef93c"
OUTPUT_PACKAGE_ID = "20260720-a10m5r13r2-semantic-plan-replay-authentication-remedy"
TERMINALS = {
    "A10M5R13-TEMPORAL-READY",
    "HOLD-A10M5R13-NO-TEMPORALLY-ELIGIBLE-CANDIDATE",
}
COMPARATOR = {
    "bytes": 57004072,
    "sha256": "615aba134dcb8878046640d9672d42f470982afd26df7e1b5f0ee4c2a1835e79",
}
SELECTOR_ASSETS = (
    "temporal_select.py",
    "temporal_metrics.py",
    "temporal-contract.json",
    "portfolio-contract.json",
    "sites.json",
    "calendar-control-expectation.json",
)
PREDECESSOR_PIN = Path(__file__).resolve().parent / "replay-predecessor-pin.json"
INPUT_PIN = Path(__file__).resolve().parent / "r13r1-input-pin.json"


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    value = {}
    for key, item in pairs:
        if key in value:
            raise RuntimeError(f"duplicate JSON key: {key!r}")
        value[key] = item
    return value


def validate_json_value(value: object, path: str = "$") -> None:
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, str):
        try:
            value.encode("utf-8")
        except UnicodeEncodeError as error:
            raise RuntimeError(f"unpaired Unicode surrogate at {path}") from error
        return
    if isinstance(value, int):
        if abs(value) > SAFE_INTEGER:
            raise RuntimeError(f"unsafe JSON integer at {path}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            validate_json_value(item, f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise RuntimeError(f"non-string JSON key at {path}")
            validate_json_value(key, f"{path}.<key>")
            validate_json_value(item, f"{path}.{key}")
        return
    raise RuntimeError(f"unsupported JSON type {type(value).__name__} at {path}")


def loads_strict(text: str) -> object:
    def reject_float(value: str) -> None:
        raise RuntimeError(f"floating JSON number prohibited: {value}")

    def reject_constant(value: str) -> None:
        raise RuntimeError(f"JSON constant prohibited: {value}")

    try:
        result = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_float=reject_float,
            parse_constant=reject_constant,
        )
    except RuntimeError:
        raise
    except (UnicodeError, json.JSONDecodeError) as error:
        raise RuntimeError(f"invalid I-JSON: {error}") from error
    validate_json_value(result)
    return result


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
    raise RuntimeError(f"unsupported JSON type {type(value).__name__}")


def canonical(value: object) -> bytes:
    """Return RFC-8785 bytes for the integer-only I-JSON toolkit subset."""
    validate_json_value(value)
    try:
        return _jcs_text(value).encode("utf-8")
    except UnicodeEncodeError as error:
        raise RuntimeError("unpaired Unicode surrogate") from error


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def read(path: Path) -> dict:
    value = loads_strict(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON object required: {path}")
    return value


def file_identity(path: Path) -> dict:
    return {"bytes": path.stat().st_size, "sha256": digest(path)}


def authenticate_pinned_file(path: Path, expected: object, label: str) -> None:
    if not isinstance(expected, dict) or file_identity(path) != {
        "bytes": expected.get("bytes"),
        "sha256": expected.get("sha256"),
    }:
        raise RuntimeError(f"pinned R13R1 {label} file identity drift")


def validate_input_pin(pin: dict) -> None:
    required = {
        "asset_manifest",
        "collection",
        "package_id",
        "plan_id",
        "plan_receipt",
        "raw_semantic_plan",
        "run_id",
        "schema_version",
        "source_commit",
    }
    if not (
        required == set(pin)
        and pin.get("schema_version") == "a10m5r13r2-r13r1-input-pin-1"
        and pin.get("package_id") == INPUT_PACKAGE_ID
        and pin.get("run_id") == INPUT_RUN_ID
        and pin.get("source_commit") == INPUT_SOURCE_COMMIT
        and isinstance(pin.get("plan_id"), str)
        and len(pin["plan_id"]) == 64
    ):
        raise RuntimeError("R13R1 committed input pin is malformed")
    for label in ("asset_manifest", "collection", "plan_receipt", "raw_semantic_plan"):
        value = pin[label]
        if not (
            isinstance(value, dict)
            and isinstance(value.get("bytes"), int)
            and value["bytes"] > 0
            and isinstance(value.get("sha256"), str)
            and len(value["sha256"]) == 64
        ):
            raise RuntimeError(f"R13R1 committed {label} pin is malformed")
    for label in ("collection", "plan_receipt"):
        value = pin[label]
        if set(value) != {"bytes", "record_sha256", "sha256"} or not (
            isinstance(value["record_sha256"], str)
            and len(value["record_sha256"]) == 64
        ):
            raise RuntimeError(f"R13R1 committed {label} record pin is malformed")
    for label in ("asset_manifest", "raw_semantic_plan"):
        if set(pin[label]) != {"bytes", "sha256"}:
            raise RuntimeError(f"R13R1 committed {label} file pin has extra fields")


def authenticated_record(value: dict) -> bool:
    semantic = dict(value)
    recorded = semantic.pop("record_sha256", None)
    return (
        isinstance(recorded, str)
        and len(recorded) == 64
        and recorded == hashlib.sha256(canonical(semantic)).hexdigest()
    )


def reconstruct_semantic_plan(raw_plan: dict, plan_receipt: dict) -> dict:
    """Reproduce LemhiToolkit._semantic_plan without loading provider files."""
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
    paths: list[str] = []
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


def authenticate_plan(raw_plan: dict, plan_receipt: dict) -> dict:
    if not (
        authenticated_record(plan_receipt)
        and plan_receipt.get("record_type") == "run_plan_receipt"
        and plan_receipt.get("package_id") == INPUT_PACKAGE_ID
        and plan_receipt.get("run_id") == INPUT_RUN_ID
        and plan_receipt.get("source_commit") == INPUT_SOURCE_COMMIT
        and raw_plan.get("package_id") == INPUT_PACKAGE_ID
        and raw_plan.get("run_id") == INPUT_RUN_ID
        and raw_plan.get("source_commit") == INPUT_SOURCE_COMMIT
    ):
        raise RuntimeError("R13R1 raw plan or publication receipt authentication failed")
    semantic = reconstruct_semantic_plan(raw_plan, plan_receipt)
    semantic_id = hashlib.sha256(canonical(semantic)).hexdigest()
    if semantic_id != plan_receipt.get("plan_id"):
        raise RuntimeError("R13R1 semantic plan does not match authenticated plan_id")
    validate_allowlist(semantic.get("evidence_allowlist"))
    return semantic


def verify_published_binding(
    repo: Path, published_paths: tuple[Path, ...], head: str, upstream: str
) -> None:
    if head != upstream:
        raise RuntimeError("replay remedy is not at published origin/main")
    for published_path in published_paths:
        try:
            relative = published_path.resolve().relative_to(repo.resolve()).as_posix()
        except ValueError as error:
            raise RuntimeError("published replay path is outside repository") from error
        payload = subprocess.run(
            ("git", "show", f"{head}:{relative}"),
            cwd=repo,
            check=True,
            capture_output=True,
        ).stdout
        if payload != published_path.read_bytes():
            raise RuntimeError(f"replay source differs from published main: {relative}")


def verify_input_ancestry(repo: Path, input_commit: str, head: str) -> None:
    result = subprocess.run(
        ("git", "merge-base", "--is-ancestor", input_commit, head),
        cwd=repo,
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError("R13R1 input commit is not an ancestor of remedy HEAD")


def authenticate_manifest_from_semantic(
    semantic_plan: dict, manifest_path: Path
) -> None:
    assets = semantic_plan.get("assets")
    if not isinstance(assets, list):
        raise RuntimeError("authenticated semantic plan assets are malformed")
    matches = [
        asset
        for asset in assets
        if isinstance(asset, dict) and asset.get("logical_name") == "asset-manifest.json"
    ]
    if len(matches) != 1:
        raise RuntimeError("authenticated semantic plan does not name one asset manifest")
    expected = matches[0]
    if file_identity(manifest_path) != {
        "bytes": expected.get("bytes"),
        "sha256": expected.get("sha256"),
    }:
        raise RuntimeError("asset manifest differs from authenticated semantic plan")


def validate_collection_roster(collection: dict, allowlist: set[str]) -> list[dict]:
    present = collection.get("present")
    absent = collection.get("absent")
    rows = collection.get("sanitized_files")
    if not (
        isinstance(present, list)
        and isinstance(absent, list)
        and isinstance(rows, list)
        and all(isinstance(item, str) for item in present)
        and all(isinstance(item, str) for item in absent)
        and all(isinstance(row, dict) for row in rows)
    ):
        raise RuntimeError("collection evidence rosters are malformed")
    present_set = set(present)
    absent_set = set(absent)
    if len(present) != len(present_set) or len(absent) != len(absent_set):
        raise RuntimeError("collection present/absent rosters contain duplicates")
    if present_set & absent_set:
        raise RuntimeError("collection present and absent rosters overlap")
    if present_set | absent_set != allowlist:
        raise RuntimeError("collection present/absent union differs from allowlist")
    logical_names = [row.get("logical_name") for row in rows]
    if (
        any(not isinstance(logical, str) for logical in logical_names)
        or len(logical_names) != len(set(logical_names))
        or set(logical_names) != present_set
    ):
        raise RuntimeError("collection present/identity roster drift")
    return rows


def selector_asset_identity(path: Path, manifest_entry: dict, name: str) -> dict:
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


def authenticate_collection(collection: dict, plan_receipt: dict) -> None:
    if not (
        authenticated_record(collection)
        and collection.get("record_type") == "collection_receipt"
        and collection.get("package_id") == INPUT_PACKAGE_ID
        and collection.get("run_id") == INPUT_RUN_ID
        and collection.get("source_commit") == INPUT_SOURCE_COMMIT
        and collection.get("plan_id") == plan_receipt.get("plan_id")
        and collection.get("download_promoted") is True
        and collection.get("remote_cleanup_performed") is not True
    ):
        raise RuntimeError("R13R1 collection authentication failed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--collection", type=Path, required=True)
    parser.add_argument("--plan-receipt", type=Path, required=True)
    parser.add_argument("--semantic-plan", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    options = parser.parse_args()
    if options.output_root.exists():
        raise RuntimeError("fresh replay output required")

    collection = read(options.collection)
    plan_receipt = read(options.plan_receipt)
    raw_plan = read(options.semantic_plan)
    predecessor = read(PREDECESSOR_PIN)
    input_pin = read(INPUT_PIN)
    manifest = read(options.asset_root / "asset-manifest.json")
    repo = REPO_ROOT
    head = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    upstream = subprocess.run(
        ("git", "rev-parse", "origin/main"),
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    verify_published_binding(
        repo,
        (Path(__file__).resolve(), PREDECESSOR_PIN, INPUT_PIN),
        head,
        upstream,
    )
    verify_input_ancestry(repo, INPUT_SOURCE_COMMIT, head)
    validate_input_pin(input_pin)
    authenticate_pinned_file(
        options.semantic_plan, input_pin["raw_semantic_plan"], "raw semantic plan"
    )
    authenticate_pinned_file(
        options.plan_receipt, input_pin["plan_receipt"], "plan receipt"
    )
    authenticate_pinned_file(options.collection, input_pin["collection"], "collection")
    authenticate_pinned_file(
        options.asset_root / "asset-manifest.json",
        input_pin["asset_manifest"],
        "asset manifest",
    )
    if not (
        plan_receipt.get("record_sha256")
        == input_pin["plan_receipt"]["record_sha256"]
        and collection.get("record_sha256")
        == input_pin["collection"]["record_sha256"]
        and plan_receipt.get("plan_id") == input_pin["plan_id"]
    ):
        raise RuntimeError("R13R1 pinned record or plan identity drift")

    semantic_plan = authenticate_plan(raw_plan, plan_receipt)
    authenticate_collection(collection, plan_receipt)
    authenticate_manifest_from_semantic(
        semantic_plan, options.asset_root / "asset-manifest.json"
    )
    if manifest.get("source_commit") != INPUT_SOURCE_COMMIT:
        raise RuntimeError("R13R1 asset manifest source drift")

    comparator = {"bytes": options.binary.stat().st_size, "sha256": digest(options.binary)}
    corpus = {"bytes": options.corpus.stat().st_size, "sha256": digest(options.corpus)}
    runtime = json.loads(
        subprocess.run(
            [
                str(options.python),
                "-c",
                "import json,numpy,sys; print(json.dumps({'numpy':numpy.__version__,'python':sys.version.split()[0]}))",
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    )
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

    allowlist = set(validate_allowlist(semantic_plan["evidence_allowlist"]))
    rows = validate_collection_roster(collection, allowlist)
    for row in rows:
        logical = row["logical_name"]
        path = options.evidence_root / logical
        if logical not in allowlist or path.is_symlink() or not path.is_file():
            raise RuntimeError(f"collected evidence outside allowlist: {logical}")
        if {"bytes": path.stat().st_size, "sha256": digest(path)} != {
            "bytes": row["bytes"],
            "sha256": row["sha256"],
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
            subprocess.run(
                [
                    str(options.python),
                    str(options.asset_root / "temporal_select.py"),
                    "--binary",
                    str(options.binary),
                    "--data-root",
                    str(options.data_root),
                    "--observation-shards",
                    str(observations),
                    "--neural-root",
                    str(options.evidence_root),
                    "--scratch",
                    str(root / "scratch"),
                    "--output",
                    str(result),
                    "--contract",
                    str(options.asset_root / "temporal-contract.json"),
                    "--portfolio-contract",
                    str(options.asset_root / "portfolio-contract.json"),
                    "--calendar-control-expectation",
                    str(options.asset_root / "calendar-control-expectation.json"),
                    "--sites",
                    str(options.asset_root / "sites.json"),
                ],
                check=True,
            )
            results.append(result)
        if results[0].read_bytes() != results[1].read_bytes():
            raise RuntimeError("isolated selector passes differ")
        result = read(results[0])
        if (
            result.get("terminal") not in TERMINALS
            or result.get("protected_roles_opened") != []
        ):
            raise RuntimeError("selector terminal/firewall drift")
        if result.get("prism_provenance") != predecessor["prism_provenance"]:
            raise RuntimeError("inherited PRISM comparator provenance drift")
        shutil.copy2(results[0], options.output_root / "temporal-result.json")
        record = {
            "asset_manifest_sha256": digest(options.asset_root / "asset-manifest.json"),
            "byte_identical_passes": True,
            "collection_record_sha256": collection["record_sha256"],
            "comparator_binary": comparator,
            "corpus": corpus,
            "data_root_tree": data_root,
            "evaluation_runtime": runtime,
            "input_package_id": INPUT_PACKAGE_ID,
            "input_run_id": INPUT_RUN_ID,
            "input_source_commit": INPUT_SOURCE_COMMIT,
            "output_package_id": OUTPUT_PACKAGE_ID,
            "plan_id": plan_receipt["plan_id"],
            "plan_receipt_record_sha256": plan_receipt["record_sha256"],
            "predecessor_replay_record_sha256": predecessor["replay_record_sha256"],
            "prism_provenance": result["prism_provenance"],
            "protected_roles_opened": [],
            "record_type": "a10m5r13r2-precleanup-replay",
            "remedy_source_commit": head,
            "selector_assets": selector_identities,
            "semantic_plan_sha256": hashlib.sha256(canonical(semantic_plan)).hexdigest(),
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
