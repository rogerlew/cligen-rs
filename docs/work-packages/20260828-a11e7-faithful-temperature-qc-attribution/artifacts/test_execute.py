#!/usr/bin/env python3
"""Synthetic contract tests for A11E7."""

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("a11e7_execute_tested", HERE / "execute.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC); sys.modules[SPEC.name] = MODULE; SPEC.loader.exec_module(MODULE)


class ContractTests(unittest.TestCase):
    def test_manifest_and_schema(self):
        value = json.loads(MODULE.MANIFEST.read_text()); schema = json.loads(MODULE.SCHEMA.read_text())
        self.assertEqual(len(MODULE.validate_manifest(value)["burns"]), 32)
        self.assertEqual(set(value), set(schema["required"]))
        for name, rule in schema["properties"].items():
            if "const" in rule: self.assertEqual(value[name], rule["const"])

    def test_parse_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.cli"; lines = ["header"]
            for year in range(1, 17):
                for month in range(1, 13):
                    import calendar
                    for day in range(1, calendar.monthrange(year, month)[1] + 1): lines.append(f"{day} {month} {year} 1 0 0 0 10 0 0 0 0 0")
            path.write_text("\n".join(lines) + "\n"); precipitation, temperature, daily_range, wet = MODULE.parse_cli(path)
            self.assertTrue(np.allclose(precipitation, 30.4375)); self.assertTrue(np.allclose(temperature, 5.0)); self.assertTrue(np.allclose(daily_range, 10.0)); self.assertTrue(np.allclose(wet, 1.0))

    def test_process_summaries(self):
        months = {name: 16 for name in ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")}; zeros = {name: 0 for name in months}
        retries = [{"parameter": parameter, "rejected_attempts": (months if parameter in (2, 3) else zeros), "accepted_batches": months} for parameter in range(1, 10)]
        faithful = {"process": {"qc_filter": "faithful", "retries": retries, "counterfactual": None, "cap_give_ups": []}}
        self.assertEqual(MODULE.process_summary(faithful, "faithful")["temperature_rejected_attempts"], 384)
        by_parameter = [{"parameter": parameter, "batches": months, "would_reject": (months if parameter == 2 else zeros)} for parameter in range(1, 10)]
        off = {"process": {"qc_filter": "off", "counterfactual": {"by_parameter": by_parameter}}}
        self.assertEqual(MODULE.process_summary(off, "off")["temperature_counterfactual_rejection_fraction"], 0.5)

    def test_decision_material_structural(self):
        rows = []
        for station in range(20):
            for member in range(32):
                base = {name: 1.0 for name in MODULE.METRICS}; off = dict(base); off[MODULE.METRICS[1]] = 0.8
                rows.append({"station_id": str(station), "member_id": member, "arms": {"faithful": {"annual_temperature_variance_ratio": 0.1, "metrics": base}, "off": {"annual_temperature_variance_ratio": 0.2, "metrics": off}}})
        manifest = json.loads(MODULE.MANIFEST.read_text()); decision = MODULE.build_decision(rows, manifest)
        self.assertEqual(decision["disposition"], "QC_MATERIAL_AND_STRUCTURAL_DEFICIT_REMAINS")


if __name__ == "__main__": unittest.main()
