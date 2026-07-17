"""Executable A10M3 contract vectors."""

from __future__ import annotations

import copy
import unittest

from research.a10.m3_contract import (
    CANONICAL_CONFIGURATION_ID,
    CANONICAL_CONFIGURATION_SHA256,
    ContractError,
    classify_runtime,
    regime_is_applicable,
    select_candidate,
    validate_checkpoint_record,
    validate_generation_record,
    validate_model_record,
)


SHA = "1" * 64


def model() -> dict:
    return {
        "schema_version": 1,
        "model_id": "n0-l32-lognormal-s147031",
        "family_id": "neural_point_weather_state_space_v1",
        "pooling_class": "N0_complete",
        "configuration_id": CANONICAL_CONFIGURATION_ID,
        "configuration_sha256": CANONICAL_CONFIGURATION_SHA256,
        "parameter_count": 1_000_000,
        "architecture": {"latent_dim": 32, "width": 128, "depth": 2, "tail_head": "lognormal"},
        "corpus_manifest_sha256": SHA,
        "normalization_sha256": SHA,
    }


def checkpoint() -> dict:
    return {
        "schema_version": 1,
        "checkpoint_id": "ckpt-1",
        "model_id": "model-1",
        "epoch": 2,
        "global_step": 42,
        "training_seed": 147031,
        "payload_sha256": SHA,
        "payload_bytes": 100,
        "state": {key: True for key in ("model", "optimizer", "scheduler", "scaler", "rng", "sampler")},
        "corpus_cursor": {"epoch_order_sha256": SHA, "next_batch": 7},
        "created_utc": "2026-07-17T00:00:00Z",
    }


def generation() -> dict:
    return {
        "schema_version": 1,
        "stream_id": "stream-1",
        "model_id": "model-1",
        "model_sha256": SHA,
        "station_id": "az026481",
        "regime": "hot_arid",
        "burn_id": 101,
        "member_id": 0,
        "horizon_years": 100,
        "rng": {"algorithm": "random123_philox4x32_10", "key": "a10", "counter_layout": "station,burn,member,date,draw"},
        "row_count": 36524,
        "stream_sha256": SHA,
        "prefix_30_sha256": SHA,
    }


def regime(name: str = "hot_arid") -> dict:
    return {
        "regime": name,
        "horizons": [
            {
                "years": years,
                "comparators": [
                    {"id": comparator, "available": True, "delta": -0.11, "upper_95": -0.001}
                    for comparator in ("B0", "B1")
                ],
                "guards": [
                    {"family": family, "available": True, "upper_95": 0.0}
                    for family in ("occurrence_spell", "aggregate_extreme", "compound_context", "winter_proxy")
                ],
            }
            for years in (30, 100)
        ],
    }


class RecordTests(unittest.TestCase):
    def test_valid_records(self) -> None:
        validate_model_record(model())
        validate_checkpoint_record(checkpoint())
        validate_generation_record(generation())

    def test_model_rejects_unknown_key(self) -> None:
        value = model(); value["surprise"] = True
        with self.assertRaises(ContractError): validate_model_record(value)

    def test_model_rejects_legacy_runtime(self) -> None:
        value = model(); value["configuration_id"] = "python-3.8-legacy"
        with self.assertRaises(ContractError): validate_model_record(value)

    def test_model_rejects_parameter_overrun(self) -> None:
        value = model(); value["parameter_count"] = 50_000_001
        with self.assertRaises(ContractError): validate_model_record(value)

    def test_checkpoint_requires_rng(self) -> None:
        value = checkpoint(); value["state"]["rng"] = False
        with self.assertRaises(ContractError): validate_checkpoint_record(value)

    def test_generation_requires_nested_100_year_stream(self) -> None:
        value = generation(); value["horizon_years"] = 30
        with self.assertRaises(ContractError): validate_generation_record(value)


class DecisionTests(unittest.TestCase):
    def test_runtime_boundaries(self) -> None:
        self.assertEqual(classify_runtime(4.999999), "PASS")
        self.assertEqual(classify_runtime(5.0), "WARN")
        self.assertEqual(classify_runtime(9.999999), "WARN")
        self.assertEqual(classify_runtime(10.0), "FAIL")

    def test_runtime_rejects_nonfinite(self) -> None:
        with self.assertRaises(ContractError): classify_runtime(float("nan"))

    def test_regime_passes_at_exact_margin(self) -> None:
        value = regime()
        for horizon in value["horizons"]:
            for comparator in horizon["comparators"]: comparator["delta"] = -0.10
        self.assertTrue(regime_is_applicable(value))

    def test_regime_missing_b1_is_not_favorable(self) -> None:
        value = regime(); value["horizons"][0]["comparators"][1]["available"] = False
        self.assertFalse(regime_is_applicable(value))

    def test_regime_guard_degradation_fails(self) -> None:
        value = regime(); value["horizons"][1]["guards"][0]["upper_95"] = 0.001
        self.assertFalse(regime_is_applicable(value))

    def test_regime_requires_both_horizons(self) -> None:
        value = regime(); value["horizons"].pop()
        with self.assertRaises(ContractError): regime_is_applicable(value)

    def test_selector_uses_frozen_tie_break(self) -> None:
        regimes = [regime(name) for name in ("hot_arid", "arid_boundary", "humid", "cold")]
        base = {
            "hard_gates_pass": True, "regimes": regimes, "primary_score": 0.5,
            "runtime_class": "PASS", "training_seed_sd": 0.1,
            "runtime_ratio": 2.0, "model_bytes": 100,
        }
        candidates = [dict(base, candidate_id="z"), dict(base, candidate_id="a")]
        self.assertEqual(select_candidate(candidates), "a")

    def test_selector_requires_four_regimes(self) -> None:
        candidate = {
            "candidate_id": "a", "hard_gates_pass": True,
            "regimes": [regime(name) for name in ("hot_arid", "humid", "cold")],
            "primary_score": 0.5, "runtime_class": "PASS",
            "training_seed_sd": 0.1, "runtime_ratio": 2.0, "model_bytes": 100,
        }
        self.assertIsNone(select_candidate([candidate]))

    def test_selector_rejects_runtime_label_mismatch(self) -> None:
        candidate = {
            "candidate_id": "a", "hard_gates_pass": True,
            "regimes": [regime(name) for name in ("hot_arid", "arid_boundary", "humid", "cold")],
            "primary_score": 0.5, "runtime_class": "PASS",
            "training_seed_sd": 0.1, "runtime_ratio": 5.0, "model_bytes": 100,
        }
        self.assertIsNone(select_candidate([candidate]))


if __name__ == "__main__":
    unittest.main()
