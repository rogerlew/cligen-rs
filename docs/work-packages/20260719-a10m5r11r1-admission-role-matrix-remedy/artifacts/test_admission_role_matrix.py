#!/usr/bin/env python3
"""Static mutation guards for the A10M5R11R1 admission correction."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]


class AdmissionRoleMatrixTest(unittest.TestCase):
    def test_contract_and_checker_use_derived_four_role_total(self) -> None:
        contract = json.loads(
            (PACKAGE / "artifacts/job-local-capacity-contract.json").read_text(
                encoding="utf-8"
            )
        )
        waves = contract["admission"]["waves"]
        roles = [role for wave in waves for role in wave]
        self.assertEqual(len(roles), contract["resources"]["candidate_role_count"])
        self.assertEqual(len(set(roles)), 3)
        self.assertTrue(
            contract["admission"]["admission_closes_after_any_observed_candidate_failure"]
        )
        source = (PACKAGE / "artifacts/jobs/admission_checker.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("len(set(plan_roles)) == 11", source)
        self.assertIn("len(set(plan_roles)) == len(all_roles)", source)
        self.assertIn('1 + contract["resources"]["candidate_role_count"]', source)


if __name__ == "__main__":
    unittest.main()
