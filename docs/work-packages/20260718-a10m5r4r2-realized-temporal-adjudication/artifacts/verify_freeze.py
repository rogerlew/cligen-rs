#!/usr/bin/env python3
"""Fail-closed verification of the prospective A10M5R4R2 freeze."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]
ARTIFACTS = PACKAGE / "artifacts"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    contract = json.loads((ARTIFACTS / "temporal-contract.json").read_text(encoding="utf-8"))
    sites = json.loads((ARTIFACTS / "sites.json").read_text(encoding="utf-8"))
    require(contract["generated_output_accessed_at_freeze"] is False, "freeze accessed generated output")
    require(contract["roles"]["development_selection_opened"] is False, "development role opened")
    require(contract["roles"]["confirmation_opened"] is False, "confirmation role opened")
    require(len(contract["models"]) == 6, "expected six accepted model identities")
    require({value["capacity_id"] for value in contract["models"]} == {"P1", "P2"}, "capacity pair mismatch")
    require(len(sites["sites"]) == 6, "expected six regimes")
    require(len({value["regime"] for value in sites["sites"]}) == 6, "regime roster mismatch")
    require(all(value["role"] == "fit_validation" for value in sites["sites"]), "site role mismatch")

    selected_path = REPO / sites["selection"]["source_path"]
    require(digest(selected_path) == sites["selection"]["source_sha256"], "site selection authority mismatch")
    selected = json.loads(selected_path.read_text(encoding="utf-8"))["locations"]
    expected = {}
    for value in sorted((row for row in selected if row["role"] == "fit_validation"), key=lambda row: (row["regime"], row["order"])):
        expected.setdefault(value["regime"], value["point_id"])
    require(expected == {value["regime"]: value["point_id"] for value in sites["sites"]}, "value-blind site selection mismatch")

    predecessor = REPO / "docs/work-packages/20260718-a10m5r3-candidate-family-capacity-knee/artifacts/toolkit-recovered/evidence/results"
    for model in contract["models"]:
        metadata = json.loads((predecessor / model["row_id"] / "export-metadata.json").read_text(encoding="utf-8"))
        for key in ("capacity_id", "training_seed", "parameter_count", "export_bytes", "export_sha256"):
            require(metadata[key] == model[key], f"accepted model mismatch: {model['row_id']} {key}")
    for site in sites["sites"]:
        shard = REPO / "docs/work-packages/20260717-a10m1-corpus-role-freeze/raw/training/daymet-v2" / site["daymet_shard"]
        require(digest(shard) == site["daymet_shard_sha256"], f"Daymet shard mismatch: {site['point_id']}")
    print("A10M5R4R2-FREEZE-READY")


if __name__ == "__main__":
    main()
