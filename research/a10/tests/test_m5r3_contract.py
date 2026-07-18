import unittest

from research.a10.m5r3_contract import (
    CAPACITY_LADDER,
    FAMILIES,
    SEEDS,
    parameter_count,
    select_capacity,
    select_family,
    validate_pair,
)


def row(family, seed, capacity="FAMILY", score=1.0, parameters=50_000):
    return {
        "amount_family": family, "training_seed": seed, "capacity_id": capacity,
        "validation_primary_nll": score, "validation_tail_score": 0.2,
        "validation_stability": 0.1, "runtime_ratio_max": parameters / 100_000,
        "peak_rss_bytes": parameters * 10, "export_bytes": parameters * 4,
        "gpu_fit_wall_seconds": parameters / 1000, "parameter_count": parameters,
        "gates": {"complete": True}, "valid": True,
    }


class ContractTests(unittest.TestCase):
    def test_parameter_count_changes_only_by_three_heads(self):
        base = parameter_count(FAMILIES[0], 64, 128, 2)
        splice = parameter_count(FAMILIES[2], 64, 128, 2)
        self.assertEqual(splice - base, 3 * 65)

    def test_family_order_is_prospective_tuple(self):
        rows = [row(family, seed, score=1.0 + FAMILIES.index(family)) for family in FAMILIES for seed in SEEDS]
        self.assertEqual(select_family(rows)["winner"], FAMILIES[0])

    def test_capacity_pair_is_neighboring_frontier(self):
        family = FAMILIES[0]
        rows = []
        scores = [3.0, 2.0, 1.4, 1.2, 1.19]
        for index, (capacity, architecture) in enumerate(CAPACITY_LADDER.items()):
            count = parameter_count(family, architecture["latent_dim"], architecture["width"], architecture["depth"])
            rows.append(row(family, SEEDS[0], capacity, scores[index], count))
        result = select_capacity(rows, family)
        self.assertEqual(len(result["pair"]), 2)
        self.assertEqual(result["frontier"].index(result["pair"][1]), result["frontier"].index(result["pair"][0]) + 1)

    def test_pair_stability(self):
        family = FAMILIES[1]
        rows = [row(family, seed, capacity, 1.0 + (seed % 3) * 0.01) for capacity in ("P1", "P2") for seed in SEEDS]
        self.assertTrue(validate_pair(rows, family, ("P1", "P2"))["ready"])


if __name__ == "__main__":
    unittest.main()
