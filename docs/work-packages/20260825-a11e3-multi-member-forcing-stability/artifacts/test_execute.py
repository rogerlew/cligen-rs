#!/usr/bin/env python3
"""Synthetic contract tests for the A11E3 executor."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

import numpy as np


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("a11e3_execute", HERE / "execute.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot import executor")
execute = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = execute
SPEC.loader.exec_module(execute)

STATIONS = [f"s{index:02d}" for index in range(20)]


def hypothesis_rows(region_precip: float = 2.0, nearest_precip: float = 1.0,
                    region_temp: float = 3.0, nearest_temp: float = 2.0) -> list[dict]:
    rows = []
    for member_id in execute.MEMBERS:
        for site in range(20):
            rows.append({
                "station_id": f"s{site:02d}", "member_id": member_id,
                "region_metrics": {
                    execute.PRIMARY_METRICS[0]: region_precip,
                    execute.PRIMARY_METRICS[1]: region_temp,
                    "daily_invariant_failures": 0,
                },
                "nearest_metrics": {
                    execute.PRIMARY_METRICS[0]: nearest_precip,
                    execute.PRIMARY_METRICS[1]: nearest_temp,
                    "daily_invariant_failures": 0,
                },
            })
    return rows


class ExecutionContractTests(unittest.TestCase):
    def test_manifest_is_strict(self) -> None:
        manifest = json.loads((HERE / "execution-manifest-v1.json").read_text())
        self.assertEqual(execute.validate_manifest(manifest), manifest)
        for path, value in (
            (("member_ids",), list(range(7))),
            (("hypothesis", "rule"), "changed"),
            (("rng", "daily_member_stride"), 1),
            (("inputs", "a11e2_evidence_sha256"), "0" * 64),
            (("confirmation_target_access",), True),
        ):
            mutated = copy.deepcopy(manifest)
            target = mutated
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            with self.assertRaises(execute.ExecutionError):
                execute.validate_manifest(mutated)

    def test_unpublished_source_fails_before_dependency_access(self) -> None:
        manifest = execute.validate_manifest(json.loads((HERE / "execution-manifest-v1.json").read_text()))
        with mock.patch.object(execute, "digest", side_effect=AssertionError("dependency accessed")):
            with self.assertRaisesRegex(execute.ExecutionError, "published origin/main"):
                execute.verify_source("not-a-commit", manifest)

    def test_daily_ordinal_preserves_member_zero_and_is_unique(self) -> None:
        self.assertEqual(execute.daily_ordinal(0, 0, 0, 0), 0)
        self.assertEqual(execute.daily_ordinal(0, 19, 15, 11), 3839)
        self.assertEqual(execute.daily_ordinal(1, 0, 0, 0), 3840)
        values = {
            execute.daily_ordinal(member, site, year, month)
            for member in execute.MEMBERS
            for site in range(20)
            for year in range(16)
            for month in range(12)
        }
        self.assertEqual(len(values), 30720)
        self.assertEqual(values, set(range(30720)))

    def test_daily_ordinal_rejects_outside_grid(self) -> None:
        for values in ((8, 0, 0, 0), (0, 20, 0, 0), (0, 0, 16, 0), (0, 0, 0, 12)):
            with self.assertRaises(execute.ExecutionError):
                execute.daily_ordinal(*values)

    def test_common_rng_contract_is_arm_neutral_and_member_specific(self) -> None:
        zero = execute.common_rng_contract("site", 0, 7)
        one = execute.common_rng_contract("site", 1, 7)
        self.assertEqual(zero["annual"]["strategy_id"], execute.ANNUAL_STRATEGY)
        self.assertEqual(zero["hurdle"]["key_strategy_id"], execute.REGION_ARM)
        self.assertEqual(zero["hurdle"]["blake2b_key"].split("\0"),
                         ["a11e1-integrated-v1", "site", execute.REGION_ARM, "0", "month_hurdle"])
        self.assertEqual(zero["daily"]["ordinal_start"], 7 * 192)
        self.assertEqual(one["daily"]["ordinal_start"], 3840 + 7 * 192)
        self.assertNotEqual(zero["hurdle"]["blake2b_key"], one["hurdle"]["blake2b_key"])

    def test_rng_preflight_counts_complete_grid(self) -> None:
        development = [{"point_id": f"s{index:02d}"} for index in range(20)]
        receipt = execute.rng_preflight(development)
        self.assertEqual(receipt["annual_identity_count"], 160)
        self.assertEqual(receipt["hurdle_identity_count"], 160)
        self.assertEqual(receipt["daily_ordinal_count"], 30720)
        self.assertEqual(receipt["daily_domain_stream_count"], 153600)

    def test_adapter_wrapper_changes_only_location(self) -> None:
        old_location = np.zeros(36)
        variances = np.ones(36)
        original = {"location": old_location, "variances": variances, "texture": {"a": 1}}
        replacement = np.full(36, 2.0)
        wrapped = execute.adapter_with_location(original, replacement)
        self.assertIs(original["location"], old_location)
        self.assertIs(wrapped["location"], replacement)
        self.assertIs(wrapped["variances"], variances)
        self.assertIs(wrapped["texture"], original["texture"])
        self.assertEqual(set(wrapped), set(original))

    def test_hypothesis_requires_all_sixteen_strict_improvements(self) -> None:
        rows = hypothesis_rows()
        result = execute.evaluate_hypothesis(rows, STATIONS)
        self.assertEqual(result["disposition"], "STABLE_FOR_EXPLORATION")
        self.assertTrue(result["all_16_primary_deltas_strictly_negative"])
        for row in rows:
            if row["member_id"] == 7:
                row["nearest_metrics"][execute.PRIMARY_METRICS[1]] = 4.0
        result = execute.evaluate_hypothesis(rows, STATIONS)
        self.assertEqual(result["disposition"], "NOT_STABLE_FOR_EXPLORATION")
        self.assertFalse(result["members"]["7"]["both_strictly_improve"])

    def test_hypothesis_tie_is_not_stable(self) -> None:
        rows = hypothesis_rows(nearest_precip=2.0)
        result = execute.evaluate_hypothesis(rows, STATIONS)
        self.assertEqual(result["disposition"], "NOT_STABLE_FOR_EXPLORATION")
        self.assertTrue(all(not member["primary_metrics"][execute.PRIMARY_METRICS[0]]["strictly_negative"] for member in result["members"].values()))

    def test_hypothesis_fails_closed_on_invariant(self) -> None:
        rows = hypothesis_rows()
        rows[0]["nearest_metrics"]["daily_invariant_failures"] = 1
        with self.assertRaisesRegex(execute.ExecutionError, "invariant failure"):
            execute.evaluate_hypothesis(rows, STATIONS)

    def test_hypothesis_fails_closed_on_nonfinite(self) -> None:
        rows = hypothesis_rows()
        rows[0]["nearest_metrics"][execute.PRIMARY_METRICS[0]] = float("nan")
        with self.assertRaisesRegex(execute.ExecutionError, "nonfinite metric"):
            execute.evaluate_hypothesis(rows, STATIONS)

    def test_hypothesis_rejects_incomplete_or_duplicate_grid(self) -> None:
        rows = hypothesis_rows()
        with self.assertRaisesRegex(execute.ExecutionError, "Cartesian grid"):
            execute.evaluate_hypothesis(rows[:-1], STATIONS)
        rows[-1] = copy.deepcopy(rows[0])
        with self.assertRaisesRegex(execute.ExecutionError, "Cartesian grid"):
            execute.evaluate_hypothesis(rows, STATIONS)

    def test_hypothesis_rejects_uneven_station_grid(self) -> None:
        rows = hypothesis_rows()
        rows[0]["station_id"] = "extra-station"
        with self.assertRaisesRegex(execute.ExecutionError, "Cartesian grid"):
            execute.evaluate_hypothesis(rows, STATIONS)

    def test_member_zero_replay_checks_metrics_and_stream_hashes(self) -> None:
        baseline = json.loads(execute.A11E1_EVIDENCE.read_text())
        nearest = json.loads(execute.A11E2_EVIDENCE.read_text())
        baseline_rows = {row["point_id"]: row for row in baseline["rows"] if row["strategy_id"] == execute.REGION_ARM}
        nearest_rows = {row["station_id"]: row for row in nearest["rows"]}
        rows = [{
            "station_id": point, "member_id": 0,
            "region_metrics": baseline_rows[point]["metrics"],
            "region_stream_summary_sha256": baseline_rows[point]["stream_summary_sha256"],
            "nearest_metrics": nearest_rows[point]["candidate_metrics"],
            "nearest_stream_summary_sha256": nearest_rows[point]["stream_summary_sha256"],
        } for point in sorted(baseline_rows)]
        stations = sorted(baseline_rows)
        self.assertTrue(execute.assert_member_zero(rows, stations)["metrics_and_stream_summaries_exact"])
        rows[0]["nearest_stream_summary_sha256"] = "0" * 64
        with self.assertRaisesRegex(execute.ExecutionError, "nearest member-0 replay differs"):
            execute.assert_member_zero(rows, stations)

    def test_strategy_dependency_drift_fails_before_import(self) -> None:
        self.assertIsNone(execute.a11e2)
        with mock.patch.object(execute, "verify_file_at_commit", side_effect=execute.ExecutionError("drift")):
            with self.assertRaisesRegex(execute.ExecutionError, "drift"):
                execute.verify_strategy_dependencies_before_import()
        self.assertIsNone(execute.a11e2)

    def test_runtime_mismatch_fails_before_dependency_import(self) -> None:
        manifest = json.loads((HERE / "execution-manifest-v1.json").read_text())
        with mock.patch.object(execute.np, "__version__", "changed"):
            with self.assertRaisesRegex(execute.ExecutionError, "runtime identity differs"):
                execute.verify_runtime(manifest)
        self.assertIsNone(execute.a11e2)

    def test_schema_pins_every_manifest_field_exactly(self) -> None:
        manifest = json.loads((HERE / "execution-manifest-v1.json").read_text())
        schema = json.loads((HERE / "execution-manifest-v1.schema.json").read_text())
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(schema["required"]), set(manifest))
        self.assertEqual(set(schema["properties"]), set(manifest))
        for name, value in manifest.items():
            self.assertEqual(schema["properties"][name]["const"], value)


if __name__ == "__main__":
    unittest.main()
