#!/usr/bin/env python3
"""Synthetic contract tests for the A11E2 executor."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from unittest import mock
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("a11e2_execute", HERE / "execute.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot import executor")
execute = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = execute
SPEC.loader.exec_module(execute)


def synthetic_selection_inputs() -> tuple[dict, dict, list[dict]]:
    stations = [{"station_id": f"s{index:02d}", "latitude": 0.0, "longitude": 0.0} for index in range(20)]
    panel = {"schema_version": 1, "daily_data_accessed": False, "selected_station_count": 20, "stations": stations}
    candidates = [{"point_id": f"p{index:04d}", "latitude": 0.0, "longitude": float(index % 170),
                   "regime": "cold", "role": "candidate_fit"} for index in range(1200)]
    cohort = {"locations": candidates}
    development = [{"station_id": f"s{index:02d}", "stratum": "cold", "role": "development"} for index in range(20)]
    return panel, cohort, development


class ExecutionContractTests(unittest.TestCase):
    def test_manifest_is_strict(self) -> None:
        manifest = json.loads((HERE / "execution-manifest-v1.json").read_text())
        self.assertEqual(execute.validate_manifest(manifest), manifest)
        for path, value in (
            (("strategy_id",), "changed"),
            (("forcing_selector", "uses_candidate_regime"), True),
            (("hypothesis", "rule"), "changed"),
            (("inherited_contract", "rng_reference_strategy_id"), "changed"),
            (("inputs", "a11e1_evidence_sha256"), "0" * 64),
        ):
            mutated = copy.deepcopy(manifest)
            target = mutated
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            with self.assertRaises(execute.ExecutionError):
                execute.validate_manifest(mutated)

    def test_unpublished_source_fails_before_input_access(self) -> None:
        manifest = execute.validate_manifest(json.loads((HERE / "execution-manifest-v1.json").read_text()))
        with self.assertRaisesRegex(execute.ExecutionError, "published origin/main"):
            execute.verify_source("not-a-commit", manifest)

    def test_strategy_dependency_drift_fails_before_import(self) -> None:
        base_manifest = json.loads(execute.BASE_MANIFEST.read_text())
        with mock.patch.object(execute, "digest", return_value="0" * 64):
            with self.assertRaisesRegex(execute.ExecutionError, "strategy dependency drifted"):
                execute.verify_strategy_dependencies(base_manifest)

    def test_haversine_is_symmetric_and_zero_at_identity(self) -> None:
        self.assertEqual(execute.haversine_km(10.0, -20.0, 10.0, -20.0), 0.0)
        left = execute.haversine_km(10.0, -20.0, 30.0, 40.0)
        right = execute.haversine_km(30.0, 40.0, 10.0, -20.0)
        self.assertAlmostEqual(left, right)

    def test_selector_is_coordinate_only_and_tie_stable(self) -> None:
        panel, cohort, development = synthetic_selection_inputs()
        cohort["locations"][0]["regime"] = "humid"
        receipt = execute.build_selection(panel, cohort, development)
        self.assertEqual(len(receipt["rows"]), 20)
        self.assertTrue(all(row["candidate_point_id"] == "p0000" for row in receipt["rows"]))
        self.assertTrue(all(row["candidate_regime"] == "humid" for row in receipt["rows"]))

    def test_selector_rejects_role_drift(self) -> None:
        panel, cohort, development = synthetic_selection_inputs()
        development[0]["role"] = "fit_validation"
        with self.assertRaises(execute.ExecutionError):
            execute.build_selection(panel, cohort, development)

    def test_candidate_location_uses_target_adapter_transform(self) -> None:
        shape = (30, 12)
        summary = {"point_id": "candidate", "regime": "source", "role": "candidate_fit",
                   "precipitation": np.full(shape, 20.0), "wet_count": np.ones(shape, dtype=np.int64),
                   "tmean": np.full(shape, 10.0), "dtr": np.full(shape, 5.0)}
        adapters = {"target": {"floors": np.full(12, 2.0)}}
        location = execute.candidate_location(summary, "target", adapters)
        np.testing.assert_allclose(location[:12], np.log(18.0))
        np.testing.assert_allclose(location[12:24], 10.0)
        np.testing.assert_allclose(location[24:], np.log(5.0))

    def test_hypothesis_requires_both_primary_improvements(self) -> None:
        rows = []
        for index in range(20):
            rows.append({"baseline_metrics": {execute.PRIMARY_METRICS[0]: 2.0, execute.PRIMARY_METRICS[1]: 3.0},
                         "candidate_metrics": {execute.PRIMARY_METRICS[0]: 1.0, execute.PRIMARY_METRICS[1]: 2.0,
                                               "daily_invariant_failures": 0}})
        self.assertEqual(execute.evaluate_hypothesis(rows)["disposition"], "SUPPORTED_FOR_EXPLORATION")
        for row in rows[:11]:
            row["candidate_metrics"][execute.PRIMARY_METRICS[1]] = 100.0
        self.assertEqual(execute.evaluate_hypothesis(rows)["disposition"], "NOT_SUPPORTED")

    def test_hypothesis_rejects_invariant_failure(self) -> None:
        rows = [{"baseline_metrics": {execute.PRIMARY_METRICS[0]: 2.0, execute.PRIMARY_METRICS[1]: 3.0},
                 "candidate_metrics": {execute.PRIMARY_METRICS[0]: 1.0, execute.PRIMARY_METRICS[1]: 2.0,
                                       "daily_invariant_failures": int(index == 0)}} for index in range(20)]
        with self.assertRaisesRegex(execute.ExecutionError, "invariant failure"):
            execute.evaluate_hypothesis(rows)

    def test_only_location_changes_and_common_rng_identity_is_inherited(self) -> None:
        class Spy:
            def __init__(self) -> None:
                self.call = None

            def evaluate_site(self, observed, strategy_id, model, adapter, site_ordinal):
                self.call = (observed, strategy_id, model, adapter, site_ordinal)
                return {"strategy_id": strategy_id}

        spy = Spy()
        original_location = np.zeros(36)
        variances = np.ones(36)
        adapter = {"location": original_location, "variances": variances, "annual_variance": 1.0}
        replacement = np.full(36, 2.0)
        observed, model = {"point_id": "site"}, {"strategy_id": execute.ANNUAL_STRATEGY}
        execute.evaluate_with_location(observed, adapter, replacement, model, 7, spy)
        self.assertIs(adapter["location"], original_location)
        self.assertIs(spy.call[3]["location"], replacement)
        self.assertIs(spy.call[3]["variances"], variances)
        self.assertEqual(spy.call[1], execute.REFERENCE_STRATEGY)
        self.assertEqual(spy.call[4], 7)
        contract = execute.common_rng_contract("site", 7)
        self.assertEqual(contract["annual"]["domain"], "annual_target")
        self.assertEqual(contract["hurdle"]["key_strategy_id"], execute.REFERENCE_STRATEGY)
        self.assertEqual(contract["hurdle"]["blake2b_key"].split("\0"),
                         ["a11e1-integrated-v1", "site", execute.REFERENCE_STRATEGY, "0", "month_hurdle"])
        self.assertEqual(contract["daily"]["domains"], ["wet_count", "occurrence", "amount", "temperature", "range"])

    def test_bootstrap_replays(self) -> None:
        differences = {f"s{index:02d}": float(index) for index in range(20)}
        manifest = json.loads((HERE / "execution-manifest-v1.json").read_text())
        self.assertEqual(execute.paired_bootstrap(differences, manifest), execute.paired_bootstrap(differences, manifest))


if __name__ == "__main__":
    unittest.main()
