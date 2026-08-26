#!/usr/bin/env python3
"""Synthetic contract tests for the A11E4 attribution analyzer."""

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
SPEC = importlib.util.spec_from_file_location("a11e4_analyze", HERE / "analyze.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot import analyzer")
analyze = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = analyze
SPEC.loader.exec_module(analyze)


def synthetic_station_summaries() -> list[dict]:
    manifest = json.loads((HERE / "analysis-manifest-v1.json").read_text())
    rows = []
    ordinal = 0
    mismatch_by_level = {"cold": 3, "monsoonal_transition": 2, "non_monsoonal_semi_arid": 3}
    for level, size in zip(manifest["model"]["station_regime_levels"], manifest["model"]["station_regime_sizes"]):
        mismatch_count = mismatch_by_level.get(level, 0)
        for within in range(size):
            mismatch = within < mismatch_count
            successes = (ordinal * 3 + 2) % 9
            rows.append({
                "station_id": f"s{ordinal:02d}", "station_regime": level,
                "candidate_regime": "different" if mismatch else level,
                "same_regime": not mismatch, "great_circle_distance_km": float(ordinal + 1),
                "both_improvement_fraction": successes / 8.0,
                "both_improvement_by_member": [index < successes for index in range(8)],
            })
            ordinal += 1
    return rows


def synthetic_evidence_and_selection() -> tuple[dict, dict]:
    summaries = synthetic_station_summaries()
    selection_rows, evidence_rows = [], []
    for summary in summaries:
        selection_rows.append({
            "station_id": summary["station_id"], "station_regime": summary["station_regime"],
            "candidate_point_id": f"p-{summary['station_id']}", "candidate_regime": summary["candidate_regime"],
            "great_circle_distance_km": summary["great_circle_distance_km"],
        })
        for member in analyze.MEMBERS:
            success = summary["both_improvement_by_member"][member]
            region = {analyze.PRIMARY_METRICS[0]: 2.0, analyze.PRIMARY_METRICS[1]: 3.0, "daily_invariant_failures": 0}
            nearest = {analyze.PRIMARY_METRICS[0]: 1.0 if success else 2.0,
                       analyze.PRIMARY_METRICS[1]: 2.0 if success else 3.0,
                       "daily_invariant_failures": 0}
            evidence_rows.append({
                "station_id": summary["station_id"], "station_regime": summary["station_regime"],
                "candidate_point_id": f"p-{summary['station_id']}", "great_circle_distance_km": summary["great_circle_distance_km"],
                "member_id": member, "region_strategy_id": analyze.REGION_ARM,
                "nearest_strategy_id": analyze.NEAREST_ARM, "region_metrics": region, "nearest_metrics": nearest,
            })
    evidence = {
        "schema_version": "a11e3-development-evidence-1", "source_commit": analyze.EXPECTED_INPUTS["a11e3_source_commit"],
        "confirmation_target_series_accessed": False, "paired_row_count": 160, "cell_count": 320,
        "rows": evidence_rows,
    }
    evidence["evidence_sha256"] = analyze.canonical_digest(evidence)
    selection = {"confirmation_target_series_accessed": False, "rows": selection_rows}
    return evidence, selection


