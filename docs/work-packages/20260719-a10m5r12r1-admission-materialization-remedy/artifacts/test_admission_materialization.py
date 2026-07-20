#!/usr/bin/env python3
"""Executable guards for the A10M5R12R1 admission materializer."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

PACKAGE = Path(__file__).resolve().parents[1]
SOURCE = PACKAGE / "artifacts/jobs/materialize_admission.py"
SPEC = importlib.util.spec_from_file_location("materialize_admission", SOURCE)
assert SPEC is not None and SPEC.loader is not None
MATERIALIZER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MATERIALIZER)


class AdmissionMaterializationTest(unittest.TestCase):
    def test_role_and_setup_matrix_is_closed(self) -> None:
        first = "continuous-medium-latent-process-k2"
        path = f"{MATERIALIZER.REMOTE_ROOT}/results/{first}/setup.json"
        self.assertEqual(MATERIALIZER.parse_setups([f"{first}={path}"]), [(first, path)])
        with self.assertRaisesRegex(RuntimeError, "invalid setup binding"):
            MATERIALIZER.parse_setups([f"unregistered={path}"])
        with self.assertRaisesRegex(RuntimeError, "invalid setup binding"):
            MATERIALIZER.parse_setups([f"{first}=/tmp/setup.json"])

    def test_local_state_and_publication_paths_are_exact(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            run = Path(raw) / "runs" / MATERIALIZER.RUN_ID
            state = run / "private/state.json"
            publication = run / "publication"
            state.parent.mkdir(parents=True)
            publication.mkdir()
            value = {
                "package_id": MATERIALIZER.PACKAGE_ID,
                "run_id": MATERIALIZER.RUN_ID,
                "run_state": "VERIFIED",
                "source_commit": "a" * 40,
            }
            state.write_text(json.dumps(value), encoding="utf-8")
            self.assertEqual(
                MATERIALIZER.verify_local_paths(state, publication, "a" * 40),
                value,
            )
            with self.assertRaisesRegex(RuntimeError, "paths are not exact"):
                MATERIALIZER.verify_local_paths(
                    state, Path(raw) / "wrong-publication", "a" * 40
                )

    def test_materializer_binds_pre_submit_sequence(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn('if digest(options.state) != state_sha256', source)
        self.assertIn('"toolkit_state_sha256"', source)
        self.assertIn('"decision") == "PASS"', source)
        self.assertIn('"record_sha256"', source)
        self.assertIn('"/bin/test",\n            "!",\n            "-e"', source)

    def test_absent_remote_receipt_invokes_checker_and_existing_reuses(self) -> None:
        with mock.patch.object(
            MATERIALIZER.subprocess,
            "run",
            return_value=SimpleNamespace(returncode=0),
        ), mock.patch.object(MATERIALIZER, "run") as invoke:
            MATERIALIZER.invoke_checker("control-materialization", [])
            invoke.assert_called_once()
            self.assertTrue(
                any(
                    item.endswith("/admission_checker.py")
                    for item in invoke.call_args.args[0]
                )
            )

        with mock.patch.object(
            MATERIALIZER.subprocess,
            "run",
            return_value=SimpleNamespace(returncode=1),
        ), mock.patch.object(MATERIALIZER, "run") as invoke:
            MATERIALIZER.invoke_checker("control-materialization", [])
            invoke.assert_not_called()


if __name__ == "__main__":
    unittest.main()
