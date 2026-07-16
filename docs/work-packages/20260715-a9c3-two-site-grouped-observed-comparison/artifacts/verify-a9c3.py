#!/usr/bin/env python3
"""Verify canonical A9c3 evidence from the repository root."""

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from research.a9c3.experiment import verify


if __name__ == "__main__":
    verify()
