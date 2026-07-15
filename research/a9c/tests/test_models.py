from __future__ import annotations

import unittest

import numpy as np

from research.a9c.models import pool_pmf, sample_pmf


class ModelHelperTests(unittest.TestCase):
    def test_hierarchical_duration_probability_is_normalized(self) -> None:
        station = np.zeros(61)
        station[1] = 2
        group = np.ones(61)
        global_ = np.arange(1, 62)
        result = pool_pmf(station, group, global_, 50.0)
        self.assertAlmostEqual(sum(result), 1.0)
        self.assertTrue(all(value > 0.0 for value in result))

    def test_discrete_sampler_uses_one_based_duration(self) -> None:
        self.assertEqual(sample_pmf([0.25, 0.75], 0.1), 1)
        self.assertEqual(sample_pmf([0.25, 0.75], 0.9), 2)


if __name__ == "__main__":
    unittest.main()
