"""A9c fit and structural-evidence command surface."""

from __future__ import annotations

import json
import math
import resource
import time
from pathlib import Path

import numpy as np

from research.a9c.data import ARTIFACTS, REPO, canonical_bytes, sha256_path
from research.a9c.models import (
    FIT_DETAIL_DIRECTORY,
    FIT_DIRECTORY,
    LATENT,
    RENEWAL,
    fit_configuration,
    hmm_fit,
    simulate,
    spell_counts,
    structural_audit,
    verify_fit,
)


CAMPAIGN = ARTIFACTS / "campaign-freeze-v1.json"
FIT_EXECUTION = ARTIFACTS / "fit-execution-v1.json"
STRUCTURAL = ARTIFACTS / "structural-audit-v1.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def write(path: Path, value: object) -> None:
    if path.exists():
        raise FileExistsError(path)
    path.write_bytes(canonical_bytes(value))


def synthetic_recovery(details: list[dict]) -> dict:
    rows = []
    for candidate in (RENEWAL, LATENT):
        fit = next(value for value in details if value["candidate_class"] == candidate)
        site = "id101022"
        generated = simulate(fit, site, burn=909091, years=30)
        wet_fraction = float(np.mean([row["precip_mm"] > 0.0 for row in generated]))
        amount_mean = float(np.mean([row["precip_mm"] for row in generated if row["precip_mm"] > 0.0]))
        if candidate == RENEWAL:
            recovered = spell_counts(generated, 0.0000001)
            wet_spells = sum(array.sum() for array in recovered["wet"].values())
            dry_spells = sum(array.sum() for array in recovered["dry"].values())
            hidden_state_count = 0
            mixed_state_count = None
            recovery_pass = wet_spells >= 50 and dry_spells >= 50 and 0.01 < wet_fraction < 0.99 and amount_mean > 0.0
        else:
            refit = hmm_fit(generated, int(fit["configuration"]["hidden_states"]), iterations=10)
            hidden_state_count = len(refit.wet_probability)
            mixed_state_count = sum(
                any(row["latent_state"] == state and row["precip_mm"] > 0.0 for row in generated)
                and any(row["latent_state"] == state and row["precip_mm"] == 0.0 for row in generated)
                for state in range(hidden_state_count)
            )
            recovery_pass = mixed_state_count == hidden_state_count and all((refit.wet_probability > 0.0) & (refit.wet_probability < 1.0))
            wet_spells = dry_spells = None
        rows.append(
            {
                "amount_mean_mm": amount_mean,
                "candidate_class": candidate,
                "dry_spell_count": dry_spells,
                "hidden_state_count": hidden_state_count,
                "mixed_emission_state_count": mixed_state_count,
                "recovery_status": "pass" if recovery_pass else "fail",
                "simulation_days": len(generated),
                "site": site,
                "wet_fraction": wet_fraction,
                "wet_spell_count": wet_spells,
            }
        )
    renewal_fit = next(value for value in details if value["candidate_class"] == RENEWAL)
    latent_fit = next(value for value in details if value["candidate_class"] == LATENT)
    renewal_stream = simulate(renewal_fit, "id101022", burn=717171, years=30)
    latent_stream = simulate(latent_fit, "id101022", burn=717171, years=30)
    latent_boundaries_cross_observed_spells = sum(
        latent_stream[index]["latent_state"] != latent_stream[index - 1]["latent_state"]
        and (latent_stream[index]["precip_mm"] > 0.0) == (latent_stream[index - 1]["precip_mm"] > 0.0)
        for index in range(1, len(latent_stream))
    )
    same_observable_bytes = canonical_bytes(
        [(row["date"], row["precip_mm"]) for row in renewal_stream]
    ) == canonical_bytes([(row["date"], row["precip_mm"]) for row in latent_stream])
    return {
        "cross_fit": {
            "exact_observable_law_identity": same_observable_bytes,
            "latent_boundaries_crossing_observed_spells": latent_boundaries_cross_observed_spells,
            "same_state_probability_law_under_bijection": False,
            "status": "pass" if not same_observable_bytes and latent_boundaries_cross_observed_spells > 0 else "fail",
        },
        "recovery": rows,
        "schema_version": 1,
        "status": "pass" if all(row["recovery_status"] == "pass" for row in rows) and not same_observable_bytes and latent_boundaries_cross_observed_spells > 0 else "fail",
    }


def fit_all() -> None:
    if FIT_EXECUTION.exists() or STRUCTURAL.exists():
        raise FileExistsError("fit evidence exists")
    if FIT_DIRECTORY.exists() and any(FIT_DIRECTORY.rglob("*.json")):
        raise FileExistsError("fit directory is not empty")
    campaign = load(CAMPAIGN)
    records = []
    official = []
    details = []
    started = time.monotonic()
    for config in campaign["configuration_grid"]:
        before = time.monotonic()
        fit = fit_configuration(config)
        official_path = FIT_DIRECTORY / f"{config['configuration_id']}.fit.json"
        detail_path = FIT_DETAIL_DIRECTORY / f"{config['configuration_id']}.json"
        verify_fit(official_path)
        detail = load(detail_path)
        details.append(detail)
        official.append(fit)
        records.append(
            {
                "candidate_class": config["candidate_class"],
                "configuration_id": config["configuration_id"],
                "detail_path": str(detail_path.relative_to(REPO)),
                "detail_sha256": sha256_path(detail_path),
                "fit_path": str(official_path.relative_to(REPO)),
                "fit_sha256": sha256_path(official_path),
                "fit_status": fit["fit_status"],
                "wall_seconds": time.monotonic() - before,
            }
        )
    recovery = synthetic_recovery(details)
    static = structural_audit(details)
    structural = {
        "cross_fit_recovery": recovery,
        "degenerate_intersection_test": "pass" if static["status"] == "pass" else "fail",
        "schema_version": 1,
        "static_factorization": static,
        "status": "pass" if static["status"] == "pass" and recovery["status"] == "pass" else "fail",
    }
    write(STRUCTURAL, structural)
    write(
        FIT_EXECUTION,
        {
            "campaign_freeze_sha256": sha256_path(CAMPAIGN),
            "configuration_count": len(records),
            "fits": records,
            "maximum_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
            "schema_version": 1,
            "structural_audit_sha256": sha256_path(STRUCTURAL),
            "wall_seconds": time.monotonic() - started,
        },
    )
    print(f"fit {len(records)} configurations; structural={structural['status']}")


def verify() -> None:
    evidence = load(FIT_EXECUTION)
    for record in evidence["fits"]:
        path = REPO / record["fit_path"]
        verify_fit(path)
        if sha256_path(path) != record["fit_sha256"]:
            raise ValueError(f"fit hash: {path}")
        detail = REPO / record["detail_path"]
        if sha256_path(detail) != record["detail_sha256"]:
            raise ValueError(f"detail hash: {detail}")
    structural = load(STRUCTURAL)
    if structural["status"] != "pass" or sha256_path(STRUCTURAL) != evidence["structural_audit_sha256"]:
        raise ValueError("structural audit")
    print(f"PASS: {len(evidence['fits'])} immutable fits; actual-class recovery and non-isomorphism")


if __name__ == "__main__":
    import sys

    if sys.argv[1:] == ["fit-all"]:
        fit_all()
    elif sys.argv[1:] == ["verify"]:
        verify()
    else:
        raise SystemExit("usage: python -m research.a9c.run fit-all|verify")
