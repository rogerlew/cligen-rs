#!/usr/bin/env python3
"""Decompose the 153 eligible A5d1 paths into count and order gates."""

from __future__ import annotations

import collections
import sys
import time

from a5d1b_common import (
    A5D1_CONTRACT,
    A5D1_PATH_RESULTS,
    CONTRACT,
    DIAGNOSTIC_RESULTS,
    ROOT,
    count_only_replay,
    feature_path,
    freeze_identity,
    load_json,
    sha256,
    write_json,
    a5d1_modules,
)


def main() -> None:
    if len(sys.argv) != 1:
        raise SystemExit("usage: diagnose-inherited-paths.py")
    freeze_sha256 = freeze_identity()
    contract = load_json(CONTRACT)
    a5d1_contract = load_json(A5D1_CONTRACT)
    published = load_json(A5D1_PATH_RESULTS)
    if not all(isinstance(value, dict) for value in (contract, a5d1_contract, published)):
        raise ValueError("invalid diagnostic inputs")
    if sha256(A5D1_PATH_RESULTS) != contract["inherited"]["a5d1_path_results_sha256"]:
        raise ValueError("A5d1 path aggregate identity mismatch")
    solver, _ = a5d1_modules()
    feature_cache = {}
    problem_cache = {}
    records = []
    started = time.monotonic()
    for row in published["records"]:
        if row["pool_size"] != 256:
            continue
        station_id = row["station_id"]
        if station_id not in feature_cache:
            feature = load_json(feature_path(station_id))
            feature_cache[station_id] = feature
            problem_cache[station_id] = solver.build_problem(
                feature["blocks"][:256], feature["targets"], a5d1_contract
            )
        feature = feature_cache[station_id]
        problem = problem_cache[station_id]
        path_file = ROOT / row["path_record"]["path"]
        if sha256(path_file) != row["path_record"]["sha256"]:
            raise ValueError(f"A5d1 path file identity mismatch: {row['cell_id']}")
        path = load_json(path_file)
        indices = path["source_year_indices_zero_based"]
        horizons = {}
        for horizon in (30, 100):
            counts = [0] * 256
            for index in indices[:horizon]:
                counts[index] += 1
            replay = count_only_replay(
                problem, feature["blocks"][:256], counts, horizon, a5d1_contract
            )
            stored = path["finite_prefix_marginal"][str(horizon)]
            if abs(replay["preservation_maximum_residual"] - stored["preservation_maximum_residual"]) > 1.0e-10:
                raise ValueError(f"A5d1 preservation replay mismatch: {row['cell_id']}:{horizon}")
            horizons[str(horizon)] = {
                "count_only": replay,
                "january_transition_pass": stored["january_transition"]["pass"],
                "full_finite_prefix_pass": stored["pass"],
                "support_count": sum(value > 0 for value in counts),
                "maximum_reuse": max(counts),
            }
        count_pass = all(horizons[str(horizon)]["count_only"]["pass"] for horizon in (30, 100))
        records.append(
            {
                "cell_id": row["cell_id"],
                "station_id": station_id,
                "algorithm": row["algorithm"],
                "path_seed": row["path_seed"],
                "horizons": horizons,
                "count_only_both_horizons_pass": count_pass,
                "boundary_pass": path["boundary"]["pass"],
                "dependence_noninferiority": path["dependence"]["noninferiority"],
                "dependence_strict_improvement": path["dependence"]["strict_improvement"],
                "path_pass": path["path_pass"],
                "published_first_failed_criterion": row["first_failed_criterion"],
            }
        )
    if len(records) != contract["diagnostic"]["eligible_a5d1_cells"]:
        raise ValueError("eligible diagnostic matrix does not close")
    horizon_summary = {}
    for horizon in (30, 100):
        values = [row["horizons"][str(horizon)] for row in records]
        horizon_summary[str(horizon)] = {
            "cells": len(values),
            "base_preservation_pass": sum(v["count_only"]["preservation_pass"] for v in values),
            "centered_noninferiority_pass": sum(v["count_only"]["noninferiority"] for v in values),
            "centered_strict_improvement_pass": sum(v["count_only"]["strict_improvement"] for v in values),
            "count_only_pass": sum(v["count_only"]["pass"] for v in values),
            "january_transition_pass": sum(v["january_transition_pass"] for v in values),
            "full_finite_prefix_pass": sum(v["full_finite_prefix_pass"] for v in values),
        }
    value = {
        "inherited_path_diagnostics_schema_version": 1,
        "development_only": True,
        "freeze_sha256": freeze_sha256,
        "a5d1_path_results_sha256": sha256(A5D1_PATH_RESULTS),
        "expected_cells": 153,
        "actual_cells": len(records),
        "unique_cells": len({row["cell_id"] for row in records}),
        "published_first_failure_counts": dict(sorted(collections.Counter(row["published_first_failed_criterion"] for row in records).items())),
        "count_only_both_horizons_pass": sum(row["count_only_both_horizons_pass"] for row in records),
        "horizon_summary": horizon_summary,
        "records": records,
        "wall_seconds": round(time.monotonic() - started, 6),
    }
    write_json(DIAGNOSTIC_RESULTS, value)
    print(
        "A5d1b inherited diagnostics: PASS "
        f"({value['actual_cells']} cells; count-only both={value['count_only_both_horizons_pass']})"
    )


if __name__ == "__main__":
    main()

