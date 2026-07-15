#!/usr/bin/env python3
"""Verify the frozen A7a package and optionally reproduce its outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
PACKAGE = Path(__file__).resolve().parent
FREEZE = PACKAGE / "pre-analysis-freeze-v4.json"
FIRST_POST_FREEZE = PACKAGE / "post-analysis-freeze-v1.json"
POST_FREEZE = PACKAGE / "post-analysis-freeze-v2.json"
CONTRACT = PACKAGE / "measurement-contract-v1.json"
ANALYSIS = PACKAGE / "a7a-analysis-v1.json"
DECISION = PACKAGE / "a7a-decision-v1.json"
FINDINGS = PACKAGE / "findings.md"
ANALYZER = PACKAGE / "analyze-a7a.py"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load(path: Path) -> Any:
    def reject(token: str) -> None:
        raise ValueError(f"non-finite JSON token: {token}")

    def unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
        value: dict[str, object] = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"duplicate JSON key: {key}")
            value[key] = item
        return value

    with path.open(encoding="utf-8") as stream:
        return json.load(
            stream,
            parse_constant=reject,
            object_pairs_hook=unique,
        )


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def conventional_median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2.0


def severity_numeric(value: float | str | None) -> float | None:
    if value == "infinity":
        return math.inf
    return None if value is None else float(value)


def severity_median(values: list[float | str | None]) -> float | str | None:
    numeric = [severity_numeric(value) for value in values if value is not None]
    result = conventional_median([value for value in numeric if value is not None])
    if result is None:
        return None
    return "infinity" if math.isinf(result) else result


def verify_frozen() -> tuple[dict[str, Any], dict[str, Any]]:
    freeze = load(FREEZE)
    first_post_freeze = load(FIRST_POST_FREEZE)
    post_freeze = load(POST_FREEZE)
    contract = load(CONTRACT)
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", freeze["source_commit"], head],
        cwd=ROOT,
        check=False,
    )
    require(ancestor.returncode == 0, "frozen source commit is not reachable")
    production_diff = subprocess.run(
        ["git", "diff", "--quiet", freeze["source_commit"], "--", "crates"],
        cwd=ROOT,
        check=False,
    )
    require(production_diff.returncode == 0, "production sources differ from freeze")
    for name, digest in freeze["frozen_sources"].items():
        if name in first_post_freeze["superseded_source_hashes"]:
            require(
                digest == first_post_freeze["superseded_source_hashes"][name],
                f"superseded source history mismatch: {name}",
            )
            continue
        require(sha256(PACKAGE / name) == digest, f"frozen source changed: {name}")
    require(
        sha256(FREEZE) == first_post_freeze["prior_freeze"]["sha256"],
        "first post-analysis prior-freeze hash mismatch",
    )
    for name, digest in first_post_freeze["current_sources"].items():
        if name in post_freeze["superseded_source_hashes"]:
            require(
                digest == post_freeze["superseded_source_hashes"][name],
                f"second superseded source history mismatch: {name}",
            )
            continue
        require(
            sha256(PACKAGE / name) == digest,
            f"first post-analysis source changed: {name}",
        )
    require(
        sha256(FIRST_POST_FREEZE) == post_freeze["prior_post_freeze"]["sha256"],
        "second post-analysis prior-freeze hash mismatch",
    )
    for name, digest in post_freeze["current_sources"].items():
        require(
            sha256(PACKAGE / name) == digest,
            f"post-analysis source changed: {name}",
        )
    for name, digest in post_freeze["outputs"].items():
        require(
            sha256(PACKAGE / name) == digest,
            f"post-analysis output changed: {name}",
        )
    for name, record in freeze["parent_inputs"].items():
        require(
            sha256(ROOT / record["path"]) == record["sha256"],
            f"parent input changed: {name}",
        )
    require(
        contract["source_commit"] == freeze["source_commit"],
        "contract/freeze source commit mismatch",
    )
    return freeze, contract


def verify_analysis(contract: dict[str, Any]) -> None:
    analysis = load(ANALYSIS)
    decision = load(DECISION)
    require(
        analysis["analysis_id"] == contract["analysis_id"],
        "analysis identifier mismatch",
    )
    require(
        analysis["contract_sha256"] == sha256(CONTRACT),
        "analysis contract hash mismatch",
    )
    execution = analysis["execution"]
    require(
        execution["generated_100_year_streams"]
        == contract["minimum_records"]["generated_100_year_streams"],
        "generated stream count mismatch",
    )
    require(
        execution["generated_nested_horizon_records"]
        == contract["minimum_records"]["generated_nested_horizon_records"],
        "nested horizon count mismatch",
    )
    require(
        execution["retained_quality_reports_used"]
        == contract["minimum_records"]["retained_quality_reports"],
        "retained report count mismatch",
    )
    generated = analysis["generated"]
    generated_keys = {
        (
            row["station"],
            row["horizon_years"],
            row["qc_filter"],
            row["burn"],
        )
        for row in generated
    }
    require(len(generated_keys) == len(generated) == 544, "generated keys incomplete")
    observed = analysis["observed"]
    require(
        sum(row["source"] == "daymet" for row in observed) == 17,
        "Daymet station count mismatch",
    )
    require(
        sum(row["source"] == "ghcn" for row in observed) == 8,
        "GHCN station count mismatch",
    )
    require(len(analysis["comparisons"]) == 700, "comparison matrix count mismatch")
    require(len(analysis["comparison_summaries"]) == 56, "summary count mismatch")
    for row in analysis["comparisons"]:
        if row["available"]:
            require(
                row["null_common_components_min"] == row["common_components"]
                and row["null_common_components_max"] == row["common_components"],
                "available comparison uses inconsistent component support",
            )
        observed = row["observed_distance"]
        ceiling = row["null_ceiling"]
        severity = row["severity_ratio"]
        if not row["available"]:
            require(severity is None, "unavailable comparison has severity")
        elif ceiling == 0.0 and observed == 0.0:
            require(severity == 0.0, "zero-over-zero severity policy mismatch")
        elif ceiling == 0.0:
            require(severity == "infinity", "zero-ceiling severity policy mismatch")
        else:
            require(
                severity == observed / ceiling,
                "finite comparison severity arithmetic mismatch",
            )
    require(len(decision["ranking"]) == 5, "ranking count mismatch")
    for row in decision["ranking"]:
        pooled = [
            item["severity_ratio"]
            for item in analysis["comparisons"]
            if item["family"] == row["family"]
            and item["source"] == "daymet"
            and item["qc_filter"] == "off"
            and item["available"]
        ]
        require(
            row["daymet_off_median_severity_ratio"] == severity_median(pooled),
            f"pooled severity mismatch: {row['family']}",
        )
    ranks = [row["rank"] for row in decision["ranking"]]
    require(ranks == [1, 2, 3, 4, 5], "ranking positions malformed")
    qualifying = [row["family"] for row in decision["ranking"] if row["qualifying"]]
    require(
        qualifying == decision["qualifying_families"],
        "qualifying family list mismatch",
    )
    expected_terminal = (
        contract["decision"]["gap_terminal"]
        if qualifying
        else contract["decision"]["no_gap_terminal"]
    )
    require(decision["terminal_decision"] == expected_terminal, "terminal rule mismatch")
    require(
        f"`{expected_terminal}`" in FINDINGS.read_text(encoding="utf-8"),
        "findings terminal mismatch",
    )


def reproduce() -> None:
    with tempfile.TemporaryDirectory(prefix="a7a-reproduce-") as temporary:
        root = Path(temporary)
        output = root / "output"
        target = root / "target"
        subprocess.run(
            [
                "python3",
                str(ANALYZER),
                "--output-dir",
                str(output),
                "--target-dir",
                str(target),
            ],
            cwd=ROOT,
            check=True,
        )
        for name in ("a7a-analysis-v1.json", "a7a-decision-v1.json", "findings.md"):
            require(
                (output / name).read_bytes() == (PACKAGE / name).read_bytes(),
                f"reproduction differs: {name}",
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-reproduce", action="store_true")
    args = parser.parse_args()
    _, contract = verify_frozen()
    verify_analysis(contract)
    if not args.no_reproduce:
        reproduce()
    target = ROOT / "target" / "a7a-daily-precipitation-structure"
    if target.exists():
        shutil.rmtree(target)
    print("A7a freeze, matrix, arithmetic, and reproduction: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
