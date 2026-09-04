#!/usr/bin/env python3
"""Synthetic tests for the prospective A11E8 executor."""

from __future__ import annotations

import calendar
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("a11e8_execute_tested", HERE / "execute.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def daily_row(day: int, month: int, year: int) -> str:
    row = (
        f"{day:3d}{month:3d} {year:5d} "
        f"{1.0:5.1f} {2.0:5.2f} {0.5:4.2f} {3.0:6.2f} "
        f"{10.0:5.1f} {2.0:5.1f} {100.0:4.0f} {4.0:4.1f}  "
        f"{180.0:4.0f} {0.0:5.1f}"
    )
    assert len(row) == 70
    return row + "\n"


def synthetic_cli(path: Path) -> None:
    lines = [
        "synthetic header\n",
        " da mo year  prcp  dur   tp     ip  tmax  tmin  rad  w-vl w-dir  tdew\n",
        "             (mm)  (h)               (C)   (C) (l/d) (m/s)(Deg)   (C)\n",
    ]
    for year in range(1, 17):
        for month in range(1, 13):
            for day in range(1, calendar.monthrange(year, month)[1] + 1):
                lines.append(daily_row(day, month, year))
    path.write_text("".join(lines))


def scorecard(annual: float, other: float) -> dict[str, float]:
    values = {metric: other for metric in MODULE.SCORECARD_METRICS}
    values["annual_temperature_dispersion_error"] = annual
    return values


class ExecutorTests(unittest.TestCase):
    def test_manifest_and_runtime_are_frozen(self):
        manifest = MODULE.validate_manifest(json.loads(MODULE.MANIFEST.read_text()))
        self.assertEqual(
            manifest["runtime"],
            {
                "python": "3.12.14",
                "numpy": "2.3.5",
                "system": "Darwin",
                "machine": "arm64",
                "linear_algebra_threads": 1,
                "rustc": "rustc 1.97.1 (8bab26f4f 2026-07-14)",
                "cargo": "cargo 1.97.1 (c980f4866 2026-06-30)",
            },
        )
        self.assertEqual(sum(len(row["burns"]) for row in manifest["cohorts"]), 32)

    def test_rank_one_fit_recovers_positive_loading_direction(self):
        state = np.arange(16, dtype=np.float64) - 7.5
        basis = np.arange(1, 13, dtype=np.float64) / 12.0
        observed = np.outer(state, basis)
        result = MODULE.fit_thermal_loading(observed, [np.zeros((16, 12)) for _ in range(32)])
        expected = basis * float(np.std(state, ddof=1))
        self.assertTrue(np.allclose(result["loading_c"], expected, rtol=1e-12, atol=1e-12))

    def test_overlay_changes_only_temperature_and_preserves_differences(self):
        with tempfile.TemporaryDirectory() as directory:
            faithful = Path(directory) / "faithful.cli"
            candidate = Path(directory) / "candidate.cli"
            synthetic_cli(faithful)
            receipt = MODULE.overlay_cli(
                faithful,
                candidate,
                np.full(12, 0.1, dtype=np.float64),
                [1.0] * 16,
            )
            self.assertEqual(receipt["daily_rows"], 5844)
            original_lines = faithful.read_text().splitlines()
            candidate_lines = candidate.read_text().splitlines()
            for original, changed in zip(original_lines[3:], candidate_lines[3:]):
                self.assertEqual(original[:37], changed[:37])
                self.assertEqual(original[42:43], changed[42:43])
                self.assertEqual(original[48:65], changed[48:65])
                self.assertEqual(int(10 * float(changed[37:42])), 101)
                self.assertEqual(int(10 * float(changed[43:48])), 21)
                self.assertEqual(int(10 * float(changed[65:70])), 1)
            original = MODULE.parse_cli(faithful)
            changed = MODULE.parse_cli(candidate)
            self.assertTrue(np.array_equal(original[0], changed[0]))
            self.assertTrue(np.allclose(changed[1] - original[1], 0.1))
            self.assertTrue(np.array_equal(original[2], changed[2]))

    def test_component_and_selector_gates_are_independent(self):
        manifest = json.loads(MODULE.MANIFEST.read_text())
        rows = []
        for station in range(20):
            for cohort in range(4):
                for index in range(8):
                    rows.append(
                        {
                            "station_id": f"station-{station}",
                            "cohort_id": cohort,
                            "candidate_index": index,
                            "models": {
                                MODULE.contract.MODEL_ORDER[0]: {"metrics": scorecard(1.0, 1.0)},
                                MODULE.contract.MODEL_ORDER[1]: {"metrics": scorecard(0.8, 0.9)},
                            },
                        }
                    )
        selections = []
        for station in range(20):
            for cohort in range(4):
                selections.append(
                    {
                        "station_id": f"station-{station}",
                        "cohort_id": cohort,
                        "mixed": {
                            "model_id": MODULE.contract.MODEL_ORDER[1],
                            "metrics": scorecard(0.8, 0.9),
                        },
                        "faithful_only": {
                            "model_id": MODULE.contract.MODEL_ORDER[0],
                            "metrics": scorecard(1.0, 1.0),
                        },
                    }
                )
        decision = MODULE.build_decision(rows, selections, manifest)
        self.assertEqual(decision["disposition"], "THERMAL_COMPONENT_RETAINED_SELECTOR_USEFUL")
        self.assertTrue(decision["component"]["passes"])
        self.assertTrue(decision["selector"]["useful"])


if __name__ == "__main__":
    unittest.main()
