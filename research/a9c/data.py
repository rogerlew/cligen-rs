"""Freeze-bound A9c observed-data acquisition and normalization.

This module is research tooling. It never opens an A9 confirmation object.
Raw USCRN station-year bytes are hashed, parsed, summarized, and discarded;
the access ledger and normalized logical objects are retained.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import os
import tempfile
import urllib.request
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


REPO = Path(__file__).resolve().parents[2]
PACKAGE = REPO / "docs/work-packages/20260715-a9c-observed-development"
ARTIFACTS = PACKAGE / "artifacts"
LARGE = ARTIFACTS / "large/observed"
FREEZE = ARTIFACTS / "data-role-freeze-v1.json"
CONFIRMATION = REPO / (
    "docs/work-packages/20260715-a9a-successor-family-foundation/"
    "artifacts/confirmation-metadata-selection-v1.json"
)
A8A_SOURCES = REPO / (
    "docs/work-packages/20260715-a8a-dry-regime-applicability/"
    "artifacts/source-manifest-v1.json"
)
ACCESS_LOG = ARTIFACTS / "observed-access-log-v1.ndjson"
SOURCE_MANIFEST = ARTIFACTS / "observed-source-manifest-v1.json"


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(path)
    path.write_bytes(canonical_bytes(value))


def deterministic_gzip(path: Path, value: Any) -> dict[str, Any]:
    logical = canonical_bytes(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(path)
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=9) as stream:
            stream.write(logical)
    return {
        "path": str(path.relative_to(REPO)),
        "bytes": path.stat().st_size,
        "object_sha256": sha256_path(path),
        "logical_bytes": len(logical),
        "logical_sha256": sha256_bytes(logical),
    }


def append_access(record: dict[str, Any]) -> None:
    ACCESS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with ACCESS_LOG.open("ab", buffering=0) as stream:
        stream.write(canonical_bytes(record))
        os.fsync(stream.fileno())


def daymet_date(year: int, yday: int) -> date:
    if not 1 <= yday <= 365:
        raise ValueError(f"Daymet yday outside 1..365: {year}/{yday}")
    return date(year, 1, 1) + timedelta(days=yday - 1)


def parse_period(value: str) -> tuple[date, date]:
    first, last = value.split("/")
    return date.fromisoformat(first), date.fromisoformat(last)


def normalize_daymet(freeze: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    source_manifest = read_json(A8A_SOURCES)
    indexed = {row["station_id"]: row for row in source_manifest["stations"]}
    role_periods = {
        "coefficient_fit": parse_period(freeze["daymet"]["fit_period"]),
        "development": parse_period(freeze["daymet"]["development_period"]),
    }
    outputs: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    for selected in freeze["daymet"]["stations"]:
        station_id = selected["station_id"]
        upstream = indexed[station_id]["sources"]["daymet"]
        source_path = REPO / upstream["archive_path"]
        actual_archive_hash = sha256_path(source_path)
        if actual_archive_hash != upstream["archive_sha256"]:
            raise ValueError(f"Daymet archive hash mismatch: {station_id}")
        role_rows: dict[str, list[dict[str, Any]]] = {role: [] for role in role_periods}
        with gzip.open(source_path, "rt", encoding="utf-8", newline="") as stream:
            for _ in range(6):
                next(stream)
            reader = csv.DictReader(stream)
            for row in reader:
                civil = daymet_date(int(row["year"]), int(row["yday"]))
                normalized = {
                    "date": civil.isoformat(),
                    "prcp_mm": float(row["prcp (mm/day)"]),
                    "tmax_c": float(row["tmax (deg c)"]),
                    "tmin_c": float(row["tmin (deg c)"]),
                }
                for role, (first, last) in role_periods.items():
                    if first <= civil <= last:
                        role_rows[role].append(normalized)
        for role, rows in role_rows.items():
            first, last = role_periods[role]
            expected = sum(365 for _ in range(first.year, last.year + 1))
            if len(rows) != expected:
                raise ValueError(f"Daymet incomplete {station_id}/{role}: {len(rows)} != {expected}")
            payload = {
                "calendar": "daymet_official_365_v1",
                "cold_arid_cross_tag": selected["cold_arid_cross_tag"],
                "product": freeze["daymet"]["product"],
                "records": rows,
                "role": role,
                "schema_version": 1,
                "station_id": station_id,
                "stratum": selected["primary_stratum"],
            }
            output_path = LARGE / "daymet" / role / f"{station_id}.json.gz"
            identity = deterministic_gzip(output_path, payload)
            identity.update(
                {
                    "calendar": "daymet_official_365_v1",
                    "day_boundary": "civil_daymet",
                    "period_end": last.isoformat(),
                    "period_start": first.isoformat(),
                    "product_version": "V4 R1 / 4.1",
                    "record_count": len(rows),
                    "role": role,
                    "source_id": "daymet",
                    "station_id": station_id,
                    "stratum": selected["primary_stratum"],
                    "variables": ["prcp", "tmax", "tmin"],
                }
            )
            outputs.append(identity)
        sources.append(
            {
                "archive_bytes": source_path.stat().st_size,
                "archive_path": upstream["archive_path"],
                "archive_sha256": actual_archive_hash,
                "source_sha256": upstream["source_sha256"],
                "station_id": station_id,
                "upstream_url": upstream["upstream_url"],
            }
        )
    return outputs, sources


@dataclass
class EventState:
    zero_run: int = 0
    active: bool = False
    invalid: bool = False
    first_end: datetime | None = None
    last_positive_end: datetime | None = None
    positive: list[tuple[datetime, float, float | None, float | None, float | None, float | None]] = field(default_factory=list)


def valid_value(raw: str) -> float | None:
    value = float(raw)
    return None if value <= -99.0 else value


def interval_end(lst_date: str, lst_time: str) -> datetime:
    day = datetime.strptime(lst_date, "%Y%m%d").date()
    hour = int(lst_time) // 100
    minute = int(lst_time) % 100
    return datetime.combine(day, time(hour=hour, minute=minute))


def event_record(state: EventState, station_id: str, stratum: str) -> dict[str, Any] | None:
    if state.invalid or not state.positive or state.first_end is None or state.last_positive_end is None:
        return None
    first_lower = state.first_end - timedelta(minutes=5)
    duration = (state.last_positive_end - first_lower).total_seconds() / 60.0
    total = sum(row[1] for row in state.positive)
    peak = max(row[1] for row in state.positive)
    earliest_peak_end = next(row[0] for row in state.positive if row[1] == peak)
    peak_midpoint = earliest_peak_end - timedelta(minutes=2.5)
    time_to_peak = (peak_midpoint - first_lower).total_seconds() / 60.0 / duration
    interval_count = duration / 5.0
    peak_ratio = peak * interval_count / total

    def mean_at(index: int) -> float | None:
        values = [row[index] for row in state.positive if row[index] is not None]
        return sum(values) / len(values) if len(values) == len(state.positive) else None

    return {
        "air_temperature_c": mean_at(2),
        "depth_mm": total,
        "duration_min": duration,
        "peak_ratio": peak_ratio,
        "relative_humidity_pct": mean_at(4),
        "solar_radiation_w_m2": mean_at(3),
        "start_lst": first_lower.isoformat(timespec="minutes"),
        "station_id": station_id,
        "stratum": stratum,
        "time_to_peak_fraction": time_to_peak,
        "wind_speed_1_5m_m_s": mean_at(5),
    }


def advance_event(
    state: EventState,
    end: datetime,
    precip: float | None,
    context: tuple[float | None, float | None, float | None, float | None],
    station_id: str,
    stratum: str,
) -> dict[str, Any] | None:
    if precip is None:
        state.zero_run = 0
        if state.active:
            state.invalid = True
        return None
    if precip == 0.0:
        state.zero_run += 1
        if state.active and state.zero_run == 72:
            result = event_record(state, station_id, stratum)
            state.active = False
            state.invalid = False
            state.first_end = None
            state.last_positive_end = None
            state.positive.clear()
            return result
        return None
    if precip < 0.0:
        raise ValueError("negative valid precipitation")
    if not state.active:
        if state.zero_run < 72:
            state.zero_run = 0
            return None
        state.active = True
        state.invalid = False
        state.first_end = end
        state.positive.clear()
    state.zero_run = 0
    state.last_positive_end = end
    state.positive.append((end, precip, *context))
    return None


def source_url(root: str, year: int, source_name: str) -> str:
    return f"{root}/{year}/CRNS0101-05-{year}-{source_name}.txt"


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "cligen-rs-a9c/1"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def parse_uscrn_role(
    freeze: dict[str, Any], station: dict[str, Any], role: str, first_year: int, last_year: int
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    station_id = station["station_id"]
    stratum = station["primary_stratum"]
    state = EventState()
    events: list[dict[str, Any]] = []
    daily: dict[date, dict[str, list[float | None]]] = defaultdict(
        lambda: {name: [] for name in ("precip", "temp", "solar", "rh", "wetness", "wind")}
    )
    source_records: list[dict[str, Any]] = []
    previous_end: datetime | None = None
    for year in range(first_year, last_year + 1):
        url = source_url(freeze["uscrn"]["source_root"], year, station["source_name"])
        raw = download(url)
        access = {
            "accessed_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "bytes": len(raw),
            "object_sha256": sha256_bytes(raw),
            "role": role,
            "source_id": "uscrn_subhourly01",
            "station_id": station_id,
            "url": url,
            "year": year,
        }
        append_access(access)
        line_count = 0
        first_utc = last_utc = None
        for binary_line in io.BytesIO(raw):
            fields = binary_line.decode("ascii").split()
            if len(fields) != 23:
                raise ValueError(f"USCRN field count {station_id}/{year}: {len(fields)}")
            line_count += 1
            first_utc = first_utc or f"{fields[1]}T{fields[2]}"
            last_utc = f"{fields[1]}T{fields[2]}"
            end = interval_end(fields[3], fields[4])
            if previous_end is not None and end != previous_end + timedelta(minutes=5):
                advance_event(state, end, None, (None, None, None, None), station_id, stratum)
            previous_end = end
            precip = valid_value(fields[9])
            temp = valid_value(fields[8])
            solar = valid_value(fields[10]) if fields[11] == "0" else None
            rh = valid_value(fields[15]) if fields[16] == "0" else None
            wetness = valid_value(fields[19]) if fields[20] == "0" else None
            wind = valid_value(fields[21]) if fields[22] == "0" else None
            completed = advance_event(state, end, precip, (temp, solar, rh, wind), station_id, stratum)
            if completed is not None:
                events.append(completed)
            interval_day = (end - timedelta(microseconds=1)).date()
            values = daily[interval_day]
            for name, value in (
                ("precip", precip),
                ("temp", temp),
                ("solar", solar),
                ("rh", rh),
                ("wetness", wetness),
                ("wind", wind),
            ):
                values[name].append(value)
        source_records.append({**access, "line_count": line_count, "first_utc": first_utc, "last_utc": last_utc})
    normalized_daily: list[dict[str, Any]] = []
    period_first = date(first_year, 1, 1)
    period_last = date(last_year, 12, 31)
    for day in sorted(daily):
        if not period_first <= day <= period_last:
            continue
        values = daily[day]

        def complete(name: str, reducer: str = "mean") -> float | None:
            rows = values[name]
            if len(rows) != 288 or any(value is None for value in rows):
                return None
            present = [float(value) for value in rows if value is not None]
            if reducer == "sum":
                return sum(present)
            if reducer == "min":
                return min(present)
            if reducer == "max":
                return max(present)
            return sum(present) / len(present)

        normalized_daily.append(
            {
                "air_temperature_max_c": complete("temp", "max"),
                "air_temperature_mean_c": complete("temp"),
                "air_temperature_min_c": complete("temp", "min"),
                "date": day.isoformat(),
                "precip_mm": complete("precip", "sum"),
                "relative_humidity_pct": complete("rh"),
                "solar_radiation_w_m2": complete("solar"),
                "wetness_ohm": complete("wetness"),
                "wind_speed_1_5m_m_s": complete("wind"),
            }
        )
    payload = {
        "daily_records": normalized_daily,
        "event_definition": freeze["event_definition"],
        "events": events,
        "product": freeze["uscrn"]["product"],
        "role": role,
        "schema_version": 1,
        "station_id": station_id,
        "stratum": stratum,
    }
    return payload, source_records


def normalize_uscrn(freeze: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    periods = {
        "coefficient_fit": parse_period(freeze["uscrn"]["fit_period"]),
        "development": parse_period(freeze["uscrn"]["development_period"]),
    }
    outputs: list[dict[str, Any]] = []
    source_records: list[dict[str, Any]] = []
    for station in freeze["uscrn"]["stations"]:
        for role, (first, last) in periods.items():
            payload, accessed = parse_uscrn_role(freeze, station, role, first.year, last.year)
            output_path = LARGE / "uscrn" / role / f"{station['station_id']}.json.gz"
            identity = deterministic_gzip(output_path, payload)
            identity.update(
                {
                    "calendar": "gregorian",
                    "daily_record_count": len(payload["daily_records"]),
                    "day_boundary": "local_standard_time",
                    "event_count": len(payload["events"]),
                    "period_end": last.isoformat(),
                    "period_start": first.isoformat(),
                    "product_version": "Subhourly01 format 01 / OAP 2.1.1 archive",
                    "role": role,
                    "source_id": "uscrn_subhourly01",
                    "station_id": station["station_id"],
                    "stratum": station["primary_stratum"],
                    "variables": freeze["uscrn"]["variables"],
                }
            )
            outputs.append(identity)
            source_records.extend(accessed)
    return outputs, source_records


def confirmation_guard(freeze: dict[str, Any]) -> None:
    confirmation = read_json(CONFIRMATION)
    locked = {row["station_id"] for row in confirmation["stations"]}
    selected = {row["station_id"] for row in freeze["uscrn"]["stations"]}
    overlap = sorted(locked & selected)
    if overlap:
        raise ValueError(f"confirmation station overlap: {overlap}")
    locked_tokens = {
        row["station_name"].lower().replace(" ", "_").replace(".", "")
        for row in confirmation["stations"]
    }
    selected_tokens = {row["source_name"].lower().replace(".", "") for row in freeze["uscrn"]["stations"]}
    if locked_tokens & selected_tokens:
        raise ValueError("confirmation source-name overlap")


def acquire() -> None:
    if SOURCE_MANIFEST.exists() or ACCESS_LOG.exists() or LARGE.exists():
        raise FileExistsError("A9c observed outputs already exist; use --verify")
    freeze = read_json(FREEZE)
    confirmation_guard(freeze)
    daymet_outputs, daymet_sources = normalize_daymet(freeze)
    uscrn_outputs, uscrn_sources = normalize_uscrn(freeze)
    documents = []
    for name, url in (
        ("stations.tsv", "https://www.ncei.noaa.gov/pub/data/uscrn/products/stations.tsv"),
        ("subhourly01-headers.txt", f"{freeze['uscrn']['source_root']}/headers.txt"),
        ("subhourly01-readme.txt", f"{freeze['uscrn']['source_root']}/readme.txt"),
    ):
        raw = download(url)
        path = ARTIFACTS / "source-documents" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            raise FileExistsError(path)
        path.write_bytes(raw)
        documents.append(
            {"bytes": len(raw), "path": str(path.relative_to(REPO)), "sha256": sha256_bytes(raw), "url": url}
        )
    manifest = {
        "confirmation_series_accessed": False,
        "data_role_freeze_sha256": sha256_path(FREEZE),
        "daymet_normalized_objects": daymet_outputs,
        "daymet_source_objects": daymet_sources,
        "documents": documents,
        "manifest_id": "a9c-observed-source-v1",
        "schema_version": 1,
        "uscrn_normalized_objects": uscrn_outputs,
        "uscrn_source_station_years": uscrn_sources,
    }
    write_json(SOURCE_MANIFEST, manifest)


def recover_manifest() -> None:
    """Recover only the final manifest after a post-normalization interruption."""

    if SOURCE_MANIFEST.exists():
        raise FileExistsError(SOURCE_MANIFEST)
    freeze = read_json(FREEZE)
    confirmation_guard(freeze)
    daymet_outputs = []
    uscrn_outputs = []
    period_lookup = {
        ("daymet", "coefficient_fit"): parse_period(freeze["daymet"]["fit_period"]),
        ("daymet", "development"): parse_period(freeze["daymet"]["development_period"]),
        ("uscrn", "coefficient_fit"): parse_period(freeze["uscrn"]["fit_period"]),
        ("uscrn", "development"): parse_period(freeze["uscrn"]["development_period"]),
    }
    for source_name, root, target in (
        ("daymet", LARGE / "daymet", daymet_outputs),
        ("uscrn", LARGE / "uscrn", uscrn_outputs),
    ):
        for path in sorted(root.glob("*/*.json.gz")):
            role = path.parent.name
            payload = load_normalized(path)
            with gzip.open(path, "rb") as stream:
                logical = stream.read()
            first, last = period_lookup[(source_name, role)]
            identity = {
                "bytes": path.stat().st_size,
                "calendar": "daymet_official_365_v1" if source_name == "daymet" else "gregorian",
                "day_boundary": "civil_daymet" if source_name == "daymet" else "local_standard_time",
                "logical_bytes": len(logical),
                "logical_sha256": sha256_bytes(logical),
                "object_sha256": sha256_path(path),
                "path": str(path.relative_to(REPO)),
                "period_end": last.isoformat(),
                "period_start": first.isoformat(),
                "product_version": "V4 R1 / 4.1" if source_name == "daymet" else "Subhourly01 format 01 / OAP 2.1.1 archive",
                "role": role,
                "source_id": "daymet" if source_name == "daymet" else "uscrn_subhourly01",
                "station_id": payload["station_id"],
                "stratum": payload["stratum"],
                "variables": freeze[source_name]["variables"],
            }
            if source_name == "daymet":
                identity["record_count"] = len(payload["records"])
            else:
                identity["daily_record_count"] = len(payload["daily_records"])
                identity["event_count"] = len(payload["events"])
            target.append(identity)
    if len(daymet_outputs) != 40 or len(uscrn_outputs) != 24:
        raise ValueError(f"recovery object count: {len(daymet_outputs)}/{len(uscrn_outputs)}")
    source_manifest = read_json(A8A_SOURCES)
    selected = {row["station_id"] for row in freeze["daymet"]["stations"]}
    daymet_sources = []
    for row in source_manifest["stations"]:
        if row["station_id"] not in selected:
            continue
        source = row["sources"]["daymet"]
        path = REPO / source["archive_path"]
        if sha256_path(path) != source["archive_sha256"]:
            raise ValueError(f"Daymet source changed: {row['station_id']}")
        daymet_sources.append(
            {
                "archive_bytes": path.stat().st_size,
                "archive_path": source["archive_path"],
                "archive_sha256": source["archive_sha256"],
                "source_sha256": source["source_sha256"],
                "station_id": row["station_id"],
                "upstream_url": source["upstream_url"],
            }
        )
    uscrn_sources = [json.loads(line) for line in ACCESS_LOG.read_text().splitlines()]
    if len(uscrn_sources) != 180:
        raise ValueError(f"recovery access count: {len(uscrn_sources)}")
    document_urls = {
        "stations.tsv": "https://www.ncei.noaa.gov/pub/data/uscrn/products/stations.tsv",
        "subhourly01-headers.txt": f"{freeze['uscrn']['source_root']}/headers.txt",
        "subhourly01-readme.txt": f"{freeze['uscrn']['source_root']}/readme.txt",
    }
    documents = []
    for name, url in document_urls.items():
        path = ARTIFACTS / "source-documents" / name
        documents.append(
            {"bytes": path.stat().st_size, "path": str(path.relative_to(REPO)), "sha256": sha256_path(path), "url": url}
        )
    write_json(
        SOURCE_MANIFEST,
        {
            "confirmation_series_accessed": False,
            "data_role_freeze_sha256": sha256_path(FREEZE),
            "daymet_normalized_objects": daymet_outputs,
            "daymet_source_objects": daymet_sources,
            "documents": documents,
            "infrastructure_recovery": "final-manifest-only recovery after boolean spelling defect; no source object reacquired",
            "manifest_id": "a9c-observed-source-v1",
            "schema_version": 1,
            "uscrn_normalized_objects": uscrn_outputs,
            "uscrn_source_station_years": uscrn_sources,
        },
    )


def load_normalized(path: Path) -> dict[str, Any]:
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)


def verify() -> None:
    freeze = read_json(FREEZE)
    confirmation_guard(freeze)
    manifest = read_json(SOURCE_MANIFEST)
    if manifest["data_role_freeze_sha256"] != sha256_path(FREEZE):
        raise ValueError("data-role freeze hash mismatch")
    if manifest["confirmation_series_accessed"] is not False:
        raise ValueError("confirmation access flag")
    for group in ("daymet_normalized_objects", "uscrn_normalized_objects"):
        for record in manifest[group]:
            path = REPO / record["path"]
            if sha256_path(path) != record["object_sha256"]:
                raise ValueError(f"normalized object hash mismatch: {path}")
            with gzip.open(path, "rb") as stream:
                logical = stream.read()
            if sha256_bytes(logical) != record["logical_sha256"]:
                raise ValueError(f"logical hash mismatch: {path}")
    for document in manifest["documents"]:
        if sha256_path(REPO / document["path"]) != document["sha256"]:
            raise ValueError(f"document hash mismatch: {document['path']}")
    access = [json.loads(line) for line in ACCESS_LOG.read_text().splitlines()]
    if len(access) != len(manifest["uscrn_source_station_years"]):
        raise ValueError("access/source count mismatch")
    access_keys = {(row["url"], row["object_sha256"]) for row in access}
    source_keys = {(row["url"], row["object_sha256"]) for row in manifest["uscrn_source_station_years"]}
    if access_keys != source_keys:
        raise ValueError("access/source identity mismatch")
    print(
        f"PASS: {len(manifest['daymet_normalized_objects'])} Daymet objects; "
        f"{len(manifest['uscrn_normalized_objects'])} USCRN objects; "
        f"{len(access)} station-years; zero confirmation access"
    )


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("acquire", "recover-manifest", "verify"))
    args = parser.parse_args(argv)
    if args.mode == "acquire":
        acquire()
    elif args.mode == "recover-manifest":
        recover_manifest()
    else:
        verify()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
