#!/usr/bin/env python3
"""Execute R1's identity-bound scorer with century-safe year labels."""

from __future__ import annotations

import datetime as dt
import importlib.util
import sys
from pathlib import Path
from typing import Any

import numpy as np

PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]
R1_SCRIPT = REPO / "docs/work-packages/20260718-a10m5r4r2r1r1-evaluation-year-axis-remedy/artifacts/jobs/score.py"


def load_r1() -> Any:
    spec = importlib.util.spec_from_file_location("a10m5r4r2r1r1_score", R1_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load R1 scorer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def corrected_resample(parent: Any, blocks: list[dict[str, Any]], indices: np.ndarray) -> dict[str, float]:
    dates: list[dt.date] = []
    precipitation: list[np.ndarray] = []
    tmax: list[np.ndarray] = []
    tmin: list[np.ndarray] = []
    for position, index in enumerate(indices):
        block = blocks[int(index)]
        leap = any(date.month == 2 and date.day == 29 for date in block["dates"])
        target_year = 2000 + 16 * position + (0 if leap else 1)
        dates.extend(date.replace(year=target_year) for date in block["dates"])
        precipitation.append(block["precipitation"])
        tmax.append(block["tmax"])
        tmin.append(block["tmin"])
    return parent.realized_metrics(dates, np.concatenate(precipitation), np.concatenate(tmax), np.concatenate(tmin))


def main() -> None:
    r1 = load_r1()
    original_loader = r1.load_parent

    def load_parent() -> Any:
        parent = original_loader()
        r1.corrected_resample = lambda _module, blocks, indices: corrected_resample(parent, blocks, indices)
        return parent

    r1.load_parent = load_parent
    r1.main()


if __name__ == "__main__":
    main()
