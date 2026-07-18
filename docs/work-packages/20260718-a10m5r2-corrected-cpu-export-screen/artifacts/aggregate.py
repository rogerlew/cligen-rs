#!/usr/bin/env python3
"""Aggregate A10M5R2 rows and apply the frozen screen promotion order."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]
sys.path.insert(0, str(REPO))

from research.a10.m5_screen import CONFIGURATION_IDS, select_promotions  # noqa: E402


def atomic_json(path: Path, value: object) -> None:
    partial = path.with_suffix(path.suffix + ".part")
    partial.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(partial, path)


def main() -> None:
    evidence_root = PACKAGE / "artifacts/toolkit/evidence/results"
    rows = []
    for configuration in CONFIGURATION_IDS:
        evidence = json.loads(
            (evidence_root / configuration.lower() / "evidence.json").read_text(encoding="utf-8")
        )
        rows.append(evidence)
    decision = select_promotions(rows)
    decision["selector_terminal"] = decision["terminal"]
    if decision["promoted_count"]:
        decision["terminal"] = "A10M5R2-PROMOTIONS-READY"
    atomic_json(PACKAGE / "artifacts/screen-results.json", {"schema_version": 1, "configurations": rows})
    atomic_json(PACKAGE / "artifacts/promotion-trace.json", decision)
    print(decision["terminal"])


if __name__ == "__main__":
    main()
