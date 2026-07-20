#!/usr/bin/env python3
"""Static protocol tests for A10M5R12 continuous latent processes."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]


class ContinuousProtocolTest(unittest.TestCase):
    def test_state_clock_and_matched_ablation(self) -> None:
        contract = json.loads(
            (PACKAGE / "artifacts/portfolio-contract.json").read_text()
        )
        medium = contract["architectures"]["continuous_medium_latent_process"]
        hierarchy = contract["architectures"]["continuous_hierarchical_latent_process"]
        self.assertEqual(medium["state_reset_boundaries"], [])
        self.assertEqual(hierarchy["state_reset_boundaries"], [])
        self.assertEqual(medium["state_clock"], hierarchy["state_clock"])
        self.assertEqual(medium["medium_time_scale_days"], [14.0, 180.0])
        self.assertEqual(hierarchy["medium_time_scale_days"], [14.0, 180.0])
        self.assertFalse(medium["slow_state"])
        self.assertTrue(hierarchy["slow_state"])
        self.assertEqual(medium["observed_weather_inputs"], [])
        self.assertEqual(hierarchy["observed_weather_inputs"], [])
        self.assertNotIn("leap_phase", medium["context_inputs"])
        self.assertNotIn("leap_phase", hierarchy["context_inputs"])

    def test_temporal_protocol_remains_stochastic_and_leap_safe(self) -> None:
        contract = json.loads(
            (PACKAGE / "artifacts/temporal-contract.json").read_text()
        )
        self.assertEqual(contract["metrics"]["paired_daily_pattern_weight"], 0.0)
        self.assertIn("standard_deviation", contract["metrics"]["monthly_precipitation"])
        self.assertIn("precipitation_standard_deviation", contract["metrics"]["annual"])
        self.assertEqual(
            contract["observation"]["bootstrap_year_relabel"],
            "2000 + 16 * position + (0 if source block contains February 29 else 1)",
        )
        self.assertFalse(contract["solar"]["opened"])

    def test_conditional_member_daily_nll_is_diagnostic_only(self) -> None:
        contract = json.loads(
            (PACKAGE / "artifacts/portfolio-contract.json").read_text()
        )
        self.assertEqual(contract["objective"]["daily_proper_nll_weight"], 0.0)
        self.assertEqual(
            contract["checkpoint"]["selection_scalar"]["daily_proper_nll_weight"],
            0.0,
        )

    def test_source_ignores_calendar_bins_for_state_evolution(self) -> None:
        source = (PACKAGE / "artifacts/jobs/continuous_core.py").read_text()
        self.assertIn("del regimes, months, years", source)
        self.assertIn("torch.exp(-1.0 / time_scales)", source)
        self.assertIn("features[..., (0, 1, 3, 4, 5)]", source)
        self.assertIn("matched medium-process initialization drift", source)
        self.assertIn("conditional-member daily NLL must remain diagnostic only", source)
        self.assertIn("A10M5R12-CONTINUOUS-CORE-SELF-TEST-PASS", source)

    def test_selector_requires_authenticated_complete_candidate_evidence(self) -> None:
        source = (PACKAGE / "artifacts/jobs/temporal_select.py").read_text()
        self.assertIn("authenticated(admission)", source)
        self.assertIn("candidate terminal evidence failed", source)
        self.assertIn("candidate stream matrix mismatch", source)
        self.assertIn("temporal_contract_sha256", source)
        self.assertIn("portfolio_contract_sha256", source)
        self.assertIn("calendar != expected_calendar", source)
        self.assertIn("candidate stream replay failed", source)
        contract = json.loads(
            (PACKAGE / "artifacts/portfolio-contract.json").read_text()
        )
        self.assertIn("streams.npz", contract["evidence_layout"]["candidate_files"])
        self.assertEqual(
            len(contract["evidence_layout"]["candidate_checkpoint_files_required"]),
            3,
        )

    def test_local_replay_is_source_and_receipt_bound(self) -> None:
        source = (PACKAGE / "artifacts/run_temporal_replay.py").read_text()
        self.assertIn('("git", "rev-parse", "origin/main")', source)
        self.assertIn("collection/cleanup/terminal receipt identity failed", source)
        self.assertIn("isolated temporal selector replays differ", source)


if __name__ == "__main__":
    unittest.main()
