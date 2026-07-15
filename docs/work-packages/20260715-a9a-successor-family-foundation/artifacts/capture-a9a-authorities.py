#!/usr/bin/env python3
"""Capture immutable A9a authority and prior-exposure manifests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
DISPATCH_COMMIT = "5c7f5d271b93e953986b88f7987044c5270d6c61"

AUTHORITIES = {
    "adr_0001": "docs/decisions/0001-source-code-authority-port.md",
    "adr_0002": "docs/decisions/0002-quality-metrics-authority.md",
    "adr_0004": "docs/decisions/0004-a5b-interannual-no-promotion.md",
    "a5d0_package": "docs/work-packages/20260714-a5d0-successor-feasibility-calibration/package.md",
    "a5f0_package": "docs/work-packages/20260714-a5f0-annual-state-failure-attribution/package.md",
    "a5f0_decision": "docs/work-packages/20260714-a5f0-annual-state-failure-attribution/artifacts/a5f0-decision-v1.json",
    "a7a_package": "docs/work-packages/20260714-a7a-daily-precipitation-structure-baseline/package.md",
    "a7a_report": "docs/reports/a7a-daily-precipitation-structure-report.md",
    "a7a_decision": "docs/work-packages/20260714-a7a-daily-precipitation-structure-baseline/artifacts/a7a-decision-v1.json",
    "a7b_package": "docs/work-packages/20260714-a7b-analytic-precipitation-feasibility/package.md",
    "a7b_decision": "docs/work-packages/20260714-a7b-analytic-precipitation-feasibility/artifacts/a7b-decision-v1.json",
    "a7b_equivalence_review": "docs/work-packages/20260714-a7b-analytic-precipitation-feasibility/artifacts/post-analysis-equivalence-review.md",
    "a8a_package": "docs/work-packages/20260715-a8a-dry-regime-applicability/package.md",
    "a8a_decision": "docs/work-packages/20260715-a8a-dry-regime-applicability/artifacts/a8a-decision-v1.json",
    "a8b_package": "docs/work-packages/20260715-a8b-secondary-year-fallback/package.md",
    "a8b_decision": "docs/work-packages/20260715-a8b-secondary-year-fallback/artifacts/a8b-decision-v1.json",
    "a8c_package": "docs/work-packages/20260715-a8c-routed-daily-pilot/package.md",
    "a8c_decision": "docs/work-packages/20260715-a8c-routed-daily-pilot/artifacts/a8c-decision-v1.json",
    "a8c_review": "docs/work-packages/20260715-a8c-routed-daily-pilot/artifacts/review.md",
    "a8c1_package": "docs/work-packages/20260715-a8c1-routed-daily-retirement/package.md",
    "sota_gap_analysis": "docs/lit-reviews/sota-climate-generator-gap-analysis.md",
    "daily_source_assessment": "docs/work-packages/20260713-a5b-coefficient-source-assessment/artifacts/daily-source-assessment.md",
    "scientific_report_standard": "docs/standards/scientific-report-standard.md",
    "scientific_authoring_protocol": "docs/standards/scientific-report-authoring-protocol.md",
    "rust_scientific_standard": "docs/standards/rust-scientific-coding-standard.md",
}

EXPOSURE_SOURCES = {
    "a5_corpus_config": "docs/work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts/corpus/corpus-config-v1.json",
    "a5_corpus_manifest": "docs/work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts/corpus/manifest-v1.json",
    "a5_source_manifest": "docs/work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts/corpus/source-manifest-v1.json",
    "a5b_pre_candidate_freeze": "docs/work-packages/20260713-a5b-interannual-candidate-spike/artifacts/freeze/pre-candidate-freeze-v1.json",
    "a5b_candidate_manifest": "docs/work-packages/20260713-a5b-interannual-candidate-spike/artifacts/climate/candidate-evidence-manifest-v1.json",
    "a8a_panel": "docs/work-packages/20260715-a8a-dry-regime-applicability/artifacts/panel-v1.json",
    "a8a_source_manifest": "docs/work-packages/20260715-a8a-dry-regime-applicability/artifacts/source-manifest-v1.json",
    "a8b_feasibility_contract": "docs/work-packages/20260715-a8b-secondary-year-fallback/artifacts/feasibility-contract-v1.json",
    "a8c_pilot_contract": "docs/work-packages/20260715-a8c-routed-daily-pilot/artifacts/pilot-contract-v1.json",
    "a8c_closure_manifest": "docs/work-packages/20260715-a8c-routed-daily-pilot/artifacts/closure-manifest-v1.json",
}

EXPOSED_MODEL_IDS = [
    "rank_one_monthly_sd",
    "full_monthly_covariance",
    "fourier_eof",
    "vector_ar",
    "gaussian_hmm",
    "spectral_random_phase",
    "precip_counterfactual",
    "a5e0_direct_annual_state_v1",
    "a5e0_direct_monthly_loading_fit_v1",
    "o2_logqspline_gaussian_copula_v1",
    "sm2_logqspline_gaussian_copula_v1",
    "bounded_eof2_copula_ar1_reallocation_v1",
    "legacy_daily_only_v1",
    "a8c_routed_daily_v1",
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return (
        json.dumps(value, allow_nan=False, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n"
    ).encode("utf-8")


def identity(path: str) -> dict[str, object]:
    data = (ROOT / path).read_bytes()
    return {"bytes": len(data), "path": path, "sha256": sha256(data)}


def load(path: str) -> dict[str, Any]:
    value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def station_sources() -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}

    def add(station_id: str, source: str) -> None:
        result.setdefault(station_id, set()).add(source)

    a5 = load(EXPOSURE_SOURCES["a5_corpus_config"])
    for station in a5["stations"]:
        add(station["station_id"], "A5a/A5b/A7a")

    a8a = load(EXPOSURE_SOURCES["a8a_panel"])
    for station in a8a["stations"]:
        add(station["station_id"], "A8a")

    a8b = load(EXPOSURE_SOURCES["a8b_feasibility_contract"])["corpus"]
    for key in ("expected_development_station_ids", "expected_heldout_station_ids"):
        for station_id in a8b[key]:
            add(station_id, "A8b")

    a8c = load(EXPOSURE_SOURCES["a8c_pilot_contract"])
    for station in a8c["stations"]:
        add(station["station_id"], "A8c")
    return result


def main() -> None:
    authority = {
        "captured_at": "2026-07-15T14:13:23-07:00",
        "dispatch_commit": DISPATCH_COMMIT,
        "files": [
            {"authority_id": key, **identity(path)}
            for key, path in sorted(AUTHORITIES.items())
        ],
        "predecessor_terminal": "A8C-ROUTED-DAILY-RUNTIME-RETIRED",
        "schema_version": 1,
    }
    (HERE / "authority-manifest-v1.json").write_bytes(canonical(authority))

    stations = station_sources()
    exposure = {
        "a9a_confirmation_target_accessed": False,
        "candidate_outputs_and_thresholds_are_development_only": True,
        "exposed_model_ids": EXPOSED_MODEL_IDS,
        "exposed_periods": [
            {
                "period": "1980-01-01/2009-12-31",
                "role": "A5/A8 coefficient fit and exposed development",
                "sources": ["Daymet V4 R1", "available GHCN-Daily sensitivities"],
            },
            {
                "period": "2010-01-01/2025-12-31",
                "role": "A5/A7/A8 evaluation and exposed development",
                "sources": ["Daymet V4 R1", "available GHCN-Daily sensitivities"],
            },
        ],
        "source_records": [
            {"source_id": key, **identity(path)}
            for key, path in sorted(EXPOSURE_SOURCES.items())
        ],
        "stations": [
            {"prior_packages": sorted(sources), "station_id": station_id}
            for station_id, sources in sorted(stations.items())
        ],
        "schema_version": 1,
        "summary": {
            "exposed_model_ids": len(EXPOSED_MODEL_IDS),
            "exposed_source_records": len(EXPOSURE_SOURCES),
            "exposed_station_ids": len(stations),
        },
    }
    (HERE / "exposure-manifest-v1.json").write_bytes(canonical(exposure))
    print(
        f"captured {len(AUTHORITIES)} authorities, {len(EXPOSURE_SOURCES)} "
        f"exposure sources, and {len(stations)} exposed stations"
    )


if __name__ == "__main__":
    main()