class AnalysisContractTests(unittest.TestCase):
    def test_manifest_is_strict(self) -> None:
        manifest = json.loads((HERE / "analysis-manifest-v1.json").read_text())
        self.assertEqual(analyze.validate_manifest(manifest), manifest)
        for path, value in (
            (("decision", "alpha_familywise"), 0.10),
            (("model", "exact_assignment_count"), 1),
            (("model", "reference_regime"), "changed"),
            (("inputs", "a11e3_evidence_sha256"), "0" * 64),
            (("confirmation_target_access",), True),
        ):
            mutated = copy.deepcopy(manifest)
            target = mutated
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            with self.assertRaises(analyze.AnalysisError):
                analyze.validate_manifest(mutated)

    def test_schema_pins_every_manifest_field(self) -> None:
        manifest = json.loads((HERE / "analysis-manifest-v1.json").read_text())
        schema = json.loads((HERE / "analysis-manifest-v1.schema.json").read_text())
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(schema["required"]), set(manifest))
        for name, value in manifest.items():
            self.assertEqual(schema["properties"][name]["const"], value)

    def test_unpublished_source_fails_before_input_access(self) -> None:
        manifest = json.loads((HERE / "analysis-manifest-v1.json").read_text())
        with mock.patch.object(analyze, "digest", side_effect=AssertionError("input accessed")):
            with self.assertRaisesRegex(analyze.AnalysisError, "published origin/main"):
                analyze.verify_source("not-a-commit", manifest)

    def test_runtime_mismatch_fails_closed(self) -> None:
        manifest = json.loads((HERE / "analysis-manifest-v1.json").read_text())
        with mock.patch.object(analyze.np, "__version__", "changed"):
            with self.assertRaisesRegex(analyze.AnalysisError, "runtime identity differs"):
                analyze.verify_runtime(manifest)

    def test_average_ranks_are_tie_stable(self) -> None:
        values = np.asarray([10.0, 5.0, 10.0, 20.0])
        np.testing.assert_allclose(analyze.average_ranks(values), [2.5, 1.0, 2.5, 4.0])

    def test_joint_design_is_full_rank_and_frozen(self) -> None:
        manifest = json.loads((HERE / "analysis-manifest-v1.json").read_text())
        matrix, names = analyze.design_matrix(synthetic_station_summaries(), manifest)
        self.assertEqual(matrix.shape, (20, 8))
        self.assertEqual(np.linalg.matrix_rank(matrix), 8)
        self.assertEqual(names[-2:], ["ranked_distance", "regime_mismatch"])
        self.assertAlmostEqual(float(np.mean(matrix[:, -2])), 0.0)
        self.assertAlmostEqual(float(np.std(matrix[:, -2], ddof=0)), 1.0)

    def test_design_rejects_regime_size_or_rank_drift(self) -> None:
        manifest = json.loads((HERE / "analysis-manifest-v1.json").read_text())
        rows = synthetic_station_summaries()
        rows[0]["station_regime"] = "cold"
        with self.assertRaises(analyze.AnalysisError):
            analyze.design_matrix(rows, manifest)

    def test_ols_rejects_nonfinite_or_zero_residual_variance(self) -> None:
        matrix = np.column_stack([np.ones(6), np.arange(6, dtype=float)])
        with self.assertRaises(analyze.AnalysisError):
            analyze.ols_fit(matrix, np.arange(6, dtype=float))
        outcomes = np.asarray([0.0, 1.0, 0.0, 1.0, np.nan, 1.0])
        with self.assertRaises(analyze.AnalysisError):
            analyze.ols_fit(matrix, outcomes)

    def test_exact_max_t_enumerates_identity_and_all_assignments(self) -> None:
        matrix = np.column_stack([np.ones(6), [-1, -1, 0, 0, 1, 1], [0, 1, 0, 1, 0, 1]]).astype(float)
        outcomes = np.asarray([0.0, 0.5, 0.25, 1.0, 0.75, 0.0])
        fit = analyze.ols_fit(matrix, outcomes)
        tolerance = 1e-12
        result = analyze.exact_max_t(matrix, outcomes, [np.asarray([0, 1]), np.asarray([2, 3]), np.asarray([4, 5])],
                                     (abs(float(fit["t"][-2])), abs(float(fit["t"][-1]))), 8, tolerance)
        self.assertEqual(result["assignment_count"], 8)
        self.assertTrue(result["identity_included"])
        self.assertTrue(result["identity_counted_for_both_thresholds"])
        self.assertGreaterEqual(result["distance_extreme_count"], 1)
        self.assertGreaterEqual(result["mismatch_extreme_count"], 1)
        self.assertTrue(0.0 <= result["distance_adjusted_p"] <= 1.0)
        self.assertTrue(0.0 <= result["mismatch_adjusted_p"] <= 1.0)
        thresholds = np.abs(fit["t"][-2:])
        brute = np.zeros(2, dtype=int)
        groups = ([0, 1], [2, 3], [4, 5])
        for first in ((outcomes[0], outcomes[1]), (outcomes[1], outcomes[0])):
            for second in ((outcomes[2], outcomes[3]), (outcomes[3], outcomes[2])):
                for third in ((outcomes[4], outcomes[5]), (outcomes[5], outcomes[4])):
                    permuted = outcomes.copy()
                    for indices, values in zip(groups, (first, second, third)):
                        permuted[list(indices)] = values
                    maximum = float(np.max(np.abs(analyze.ols_fit(matrix, permuted)["t"][-2:])))
                    limits = thresholds - tolerance * np.maximum(1.0, thresholds)
                    brute += maximum >= limits
        self.assertEqual(result["distance_extreme_count"], int(brute[0]))
        self.assertEqual(result["mismatch_extreme_count"], int(brute[1]))

    def test_degenerate_permutation_uses_frozen_conservative_infinite_t_rule(self) -> None:
        matrix = np.column_stack([np.ones(6), [-1, -1, 0, 0, 1, 1], [0, 1, 0, 1, 0, 1]]).astype(float)
        outcomes = np.asarray([1.0, 0.0, 1.0, 2.0, 2.0, 3.0])
        fit = analyze.ols_fit(matrix, outcomes)
        result = analyze.exact_max_t(
            matrix, outcomes, [np.asarray([0, 1]), np.asarray([2, 3]), np.asarray([4, 5])],
            (abs(float(fit["t"][-2])), abs(float(fit["t"][-1]))), 8, 1e-12,
        )
        self.assertGreaterEqual(result["degenerate_assignment_count"], 1)
        self.assertTrue(result["identity_counted_for_both_thresholds"])
        degenerate_values = np.asarray([[0.0, 1.0, 1.0, 2.0, 2.0, 3.0]])
        selected_t, degenerate = analyze.selected_t_batch(matrix, degenerate_values)
        self.assertTrue(bool(degenerate[0]))
        self.assertTrue(np.isinf(selected_t[0]).all())

    def test_predictor_support_requires_p_and_both_sign_checks(self) -> None:
        positive_lomo, positive_loso = np.ones(8), np.ones(20)
        self.assertEqual(analyze.predictor_supported(0.05, 1.0, positive_lomo, positive_loso, 0.05), (True, True, True))
        unstable = positive_loso.copy(); unstable[0] = -1.0
        self.assertEqual(analyze.predictor_supported(0.01, 1.0, positive_lomo, unstable, 0.05), (False, True, False))
        self.assertEqual(analyze.predictor_supported(0.051, 1.0, positive_lomo, positive_loso, 0.05)[0], False)

    def test_joint_attribution_wires_lomo_loso_and_incremental_r_squared(self) -> None:
        manifest = json.loads((HERE / "analysis-manifest-v1.json").read_text())
        stations = synthetic_station_summaries()

        def independent_matrix(rows: list[dict]) -> np.ndarray:
            levels = manifest["model"]["station_regime_levels"]
            distances = np.asarray([row["great_circle_distance_km"] for row in rows])
            order = np.argsort(distances, kind="stable")
            ranks = np.empty(len(rows), dtype=float)
            ranks[order] = np.arange(1, len(rows) + 1, dtype=float)
            ranked = (ranks - np.mean(ranks)) / np.std(ranks, ddof=0)
            columns = [np.ones(len(rows))]
            columns.extend(np.asarray([row["station_regime"] == level for row in rows], dtype=float) for level in levels[1:])
            columns.append(ranked)
            columns.append(np.asarray([not row["same_regime"] for row in rows], dtype=float))
            return np.column_stack(columns)

        def independent_beta_r2(matrix: np.ndarray, outcome: np.ndarray) -> tuple[np.ndarray, float]:
            beta = np.linalg.lstsq(matrix, outcome, rcond=None)[0]
            residual = outcome - matrix @ beta
            centered = outcome - np.mean(outcome)
            return beta, 1.0 - float(residual @ residual) / float(centered @ centered)

        matrix = independent_matrix(stations)
        outcome = np.asarray([row["both_improvement_fraction"] for row in stations])
        full_beta, full_r2 = independent_beta_r2(matrix, outcome)
        expected_lomo = []
        for omitted in analyze.MEMBERS:
            member_outcome = np.asarray([sum(value for index, value in enumerate(row["both_improvement_by_member"]) if index != omitted) / 7.0 for row in stations])
            expected_lomo.append(independent_beta_r2(matrix, member_outcome)[0][-2:])
        expected_loso = []
        for omitted in range(20):
            subset = [row for index, row in enumerate(stations) if index != omitted]
            subset_matrix = independent_matrix(subset)
            subset_outcome = np.asarray([row["both_improvement_fraction"] for row in subset])
            expected_loso.append(independent_beta_r2(subset_matrix, subset_outcome)[0][-2:])
        expected_lomo_array, expected_loso_array = np.asarray(expected_lomo), np.asarray(expected_loso)
        expected_incremental = []
        for column in (-2, -1):
            reduced = np.delete(matrix, column, axis=1)
            expected_incremental.append(full_r2 - independent_beta_r2(reduced, outcome)[1])

        exact = {"distance_adjusted_p": 0.01, "mismatch_adjusted_p": 0.02, "assignment_count": 1327104}
        with mock.patch.object(analyze, "exact_max_t", return_value=exact):
            with mock.patch.object(analyze, "design_matrix", wraps=analyze.design_matrix) as design_spy:
                result = analyze.joint_attribution(stations, manifest)
        self.assertEqual(sum(call.kwargs.get("require_full_roster") is False for call in design_spy.call_args_list), 20)
        for offset, name in enumerate(("ranked_distance", "regime_mismatch")):
            predictor = result["predictors"][name]
            self.assertAlmostEqual(predictor["coefficient"], float(full_beta[-2 + offset]))
            self.assertAlmostEqual(predictor["incremental_r_squared"], expected_incremental[offset])
            self.assertAlmostEqual(predictor["leave_one_member_out_coefficient_min"], float(np.min(expected_lomo_array[:, offset])))
            self.assertAlmostEqual(predictor["leave_one_member_out_coefficient_max"], float(np.max(expected_lomo_array[:, offset])))
            self.assertAlmostEqual(predictor["leave_one_station_out_coefficient_min"], float(np.min(expected_loso_array[:, offset])))
            self.assertAlmostEqual(predictor["leave_one_station_out_coefficient_max"], float(np.max(expected_loso_array[:, offset])))
            self.assertEqual(predictor["leave_one_member_out_sign_stable"], bool(np.all(expected_lomo_array[:, offset] * full_beta[-2 + offset] > 0.0)))
            self.assertEqual(predictor["leave_one_station_out_sign_stable"], bool(np.all(expected_loso_array[:, offset] * full_beta[-2 + offset] > 0.0)))

    def test_station_summary_requires_exact_grid_join_and_self_hash(self) -> None:
        evidence, selection = synthetic_evidence_and_selection()
        with mock.patch.dict(analyze.EXPECTED_INPUTS, {"a11e3_evidence_self_sha256": evidence["evidence_sha256"]}):
            summaries = analyze.build_station_summaries(evidence, selection)
            self.assertEqual(len(summaries), 20)
            self.assertEqual(sum(row["both_improvement_count"] for row in summaries),
                             sum(sum(row["both_improvement_by_member"]) for row in synthetic_station_summaries()))
            broken = copy.deepcopy(evidence); broken["rows"].pop()
            broken["evidence_sha256"] = analyze.canonical_digest({key: value for key, value in broken.items() if key != "evidence_sha256"})
            with mock.patch.dict(analyze.EXPECTED_INPUTS, {"a11e3_evidence_self_sha256": broken["evidence_sha256"]}):
                with self.assertRaisesRegex(analyze.AnalysisError, "exact selector-station"):
                    analyze.build_station_summaries(broken, selection)

    def test_station_summary_fails_on_join_nonfinite_invariant_or_firewall(self) -> None:
        for mutation in ("join", "nonfinite", "invariant", "firewall"):
            evidence, selection = synthetic_evidence_and_selection()
            if mutation == "join": selection["rows"][0]["candidate_point_id"] = "changed"
            elif mutation == "nonfinite": evidence["rows"][0]["nearest_metrics"][analyze.PRIMARY_METRICS[0]] = float("nan")
            elif mutation == "invariant": evidence["rows"][0]["nearest_metrics"]["daily_invariant_failures"] = 1
            else: evidence["confirmation_target_series_accessed"] = True
            if mutation == "nonfinite":
                with mock.patch.object(analyze, "canonical_digest", return_value=evidence["evidence_sha256"]):
                    with mock.patch.dict(analyze.EXPECTED_INPUTS, {"a11e3_evidence_self_sha256": evidence["evidence_sha256"]}):
                        with self.assertRaises(analyze.AnalysisError):
                            analyze.build_station_summaries(evidence, selection)
            else:
                without = {key: value for key, value in evidence.items() if key != "evidence_sha256"}
                evidence["evidence_sha256"] = analyze.canonical_digest(without)
                with mock.patch.dict(analyze.EXPECTED_INPUTS, {"a11e3_evidence_self_sha256": evidence["evidence_sha256"]}):
                    with self.assertRaises(analyze.AnalysisError):
                        analyze.build_station_summaries(evidence, selection)

    def test_disposition_table_is_exact(self) -> None:
        self.assertEqual(analyze.disposition(True, True), "SUPPORTED_BOTH_METADATA_ASSOCIATIONS")
        self.assertEqual(analyze.disposition(True, False), "SUPPORTED_DISTANCE_ASSOCIATION")
        self.assertEqual(analyze.disposition(False, True), "SUPPORTED_REGIME_MISMATCH_ASSOCIATION")
        self.assertEqual(analyze.disposition(False, False), "NO_STABLE_METADATA_ASSOCIATION")


if __name__ == "__main__":
    unittest.main()
