from __future__ import annotations

import unittest

from research.a9d.campaign import (
    inverse_logistic,
    renewal_occurrence_calibration,
    simulate_bounded,
    tilt_pmf,
)


class A9dCampaignTests(unittest.TestCase):
    def test_tilt_pmf_is_normalized_and_positive(self) -> None:
        result = tilt_pmf([0.2, 0.3, 0.5], 2.0)
        self.assertAlmostEqual(sum(result), 1.0)
        self.assertTrue(all(value > 0.0 for value in result))

    def test_renewal_calibration_matches_target(self) -> None:
        parameters = {
            "wet_duration_pmf": [0.7, 0.2, 0.1],
            "dry_duration_pmf": [0.2, 0.3, 0.5],
        }
        realized = renewal_occurrence_calibration(parameters, 0.4)
        self.assertAlmostEqual(realized, 0.4, places=10)
        self.assertAlmostEqual(sum(parameters["wet_duration_pmf"]), 1.0)
        self.assertAlmostEqual(sum(parameters["dry_duration_pmf"]), 1.0)

    def test_inverse_logistic_has_open_unit_support(self) -> None:
        for value in (-20.0, -1.0, 0.0, 1.0, 20.0):
            self.assertGreater(inverse_logistic(value), 0.0)
            self.assertLess(inverse_logistic(value), 1.0)

    def test_bounded_simulator_symbol_is_callable(self) -> None:
        self.assertTrue(callable(simulate_bounded))


if __name__ == "__main__":
    unittest.main()
