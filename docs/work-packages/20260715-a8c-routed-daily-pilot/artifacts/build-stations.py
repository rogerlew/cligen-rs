#!/usr/bin/env python3
"""Build the six frozen A8c station documents from A8a parent evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import tarfile
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
PACKAGE = Path(__file__).resolve().parents[1]
A8A = ROOT / "docs/work-packages/20260715-a8a-dry-regime-applicability/artifacts"
ARCHIVE = A8A / "selected-parameters-v1.tar.gz"
ANALYSIS = A8A / "a8a-analysis-v1.json"
CONTRACT = PACKAGE / "artifacts/pilot-contract-v1.json"
OUTPUT = PACKAGE / "artifacts/stations"
A8A_SHA = "78b9b9bb5cd5172459bfb27ba13f7b20ca2cec5af19cab9547c425c7a6e6e89b"
A8B_SHA = "b227951faa72287afd859fb9872eb75aa559714ab6b5efd2303560b73e5a1efb"
SEASONS = ["DJF", "MAM", "JJA", "SON"]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def base_document(binary: Path, station_id: str, archive: tarfile.TarFile, work: Path) -> dict:
    member = archive.getmember(f"station-parameters/{station_id}.par")
    source = archive.extractfile(member)
    if source is None:
        raise RuntimeError(f"missing archive member for {station_id}")
    par = work / f"{station_id}.par"
    destination = work / f"{station_id}.station.json"
    par.write_bytes(source.read())
    subprocess.run(
        [str(binary), "stations", "convert", str(par), str(destination)],
        cwd=ROOT,
        check=True,
    )
    return load_json(destination)


def integrated_block(result: dict) -> dict:
    full = result["full_record"]
    seasons = []
    for season in SEASONS:
        amount = full["amount_fits"][season]
        seasons.append(
            {
                "season": season,
                "log_quantile_knots_mm": amount["log_quantile_knots_mm"],
                "gaussian_copula_rho": amount["gaussian_copula_rho"],
            }
        )
    months = []
    for cell in full["cells"]:
        months.append(
            {
                "month": cell["month"],
                "occurrence_probabilities": cell["kernel"]["probabilities"],
                "amount_dispersion": cell["budget"]["budget_dispersion"],
                "legacy_amount_dispersion": cell["budget"]["legacy_dispersion"],
            }
        )
    return {
        "route": "integrated_daily",
        "fit_id": "a8a_o2_logqspline_gaussian_copula_v1",
        "source_analysis_sha256": A8A_SHA,
        "seasons": seasons,
        "months": months,
    }


def fallback_block() -> dict:
    return {
        "route": "legacy_daily_fallback",
        "fit_id": "legacy_daily_only_v1",
        "source_analysis_sha256": A8B_SHA,
        "seasons": [],
        "months": [],
    }


def build(binary: Path) -> None:
    contract = load_json(CONTRACT)
    analysis = load_json(ANALYSIS)
    results = {entry["station_id"]: entry for entry in analysis["station_results"]}
    OUTPUT.mkdir(parents=True, exist_ok=True)
    expected = {f"{entry['station_id']}.station.json" for entry in contract["stations"]}
    for path in OUTPUT.glob("*.station.json"):
        if path.name not in expected:
            path.unlink()
    with tarfile.open(ARCHIVE, "r:gz") as archive, tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        for station in contract["stations"]:
            station_id = station["station_id"]
            result = results[station_id]
            if result["classification"] != station["route"]:
                raise RuntimeError(f"{station_id}: route differs from A8a")
            document = base_document(binary, station_id, archive, work)
            document["station_schema_version"] = 2
            if station["route"] == "integrated_daily":
                document["station_model"] = "a8c_integrated_daily_v1"
                document["daily_precipitation"] = integrated_block(result)
            else:
                document["station_model"] = "fixed_monthly_5_32_3"
                document["daily_precipitation"] = fallback_block()
            destination = OUTPUT / f"{station_id}.station.json"
            destination.write_text(
                json.dumps(document, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, default=ROOT / "target/debug/cligen")
    args = parser.parse_args()
    build(args.binary.resolve())


if __name__ == "__main__":
    main()
