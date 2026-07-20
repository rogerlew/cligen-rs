#!/usr/bin/env python3
"""Executable fail-closed tests for the A10M5R12 temporal selector."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
SOURCE = PACKAGE / "artifacts/jobs/temporal_select.py"
try:
    import numpy  # noqa: F401
except ModuleNotFoundError:
    HAS_NUMPY = False
else:
    HAS_NUMPY = True


def selector():
    sys.path.insert(0, str(SOURCE.parent))
    spec = importlib.util.spec_from_file_location("a10m5r12_selector", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load temporal selector")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(HAS_NUMPY, "selector tests require the pinned NumPy runtime")
class TemporalSelectorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = selector()

    def test_metric_registry_is_exact(self) -> None:
        contract = json.loads(
            (PACKAGE / "artifacts/temporal-contract.json").read_text()
        )
        keys = self.module.expected_metric_keys(contract)
        self.assertEqual(len(keys), 188)
        self.assertIn("monthly.12.precipitation_standard_deviation", keys)
        self.assertIn("annual.precipitation_lag1", keys)
        self.assertIn("occurrence.dry_spell_survival_7", keys)

    def test_metric_replay_tolerance_is_tight(self) -> None:
        self.assertTrue(self.module.metrics_close({"x": 1.0}, {"x": 1.0 + 1e-13}))
        self.assertFalse(self.module.metrics_close({"x": 1.0}, {"x": 1.0 + 1e-8}))

    def test_truncated_comparator_fails(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "truncated.cli"
            path.write_text(
                "da mo year prcp dur tp ip tmax tmin rad w-vl w-dir tdew\n"
                "1 1 2001 0 0 0 0 10 0 100 1 2 0\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(RuntimeError, "axis/support failure"):
                self.module.parse_cli(path)

    def test_malformed_numeric_comparator_row_fails(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "malformed.cli"
            path.write_text(
                "1 1 2001 bad 0 0 0 10 0 100 1 2 0\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(RuntimeError, "malformed comparator"):
                self.module.parse_cli(path)


if __name__ == "__main__":
    unittest.main()
