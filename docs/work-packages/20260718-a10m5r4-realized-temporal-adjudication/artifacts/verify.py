#!/usr/bin/env python3
"""Verify the minimal, no-output A10M5R4 prerequisite hold."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    audit = json.loads((ROOT / "artifacts/prerequisite-audit.json").read_text())
    assert audit["terminal"] == "HOLD-A10-REVISED-STOCHASTIC-PRISM-COMPARATOR"
    assert audit["generated_output_accessed"] is False
    assert audit["protected_roles_opened"] == []
    assert audit["successor"] == "A10M5R4R1"
    assert [row["capacity_id"] for row in audit["accepted_pair"]] == ["P1", "P2"]
    assert not any(audit["comparator_at_entry"].values())
    package = (ROOT / "package.md").read_text()
    assert "EXECUTED-HOLD-A10-REVISED-STOCHASTIC-PRISM-COMPARATOR" in package
    assert "no neural output" in package.lower()
    print("A10M5R4-HOLD-VERIFIED")


if __name__ == "__main__":
    main()
