#!/usr/bin/env python3
"""Synthetic contract tests for A11E6."""

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("a11e6_execute_tested", HERE / "execute.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC); sys.modules[SPEC.name] = MODULE; SPEC.loader.exec_module(MODULE)


class ContractTests(unittest.TestCase):
    def test_manifest_and_schema(self):
        value = json.loads(MODULE.MANIFEST.read_text())
        self.assertEqual(MODULE.validate_manifest(value)["member_burns"], list(MODULE.BURNS))
        schema = json.loads(MODULE.SCHEMA.read_text())
        self.assertEqual(set(value), set(schema["required"]))
        for name, rule in schema["properties"].items():
            if "const" in rule:
                self.assertEqual(value[name], rule["const"])

    def test_parse_cli_calendar_and_units(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.cli"
            lines = ["header"]
            for year in range(1, 17):
                for month in range(1, 13):
                    import calendar
                    for day in range(1, calendar.monthrange(year, month)[1] + 1):
                        lines.append(f"{day} {month} {year} 1 0 0 0 10 0 0 0 0 0")
            path.write_text("\n".join(lines) + "\n")
            precip, temp, daily_range, wet = MODULE.parse_cli(path)
            self.assertTrue(np.allclose(precip, 30.4375))
            self.assertTrue(np.allclose(temp, 5.0))
            self.assertTrue(np.allclose(daily_range, 10.0))
            self.assertTrue(np.allclose(wet, 1.0))

    def test_decision_rules(self):
        rows = []
        for station in range(20):
            for member in range(8):
                faithful = {metric: 1.0 for metric in MODULE.METRICS}
                circular = {metric: (0.9 if metric in MODULE.INTERANNUAL[:4] else 1.0) for metric in MODULE.METRICS}
                rows.append({"station_id": str(station), "member_id": member, "faithful_metrics": faithful, "circular_metrics": circular})
        decision = MODULE.evaluate(rows, 0.05, 4)
        self.assertEqual(decision["disposition"], "BETTER_THAN_FAITHFUL_FOR_EXPLORATION")
        rows[0]["circular_metrics"][MODULE.LEVEL[0]] = 1.2
        for row in rows[1:81]: row["circular_metrics"][MODULE.LEVEL[0]] = 1.2
        self.assertEqual(MODULE.evaluate(rows, 0.05, 4)["disposition"], "MIXED_VS_FAITHFUL")


if __name__ == "__main__": unittest.main()
