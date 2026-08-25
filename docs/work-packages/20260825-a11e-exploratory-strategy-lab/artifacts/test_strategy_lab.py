#!/usr/bin/env python3
"""Synthetic contract tests for the A11 exploratory strategy lab."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("strategy_lab", ROOT / "strategy_lab.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot import strategy lab")
lab = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = lab
SPEC.loader.exec_module(lab)


class StrategyLabTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads((ROOT / "strategy-manifest-v1.json").read_text())

    def test_manifest_is_strict_and_canonical(self) -> None:
        self.assertEqual(lab.validate_manifest(self.manifest), self.manifest)
        self.assertEqual(len(lab.canonical_sha256(self.manifest)), 64)
        mutation = copy.deepcopy(self.manifest)
        mutation["unknown"] = True
        with self.assertRaisesRegex(lab.ContractError, "fields differ"):
            lab.validate_manifest(mutation)
        mutation = copy.deepcopy(self.manifest)
        mutation["strategies"][1]["strategy_id"] = mutation["strategies"][0]["strategy_id"]
        with self.assertRaises(lab.ContractError):
            lab.validate_manifest(mutation)
        mutation = copy.deepcopy(self.manifest)
        mutation["strategies"].pop()
        with self.assertRaisesRegex(lab.ContractError, "each initial strategy"):
            lab.validate_manifest(mutation)
        mutation = copy.deepcopy(self.manifest)
        mutation["strategies"][0]["capabilities"].append("wepp")
        with self.assertRaisesRegex(lab.ContractError, "capabilities differ"):
            lab.validate_manifest(mutation)
        schema = json.loads((ROOT / "strategy-manifest-v1.schema.json").read_text())
        item_properties = schema["properties"]["strategies"]["items"]["properties"]
        self.assertEqual(item_properties["capabilities"]["const"], lab.CORE_CAPABILITIES)
        self.assertEqual(item_properties["evaluation_stages"]["const"], lab.CORE_STAGES)
        self.assertEqual(item_properties["evaluator_id"]["const"], lab.EVALUATOR_ID)
        self.assertEqual(item_properties["metric_set_id"]["const"], lab.METRIC_SET_ID)
        self.assertEqual(item_properties["uncertainty_id"]["const"], lab.UNCERTAINTY_ID)

    def test_random_domains_replay_and_separate(self) -> None:
        left = lab.domain_rng("fixture", "gaussian_latent_scalar_ar1_v1", 3, "annual_target").random(8)
        replay = lab.domain_rng("fixture", "gaussian_latent_scalar_ar1_v1", 3, "annual_target").random(8)
        other = lab.domain_rng("fixture", "gaussian_latent_scalar_ar1_v1", 3, "wet_count").random(8)
        np.testing.assert_array_equal(left, replay)
        self.assertFalse(np.array_equal(left, other))

    def test_within_site_standardization_removes_climatology(self) -> None:
        sites = ["a"] * 5 + ["b"] * 5
        years = list(range(2000, 2005)) * 2
        common = np.column_stack((np.arange(5.0), np.arange(5.0) ** 2 + 1.0))
        values = np.vstack((common + np.array([100.0, -50.0]), common + np.array([-200.0, 80.0])))
        result = lab.within_site_standardize(sites, years, values)
        anomalies = result["anomalies"]
        for group in (anomalies[:5], anomalies[5:]):
            np.testing.assert_allclose(np.mean(group, axis=0), 0.0, atol=1e-14)
            np.testing.assert_allclose(np.std(group, axis=0, ddof=1), 1.0, atol=1e-14)
        np.testing.assert_allclose(anomalies[:5], anomalies[5:], atol=1e-14)

    def test_constant_site_field_fails_closed(self) -> None:
        with self.assertRaisesRegex(lab.ContractError, "constant"):
            lab.within_site_standardize(["a"] * 3, [1, 2, 3], np.ones((3, 2)))

    def test_average_ranks_preserve_ties(self) -> None:
        np.testing.assert_array_equal(lab.average_ranks([2.0, 1.0, 2.0, 4.0]), [2.5, 1.0, 2.5, 4.0])

    def test_covariance_reconciliation_hits_feasible_target(self) -> None:
        requested = np.array([[1.0, 0.5], [0.5, 4.0]])
        effective, receipt = lab.reconcile_covariance(requested, [1.0, 4.0], [1.0, 1.0], 6.0)
        np.testing.assert_allclose(np.diag(effective), [1.0, 4.0], atol=1e-10)
        self.assertAlmostEqual(float(np.ones(2) @ effective @ np.ones(2)), 6.0)
        self.assertFalse(receipt["projected_to_boundary"])
        self.assertGreaterEqual(receipt["minimum_eigenvalue"], -1e-10)

    def test_covariance_reconciliation_reports_infeasible_projection(self) -> None:
        requested = np.array([[1.0, 0.5], [0.5, 4.0]])
        effective, receipt = lab.reconcile_covariance(requested, [1.0, 4.0], [1.0, 1.0], 20.0)
        self.assertTrue(receipt["projected_to_boundary"])
        self.assertLess(receipt["effective_annual_variance"], 20.0)
        self.assertGreaterEqual(float(np.min(np.linalg.eigvalsh(effective))), -1e-10)

    def test_zero_off_diagonal_reports_unsatisfied_annual_target(self) -> None:
        _, receipt = lab.reconcile_covariance(np.eye(2), [1.0, 1.0], [1.0, 1.0], 8.0)
        self.assertTrue(receipt["projected_to_boundary"])
        self.assertFalse(receipt["annual_target_satisfied"])
        self.assertAlmostEqual(receipt["effective_annual_variance"], 2.0)

    def test_covariance_reconciliation_rejects_silent_normalization(self) -> None:
        with self.assertRaisesRegex(lab.ContractError, "symmetric"):
            lab.reconcile_covariance([[1.0, 0.2], [0.1, 1.0]], [1.0, 1.0], [1.0, 1.0], 2.3)
        with self.assertRaisesRegex(lab.ContractError, "diagonal"):
            lab.reconcile_covariance([[2.0, 0.2], [0.2, 1.0]], [1.0, 1.0], [1.0, 1.0], 2.4)
        effective, receipt = lab.reconcile_covariance(
            [[1.0, 0.5], [0.5, 1.0]], [1.0, 1.0], [1.0, -1.0], 1.0
        )
        self.assertEqual(receipt["effective_alpha"], 1.0)
        np.testing.assert_array_equal(effective, [[1.0, 0.5], [0.5, 1.0]])

    @staticmethod
    def synthetic_fit() -> tuple[list[str], list[int], np.ndarray]:
        generator = np.random.default_rng(4411)
        sites = []
        years = []
        rows = []
        for site_index, site in enumerate(("a", "b", "c")):
            state = np.zeros(4)
            for year in range(30):
                state = 0.55 * state + generator.normal(size=4)
                sites.append(site)
                years.append(1980 + year)
                rows.append(state * np.array([1.0, 2.0, 0.5, 3.0]) + site_index * 50.0)
        return sites, years, np.asarray(rows)

    def test_gaussian_strategy_fits_persistence_and_replays(self) -> None:
        sites, years, values = self.synthetic_fit()
        model = lab.fit_gaussian_ar1(sites, years, values, "fixture-region")
        self.assertEqual(model["strategy_id"], "gaussian_latent_scalar_ar1_v1")
        self.assertAlmostEqual(model["scalar_persistence"], 0.55, delta=0.12)
        output = lab.generate_gaussian_ar1(
            model, 5000, lab.domain_rng("fixture", model["strategy_id"], 0, "annual_target")
        )
        replay = lab.generate_gaussian_ar1(
            model, 5000, lab.domain_rng("fixture", model["strategy_id"], 0, "annual_target")
        )
        np.testing.assert_array_equal(output, replay)
        self.assertEqual(output.shape, (5000, 4))
        self.assertAlmostEqual(
            float(np.corrcoef(output[:-1, 0], output[1:, 0])[0, 1]),
            model["scalar_persistence"], delta=0.08,
        )
        np.testing.assert_allclose(np.mean(output, axis=0), 0.0, atol=0.08)
        np.testing.assert_allclose(np.std(output, axis=0, ddof=1), 1.0, atol=0.08)
        np.testing.assert_allclose(
            np.corrcoef(output, rowvar=False), model["anomaly_correlation"], atol=0.10
        )
        with self.assertRaisesRegex(lab.ContractError, "registered Philox"):
            lab.generate_gaussian_ar1(model, 2, np.random.default_rng(1))
        with self.assertRaisesRegex(lab.ContractError, "exactly 30 years"):
            lab.fit_gaussian_ar1(sites[:-1], years[:-1], values[:-1], "fixture-region")
        with self.assertRaisesRegex(lab.ContractError, "candidate_fit"):
            lab.fit_gaussian_ar1(sites, years, values, "fixture-region", "held_out_development")

    def test_block_bootstrap_replays_complete_blocks(self) -> None:
        sites, years, values = self.synthetic_fit()
        model = lab.fit_block_bootstrap(sites, years, values, 5, "fixture-region")
        output = lab.generate_block_bootstrap(
            model, 17, lab.domain_rng("fixture", model["strategy_id"], 0, "annual_target")
        )
        replay = lab.generate_block_bootstrap(
            model, 17, lab.domain_rng("fixture", model["strategy_id"], 0, "annual_target")
        )
        np.testing.assert_array_equal(output, replay)
        self.assertEqual(output.shape, (17, 4))
        sequences = [np.asarray(value["values"]) for value in model["sequences"].values()]
        for start in range(0, len(output), 5):
            chunk = output[start : start + 5]
            matches = any(
                np.array_equal(chunk, np.asarray([sequence[(offset + index) % len(sequence)] for index in range(len(chunk))]))
                for sequence in sequences for offset in range(len(sequence))
            )
            self.assertTrue(matches, "each emitted chunk must be one circular within-site block")
        malformed = copy.deepcopy(model)
        malformed["block_length_years"] = 0
        with self.assertRaises(lab.ContractError):
            lab.generate_block_bootstrap(
                malformed, 2, lab.domain_rng("fixture", model["strategy_id"], 0, "annual_target")
            )

    def test_integrated_targets_apply_reconciliation_and_location(self) -> None:
        sites, years, values = self.synthetic_fit()
        model = lab.fit_gaussian_ar1(sites, years, values, "fixture-region")
        targets, receipt = lab.generate_strategy_targets(
            model, 50000,
            lab.domain_rng("targets", model["strategy_id"], 2, "annual_target"),
            [10.0, 20.0, 30.0, 40.0], [1.0, 4.0, 9.0, 16.0],
            [1.0, 1.0, 1.0, 1.0], 35.0,
        )
        self.assertEqual(targets.shape, (50000, 4))
        self.assertEqual(receipt["region_id"], "fixture-region")
        self.assertIn("effective_annual_variance", receipt["reconciliation"])
        np.testing.assert_allclose(np.mean(targets, axis=0), [10.0, 20.0, 30.0, 40.0], atol=0.15)
        effective_annual = receipt["reconciliation"]["effective_annual_variance"]
        realized = np.cov(targets, rowvar=False, ddof=1)
        np.testing.assert_allclose(realized, receipt["realized_covariance"], atol=1e-10)
        np.testing.assert_allclose(np.diag(realized), [1.0, 4.0, 9.0, 16.0], atol=0.25)
        self.assertAlmostEqual(float(np.ones(4) @ realized @ np.ones(4)), effective_annual, delta=0.6)
        self.assertLess(receipt["maximum_realized_covariance_error"], 0.25)
        short, _ = lab.generate_strategy_targets(
            model, 30, lab.domain_rng("prefix", model["strategy_id"], 0, "annual_target"),
            [10.0, 20.0, 30.0, 40.0], [1.0, 4.0, 9.0, 16.0],
            [1.0, 1.0, 1.0, 1.0], 35.0,
        )
        long, _ = lab.generate_strategy_targets(
            model, 100, lab.domain_rng("prefix", model["strategy_id"], 0, "annual_target"),
            [10.0, 20.0, 30.0, 40.0], [1.0, 4.0, 9.0, 16.0],
            [1.0, 1.0, 1.0, 1.0], 35.0,
        )
        np.testing.assert_allclose(short, long[:30], atol=1e-12)
        invalid = lab.domain_rng("invalid-target", model["strategy_id"], 0, "annual_target")
        with self.assertRaises(lab.ContractError):
            lab.generate_strategy_targets(
                model, 30, invalid, [10.0], [1.0, 4.0, 9.0, 16.0],
                [1.0, 1.0, 1.0, 1.0], 35.0,
            )
        fresh = lab.domain_rng("invalid-target", model["strategy_id"], 0, "annual_target")
        np.testing.assert_array_equal(invalid.random(4), fresh.random(4))

    def test_target_generation_supports_more_fields_than_years(self) -> None:
        dimensions = 48
        base = np.random.default_rng(82).normal(size=(60, dimensions))
        sites = ["a"] * 30 + ["b"] * 30
        years = list(range(1980, 2010)) * 2
        models = (
            lab.fit_block_bootstrap(sites, years, base, 5, "fixture-region"),
            lab.fit_gaussian_ar1(sites, years, base, "fixture-region"),
        )
        for member, model in enumerate(models):
            correlation = np.asarray(model["anomaly_correlation"])
            requested_annual = float(np.ones(dimensions) @ correlation @ np.ones(dimensions))
            targets, receipt = lab.generate_strategy_targets(
                model, 30, lab.domain_rng("wide", model["strategy_id"], member, "annual_target"),
                np.zeros(dimensions), np.ones(dimensions), np.ones(dimensions), requested_annual,
            )
            self.assertEqual(targets.shape, (30, dimensions))
            self.assertEqual(
                receipt["moment_semantics"],
                "stationary_population_law; realized sample is diagnostic",
            )
            self.assertTrue(np.isfinite(receipt["realized_covariance"]).all())

    def test_location_forcing_is_separate_from_standardized_strategy(self) -> None:
        anomalies = np.asarray([[0.0, 1.0], [-1.0, 2.0]])
        forced = lab.apply_location_scale(anomalies, [10.0, 100.0], [2.0, 5.0])
        np.testing.assert_array_equal(forced, [[10.0, 105.0], [8.0, 110.0]])

    def test_wet_count_law_samples_only_preconditioned_support(self) -> None:
        count = lab.select_feasible_wet_count(4.2, 31, 1.0, [0, 2, 4, 7, 12], 0.99)
        self.assertEqual(count, 4)
        self.assertEqual(lab.select_feasible_wet_count(0.0, 31, 1.0, [0, 4], 0.5), 0)
        with self.assertRaisesRegex(lab.ContractError, "no fitted wet count"):
            lab.select_feasible_wet_count(0.5, 31, 1.0, [0, 2], 0.2)

    def test_markov_bridge_and_amount_allocation_are_exact(self) -> None:
        generator = lab.domain_rng("daily", "gaussian_latent_scalar_ar1_v1", 0, "occurrence")
        wet = lab.markov_bridge(31, 7, False, 0.55, 0.20, generator)
        self.assertEqual(int(np.sum(wet)), 7)
        amounts = lab.allocate_wet_amounts(25.0, wet, 1.0, np.arange(1.0, 8.0))
        self.assertAlmostEqual(float(np.sum(amounts)), 25.0)
        self.assertTrue(np.all(amounts[wet] >= 1.0))
        self.assertTrue(np.all(amounts[~wet] == 0.0))
        with self.assertRaises(lab.ContractError):
            lab.allocate_wet_amounts(25.0, wet, -1.0, np.arange(1.0, 8.0))
        with self.assertRaisesRegex(lab.ContractError, "month support"):
            lab.select_feasible_wet_count(4.2, 31, 1.0, [-1, 2], 0.2)
        with self.assertRaises(lab.ContractError):
            lab.allocate_wet_amounts(2.0, [0.0, np.nan], 1.0, [1.0])

    def test_core_month_composes_registered_domains_and_exact_constraints(self) -> None:
        strategy = "gaussian_latent_scalar_ar1_v1"
        streams = lab.domain_rngs("core", strategy, 4)
        core_streams = {name: streams[name] for name in ("wet_count", "occurrence", "amount", "temperature", "range")}
        output, receipt = lab.generate_core_month(
            strategy, 40.0, 31, [4, 7, 10], 1.0, False, 0.55, 0.20,
            12.0, 3.5, 9.0, 0.25, 0.60, 0.45, core_streams,
        )
        replay_streams = lab.domain_rngs("core", strategy, 4)
        replay, _ = lab.generate_core_month(
            strategy, 40.0, 31, [4, 7, 10], 1.0, False, 0.55, 0.20,
            12.0, 3.5, 9.0, 0.25, 0.60, 0.45,
            {name: replay_streams[name] for name in core_streams},
        )
        for name in output:
            np.testing.assert_array_equal(output[name], replay[name])
        self.assertEqual(int(np.sum(output["wet"])), receipt["wet_count"])
        self.assertAlmostEqual(float(np.sum(output["precipitation_mm"])), 40.0)
        self.assertAlmostEqual(float(np.mean(output["temperature_mean"])), 12.0)
        self.assertAlmostEqual(float(np.std(output["temperature_mean"], ddof=1)), 3.5)
        self.assertAlmostEqual(float(np.mean(output["temperature_range"])), 9.0)
        self.assertTrue(np.all(output["temperature_max"] >= output["temperature_min"]))
        self.assertGreater(
            float(np.corrcoef(output["temperature_mean"][:-1], output["temperature_mean"][1:])[0, 1]),
            0.25,
        )
        self.assertGreater(
            float(np.corrcoef(np.log(output["temperature_range"][:-1]), np.log(output["temperature_range"][1:]))[0, 1]),
            0.25,
        )
        invalid_streams = lab.domain_rngs("invalid-core", strategy, 4)
        with self.assertRaisesRegex(lab.ContractError, "must be finite"):
            lab.generate_core_month(
                strategy, 40.0, 31, [4, 7, 10], 1.0, False, 0.55, 0.20,
                float("nan"), 3.5, 9.0, 0.25, 0.60, 0.45,
                {name: invalid_streams[name] for name in core_streams},
            )
        fresh_invalid = lab.domain_rngs("invalid-core", strategy, 4)
        for name in core_streams:
            np.testing.assert_array_equal(
                invalid_streams[name].random(3), fresh_invalid[name].random(3)
            )

    def test_temperature_and_range_conditioning_are_structural(self) -> None:
        residual = lab.condition_temperature_residuals([1.0, 2.0, -1.0, 4.0], 3.5)
        self.assertAlmostEqual(float(np.mean(residual)), 0.0)
        self.assertAlmostEqual(float(np.std(residual, ddof=1)), 3.5)
        ranges = lab.condition_positive_ranges([1.0, 2.0, 4.0], 9.0)
        self.assertAlmostEqual(float(np.mean(ranges)), 9.0)
        self.assertTrue(np.all(ranges > 0.0))


if __name__ == "__main__":
    unittest.main()
