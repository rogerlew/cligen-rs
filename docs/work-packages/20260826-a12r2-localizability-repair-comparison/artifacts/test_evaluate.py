#!/usr/bin/env python3
"""Synthetic tests for the prospective A12R2 evaluator."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path

import numpy as np


PATH = Path(__file__).with_name("evaluate.py")
SPEC = importlib.util.spec_from_file_location("a12r2_evaluate", PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def ordinary_par() -> dict[str, np.ndarray]:
    return {
        "mean": np.ones(12, dtype=np.float32),
        "pww": np.full(12, 0.5, dtype=np.float32),
        "pwd": np.full(12, 0.25, dtype=np.float32),
        "intensity": np.ones(12, dtype=np.float32),
    }


def normals() -> dict[str, list[float]]:
    return {"monthly_ppt_in": [1.0] * 12, "monthly_tmax_f": [50.0] * 12,
            "monthly_tmin_f": [40.0] * 12}


class EvaluationTests(unittest.TestCase):
    def test_manifest_is_strict_and_current(self) -> None:
        manifest = MODULE.validate_manifest(json.loads(MODULE.MANIFEST_PATH.read_text()))
        self.assertEqual(tuple(manifest["policies"]), MODULE.POLICIES)
        schema = json.loads(MODULE.SCHEMA_PATH.read_text())
        for name, contract in schema["properties"].items():
            if "const" in contract:
                self.assertEqual(manifest[name], contract["const"])
        changed = json.loads(json.dumps(manifest))
        changed["bootstrap"]["seed"] += 1
        with self.assertRaises(MODULE.EvaluationError):
            MODULE.validate_manifest(changed)

    def test_selector_parity_diagnostic_self_hash_and_binding(self) -> None:
        value = json.loads(MODULE.DIAGNOSTIC_PATH.read_text())
        claimed = value.pop("receipt_sha256")
        self.assertEqual(MODULE.BASE.canonical_digest(value), claimed)
        manifest = MODULE.validate_manifest(json.loads(MODULE.MANIFEST_PATH.read_text()))
        self.assertEqual(manifest["selector_parity"]["diagnostic_receipt_sha256"], claimed)

    def test_predecessor_dependencies_authenticate_before_base_import(self) -> None:
        self.assertEqual(MODULE.AUTHENTICATED_PREDECESSORS, MODULE.FROZEN_PREDECESSORS)

    def test_production_repair_method_identifier_is_exact(self) -> None:
        source = MODULE.LOCALIZE_PATH.read_text()
        self.assertIn('Some("degenerate_occurrence_independent_prism_v1")', source)
        self.assertEqual(MODULE.REPAIR_METHOD_ID, "degenerate_occurrence_independent_prism_v1")

    def test_repair_is_identical_to_ordinary_when_no_month_is_degenerate(self) -> None:
        par = ordinary_par()
        repaired, events = MODULE.repair_parameters(par, normals())
        ordinary = MODULE.BASE.localized_parameters(par, normals())
        self.assertEqual(events, [])
        for name in repaired:
            np.testing.assert_array_equal(repaired[name], ordinary[name])

    def test_repair_revives_exact_all_dry_month_on_encoded_grid(self) -> None:
        par = ordinary_par()
        par["pww"][5] = 0.0
        par["pwd"][5] = 0.0
        repaired, events = MODULE.repair_parameters(par, normals())
        self.assertEqual([event["month"] for event in events], [6])
        self.assertEqual(repaired["pww"][5], repaired["pwd"][5])
        self.assertGreater(repaired["pww"][5], 0.0)
        self.assertAlmostEqual(MODULE.BASE.DAYS[5] * repaired["pww"][5]
                               * repaired["mean"][5], 1.0, places=2)

    def test_repair_uses_f64_decimal_q_before_rendering_mean(self) -> None:
        par = ordinary_par()
        par["pww"][5] = 0.0
        par["pwd"][5] = 0.0
        target = normals()
        target["monthly_ppt_in"][5] = np.nextafter(0.0645, 0.0)
        repaired, _ = MODULE.repair_parameters(par, target)
        self.assertEqual(float(repaired["pww"][5]), float(np.float32(0.01)))
        self.assertEqual(float(repaired["mean"][5]), float(np.float32(0.21)))

    def test_repair_rejects_noneligible_degenerate_state(self) -> None:
        par = ordinary_par()
        par["pwd"][2] = 0.0
        with self.assertRaises(MODULE.EvaluationError):
            MODULE.repair_parameters(par, normals())

    def test_failure_details_extracts_month(self) -> None:
        self.assertEqual(MODULE.failure_details(MODULE.EvaluationError("month 7 cannot be localized")),
                         (7, "month 7 cannot be localized"))

    def test_named_hold_preserves_terminal_identity(self) -> None:
        hold = MODULE.EvaluationHold("HOLD-REPAIR-INELIGIBLE", "p1", "closest: month 2")
        self.assertEqual((hold.disposition, hold.point_id, hold.detail),
                         ("HOLD-REPAIR-INELIGIBLE", "p1", "closest: month 2"))

    def test_structured_repair_receipt_tamper_fails(self) -> None:
        event = {"month": 6}
        with self.assertRaises(MODULE.EvaluationError):
            MODULE.assert_repair_receipt_parity([event], [{"month": 7}], [
                f"warning: {MODULE.REPAIR_METHOD_ID} month 6 source PWW=0 PWD=0"
            ])

    def test_selection_semantic_digest_is_temp_root_independent(self) -> None:
        def receipt(root: str) -> dict[str, object]:
            return {"selected_station_id": "s1", "selected_source_par_path": f"{root}/s1",
                    "candidates": [{"station_id": "s1", "path": f"{root}/s1"}]}
        first = MODULE.normalize_selection_receipt(receipt("/tmp/first"))
        second = MODULE.normalize_selection_receipt(receipt("/tmp/second"))
        self.assertEqual(MODULE.BASE.canonical_digest(first), MODULE.BASE.canonical_digest(second))

    def test_expected_runtime_failure_requires_nonzero_and_no_output(self) -> None:
        target = {"point_id": "p", "latitude": 1.0, "longitude": 2.0}
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(MODULE.subprocess, "run",
                              return_value=SimpleNamespace(returncode=2, stderr="failed")):
                receipt = MODULE.runtime_repair_expected_failure(
                    Path("/binary"), Path(temporary), target
                )
            self.assertTrue(receipt["expected_failure"])
            with patch.object(MODULE.subprocess, "run",
                              return_value=SimpleNamespace(returncode=0, stderr="")):
                with self.assertRaises(MODULE.EvaluationError):
                    MODULE.runtime_repair_expected_failure(Path("/binary"), Path(temporary), target)

    def test_selector_component_tolerance_accepts_empirical_libm_drift_only(self) -> None:
        manifest = MODULE.validate_manifest(json.loads(MODULE.MANIFEST_PATH.read_text()))
        station = {"id": "s"}
        diagnostic = {"station_id": "s", "distance_rank": 0, "latitude_rank": 0,
                      "ppt_rank": 0, "tmax_rank": 0, "tmin_rank": 0,
                      "distance_km": 10.0, "latitude_error": 1.0, "ppt_error": 2.0,
                      "tmax_error": 3.0, "tmin_error": 4.0}
        rust = {"selected_station_id": "s", "candidates": [{**diagnostic,
                "distance_km": 10.0 + 6.7e-13}]}
        MODULE.verify_selector_parity(rust, {"cligen_prism_rank_sum_v1": station},
                                      [diagnostic], manifest)
        rust["candidates"][0]["distance_km"] = 10.0 + 2e-12
        with self.assertRaises(MODULE.EvaluationError):
            MODULE.verify_selector_parity(rust, {"cligen_prism_rank_sum_v1": station},
                                          [diagnostic], manifest)

    def test_fixed_all_ten_scores_drive_six_arm_mapping_and_displacement(self) -> None:
        rows = [{"id": f"s{i}", "path": Path(f"/s{i}"), "distance_km": float(i)}
                for i in range(10)]
        diagnostics = [{
            "station_id": f"s{i}", "source_par_sha256": f"{i:064x}",
            "distance_km": float(i), "latitude_error": float(i), "ppt_error": float(i),
            "tmax_error": float(i), "tmin_error": float(i), "distance_rank": i,
            "latitude_rank": i, "ppt_rank": i, "tmax_rank": i, "tmin_rank": i,
            "current_score": float([0, 5, 1, 2, 3, 4, 6, 7, 8, 9][i]),
            "elevation_rank": i, "reference_score": float([5, 4, 3, 0, 1, 2, 6, 7, 8, 9][i]),
        } for i in range(10)]
        raw = {"closest_v1": rows[0], "cligen_prism_rank_sum_v1": rows[0],
               "wepppy_elevation_prism_reference_v1": rows[3]}
        cache = {row["path"]: {"eligible": row["id"] != "s0"} for row in rows}

        def localize(par: dict[str, bool], _normals: dict[str, object]) -> dict[str, object]:
            if not par["eligible"]:
                raise MODULE.EvaluationError("month 6 cannot be localized")
            return {}

        with patch.object(MODULE.BASE, "select_policies", return_value=(raw, diagnostics)), \
                patch.object(MODULE.BASE, "localized_parameters", side_effect=localize):
            arms, matrix, displacement = MODULE.select_arms(rows, {"point_id": "p"}, {}, cache)
        self.assertEqual(len(matrix), 10)
        self.assertEqual(set(arms), set(MODULE.POLICIES))
        self.assertEqual(arms[MODULE.ARM[("localizable", "closest")]]["id"], "s1")
        self.assertEqual(arms[MODULE.ARM[("localizable", "current")]]["id"], "s2")
        self.assertEqual(arms[MODULE.ARM[("localizable", "reference")]]["id"], "s3")
        self.assertTrue(displacement["closest"]["winner_changed"])
        self.assertTrue(displacement["current"]["winner_changed"])
        self.assertFalse(displacement["reference"]["winner_changed"])

    def test_zero_eligible_pool_returns_complete_matrix_without_early_raise(self) -> None:
        rows = [{"id": f"s{i}", "path": Path(f"/s{i}"), "distance_km": float(i)}
                for i in range(10)]
        diagnostics = [{"station_id": f"s{i}", "source_par_sha256": f"{i:064x}",
                        "distance_km": float(i), "current_score": float(i),
                        "reference_score": float(i)} for i in range(10)]
        raw = {"closest_v1": rows[0], "cligen_prism_rank_sum_v1": rows[0],
               "wepppy_elevation_prism_reference_v1": rows[0]}
        cache = {row["path"]: {} for row in rows}
        with patch.object(MODULE.BASE, "select_policies", return_value=(raw, diagnostics)), \
                patch.object(MODULE.BASE, "localized_parameters",
                             side_effect=MODULE.EvaluationError("month 1 cannot be localized")):
            arms, matrix, _ = MODULE.select_arms(rows, {"point_id": "p"}, {}, cache)
        self.assertEqual(len(matrix), 10)
        self.assertEqual(len(arms), 3)

    def test_paired_support_rule_accepts_uniform_improvement(self) -> None:
        manifest = MODULE.validate_manifest(json.loads(MODULE.MANIFEST_PATH.read_text()))
        baseline, candidate = [], []
        for _ in range(20):
            base_metrics = {metric: 1.0 for metric in MODULE.METRICS}
            candidate_metrics = {metric: 0.8 for metric in MODULE.METRICS}
            base_metrics["composite"] = 1.0
            candidate_metrics["composite"] = 0.8
            baseline.append({"metrics": base_metrics})
            candidate.append({"metrics": candidate_metrics})
        comparison = MODULE.paired_comparison(candidate, baseline, manifest)
        self.assertTrue(comparison["supported"])
        self.assertAlmostEqual(comparison["paired_composite_median_delta"], -0.2)

    def test_paired_support_rule_rejects_family_worsening(self) -> None:
        manifest = MODULE.validate_manifest(json.loads(MODULE.MANIFEST_PATH.read_text()))
        baseline, candidate = [], []
        for _ in range(20):
            base_metrics = {metric: 1.0 for metric in MODULE.METRICS}
            candidate_metrics = {metric: 0.7 for metric in MODULE.METRICS}
            candidate_metrics[MODULE.METRICS[0]] = 1.2
            base_metrics["composite"] = 1.0
            candidate_metrics["composite"] = float(np.mean(list(candidate_metrics.values())))
            baseline.append({"metrics": base_metrics})
            candidate.append({"metrics": candidate_metrics})
        self.assertFalse(MODULE.paired_comparison(candidate, baseline, manifest)["supported"])

    def test_strategy_disposition_four_way_table(self) -> None:
        self.assertEqual(MODULE.strategy_disposition([True] * 3, [False] * 3),
                         "LOCALIZABILITY_FILTER_PREFERRED")
        self.assertEqual(MODULE.strategy_disposition([False] * 3, [True] * 3),
                         "SELECTED_DONOR_REPAIR_PREFERRED")
        self.assertEqual(MODULE.strategy_disposition([True, False, False], [False] * 3),
                         "STRATEGY_EFFECT_MIXED")
        self.assertEqual(MODULE.strategy_disposition([False] * 3, [False] * 3),
                         "NO_UNIFORM_STRATEGY_ADVANTAGE")

    def test_bootstrap_is_replayable_and_domain_separated(self) -> None:
        manifest = MODULE.validate_manifest(json.loads(MODULE.MANIFEST_PATH.read_text()))
        values = np.linspace(-1.0, 1.0, 31)
        self.assertEqual(MODULE.BASE.bootstrap_interval(values, manifest),
                         MODULE.BASE.bootstrap_interval(values, manifest))
        changed = json.loads(json.dumps(manifest))
        changed["bootstrap"]["domain"] = "other"
        self.assertNotEqual(
            MODULE.BASE.bootstrap_rng(manifest["bootstrap"]).integers(0, 100, 10).tolist(),
            MODULE.BASE.bootstrap_rng(changed["bootstrap"]).integers(0, 100, 10).tolist(),
        )


if __name__ == "__main__":
    unittest.main()
