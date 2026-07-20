#!/usr/bin/env python3
"""Fail-closed verifier for the A10M5R11R2 local scoring remedy."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
PACKAGE = Path(__file__).resolve().parents[1]
R1 = REPO / "docs/work-packages/20260719-a10m5r11r1-admission-role-matrix-remedy/artifacts"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    identity = json.loads((PACKAGE / "artifacts/evidence-identity.json").read_text())
    contract = json.loads((PACKAGE / "artifacts/evaluation-contract.json").read_text())
    inherited = json.loads((R1 / "temporal-contract.json").read_text())
    paths = {
        "scorer_sha256": R1 / "jobs/temporal_select.py",
        "temporal_metrics_sha256": R1 / "jobs/temporal_metrics.py",
        "sites_sha256": R1 / "sites.json",
        "collection_sha256": R1 / "toolkit-recovered/collection.json",
        "cleanup_sha256": R1 / "toolkit-recovered/cleanup.json",
        "terminal_sha256": R1 / "toolkit-recovered/terminal.json",
        "annual_monthly_residual_adapter_k1_streams_sha256": R1 / "toolkit-recovered/evidence/results/annual-monthly-residual-adapter-k1/streams.json",
        "monthly_residual_adapter_k2_streams_sha256": R1 / "toolkit-recovered/evidence/results/monthly-residual-adapter-k2/streams.json",
        "annual_monthly_residual_adapter_k2_streams_sha256": R1 / "toolkit-recovered/evidence/results/annual-monthly-residual-adapter-k2/streams.json",
    }
    for key, path in paths.items():
        if digest(path) != identity["inputs"][key]:
            raise SystemExit(f"identity mismatch: {key}")
    binary = REPO / "target/debug/cligen"
    if digest(binary) != identity["binary_sha256"]:
        raise SystemExit("local comparator binary identity mismatch")
    if contract["generation"]["stochastic_burn_counts"] != [101, 1101, 2101, 3101, 4101, 5101, 6101, 7101]:
        raise SystemExit("comparator burn list drift")
    if contract["resources"] != {"gpu_minute_ceiling": 0, "gpu_jobs": 0}:
        raise SystemExit("local-only resource contract drift")
    if contract["protected_roles_opened"] or contract["solar"]["opened"]:
        raise SystemExit("role firewall drift")
    for key in ("roles", "observation", "metrics", "scoring", "solar"):
        if contract[key] != inherited[key]:
            raise SystemExit(f"inherited science drift: {key}")
    inherited_generation = dict(inherited["generation"])
    corrected_generation = dict(contract["generation"])
    corrected_generation.pop("stochastic_burn_counts")
    if corrected_generation != inherited_generation:
        raise SystemExit("generation contract drift beyond comparator burns")
    print("A10M5R11R2-FREEZE-READY")


if __name__ == "__main__":
    main()
