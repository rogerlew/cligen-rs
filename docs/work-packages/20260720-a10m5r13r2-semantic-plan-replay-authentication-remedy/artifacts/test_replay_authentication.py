#!/usr/bin/env python3
"""Focused fail-closed tests for R13R2 semantic-plan replay authentication."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPLAY_PATH = Path(__file__).parent / "run_temporal_replay.py"
REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))
SPEC = importlib.util.spec_from_file_location("r13r2_replay", REPLAY_PATH)
assert SPEC and SPEC.loader
REPLAY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REPLAY)

from research.a10.lemhi_toolkit.core import ToolkitError, canonical_bytes


def signed(value: dict) -> dict:
    result = dict(value)
    result["record_sha256"] = hashlib.sha256(REPLAY.canonical(result)).hexdigest()
    return result


def fixture() -> tuple[dict, dict]:
    raw = {
        "created_at": "ignored-by-toolkit-semantic",
        "package_id": REPLAY.INPUT_PACKAGE_ID,
        "run_id": REPLAY.INPUT_RUN_ID,
        "source_commit": REPLAY.INPUT_SOURCE_COMMIT,
        "evidence_allowlist": ["results/a/streams.npz", "slurm/a.0.out"],
        "providers": ["provider-definition.json"],
    }
    additions = {
        "cluster_profile_sha256": "a" * 64,
        "provider_stack": [
            {
                "definition_sha256": "b" * 64,
                "implementation_version": "2.0.0",
                "name": "test-provider-v2",
                "provider_api_version": 2,
                "selection_reason": "explicit-plan-order",
            }
        ],
    }
    semantic = dict(raw)
    semantic.pop("created_at")
    semantic.update(additions)
    receipt = signed(
        {
            **additions,
            "package_id": REPLAY.INPUT_PACKAGE_ID,
            "plan_id": hashlib.sha256(REPLAY.canonical(semantic)).hexdigest(),
            "record_type": "run_plan_receipt",
            "run_id": REPLAY.INPUT_RUN_ID,
            "source_commit": REPLAY.INPUT_SOURCE_COMMIT,
        }
    )
    return raw, receipt


def require_rejection(callable_value, label: str) -> None:
    try:
        callable_value()
    except (RuntimeError, ToolkitError):
        return
    raise RuntimeError(f"authentication accepted {label}")


def test_semantic_identity_and_allowlist_tamper() -> None:
    raw, receipt = fixture()
    semantic = REPLAY.authenticate_plan(raw, receipt)
    if semantic["evidence_allowlist"] != raw["evidence_allowlist"]:
        raise RuntimeError("authenticated allowlist was not retained")
    if "created_at" in semantic:
        raise RuntimeError("optional created_at entered toolkit semantic identity")

    tampered = dict(raw)
    tampered["evidence_allowlist"] = [*raw["evidence_allowlist"], "results/evil"]
    require_rejection(
        lambda: REPLAY.authenticate_plan(tampered, receipt),
        "tampered semantic allowlist",
    )


def test_toolkit_canonical_exactness() -> None:
    value = {
        "\U0001f600": [True, None, "quoted\ntext"],
        "\ue000": {"integer": 9007199254740991},
    }
    if REPLAY.canonical(value) != canonical_bytes(value):
        raise RuntimeError("replay canonical bytes differ from toolkit canonical bytes")
    require_rejection(
        lambda: REPLAY.canonical({"floating": float("nan")}),
        "non-I-JSON value in canonical identity",
    )
    for text, label in (
        ('{"duplicate":1,"duplicate":2}', "duplicate JSON key"),
        ('{"floating":1.5}', "floating JSON number"),
        ('{"constant":NaN}', "non-I-JSON constant"),
        ('{"unsafe":9007199254740992}', "unsafe JSON integer"),
        ('{"surrogate":"\\ud800"}', "unpaired Unicode surrogate"),
    ):
        require_rejection(lambda value=text: REPLAY.loads_strict(value), label)


def test_receipt_tamper() -> None:
    raw, receipt = fixture()
    tampered_unsigned = dict(receipt)
    tampered_unsigned["cluster_profile_sha256"] = "c" * 64
    require_rejection(
        lambda: REPLAY.authenticate_plan(raw, tampered_unsigned),
        "receipt with invalid record hash",
    )

    tampered_resigned = dict(receipt)
    tampered_resigned.pop("record_sha256")
    tampered_resigned["provider_stack"] = [{"name": "substituted-provider"}]
    tampered_resigned = signed(tampered_resigned)
    require_rejection(
        lambda: REPLAY.authenticate_plan(raw, tampered_resigned),
        "resigned receipt inconsistent with plan_id",
    )


def git(repo: Path, *arguments: str, env: dict | None = None) -> str:
    return subprocess.run(
        ("git", *arguments),
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    ).stdout.strip()


def test_published_binding_tamper() -> None:
    with tempfile.TemporaryDirectory() as scratch:
        repo = Path(scratch)
        git(repo, "init", "-q")
        artifact = repo / "artifact.py"
        artifact.write_text("published = True\n", encoding="utf-8")
        git(repo, "add", "artifact.py")
        environment = dict(os.environ)
        environment.update(
            {
                "GIT_AUTHOR_NAME": "R13R2 Test",
                "GIT_AUTHOR_EMAIL": "r13r2@example.invalid",
                "GIT_COMMITTER_NAME": "R13R2 Test",
                "GIT_COMMITTER_EMAIL": "r13r2@example.invalid",
            }
        )
        git(repo, "commit", "-q", "-m", "fixture", env=environment)
        input_commit = git(repo, "rev-parse", "HEAD")
        artifact.write_text("published = True\nsecond = True\n", encoding="utf-8")
        git(repo, "add", "artifact.py")
        git(repo, "commit", "-q", "-m", "descendant", env=environment)
        head = git(repo, "rev-parse", "HEAD")
        REPLAY.verify_published_binding(repo, (artifact,), head, head)
        REPLAY.verify_input_ancestry(repo, input_commit, head)

        artifact.write_text("published = False\n", encoding="utf-8")
        require_rejection(
            lambda: REPLAY.verify_published_binding(repo, (artifact,), head, head),
            "working bytes different from published bytes",
        )
        require_rejection(
            lambda: REPLAY.verify_published_binding(repo, (artifact,), head, "f" * 40),
            "HEAD different from origin/main",
        )
        require_rejection(
            lambda: REPLAY.verify_input_ancestry(repo, "f" * 40, head),
            "unknown or non-ancestor input commit",
        )


def test_pinned_files_and_manifest_binding() -> None:
    with tempfile.TemporaryDirectory() as scratch:
        root = Path(scratch)
        raw = root / "raw-plan.json"
        receipt = root / "plan-receipt.json"
        collection = root / "collection.json"
        manifest = root / "asset-manifest.json"
        for path, payload in (
            (raw, b"raw-plan"),
            (receipt, b"plan-receipt"),
            (collection, b"collection"),
            (manifest, b"asset-manifest"),
        ):
            path.write_bytes(payload)

        pin = {
            "asset_manifest": REPLAY.file_identity(manifest),
            "collection": {
                **REPLAY.file_identity(collection),
                "record_sha256": "c" * 64,
            },
            "package_id": REPLAY.INPUT_PACKAGE_ID,
            "plan_id": "d" * 64,
            "plan_receipt": {
                **REPLAY.file_identity(receipt),
                "record_sha256": "e" * 64,
            },
            "raw_semantic_plan": REPLAY.file_identity(raw),
            "run_id": REPLAY.INPUT_RUN_ID,
            "schema_version": "a10m5r13r2-r13r1-input-pin-1",
            "source_commit": REPLAY.INPUT_SOURCE_COMMIT,
        }
        REPLAY.validate_input_pin(pin)
        for label, path, key in (
            ("raw semantic plan", raw, "raw_semantic_plan"),
            ("plan receipt", receipt, "plan_receipt"),
            ("collection", collection, "collection"),
            ("asset manifest", manifest, "asset_manifest"),
        ):
            REPLAY.authenticate_pinned_file(path, pin[key], label)

        semantic = {
            "assets": [
                {
                    "bytes": manifest.stat().st_size,
                    "logical_name": "asset-manifest.json",
                    "sha256": REPLAY.digest(manifest),
                }
            ]
        }
        REPLAY.authenticate_manifest_from_semantic(semantic, manifest)
        bad_semantic = json.loads(json.dumps(semantic))
        bad_semantic["assets"][0]["sha256"] = "0" * 64
        require_rejection(
            lambda: REPLAY.authenticate_manifest_from_semantic(
                bad_semantic, manifest
            ),
            "asset manifest outside authenticated semantic asset identity",
        )
        duplicate = {"assets": [semantic["assets"][0], semantic["assets"][0]]}
        require_rejection(
            lambda: REPLAY.authenticate_manifest_from_semantic(duplicate, manifest),
            "duplicate semantic asset-manifest entries",
        )

        raw.write_bytes(b"tampered-raw-plan")
        require_rejection(
            lambda: REPLAY.authenticate_pinned_file(
                raw, pin["raw_semantic_plan"], "raw semantic plan"
            ),
            "pinned raw semantic-plan bytes",
        )


def test_collection_roster_partition() -> None:
    allowlist = {"a", "b", "c"}
    base = {
        "present": ["a", "b"],
        "absent": ["c"],
        "sanitized_files": [{"logical_name": "a"}, {"logical_name": "b"}],
    }
    if REPLAY.validate_collection_roster(base, allowlist) != base["sanitized_files"]:
        raise RuntimeError("valid collection roster partition was changed")

    mutations = []
    for key, value in (
        ("present", ["a", "a", "b"]),
        ("absent", ["c", "c"]),
        ("absent", ["b", "c"]),
        ("absent", []),
        ("absent", ["c", "d"]),
        ("sanitized_files", [{"logical_name": "a"}, {"logical_name": "a"}]),
        ("sanitized_files", [{"logical_name": "a"}]),
    ):
        mutation = json.loads(json.dumps(base))
        mutation[key] = value
        mutations.append(mutation)
    for mutation in mutations:
        require_rejection(
            lambda value=mutation: REPLAY.validate_collection_roster(
                value, allowlist
            ),
            "invalid collection present/absent/identity partition",
        )


def test_actual_r13r1_input_pin() -> None:
    root = Path(
        "/Users/roger/.cache/cligen-rs/"
        "a10m5r13r1-admission-controller-materialization-remedy"
    )
    if not root.exists():
        return
    pin = REPLAY.read(Path(__file__).parent / "r13r1-input-pin.json")
    REPLAY.validate_input_pin(pin)
    paths = {
        "raw_semantic_plan": root / "records/plan.json",
        "plan_receipt": root
        / "state/runs/a10m5r13r1-admission-controller-materialization-remedy-r0/"
        "publication/plan.json",
        "collection": root
        / "state/runs/a10m5r13r1-admission-controller-materialization-remedy-r0/"
        "publication/collection.json",
        "asset_manifest": root / "assets/asset-manifest.json",
    }
    for key, path in paths.items():
        REPLAY.authenticate_pinned_file(path, pin[key], key)
    plan_receipt = REPLAY.read(paths["plan_receipt"])
    collection = REPLAY.read(paths["collection"])
    raw_plan = REPLAY.read(paths["raw_semantic_plan"])
    semantic = REPLAY.authenticate_plan(raw_plan, plan_receipt)
    REPLAY.authenticate_collection(collection, plan_receipt)
    REPLAY.authenticate_manifest_from_semantic(semantic, paths["asset_manifest"])
    REPLAY.validate_collection_roster(
        collection, set(REPLAY.validate_allowlist(semantic["evidence_allowlist"]))
    )
    if not (
        plan_receipt["record_sha256"] == pin["plan_receipt"]["record_sha256"]
        and collection["record_sha256"] == pin["collection"]["record_sha256"]
        and plan_receipt["plan_id"] == pin["plan_id"]
    ):
        raise RuntimeError("actual R13R1 record identities differ from committed pin")


def test_command_surface() -> None:
    source = REPLAY_PATH.read_text(encoding="utf-8")
    required = (
        'parser.add_argument("--plan-receipt"',
        'parser.add_argument("--semantic-plan"',
        'semantic.pop("created_at", None)',
        'semantic["cluster_profile_sha256"] = cluster_profile',
        'semantic["provider_stack"] = provider_stack',
        'allowlist = set(validate_allowlist(semantic_plan["evidence_allowlist"]))',
        'collection.get("source_commit") == INPUT_SOURCE_COMMIT',
        'verify_input_ancestry(repo, INPUT_SOURCE_COMMIT, head)',
        'authenticate_manifest_from_semantic(',
        'rows = validate_collection_roster(collection, allowlist)',
        'PREDECESSOR_PIN, INPUT_PIN',
        '"remedy_source_commit": head',
    )
    if any(item not in source for item in required):
        raise RuntimeError("R13R2 replay command surface is incomplete")
    if 'parser.add_argument("--plan"' in source:
        raise RuntimeError("ambiguous legacy --plan input remains")


if __name__ == "__main__":
    test_semantic_identity_and_allowlist_tamper()
    test_toolkit_canonical_exactness()
    test_receipt_tamper()
    test_published_binding_tamper()
    test_pinned_files_and_manifest_binding()
    test_collection_roster_partition()
    test_actual_r13r1_input_pin()
    test_command_surface()
    print("A10M5R13R2-REPLAY-AUTHENTICATION-TEST-PASS")
