#!/usr/bin/env python3
"""Executable tests for the exact real two-checker migration contract."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


outer = load("r14r2r1_outer", PACKAGE / "artifacts/jobs/admission_checker.py")
prepare = load("r14r2r1_prepare", PACKAGE / "artifacts/jobs/prepare_assets.py")
materializer = load(
    "r14r2r1_materializer", PACKAGE / "artifacts/jobs/materialize_admission.py"
)


class ComposedCheckerIdentityTests(unittest.TestCase):
    def fixture(self):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        own = root / "admission_checker.py"
        delegate = root / "inherited_admission_checker.py"
        own.write_bytes(b"outer-real-bytes")
        delegate.write_bytes(b"delegate-real-bytes")
        identities = {
            path.name: {"bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            for path in (own, delegate)
        }
        assets = [{"logical_name": name, **identities[name]} for name in outer.SLOTS]
        plan = {
            "admission_materialization": {
                "checker_assets": {"logical_names": outer.SLOTS, "protocol": outer.PROTOCOL}
            },
            "assets": assets,
        }
        plan_id = hashlib.sha256(outer.canonical(plan)).hexdigest()
        state = {"current_plan_id": plan_id, "plan_revisions": [{"plan_id": plan_id, "semantic": plan}]}
        manifest = {"assets": identities}
        return temporary, root, own, delegate, state, manifest

    def test_positive_exact_ordered_projection(self):
        temporary, root, own, delegate, state, manifest = self.fixture()
        with temporary:
            self.assertEqual(
                outer.checker_projection(state, manifest, root, own, delegate),
                {
                    "assets": [
                        {"logical_name": name, **manifest["assets"][name]}
                        for name in outer.SLOTS
                    ],
                    "protocol": outer.PROTOCOL,
                },
            )

    def test_old_slot_zero_self_lookup_and_tampering_fail_closed(self):
        temporary, root, own, delegate, state, manifest = self.fixture()
        with temporary:
            state["plan_revisions"][0]["semantic"]["admission_materialization"]["checker_assets"]["logical_names"] = list(reversed(outer.SLOTS))
            changed = state["plan_revisions"][0]["semantic"]
            changed_id = hashlib.sha256(outer.canonical(changed)).hexdigest()
            state["current_plan_id"] = changed_id
            state["plan_revisions"][0]["plan_id"] = changed_id
            with self.assertRaisesRegex(RuntimeError, "contract drift"):
                outer.checker_projection(state, manifest, root, own, delegate)
        temporary, root, own, delegate, state, manifest = self.fixture()
        with temporary:
            delegate.write_bytes(b"tampered")
            with self.assertRaisesRegex(RuntimeError, "identity drift"):
                outer.checker_projection(state, manifest, root, own, delegate)

    def test_stale_ambiguous_root_and_symlink_fail_closed(self):
        temporary, root, own, delegate, state, manifest = self.fixture()
        with temporary:
            state["plan_revisions"].append(dict(state["plan_revisions"][0]))
            with self.assertRaisesRegex(RuntimeError, "ambiguous"):
                outer.checker_projection(state, manifest, root, own, delegate)
        temporary, root, own, delegate, state, manifest = self.fixture()
        with temporary:
            with self.assertRaisesRegex(RuntimeError, "escapes"):
                outer.checker_projection(state, manifest, root / "wrong", own, delegate)
            link = root / "link.py"
            link.symlink_to(delegate)
            state["plan_revisions"][0]["semantic"]["admission_materialization"]["checker_assets"]["logical_names"] = ["admission_checker.py", "link.py"]
            with self.assertRaises(RuntimeError):
                outer.checker_projection(state, manifest, root, own, link)
        temporary, root, own, delegate, state, manifest = self.fixture()
        with temporary:
            source = root / "hard-source.py"
            source.write_bytes(delegate.read_bytes())
            delegate.unlink()
            os.link(source, delegate)
            with self.assertRaisesRegex(RuntimeError, "path identity drift"):
                outer.checker_projection(state, manifest, root, own, delegate)

    def test_manifest_protocol_and_materializer_projection_fail_closed(self):
        temporary, root, own, delegate, state, manifest = self.fixture()
        with temporary:
            manifest["assets"][delegate.name]["sha256"] = "0" * 64
            with self.assertRaisesRegex(RuntimeError, "identity drift"):
                outer.checker_projection(state, manifest, root, own, delegate)
        temporary, root, own, delegate, state, manifest = self.fixture()
        with temporary:
            plan = state["plan_revisions"][0]["semantic"]
            plan["admission_materialization"]["checker_assets"]["protocol"] = "wrong"
            plan_id = hashlib.sha256(outer.canonical(plan)).hexdigest()
            state["current_plan_id"] = plan_id
            state["plan_revisions"][0]["plan_id"] = plan_id
            with self.assertRaisesRegex(RuntimeError, "contract drift"):
                outer.checker_projection(state, manifest, root, own, delegate)

        projection = {"assets": [], "protocol": "ordered-plan-assets-v1"}
        materializer.EXPECTED_PROJECTION = projection
        materializer.EXPECTED_AUTHORITY_ID = "fresh-authority"
        semantic = {
            "attempt_index": 0,
            "authority_id": "fresh-authority",
            "decision": "PASS",
            "gates": {"composed_checker_chain_authenticated": True},
            "input_identities": {
                "checker_assets": projection,
                "toolkit_state_sha256": "1" * 64,
            },
            "package_id": materializer.PACKAGE_ID,
            "record_type": materializer.RECORD_TYPE,
            "role": "control-materialization",
            "run_id": materializer.RUN_ID,
            "schema_version": "lemhi-toolkit-record-2",
            "source_commit": "2" * 40,
            "valid": True,
        }
        semantic["record_sha256"] = hashlib.sha256(
            json.dumps(semantic, separators=(",", ":"), sort_keys=True).encode()
        ).hexdigest()
        original_run = materializer.delegated.run
        original_read = materializer.delegated.read
        materializer.delegated.run = lambda _arguments: None
        materializer.delegated.read = lambda _target: semantic
        try:
            self.assertEqual(
                materializer.fetch_and_verify(
                    Path("unused"),
                    role="control-materialization",
                    state_sha256="1" * 64,
                    source_commit="2" * 40,
                )["record_sha256"],
                semantic["record_sha256"],
            )
            semantic["input_identities"]["checker_assets"] = {"assets": []}
            semantic.pop("record_sha256")
            semantic["record_sha256"] = hashlib.sha256(
                json.dumps(semantic, separators=(",", ":"), sort_keys=True).encode()
            ).hexdigest()
            with self.assertRaisesRegex(RuntimeError, "failed authentication"):
                materializer.fetch_and_verify(
                    Path("unused"),
                    role="control-materialization",
                    state_sha256="1" * 64,
                    source_commit="2" * 40,
                )
        finally:
            materializer.delegated.run = original_run
            materializer.delegated.read = original_read

    def test_real_inherited_checker_is_migrated_to_derived_slot_one(self):
        source = REPO / "docs/work-packages/20260720-a10m5r14r1-admission-role-matrix-remedy/artifacts/jobs/admission_checker.py"
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw) / "inherited_admission_checker.py"
            target.write_bytes(source.read_bytes())
            prepare.derive_inherited_checker(target)
            text = target.read_text()
            self.assertIn("Path(__file__).resolve().relative_to(remote_root).as_posix()", text)
            self.assertIn("self_logical_name == checker_names[1]", text)
            self.assertIn("plan_assets.get(self_logical_name", text)
            self.assertNotIn('plan_assets.get("admission_checker.py", {}).get("bytes")', text)


if __name__ == "__main__":
    unittest.main()
