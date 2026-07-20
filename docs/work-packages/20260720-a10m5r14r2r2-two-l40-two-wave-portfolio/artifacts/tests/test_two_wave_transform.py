#!/usr/bin/env python3
"""Focused tests for the two-L40 scheduling-only transformation."""

from __future__ import annotations

import importlib.util
import json
import py_compile
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]
PARENT = REPO / "docs/work-packages/20260720-a10m5r14r2r1-inherited-admission-checker-identity-remedy"
SOURCE = PACKAGE / "artifacts/jobs/prepare_assets.py"

spec = importlib.util.spec_from_file_location("r14r2r2_prepare", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load R14R2R2 preparer")
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


class TwoWaveTransformTests(unittest.TestCase):
    def test_role_map_is_exact_two_wave_schedule(self) -> None:
        value = json.loads((PACKAGE / "artifacts/portfolio-role-map.json").read_text())
        self.assertEqual(value["expected_allocated_devices"], 2)
        self.assertEqual(value["waves"], [[0, 1], [2, 3]])
        self.assertEqual([row["wave"] for row in value["processes"]], [0, 0, 1, 1])
        self.assertEqual([row["allocation_token_index"] for row in value["processes"]], [0, 1, 0, 1])
        self.assertEqual(len({row["role"] for row in value["processes"]}), 4)

    def test_launcher_transform_retains_four_children_and_uses_two_devices(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw) / "portfolio_launcher.py"
            shutil.copyfile(PARENT.parent / "20260720-a10m5r14r2-shared-environment-four-l40-portfolio/artifacts/jobs/portfolio_launcher.py", target)
            text = target.read_text().replace(
                "20260720-a10m5r14r2-shared-environment-four-l40-portfolio",
                prepare.PACKAGE_ID,
            ).replace(
                "a10m5r14r2-shared-environment-four-l40-portfolio-r0",
                prepare.RUN_ID,
            ).replace("a10m5r14r2-submission-admission", prepare.RECORD)
            target.write_text(text)
            prepare.transform_launcher(target)
            transformed = target.read_text()
            py_compile.compile(str(target), doraise=True)
            self.assertIn('allocated_count == 2', transformed)
            self.assertIn('for wave in (0, 1):', transformed)
            self.assertIn('"all_children_launched": len(processes) == 4', transformed)
            self.assertIn('"two_complete_nonoverlapping_waves"', transformed)
            self.assertIn('"two_unique_wave_binding_tokens": len(tokens) == 2 and len(set(tokens)) == 2', transformed)
            self.assertNotIn('"exact_four_l40_allocation"', transformed)
            self.assertNotIn('"unique_child_binding_tokens"', transformed)

    def test_admission_transform_requires_two_available_not_whole_idle_node(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw) / "admission_checker.py"
            shutil.copyfile(PARENT / "artifacts/jobs/admission_checker.py", target)
            text = target.read_text().replace(prepare.PARENT_PACKAGE_ID, prepare.PACKAGE_ID).replace(
                prepare.PARENT_RUN_ID, prepare.RUN_ID
            ).replace(prepare.PARENT_RECORD, prepare.RECORD)
            target.write_text(text)
            prepare.transform_admission(target)
            transformed = target.read_text()
            py_compile.compile(str(target), doraise=True)
            self.assertIn('"at_least_two_l40_idle": active_gpu_count <= 2', transformed)
            self.assertIn('"four_l40_inventory"', transformed)
            self.assertNotIn('"node_idle"', transformed)
            self.assertNotIn('"all_partition_active_allocation_absent"', transformed)
            checker_spec = importlib.util.spec_from_file_location("transformed_checker", target)
            self.assertIsNotNone(checker_spec)
            self.assertIsNotNone(checker_spec.loader)
            checker = importlib.util.module_from_spec(checker_spec)
            checker_spec.loader.exec_module(checker)

            def result(arguments, **_options):
                if arguments[0] == "sinfo":
                    return SimpleNamespace(stdout="node03|mixed|gpu:l40:4\nnode03|mixed|gpu:l40:4\n")
                return SimpleNamespace(stdout="101|RUNNING|other|gres/gpu:1|node03\n")

            output = Path(raw) / "occupancy.json"
            with patch.object(checker.subprocess, "run", side_effect=result):
                receipt = checker.capture_occupancy(output)
            self.assertTrue(receipt["valid"])
            self.assertEqual(receipt["active_gpu_count"], 1)
            self.assertEqual(receipt["sinfo"], ["node03|mixed|gpu:l40:4"])
            self.assertTrue(checker.authenticated(receipt))

            def crowded(arguments, **_options):
                if arguments[0] == "sinfo":
                    return SimpleNamespace(stdout="node03|mixed|gpu:l40:4\n")
                return SimpleNamespace(stdout="101|RUNNING|a|gres/gpu:1|node03\n102|RUNNING|b|gres/gpu:2|node03\n")

            crowded_output = Path(raw) / "crowded.json"
            with patch.object(checker.subprocess, "run", side_effect=crowded):
                crowded_receipt = checker.capture_occupancy(crowded_output)
            self.assertFalse(crowded_receipt["valid"])
            self.assertEqual(crowded_receipt["active_gpu_count"], 3)

    def test_contract_reduces_ceiling_without_changing_four_arm_count(self) -> None:
        value = json.loads((PACKAGE / "artifacts/job-local-capacity-contract.json").read_text())
        resources = value["resources"]
        self.assertEqual(resources["gpus_per_portfolio"], 2)
        self.assertEqual(resources["process_waves"], 2)
        self.assertEqual(resources["science_arm_count"], 4)
        self.assertEqual(resources["total_gpu_minute_ceiling"], 515)


if __name__ == "__main__":
    unittest.main()
