#!/usr/bin/env python3
"""Resolve a generic capacity/frontier role from frozen predecessor rows."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import m5r3_contract as contract


def load_rows(root: Path, prefix: str) -> list[dict]:
    paths = sorted(root.glob(f"{prefix}-*/row.json"))
    return [json.loads(path.read_text(encoding="utf-8")) for path in paths]


def atomic(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("capacity", "frontier"), required=True)
    parser.add_argument("--slot", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--results", type=Path, required=True)
    options = parser.parse_args()
    family_result = contract.select_family(load_rows(options.results, "family"))
    atomic(options.results / "family-selection.json", family_result)
    family = family_result["winner"]
    if options.phase == "capacity":
        capacities = tuple(contract.CAPACITY_LADDER)
        if options.slot not in range(len(capacities)) or options.seed != contract.SEEDS[0]:
            raise RuntimeError("capacity generic role outside frozen matrix")
        capacity = capacities[options.slot]
    else:
        capacity_result = contract.select_capacity(load_rows(options.results, "capacity"), family)
        atomic(options.results / "capacity-selection.json", capacity_result)
        if options.slot not in range(4) or options.seed not in contract.SEEDS[1:]:
            raise RuntimeError("frontier generic role outside frozen matrix")
        capacity = capacity_result["pair"][options.slot // 2]
        if options.seed != contract.SEEDS[1 + options.slot % 2]:
            raise RuntimeError("frontier seed/slot mismatch")
    print(f"{family} {capacity}")


if __name__ == "__main__":
    main()
