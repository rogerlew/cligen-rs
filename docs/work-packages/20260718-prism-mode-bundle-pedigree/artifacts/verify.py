#!/usr/bin/env python3
"""Verify the PRISM public mode pedigree and limitation contract."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]
CONTRACT = PACKAGE / "artifacts/method-record-contract.json"
EMBEDDED = REPO / "crates/cligen/src/prism/method.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert CONTRACT.read_bytes() == EMBEDDED.read_bytes()
    record = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert record["schema_version"] == 1
    assert record["method_id"] == "stochastic_prism_localized_par_v1"
    assert record["origin"].startswith("FSWEPP Rock:Clime")
    assert [entry["stage"] for entry in record["pedigree"]] == [
        "FSWEPP Rock:Clime",
        "Brooks et al. 2016",
        "WEPPcloud wepppy",
        "cligen-rs",
    ]
    assert len(record["limitations"]) == 9
    assert len({entry["id"] for entry in record["limitations"]}) == 9
    required = {
        "monthly_normals_only",
        "station_inherited_structure",
        "heuristic_occurrence_and_intensity",
        "point_cell_no_terrain",
        "station_selector_not_prior_identity",
        "static_climatology",
        "no_multi_point_coherence",
        "comparison_not_quality_certification",
        "not_official_prism_product",
    }
    assert {entry["id"] for entry in record["limitations"]} == required

    distribution = json.loads(
        (REPO / "crates/cligen/src/prism/distribution.json").read_text()
    )
    assert distribution["bundle_id"] == "prism_norm91m_9120_4km_m4_m5_v1"
    assert distribution["runtime_archive"] == {
        "url": "https://api.github.com/repos/rogerlew/cligen-rs/releases/assets/481957711",
        "file_name": "prism-normals-runtime-2026.07.tar.gz",
        "bytes": 62509110,
        "sha256": "49fe87c83511678094e1033ecc2143d5d833811135934858aab854af78c28292",
    }
    assert distribution["source_archive"] == {
        "url": "https://api.github.com/repos/rogerlew/cligen-rs/releases/assets/481957709",
        "file_name": "prism-normals-source-2026.07.tar.gz",
        "bytes": 108213469,
        "sha256": "c3b832d43de54face39486673843d6c5bc511793804f5678dcb1af809ac0475c",
    }

    spec = (
        REPO / "docs/specifications/SPEC-A10-STOCHASTIC-PRISM-COMPARATOR.md"
    ).read_text()
    assert "Revision: 3" in spec
    assert "## Pedigree and authority boundary" in spec
    assert "Every successful run emits `method.json`" in spec
    source = (REPO / "crates/cligen/src/prism/run.rs").read_text()
    assert 'output_dir.join("method.json")' in source
    assert "EMBEDDED_METHOD" in source
    print(f"PRISM-METHOD-CONTRACT-VERIFIED {sha256(CONTRACT)}")


if __name__ == "__main__":
    main()
