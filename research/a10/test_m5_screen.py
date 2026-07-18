"""Tests for the frozen A10M5 promotion arithmetic."""

from __future__ import annotations

import unittest

from research.a10.m5_screen import (
    CONFIGURATION_BY_ID,
    CONFIGURATION_IDS,
    ScreenError,
    runtime_class,
    select_promotions,
)


def result(configuration_id: str, offset: float = 0.0) -> dict[str, object]:
    definition = CONFIGURATION_BY_ID[configuration_id]
    return {
        "configuration_id": configuration_id,
        "pooling_class": definition["pooling_class"],
        "valid": True,
        "validation_primary_nll": 1.0 + offset,
        "validation_tail_score": 0.5,
        "validation_stability": 0.1,
        "parameter_count": 10_000,
        "runtime_ratio_max": 4.0,
    }


class M5ScreenTests(unittest.TestCase):
    def test_exact_runtime_boundaries(self) -> None:
        self.assertEqual(runtime_class(4.999999), "PASS")
        self.assertEqual(runtime_class(5.0), "WARN")
        self.assertEqual(runtime_class(9.999999), "WARN")
        self.assertEqual(runtime_class(10.0), "FAIL")

    def test_selects_two_per_pooling_by_frozen_order(self) -> None:
        values = [result(identifier, index / 100.0) for index, identifier in enumerate(CONFIGURATION_IDS)]
        decision = select_promotions(values)
        self.assertEqual(decision["terminal"], "A10M5-PROMOTIONS-READY")
        self.assertEqual(
            decision["promotions"]["N0_complete"],
            list(CONFIGURATION_IDS[:2]),
        )
        self.assertEqual(
            decision["promotions"]["N1_partial"],
            list(CONFIGURATION_IDS[6:8]),
        )

    def test_runtime_failure_excludes_without_reordering(self) -> None:
        values = [result(identifier, index / 100.0) for index, identifier in enumerate(CONFIGURATION_IDS)]
        values[0]["runtime_ratio_max"] = 10.0
        decision = select_promotions(values)
        self.assertEqual(
            decision["promotions"]["N0_complete"],
            [CONFIGURATION_IDS[1], CONFIGURATION_IDS[2]],
        )

    def test_requires_complete_unique_grid(self) -> None:
        with self.assertRaises(ScreenError):
            select_promotions([result(identifier) for identifier in CONFIGURATION_IDS[:-1]])


if __name__ == "__main__":
    unittest.main()
