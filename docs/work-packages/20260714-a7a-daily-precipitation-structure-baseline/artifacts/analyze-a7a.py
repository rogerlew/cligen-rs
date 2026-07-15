#!/usr/bin/env python3
"""Execute the frozen A7a daily precipitation-structure baseline."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tarfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[4]
PACKAGE = Path(__file__).resolve().parent
CONTRACT_PATH = PACKAGE / "measurement-contract-v1.json"
DEFAULT_TARGET = ROOT / "target" / "a7a-daily-precipitation-structure"
DEFAULT_OUTPUT = PACKAGE
BINARY = ROOT / "target" / "release" / "cligen"
BUILD_COMMAND = [
    "cargo",
    "build",
    "--locked",
    "--offline",
    "--release",
    "--bin",
    "cligen",
]
HORIZONS = (30, 100)
SEASONS = {
    "DJF": (12, 1, 2),
    "MAM": (3, 4, 5),
    "JJA": (6, 7, 8),
    "SON": (9, 10, 11),
}
MONTH_NAMES = (
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec",
)
EPSILON = 1.0e-12


def reject_nonfinite(token: str) -> None:
    raise ValueError(f"non-finite JSON token: {token}")


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as stream:
        return json.load(
            stream,
            parse_constant=reject_nonfinite,
            object_pairs_hook=reject_duplicate_keys,
        )


def canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def write_json(path: Path, value: object) -> None:
    path.write_bytes(canonical_json_bytes(value))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def conventional_median(values: Iterable[float]) -> float | None:
    ordered = sorted(values)
    if not ordered:
        return None
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2.0


def nearest_rank(values: Iterable[float], probability: float) -> float | None:
    ordered = sorted(values)
    if not ordered:
        return None
    return ordered[max(0, math.ceil(probability * len(ordered)) - 1)]


def mean(values: list[float]) -> float | None:
    if not values:
        return None
    total = 0.0
    for value in values:
        total += value
    return total / len(values)


def sample_sd(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    center = mean(values)
    assert center is not None
    total = 0.0
    for value in values:
        total += (value - center) * (value - center)
    return math.sqrt(total / (len(values) - 1))


def pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    mx, my = mean(xs), mean(ys)
    assert mx is not None and my is not None
    sxy = sxx = syy = 0.0
    for x, y in zip(xs, ys):
        dx, dy = x - mx, y - my
        sxy += dx * dy
        sxx += dx * dx
        syy += dy * dy
    if sxx == 0.0 or syy == 0.0:
        return None
    return max(-1.0, min(1.0, sxy / math.sqrt(sxx * syy)))


def average_ranks(values: list[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: (item[1], item[0]))
    ranks = [0.0] * len(values)
    start = 0
    while start < len(indexed):
        end = start + 1
        while end < len(indexed) and indexed[end][1] == indexed[start][1]:
            end += 1
        rank = ((start + 1) + end) / 2.0
        for index, _ in indexed[start:end]:
            ranks[index] = rank
        start = end
    return ranks


def spearman(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    return pearson(average_ranks(xs), average_ranks(ys))


def is_leap(year: int, calendar: str) -> bool:
    return calendar == "proleptic_gregorian" and year % 4 == 0 and (
        year % 100 != 0 or year % 400 == 0
    )


def days_in_month(year: int, month: int, calendar: str) -> int:
    if month == 2:
        return 29 if is_leap(year, calendar) else 28
    return 30 if month in (4, 6, 9, 11) else 31


def next_date(calendar: str, date: tuple[int, int, int]) -> tuple[int, int, int]:
    year, month, day = date
    if day < days_in_month(year, month, calendar):
        return year, month, day + 1
    if month < 12:
        return year, month + 1, 1
    return year + 1, 1, 1


def season(month: int) -> str:
    return next(name for name, months in SEASONS.items() if month in months)


def contiguous(
    left: tuple[tuple[int, int, int], float],
    right: tuple[tuple[int, int, int], float],
    calendar: str,
) -> bool:
    return next_date(calendar, left[0]) == right[0]


def distribution(values: list[float]) -> dict[str, float | int | None]:
    return {
        "n": len(values),
        "mean": mean(values),
        "sd": sample_sd(values),
        "p50": nearest_rank(values, 0.50),
        "p90": nearest_rank(values, 0.90),
        "p95": nearest_rank(values, 0.95),
        "p99": nearest_rank(values, 0.99),
        "max": max(values) if values else None,
    }


def expected_date_count(year: int, month: int | None, calendar: str) -> int:
    if month is not None:
        return days_in_month(year, month, calendar)
    return 366 if is_leap(year, calendar) else 365


def metric_bundle(
    rows: list[tuple[tuple[int, int, int], float]],
    calendar: str,
    contract: dict[str, Any],
) -> tuple[dict[str, dict[str, float]], dict[str, Any]]:
    threshold = float(contract["comparison"]["wet_day_threshold_mm"])
    minimum_histories = int(
        contract["families"]["higher_order_occurrence"]["minimum_history_count"]
    )
    minimum_pairs = int(
        contract["families"]["wet_amount_dependence"]["minimum_pair_count"]
    )
    families: dict[str, dict[str, float]] = {
        name: {}
        for name in (
            "spell_structure",
            "higher_order_occurrence",
            "wet_amount_dependence",
            "wet_amount_upper_tail",
            "multiday_extremes",
            "monthly_dispersion",
            "annual_dispersion",
        )
    }

    spell_values: dict[tuple[str, str], list[float]] = defaultdict(list)
    run_length = 0
    run_state: bool | None = None
    run_season: str | None = None
    prior: tuple[tuple[int, int, int], float] | None = None

    def finish_spell() -> None:
        if run_length and run_state is not None and run_season is not None:
            spell_values[(run_season, "wet" if run_state else "dry")].append(
                float(run_length)
            )

    for row in rows:
        wet = row[1] >= threshold
        adjacent = prior is not None and contiguous(prior, row, calendar)
        if not adjacent or wet != run_state:
            finish_spell()
            run_length = 1
            run_state = wet
            run_season = season(row[0][1])
        else:
            run_length += 1
        prior = row
    finish_spell()
    for season_name in SEASONS:
        for state in ("wet", "dry"):
            summary = distribution(spell_values[(season_name, state)])
            for quantile in ("p50", "p90", "p95"):
                value = summary[quantile]
                if value is not None:
                    families["spell_structure"][
                        f"{season_name}.{state}.{quantile}"
                    ] = float(value)

    amount_by_season: dict[str, list[float]] = defaultdict(list)
    adjacent_x: dict[str, list[float]] = defaultdict(list)
    adjacent_y: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        if row[1] >= threshold:
            amount_by_season[season(row[0][1])].append(row[1])
    for left, right in zip(rows, rows[1:]):
        if (
            contiguous(left, right, calendar)
            and left[1] >= threshold
            and right[1] >= threshold
        ):
            key = season(right[0][1])
            adjacent_x[key].append(left[1])
            adjacent_y[key].append(right[1])
    for season_name in SEASONS:
        tail = distribution(amount_by_season[season_name])
        for quantile in ("p95", "p99"):
            value = tail[quantile]
            if value is not None and value > 0.0:
                families["wet_amount_upper_tail"][
                    f"{season_name}.{quantile}"
                ] = float(value)
        if len(adjacent_x[season_name]) >= minimum_pairs:
            p = pearson(adjacent_x[season_name], adjacent_y[season_name])
            s = spearman(adjacent_x[season_name], adjacent_y[season_name])
            if p is not None:
                families["wet_amount_dependence"][
                    f"{season_name}.pearson"
                ] = p
            if s is not None:
                families["wet_amount_dependence"][
                    f"{season_name}.spearman"
                ] = s

    first_counts: dict[tuple[str, str], list[int]] = defaultdict(
        lambda: [0, 0]
    )
    history_counts: dict[tuple[str, str], list[int]] = defaultdict(
        lambda: [0, 0]
    )
    for left, right in zip(rows, rows[1:]):
        if contiguous(left, right, calendar):
            endpoint_season = season(right[0][1])
            prior_state = "W" if left[1] >= threshold else "D"
            first_counts[(endpoint_season, prior_state)][0] += 1
            first_counts[(endpoint_season, prior_state)][1] += int(
                right[1] >= threshold
            )
    for first, second, third in zip(rows, rows[1:], rows[2:]):
        if contiguous(first, second, calendar) and contiguous(
            second, third, calendar
        ):
            endpoint_season = season(third[0][1])
            history = "".join(
                "W" if row[1] >= threshold else "D" for row in (first, second)
            )
            history_counts[(endpoint_season, history)][0] += 1
            history_counts[(endpoint_season, history)][1] += int(
                third[1] >= threshold
            )
    for season_name in SEASONS:
        for history in ("DD", "DW", "WD", "WW"):
            history_n, history_wet = history_counts[(season_name, history)]
            first_n, first_wet = first_counts[(season_name, history[-1])]
            if history_n >= minimum_histories and first_n:
                residual = history_wet / history_n - first_wet / first_n
                families["higher_order_occurrence"][
                    f"{season_name}.{history}"
                ] = residual

    years = sorted({date[0] for date, _ in rows})
    annual_counts: dict[int, int] = defaultdict(int)
    annual_sums: dict[int, float] = defaultdict(float)
    monthly_counts: dict[tuple[int, int], int] = defaultdict(int)
    monthly_sums: dict[tuple[int, int], float] = defaultdict(float)
    for date, amount in rows:
        year, month, _ = date
        annual_counts[year] += 1
        annual_sums[year] += amount
        monthly_counts[(year, month)] += 1
        monthly_sums[(year, month)] += amount
    complete_years = {
        year
        for year in years
        if annual_counts[year] == expected_date_count(year, None, calendar)
    }
    maxima: dict[int, dict[int, float]] = {window: {} for window in (1, 3, 5)}
    for window in (1, 3, 5):
        for end in range(window - 1, len(rows)):
            selected = rows[end + 1 - window : end + 1]
            if not all(
                contiguous(left, right, calendar)
                for left, right in zip(selected, selected[1:])
            ):
                continue
            end_year = selected[-1][0][0]
            total = sum(value for _, value in selected)
            maxima[window][end_year] = max(
                total, maxima[window].get(end_year, -1.0)
            )
    for window in (1, 3, 5):
        values = [maxima[window][year] for year in sorted(complete_years)]
        summary = distribution(values)
        for quantile in ("p50", "p90", "p95"):
            value = summary[quantile]
            if value is not None and value > 0.0:
                families["multiday_extremes"][
                    f"{window}day.{quantile}"
                ] = float(value)

    monthly_totals: dict[int, list[float]] = defaultdict(list)
    annual_totals = [annual_sums[year] for year in sorted(complete_years)]
    for year in years:
        for month in range(1, 13):
            key = (year, month)
            if monthly_counts[key] == expected_date_count(year, month, calendar):
                monthly_totals[month].append(monthly_sums[key])
    for month in range(1, 13):
        spread = sample_sd(monthly_totals[month])
        if spread is not None and spread > 0.0:
            families["monthly_dispersion"][MONTH_NAMES[month - 1]] = spread
    annual_spread = sample_sd(annual_totals)
    if annual_spread is not None and annual_spread > 0.0:
        families["annual_dispersion"]["annual"] = annual_spread

    wet_spells_all = [
        value
        for season_name in SEASONS
        for value in spell_values[(season_name, "wet")]
    ]
    dry_spells_all = [
        value
        for season_name in SEASONS
        for value in spell_values[(season_name, "dry")]
    ]
    wet_amounts_all = [value for _, value in rows if value >= threshold]
    all_adjacent_x = [
        value for season_name in SEASONS for value in adjacent_x[season_name]
    ]
    all_adjacent_y = [
        value for season_name in SEASONS for value in adjacent_y[season_name]
    ]
    crosscheck = {
        "wet_spell": distribution(wet_spells_all),
        "dry_spell": distribution(dry_spells_all),
        "wet_amount": distribution(wet_amounts_all),
        "adjacent_pearson": pearson(all_adjacent_x, all_adjacent_y),
        "adjacent_spearman": spearman(all_adjacent_x, all_adjacent_y),
        "maxima": {
            str(window): distribution(
                [maxima[window][year] for year in sorted(complete_years)]
            )
            for window in (1, 3, 5)
        },
        "monthly_sd": {
            MONTH_NAMES[month - 1]: sample_sd(monthly_totals[month])
            for month in range(1, 13)
        },
        "annual_sd": annual_spread,
    }
    return families, crosscheck


def parse_cli(path: Path) -> list[tuple[tuple[int, int, int], float]]:
    rows: list[tuple[tuple[int, int, int], float]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if len(fields) != 13:
            continue
        try:
            day, month, year = map(int, fields[:3])
            amount = float(fields[3])
        except ValueError:
            continue
        rows.append(((year, month, day), amount))
    if not rows:
        raise ValueError(f"no daily rows parsed: {path}")
    for left, right in zip(rows, rows[1:]):
        if not contiguous(left, right, "proleptic_gregorian"):
            raise ValueError(f"non-contiguous generated dates: {left[0]} -> {right[0]}")
    return rows


def daily_rows_sha256(rows: list[tuple[tuple[int, int, int], float]]) -> str:
    text = "".join(
        f"{year:04d}-{month:02d}-{day:02d},{format(amount, '.17g')}\n"
        for (year, month, day), amount in rows
    )
    return sha256_bytes(text.encode("ascii"))


def runspec_text(par: Path, cli: Path, burn: int, qc: str) -> str:
    return "\n".join(
        [
            "cligen_runspec: 1",
            "station:",
            f"  par: {json.dumps(str(par))}",
            "mode: continuous",
            "simulation:",
            "  begin_year: 1",
            "  years: 100",
            "  interpolation: none",
            "rng:",
            f"  burn: {burn}",
            "generation_profile: faithful_5_32_3",
            f"qc_filter: {qc}",
            "output:",
            f"  cli: {json.dumps(str(cli))}",
            "  overwrite: true",
            "  quality: false",
            "",
        ]
    )


def execute_stream(
    binary: Path,
    work: Path,
    station: str,
    par: Path,
    burn: int,
    qc: str,
    contract: dict[str, Any],
) -> list[dict[str, Any]]:
    stem = f"{station}-100yr-burn{burn}-qc-{qc}"
    cli = work / f"{stem}.cli"
    runspec = work / f"{stem}.yaml"
    provenance = work / f"{stem}.cli.provenance.json"
    runspec.write_text(runspec_text(par, cli, burn, qc), encoding="utf-8")
    result = subprocess.run(
        [str(binary), "run", str(runspec)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"{stem}: {result.stderr.strip()}")
    rows = parse_cli(cli)
    expected_100 = sum(
        expected_date_count(year, None, "proleptic_gregorian")
        for year in range(1, 101)
    )
    if len(rows) != expected_100:
        raise ValueError(f"{stem}: {len(rows)} rows != {expected_100}")
    records = []
    for horizon in HORIZONS:
        selected = [row for row in rows if row[0][0] <= horizon]
        expected = sum(
            expected_date_count(year, None, "proleptic_gregorian")
            for year in range(1, horizon + 1)
        )
        if len(selected) != expected:
            raise ValueError(f"{stem}/{horizon}: {len(selected)} rows != {expected}")
        metrics, crosscheck = metric_bundle(
            selected, "proleptic_gregorian", contract
        )
        records.append(
            {
                "burn": burn,
                "crosscheck": crosscheck,
                "daily_rows": len(selected),
                "daily_rows_sha256": daily_rows_sha256(selected),
                "horizon_years": horizon,
                "metrics": metrics,
                "qc_filter": qc,
                "station": station,
            }
        )
    for path in (cli, runspec, provenance):
        path.unlink(missing_ok=True)
    return records


def assert_close(actual: Any, expected: Any, label: str) -> None:
    if actual is None or expected is None:
        if actual != expected:
            raise ValueError(f"{label}: {actual!r} != {expected!r}")
        return
    if not math.isclose(float(actual), float(expected), rel_tol=1.0e-10, abs_tol=1.0e-10):
        raise ValueError(f"{label}: {actual!r} != {expected!r}")


def check_quality_crosscheck(crosscheck: dict[str, Any], report: dict[str, Any], label: str) -> int:
    structure = report["tails"]["precipitation_structure"]["r1mm"]
    checks = 0
    for ours, theirs, name in (
        (crosscheck["wet_spell"], structure["wet_spells_days"]["whole_run"], "wet_spell"),
        (crosscheck["dry_spell"], structure["dry_spells_days"]["whole_run"], "dry_spell"),
        (crosscheck["wet_amount"], structure["wet_day_amount_mm"], "wet_amount"),
    ):
        for field in ("p50", "p90", "p95", "p99", "max"):
            assert_close(ours[field], theirs[field], f"{label}.{name}.{field}")
            checks += 1
    for field in ("pearson", "spearman"):
        assert_close(
            crosscheck[f"adjacent_{field}"],
            structure["adjacent_wet_day_amount"][field],
            f"{label}.adjacent.{field}",
        )
        checks += 1
    for window in (1, 3, 5):
        theirs = structure[f"annual_max_{window}_day_mm"]
        ours = crosscheck["maxima"][str(window)]
        for field in ("p50", "p90", "p95", "p99", "max"):
            assert_close(ours[field], theirs[field], f"{label}.max{window}.{field}")
            checks += 1
    for month in MONTH_NAMES:
        assert_close(
            crosscheck["monthly_sd"][month],
            report["interannual"]["monthly"][month]["precip_total_mm"]["sd"],
            f"{label}.monthly_sd.{month}",
        )
        checks += 1
    assert_close(
        crosscheck["annual_sd"],
        report["interannual"]["annual"]["precip_total_mm"]["sd"],
        f"{label}.annual_sd",
    )
    return checks + 1


def check_observed_crosscheck(
    crosscheck: dict[str, Any], target: dict[str, Any], label: str
) -> int:
    structure = target["precipitation_structure"]
    checks = 0
    for ours, theirs, name in (
        (crosscheck["wet_spell"], structure["wet_spells_days"]["whole_run"], "wet_spell"),
        (crosscheck["dry_spell"], structure["dry_spells_days"]["whole_run"], "dry_spell"),
        (crosscheck["wet_amount"], structure["wet_day_amount_mm"], "wet_amount"),
    ):
        for field in ("p50", "p90", "p95", "p99", "max"):
            assert_close(ours[field], theirs[field], f"{label}.{name}.{field}")
            checks += 1
    for field in ("pearson", "spearman"):
        assert_close(
            crosscheck[f"adjacent_{field}"],
            structure["adjacent_wet_day_amount"][field],
            f"{label}.adjacent.{field}",
        )
        checks += 1
    for window in (1, 3, 5):
        theirs = structure[f"annual_max_{window}_day_mm"]
        ours = crosscheck["maxima"][str(window)]
        for field in ("p50", "p90", "p95", "p99", "max"):
            assert_close(ours[field], theirs[field], f"{label}.max{window}.{field}")
            checks += 1
    for month in MONTH_NAMES:
        assert_close(
            crosscheck["monthly_sd"][month],
            target["monthly"][month]["precip_total_mm"]["sd"],
            f"{label}.monthly_sd.{month}",
        )
        checks += 1
    assert_close(
        crosscheck["annual_sd"],
        target["annual"]["precip_total_mm"]["sd"],
        f"{label}.annual_sd",
    )
    return checks + 1


def verify_input_hashes(contract: dict[str, Any]) -> dict[str, str]:
    actual = {}
    for name, record in contract["inputs"].items():
        path = ROOT / record["path"]
        digest = sha256(path)
        if digest != record["sha256"]:
            raise ValueError(f"input hash mismatch: {name}: {path}")
        actual[name] = digest
    return actual


def load_observed(
    contract: dict[str, Any],
) -> tuple[list[dict[str, Any]], int]:
    corpus_dir = ROOT / (
        "docs/work-packages/20260712-a5a-quality-v3-observed-corpus/"
        "artifacts/corpus"
    )
    sys.path.insert(0, str(corpus_dir))
    try:
        from corpus_common import archive_records  # type: ignore
    finally:
        sys.path.pop(0)
    config = load_json(corpus_dir / "corpus-config-v1.json")
    source_manifest = load_json(corpus_dir / "source-manifest-v1.json")
    observed_targets = load_json(corpus_dir / "observed-target-corpus-v1.json")
    sources_by_station = {
        row["station_id"]: row["sources"] for row in source_manifest["stations"]
    }
    targets_by_station = {
        row["station_id"]: row for row in observed_targets["stations"]
    }
    results = []
    check_count = 0
    start, end = contract["comparison"]["observed_period"]
    for station in config["stations"]:
        station_id = station["station_id"]
        for source in ("daymet", "ghcn"):
            metadata = sources_by_station[station_id][source]
            if metadata["availability"] != "available":
                continue
            path = ROOT / metadata["archive_path"]
            records, checked = archive_records(path, source, station)
            for field in ("archive_sha256", "source_sha256", "calendar"):
                if checked[field] != metadata[field]:
                    raise ValueError(
                        f"{station_id}/{source}: source {field} mismatch"
                    )
            rows = [
                (date, values["prcp"])
                for date, values in sorted(records.items())
                if start <= date[0] <= end and "prcp" in values
            ]
            metrics, crosscheck = metric_bundle(
                rows, metadata["calendar"], contract
            )
            target = targets_by_station[station_id]["sources"][source]["periods"][
                "full"
            ]
            check_count += check_observed_crosscheck(
                crosscheck, target, f"{station_id}/{source}"
            )
            results.append(
                {
                    "calendar": metadata["calendar"],
                    "daily_rows": len(rows),
                    "daily_rows_sha256": daily_rows_sha256(rows),
                    "metrics": metrics,
                    "source": source,
                    "station": station_id,
                }
            )
    return results, check_count


def family_distance(
    left: dict[str, float],
    right: dict[str, float],
    family: str,
    contract: dict[str, Any],
    allowed_components: Iterable[str] | None = None,
) -> tuple[float | None, int, float | None]:
    common = set(left) & set(right)
    if allowed_components is not None:
        common &= set(allowed_components)
    differences = []
    signed = []
    use_absolute = family in contract["distance"]["absolute_families"]
    for component in sorted(common):
        a, b = left[component], right[component]
        if use_absolute:
            signed_difference = a - b
        else:
            if a <= 0.0 or b <= 0.0:
                continue
            signed_difference = math.log(a / b)
        signed.append(signed_difference)
        differences.append(abs(signed_difference))
    minimum = int(contract["families"][family]["minimum_common_components"])
    if len(differences) < minimum:
        return None, len(differences), None
    distance = conventional_median(differences)
    direction = conventional_median(signed)
    assert distance is not None
    return distance, len(differences), direction


def common_distance_components(
    left: dict[str, float],
    right: dict[str, float],
    family: str,
    contract: dict[str, Any],
) -> list[str]:
    use_absolute = family in contract["distance"]["absolute_families"]
    components = []
    for component in sorted(set(left) & set(right)):
        if use_absolute or (left[component] > 0.0 and right[component] > 0.0):
            components.append(component)
    return components


def encode_severity_ratio(
    observed_distance: float | None,
    null_ceiling: float | None,
    available: bool,
) -> float | str | None:
    if not available or observed_distance is None or null_ceiling is None:
        return None
    if null_ceiling > 0.0:
        return observed_distance / null_ceiling
    if observed_distance == 0.0:
        return 0.0
    return "infinity"


def severity_median(values: Iterable[float | str | None]) -> float | str | None:
    numeric = [
        math.inf if value == "infinity" else float(value)
        for value in values
        if value is not None
    ]
    result = conventional_median(numeric)
    if result is None:
        return None
    return "infinity" if math.isinf(result) else result


def severity_sort_value(value: float | str | None) -> float:
    if value == "infinity":
        return math.inf
    return -1.0 if value is None else float(value)


def component_center(vectors: list[dict[str, float]]) -> dict[str, float]:
    if not vectors:
        raise ValueError("cannot center empty vector set")
    common = set(vectors[0])
    for vector in vectors[1:]:
        common &= set(vector)
    center = {}
    for component in sorted(common):
        value = conventional_median(vector[component] for vector in vectors)
        assert value is not None
        center[component] = value
    return center


def build_comparisons(
    observed: list[dict[str, Any]],
    generated: list[dict[str, Any]],
    contract: dict[str, Any],
) -> list[dict[str, Any]]:
    generated_groups: dict[tuple[str, int, str], list[dict[str, Any]]] = defaultdict(list)
    for record in generated:
        generated_groups[
            (record["station"], record["horizon_years"], record["qc_filter"])
        ].append(record)
    observed_by_key = {(row["station"], row["source"]): row for row in observed}
    comparisons = []
    for (station, horizon, qc), records in sorted(generated_groups.items()):
        records.sort(key=lambda row: row["burn"])
        if len(records) != len(contract["comparison"]["burn_offsets"]):
            raise ValueError(f"incomplete generated group: {station}/{horizon}/{qc}")
        sources = ["daymet"]
        if (station, "ghcn") in observed_by_key:
            sources.append("ghcn")
        for source in sources:
            observed_record = observed_by_key[(station, source)]
            for family in contract["families"]:
                vectors = [record["metrics"][family] for record in records]
                center = component_center(vectors)
                observed_components = common_distance_components(
                    center, observed_record["metrics"][family], family, contract
                )
                observed_distance, component_count, direction = family_distance(
                    center,
                    observed_record["metrics"][family],
                    family,
                    contract,
                    observed_components,
                )
                null_distances = []
                null_component_counts = []
                for index, vector in enumerate(vectors):
                    leave_one_out = component_center(
                        vectors[:index] + vectors[index + 1 :]
                    )
                    null_distance, null_component_count, _ = family_distance(
                        vector,
                        leave_one_out,
                        family,
                        contract,
                        observed_components,
                    )
                    null_component_counts.append(null_component_count)
                    if null_distance is not None:
                        null_distances.append(null_distance)
                available = observed_distance is not None and len(null_distances) == len(vectors)
                null_ceiling = max(null_distances) if null_distances else None
                material = bool(
                    available
                    and null_ceiling is not None
                    and observed_distance is not None
                    and observed_distance > null_ceiling + EPSILON
                )
                severity_ratio = encode_severity_ratio(
                    observed_distance, null_ceiling, available
                )
                comparisons.append(
                    {
                        "available": available,
                        "common_components": component_count,
                        "direction": (
                            "over"
                            if available and direction is not None and direction > EPSILON
                            else "under"
                            if available and direction is not None and direction < -EPSILON
                            else "neutral_or_signed"
                            if available
                            else "unavailable"
                        ),
                        "family": family,
                        "horizon_years": horizon,
                        "material": material,
                        "null_ceiling": null_ceiling,
                        "null_common_components_max": max(null_component_counts),
                        "null_common_components_min": min(null_component_counts),
                        "observed_distance": observed_distance,
                        "qc_filter": qc,
                        "severity_ratio": severity_ratio,
                        "source": source,
                        "station": station,
                    }
                )
    return comparisons


def summarize_counts(
    comparisons: list[dict[str, Any]], contract: dict[str, Any]
) -> list[dict[str, Any]]:
    summaries = []
    for family in contract["families"]:
        for source in ("daymet", "ghcn"):
            expected = 17 if source == "daymet" else 8
            for horizon in HORIZONS:
                for qc in contract["comparison"]["qc_filters"]:
                    selected = [
                        row
                        for row in comparisons
                        if row["family"] == family
                        and row["source"] == source
                        and row["horizon_years"] == horizon
                        and row["qc_filter"] == qc
                    ]
                    if len(selected) != expected:
                        raise ValueError(
                            f"comparison count {family}/{source}/{horizon}/{qc}: "
                            f"{len(selected)} != {expected}"
                        )
                    severity_ratios = [
                        row["severity_ratio"]
                        for row in selected
                        if row["severity_ratio"] is not None
                    ]
                    summaries.append(
                        {
                            "expected_stations": expected,
                            "available_stations": sum(
                                bool(row["available"]) for row in selected
                            ),
                            "family": family,
                            "horizon_years": horizon,
                            "material_stations": sum(
                                bool(row["material"]) for row in selected
                            ),
                            "median_severity_ratio": severity_median(
                                severity_ratios
                            ),
                            "qc_filter": qc,
                            "source": source,
                        }
                    )
    return summaries


def build_ranking(
    summaries: list[dict[str, Any]],
    comparisons: list[dict[str, Any]],
    contract: dict[str, Any],
) -> list[dict[str, Any]]:
    index = {
        (row["family"], row["source"], row["horizon_years"], row["qc_filter"]): row
        for row in summaries
    }
    ranking = []
    for family in contract["decision"]["core_families"]:
        daymet_off = [
            index[(family, "daymet", horizon, "off")]["material_stations"]
            for horizon in HORIZONS
        ]
        faithful = [
            index[(family, "daymet", horizon, "faithful")]["material_stations"]
            for horizon in HORIZONS
        ]
        ghcn_off = [
            index[(family, "ghcn", horizon, "off")]["material_stations"]
            for horizon in HORIZONS
        ]
        severity = [
            row["severity_ratio"]
            for row in comparisons
            if row["family"] == family
            and row["source"] == "daymet"
            and row["qc_filter"] == "off"
            and row["horizon_years"] in HORIZONS
            and row["available"]
        ]
        qualifying = (
            min(daymet_off)
            >= contract["decision"][
                "daymet_off_min_material_stations_each_horizon"
            ]
            and min(faithful)
            >= contract["decision"][
                "faithful_min_material_stations_each_horizon"
            ]
            and min(ghcn_off)
            >= contract["decision"][
                "ghcn_off_min_material_stations_each_horizon"
            ]
        )
        ranking.append(
            {
                "daymet_off_counts_30_100": daymet_off,
                "daymet_off_min": min(daymet_off),
                "daymet_off_median_severity_ratio": severity_median(severity),
                "faithful_counts_30_100": faithful,
                "faithful_min": min(faithful),
                "family": family,
                "ghcn_off_counts_30_100": ghcn_off,
                "ghcn_off_min": min(ghcn_off),
                "qualifying": qualifying,
            }
        )
    ranking.sort(
        key=lambda row: (
            -row["daymet_off_min"],
            -row["faithful_min"],
            -row["ghcn_off_min"],
            -severity_sort_value(row["daymet_off_median_severity_ratio"]),
            row["family"],
        )
    )
    for position, row in enumerate(ranking, 1):
        row["rank"] = position
    return ranking


def build_qc_comparison(
    comparisons: list[dict[str, Any]], contract: dict[str, Any]
) -> list[dict[str, Any]]:
    index = {
        (
            row["station"],
            row["horizon_years"],
            row["family"],
            row["qc_filter"],
        ): row
        for row in comparisons
        if row["source"] == "daymet"
    }
    results = []
    stations = sorted({row["station"] for row in comparisons if row["source"] == "daymet"})
    for family in contract["decision"]["core_families"]:
        for horizon in HORIZONS:
            counts = {"off_better": 0, "equal": 0, "off_worse": 0, "unavailable": 0}
            for station in stations:
                faithful = index[(station, horizon, family, "faithful")][
                    "observed_distance"
                ]
                off = index[(station, horizon, family, "off")]["observed_distance"]
                if faithful is None or off is None:
                    counts["unavailable"] += 1
                elif off < faithful - EPSILON:
                    counts["off_better"] += 1
                elif off > faithful + EPSILON:
                    counts["off_worse"] += 1
                else:
                    counts["equal"] += 1
            results.append(
                {"family": family, "horizon_years": horizon, **counts}
            )
    return results


def build_propagation(
    comparisons: list[dict[str, Any]], contract: dict[str, Any]
) -> list[dict[str, Any]]:
    core = contract["decision"]["core_families"]
    index = {
        (
            row["station"],
            row["horizon_years"],
            row["qc_filter"],
            row["family"],
        ): row
        for row in comparisons
        if row["source"] == "daymet"
    }
    stations = sorted({key[0] for key in index})
    results = []
    for horizon in HORIZONS:
        for qc in contract["comparison"]["qc_filters"]:
            daily = []
            monthly = []
            annual = []
            joint_monthly = 0
            joint_annual = 0
            for station in stations:
                daily_distance = conventional_median(
                    index[(station, horizon, qc, family)]["observed_distance"]
                    for family in core
                    if index[(station, horizon, qc, family)]["observed_distance"]
                    is not None
                )
                assert daily_distance is not None
                monthly_row = index[(station, horizon, qc, "monthly_dispersion")]
                annual_row = index[(station, horizon, qc, "annual_dispersion")]
                daily.append(daily_distance)
                monthly.append(monthly_row["observed_distance"])
                annual.append(annual_row["observed_distance"])
                any_daily_material = any(
                    index[(station, horizon, qc, family)]["material"]
                    for family in core
                )
                joint_monthly += int(any_daily_material and monthly_row["material"])
                joint_annual += int(any_daily_material and annual_row["material"])
            results.append(
                {
                    "annual_distance_spearman": spearman(daily, annual),
                    "horizon_years": horizon,
                    "joint_daily_annual_material_stations": joint_annual,
                    "joint_daily_monthly_material_stations": joint_monthly,
                    "monthly_distance_spearman": spearman(daily, monthly),
                    "n_stations": len(stations),
                    "qc_filter": qc,
                }
            )
    return results


def findings_text(decision: dict[str, Any]) -> str:
    lines = [
        "# A7a Findings",
        "",
        f"Terminal decision: `{decision['terminal_decision']}`",
        "",
        "## Ranked core families",
        "",
        "| Rank | Family | Daymet off min | Faithful min | GHCN off min | Median severity | Qualifies |",
        "|---:|---|---:|---:|---:|---:|---|",
    ]
    for row in decision["ranking"]:
        severity = row["daymet_off_median_severity_ratio"]
        if severity == "infinity":
            severity_text = "infinity"
        elif severity is None:
            severity_text = "NA"
        else:
            severity_text = f"{severity:.3f}"
        lines.append(
            "| {rank} | `{family}` | {daymet_off_min}/17 | {faithful_min}/17 | "
            "{ghcn_off_min}/8 | {severity} | {qualifying_text} |".format(
                severity=severity_text,
                qualifying_text="yes" if row["qualifying"] else "no",
                **row,
            )
        )
    lines.extend(
        [
            "",
            "The trajectory-spread comparison is descriptive and uses deterministic burn offsets, not IID confidence intervals. Propagation diagnostics are associations and do not establish causation.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--target-dir", type=Path, default=DEFAULT_TARGET)
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    target = args.target_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if target.exists():
        shutil.rmtree(target)
    work = target / "work"
    station_dir = target / "station-parameters"
    work.mkdir(parents=True)
    station_dir.mkdir(parents=True)

    contract = load_json(CONTRACT_PATH)
    input_hashes = verify_input_hashes(contract)
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", contract["source_commit"], head],
        cwd=ROOT,
        check=False,
    )
    if ancestor.returncode != 0:
        raise ValueError(
            f"analysis source {contract['source_commit']} is not an ancestor of {head}"
        )
    production_diff = subprocess.run(
        ["git", "diff", "--quiet", contract["source_commit"], "--", "crates"],
        cwd=ROOT,
        check=False,
    )
    if production_diff.returncode != 0:
        raise ValueError("production sources differ from the frozen A7a source commit")
    subprocess.run(BUILD_COMMAND, cwd=ROOT, check=True)
    binary_sha = sha256(BINARY)

    baseline_archive = ROOT / contract["inputs"]["a5a_baseline_archive"]["path"]
    config = load_json(ROOT / contract["inputs"]["corpus_config"]["path"])
    with tarfile.open(baseline_archive, "r:gz") as archive:
        for station in config["stations"]:
            station_id = station["station_id"]
            member = archive.getmember(f"station-parameters/{station_id}.par")
            source = archive.extractfile(member)
            if source is None:
                raise ValueError(f"missing station parameter: {station_id}")
            path = station_dir / f"{station_id}.par"
            path.write_bytes(source.read())
            if sha256(path) != station["par_sha256"]:
                raise ValueError(f"station parameter hash mismatch: {station_id}")

    jobs = [
        (
            station["station_id"],
            station_dir / f"{station['station_id']}.par",
            burn,
            qc,
        )
        for station in config["stations"]
        for qc in contract["comparison"]["qc_filters"]
        for burn in contract["comparison"]["burn_offsets"]
    ]
    generated: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(
                execute_stream,
                BINARY,
                work,
                station,
                par,
                burn,
                qc,
                contract,
            )
            for station, par, burn, qc in jobs
        ]
        for future in concurrent.futures.as_completed(futures):
            generated.extend(future.result())
    generated.sort(
        key=lambda row: (
            row["station"],
            row["horizon_years"],
            row["qc_filter"],
            row["burn"],
        )
    )
    if len(jobs) != contract["minimum_records"]["generated_100_year_streams"]:
        raise ValueError("unexpected generated stream count")
    if len(generated) != contract["minimum_records"]["generated_nested_horizon_records"]:
        raise ValueError("unexpected nested horizon count")

    quality_checks = 0
    by_key = {
        (
            row["station"],
            row["horizon_years"],
            row["burn"],
            row["qc_filter"],
        ): row
        for row in generated
    }
    with tarfile.open(baseline_archive, "r:gz") as archive:
        for key, row in sorted(by_key.items()):
            station, horizon, burn, qc = key
            name = f"quality-reports/{station}-{horizon}yr-burn{burn}-qc-{qc}.cli.quality.json"
            stream = archive.extractfile(name)
            if stream is None:
                raise ValueError(f"missing retained report: {name}")
            report = json.loads(stream.read())
            quality_checks += check_quality_crosscheck(
                row["crosscheck"], report, name
            )

    observed, observed_checks = load_observed(contract)
    comparisons = build_comparisons(observed, generated, contract)
    summaries = summarize_counts(comparisons, contract)
    ranking = build_ranking(summaries, comparisons, contract)
    qc_comparison = build_qc_comparison(comparisons, contract)
    propagation = build_propagation(comparisons, contract)
    terminal = (
        contract["decision"]["gap_terminal"]
        if any(row["qualifying"] for row in ranking)
        else contract["decision"]["no_gap_terminal"]
    )
    decision = {
        "analysis_id": contract["analysis_id"],
        "decision_rule": contract["decision"],
        "qualifying_families": [
            row["family"] for row in ranking if row["qualifying"]
        ],
        "ranking": ranking,
        "schema_version": 1,
        "source_commit": contract["source_commit"],
        "terminal_decision": terminal,
    }
    analysis = {
        "analysis_id": contract["analysis_id"],
        "comparison_summaries": summaries,
        "comparisons": comparisons,
        "contract_sha256": sha256(CONTRACT_PATH),
        "execution": {
            "binary_sha256": binary_sha,
            "generated_100_year_streams": len(jobs),
            "generated_nested_horizon_records": len(generated),
            "observed_overlap_checks": observed_checks,
            "quality_report_overlap_checks": quality_checks,
            "retained_quality_reports_used": len(by_key),
        },
        "generated": generated,
        "input_hashes": input_hashes,
        "observed": observed,
        "propagation": propagation,
        "qc_comparison": qc_comparison,
        "schema_version": 1,
        "source_commit": contract["source_commit"],
    }
    write_json(output_dir / "a7a-analysis-v1.json", analysis)
    write_json(output_dir / "a7a-decision-v1.json", decision)
    (output_dir / "findings.md").write_text(
        findings_text(decision), encoding="utf-8"
    )
    shutil.rmtree(target)
    print(terminal)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
