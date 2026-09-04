#!/usr/bin/env python3
"""Contract tests for the deterministic A11E8 scaffold."""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("a11e8_contract_tested", HERE / "contract.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def record(model_ordinal: int, candidate_index: int, annual: int) -> dict[str, object]:
    return {
        "model_id": MODULE.MODEL_ORDER[model_ordinal],
        "model_ordinal": model_ordinal,
        "candidate_index": candidate_index,
        "physical_failure_count": 0,
        "monthly_temperature_mean_error_q": 10,
        "annual_temperature_dispersion_error_q": annual,
        "temperature_cross_month_correlation_rmse_q": 20,
        "annual_temperature_lag1_error_q": 30,
        "annual_temperature_low_frequency_error_q": 40,
    }


class ContractTests(unittest.TestCase):
    def test_manifest_matches_schema_constants_and_complete_burn_grid(self):
        manifest = MODULE.validate_manifest(json.loads(MODULE.MANIFEST.read_text()))
        schema = json.loads(MODULE.SCHEMA.read_text())
        self.assertEqual(set(manifest), set(schema["required"]))
        self.assertEqual(len({burn for cohort in manifest["cohorts"] for burn in cohort["burns"]}), 32)

        changed = json.loads(MODULE.MANIFEST.read_text())
        changed["dependencies"]["panel_sha256"] = "0" * 64
        with self.assertRaises(MODULE.ContractError):
            MODULE.validate_manifest(changed)

    def test_seed_derivation_is_domain_separated_and_pinned(self):
        first = MODULE.derive_thermal_seed(
            "az026481", MODULE.MODEL_ORDER[1], "0x0c8862ed55f21e2e", 0
        )
        last = MODULE.derive_thermal_seed(
            "az026481", MODULE.MODEL_ORDER[1], "0x0c8862ed55f21e2e", 7
        )
        self.assertEqual(first, 13423984198280203969)
        self.assertEqual(last, 8137402885486637624)
        self.assertNotEqual(first, last)
        vectors = MODULE.vectors()
        self.assertEqual(
            vectors["manifest_sha256"],
            "6aa07fd460acb5b30ed4e9863b38a26787f75891a3d67caae0113844ec711aa1",
        )
        self.assertEqual(
            vectors["thermal_state_candidate_0_sha256"],
            "10ef6054ab6af5c76ed596bc552149d3b6a05ca4e2a66038eee1034ef2bcdf79",
        )
        self.assertEqual(vectors["thermal_state_candidate_0_first"], -0.8166920963129024)
        self.assertEqual(vectors["thermal_state_candidate_0_last"], -0.8254334736455715)

    def test_quantization_uses_exact_ties_to_even(self):
        self.assertEqual(MODULE.quantize_score(0.5, 1), 0)
        self.assertEqual(MODULE.quantize_score(1.5, 1), 2)
        with self.assertRaises(MODULE.ContractError):
            MODULE.quantize_score(float("nan"))
        with self.assertRaises(MODULE.ContractError):
            MODULE.quantize_score(True)

    def test_selection_is_order_invariant_and_ties_favor_faithful_then_index(self):
        rows = [record(ordinal, index, 5) for ordinal in range(2) for index in range(8)]
        self.assertEqual(MODULE.select_candidate(rows)["candidate_index"], 0)
        self.assertEqual(MODULE.select_candidate(rows)["model_id"], MODULE.MODEL_ORDER[0])
        self.assertEqual(MODULE.select_candidate(list(reversed(rows))), MODULE.select_candidate(rows))

    def test_hard_eligibility_precedes_scoring_and_invalid_cohorts_fail_closed(self):
        ineligible = record(1, 0, 1)
        ineligible["monthly_temperature_mean_error_q"] = 11
        rows = [record(0, index, 100 + index) for index in range(8)]
        rows.extend(record(1, index, 1 + index) for index in range(8))
        rows[8] = ineligible
        for row in rows[9:]:
            row["monthly_temperature_mean_error_q"] = 11
        selected = MODULE.select_candidate(rows)
        self.assertEqual(selected["model_id"], MODULE.MODEL_ORDER[0])
        with self.assertRaises(MODULE.ContractError):
            MODULE.select_candidate(rows[:-1])
        with self.assertRaises(MODULE.ContractError):
            MODULE.select_candidate([*rows[:-1], rows[0]])


if __name__ == "__main__":
    unittest.main()
