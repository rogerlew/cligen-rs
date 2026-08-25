#!/usr/bin/env python3
"""Synthetic contract tests for the A11E1 executor."""

from __future__ import annotations

import datetime as dt
import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("a11e1_execute", HERE / "execute.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot import executor")
execute = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = execute
SPEC.loader.exec_module(execute)


class ExecutionContractTests(unittest.TestCase):
    def test_manifest_is_strict_and_registered(self) -> None:
        manifest = json.loads((HERE / "execution-manifest-v1.json").read_text())
        self.assertEqual(execute.validate_manifest(manifest), manifest)
        manifest["unexpected"] = True
        with self.assertRaises(execute.ExecutionError):
            execute.validate_manifest(manifest)

    def test_nested_manifest_mutations_fail_closed(self) -> None:
        original = json.loads((HERE / "execution-manifest-v1.json").read_text())
        for path, value in (
            (("development", "role"), "fit_validation"),
            (("fit", "role"), "development"),
            (("integrated_strategies", 0, "strategy_id"), "changed"),
            (("bootstrap", "seed"), 0),
        ):
            manifest = copy.deepcopy(original)
            target = manifest
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            with self.assertRaises(execute.ExecutionError):
                execute.validate_manifest(manifest)

    def test_unpublished_source_fails_before_input_access(self) -> None:
        manifest = execute.validate_manifest(json.loads((HERE / "execution-manifest-v1.json").read_text()))
        with self.assertRaisesRegex(execute.ExecutionError, "published origin/main"):
            execute.verify_source("not-a-commit", manifest)

    def test_frozen_calendar_masks_and_boundaries(self) -> None:
        self.assertEqual(execute.FIT_MASKED[0], "1980-12-31")
        self.assertEqual(execute.FIT_MASKED[-1], "2008-12-31")
        self.assertEqual(len(execute.FIT_MASKED), 8)
        self.assertEqual(execute.DEVELOPMENT_MASKED, ("2012-12-31", "2016-12-31", "2020-12-31", "2024-12-31"))
        self.assertEqual((execute.FIT_YEARS[0], execute.FIT_YEARS[-1]), (1980, 2009))
        self.assertEqual((execute.DEVELOPMENT_YEARS[0], execute.DEVELOPMENT_YEARS[-1]), (2010, 2025))

    def test_mask_normalized_month_is_support_comparable(self) -> None:
        full = [(dt.date(2011, 1, day), 2.0, 10.0, 0.0) for day in range(1, 32)]
        short = [(dt.date(2012, 1, day), 2.0, 10.0, 0.0) for day in range(1, 31)]
        records = full + short
        for year in (2011, 2012):
            for month in range(2, 13):
                records.extend((dt.date(year, month, day), 2.0, 10.0, 0.0) for day in (1, 2))
        summary = execute.aggregate_months("synthetic", "cold", "development", records, (2011, 2012))
        np.testing.assert_allclose(summary["precipitation"][:, 0], [60.875, 60.875])
        np.testing.assert_allclose(summary["wet_fraction"][:, 0], [1.0, 1.0])

    def test_two_part_adapter_preserves_dry_support(self) -> None:
        shape = (2, 12)
        summary = {
            "point_id": "synthetic", "regime": "arid_boundary", "role": "candidate_fit",
            "precipitation": np.full(shape, 10.0), "wet_count": np.ones(shape, dtype=np.int64),
            "wet_fraction": np.ones(shape), "tmean": np.zeros(shape), "dtr": np.ones(shape),
            "texture": {}, "observed_days": np.full(shape, 30),
        }
        summary["wet_count"][0, 0] = 0
        adapters = execute.adapter_parameters([summary])
        self.assertEqual(adapters["arid_boundary"]["dry_probability"][0], 0.5)
        self.assertGreater(adapters["arid_boundary"]["floors"][0], 0.9)
        self.assertTrue(np.isfinite(execute.state_matrix(summary, adapters)).all())

    def test_hurdle_rng_replays(self) -> None:
        left = execute.hurdle_rng("site", execute.INTEGRATED_STRATEGIES[0], 0).random(8)
        right = execute.hurdle_rng("site", execute.INTEGRATED_STRATEGIES[0], 0).random(8)
        np.testing.assert_array_equal(left, right)

    def test_wet_count_support_conditions_leap_february(self) -> None:
        self.assertEqual(execute.eligible_wet_counts([0, 1, 28, 29], 28), [0, 1, 28])
        self.assertEqual(execute.eligible_wet_counts([0, 1, 28, 29], 29), [0, 1, 28, 29])
        with self.assertRaises(execute.ExecutionError):
            execute.eligible_wet_counts([29], 28)

    def test_integrated_dry_month_generates_exact_zero(self) -> None:
        base = execute.BASE_STRATEGIES[0]
        streams = execute.lab.domain_rngs("a11e1-test-dry", base, 0)
        required = {name: streams[name] for name in ("wet_count", "occurrence", "amount", "temperature", "range")}
        generated, receipt = execute.lab.generate_core_month(
            base, 0.0, 28, execute.eligible_wet_counts([0, 29], 28), 1.0, False,
            0.4, 0.2, 10.0, 2.0, 8.0, 0.0, 0.0, 0.0, required,
        )
        self.assertEqual(receipt["wet_count"], 0)
        self.assertEqual(receipt["precipitation_total_mm"], 0.0)
        self.assertFalse(np.any(generated["wet"]))

    def test_both_annual_laws_generate_16_by_36(self) -> None:
        generator = np.random.Generator(np.random.Philox(11))
        values = generator.normal(size=(60, 36))
        sites = ["a"] * 30 + ["b"] * 30
        years = list(range(1980, 2010)) * 2
        gaussian = execute.lab.fit_gaussian_ar1(sites, years, values, "synthetic")
        block = execute.lab.fit_block_bootstrap(sites, years, values, 5, "synthetic")
        gaussian_values = execute.lab.generate_gaussian_ar1(
            gaussian, 16, execute.lab.domain_rng("test", execute.BASE_STRATEGIES[0], 0, "annual_target")
        )
        block_values = execute.lab.generate_block_bootstrap(
            block, 16, execute.lab.domain_rng("test", execute.BASE_STRATEGIES[1], 0, "annual_target")
        )
        self.assertEqual(gaussian_values.shape, (16, 36))
        self.assertEqual(block_values.shape, (16, 36))

    def test_pooled_lag_does_not_cross_site_boundaries(self) -> None:
        sequences = [np.arange(12.0).reshape(3, 4), np.arange(100.0, 112.0).reshape(3, 4)]
        self.assertAlmostEqual(execute.pooled_lag(sequences), 1.0)

    def test_paired_bootstrap_replays(self) -> None:
        rows = []
        for index in range(20):
            for offset, strategy in enumerate(execute.INTEGRATED_STRATEGIES):
                rows.append({"point_id": f"s{index:02d}", "strategy_id": strategy,
                             "metrics": {"descriptive_composite_score": float(index + offset)}})
        manifest = json.loads((HERE / "execution-manifest-v1.json").read_text())
        self.assertEqual(execute.paired_bootstrap(rows, manifest), execute.paired_bootstrap(rows, manifest))


if __name__ == "__main__":
    unittest.main()
