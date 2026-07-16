from __future__ import annotations

import unittest

from research.a9c.models import load_uscrn
from research.a9c3.experiment import (
    GROUP_SITES,
    event_vectors,
    feature_distance,
    finite,
    load,
    predecessor_feature_rows,
    sha256_path,
    station_year_resample,
    validate_rows,
    ARTIFACTS,
    DESIGN,
)


class GroupedStormTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.development = load_uscrn("development")

    def test_registered_hot_arid_counts_and_components(self) -> None:
        self.assertEqual(
            {site: len(self.development[site]["events"]) for site in GROUP_SITES},
            {"az_yuma_27_ene": 136, "ca_stovepipe_wells_1_sw": 97},
        )
        for site in GROUP_SITES:
            vectors = event_vectors(self.development[site]["events"])
            self.assertEqual(len(vectors["storm_duration"]), 3)
            self.assertEqual(len(vectors["storm_time_to_peak"]), 3)
            self.assertEqual(len(vectors["storm_peak_ratio"]), 3)
            self.assertEqual(len(vectors["storm_joint_dependence"]), 15)
            self.assertTrue(all(finite(values) for values in vectors.values()))

    def test_station_year_resampling_is_replayable(self) -> None:
        events = self.development[GROUP_SITES[0]]["events"]
        first = station_year_resample(events, 30, 7, GROUP_SITES[0], "test")
        second = station_year_resample(events, 30, 7, GROUP_SITES[0], "test")
        self.assertEqual(first, second)
        self.assertGreater(len(first), len(events))
        self.assertTrue(all(finite(values) for values in event_vectors(first).values()))

    def test_design_binds_amended_objective_registry(self) -> None:
        design = load(DESIGN)
        grouped = design["grouped_storm_amendment"]
        amendment = ARTIFACTS / "grouped-storm-objective-amendment-v1.json"
        self.assertEqual(grouped["objective_amendment_sha256"], sha256_path(amendment))
        self.assertEqual(
            sum(len(value) for value in grouped["generated_contributors"].values()), 20
        )
        self.assertEqual(
            design["all_family_threshold_calibration"]["threshold_count"], 14
        )

    def test_objective_specific_distance_rules(self) -> None:
        available = {"available": True, "values": [0.2, 0.4]}
        shifted = {"available": True, "values": [0.3, 0.5]}
        self.assertAlmostEqual(
            feature_distance("occ_monthly_wet_frequency", shifted, available, 0.01),
            0.1,
        )
        self.assertIsNone(
            feature_distance(
                "occ_monthly_wet_frequency",
                {"available": False, "values": [0.3, 0.5]},
                available,
                0.01,
            )
        )

    def test_engineering_validator_rejects_support_violation(self) -> None:
        invalid = [
            {
                "date": "2001-01-01",
                "precip_mm": -1.0,
                "tmax_c": 0.0,
                "tmin_c": 1.0,
            }
        ]
        result = validate_rows(invalid, 2001, 1)
        self.assertEqual(result["status"], "fail")
        self.assertGreaterEqual(result["violation_count"], 3)

    def test_predecessor_feature_adapter_preserves_precipitation(self) -> None:
        row = {
            "date": "2001-01-01",
            "precip_mm": 2.5,
            "tmax_c": 8.0,
            "tmin_c": 1.0,
        }
        adapted = predecessor_feature_rows([row])
        self.assertEqual(adapted[0]["prcp_mm"], 2.5)
        self.assertEqual(adapted[0]["precip_mm"], 2.5)
        self.assertEqual(row.get("prcp_mm"), None)


if __name__ == "__main__":
    unittest.main()
