#!/usr/bin/env python3
"""Reproduce one accepted export and summarize complete neural streams."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import torch

import legacy_core as legacy
import screen_core_v2 as core
from temporal_metrics import realized_metrics


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def dates(years: int) -> list[dt.date]:
    start = dt.date(2001, 1, 1)
    return [start + dt.timedelta(days=index) for index in range(legacy.days_for_years(years))]


def stream(
    module: Any,
    hidden_size: int,
    point_id: str,
    latitude: float,
    longitude: float,
    elevation_m: float,
    years: int,
    burn: int,
    member: int,
) -> tuple[np.ndarray, str]:
    days = legacy.days_for_years(years)
    words = legacy.philox_words(point_id, burn, member, days)
    uniforms = (words.astype(np.float64) + 0.5) / 4294967296.0
    features = torch.from_numpy(legacy.generation_features(years, latitude, longitude, elevation_m)).unsqueeze(0)
    station = torch.tensor([1200])
    hidden = torch.zeros((1, 1, hidden_size))
    chunks = []
    with torch.inference_mode():
        for start in range(0, days, 365):
            heads, hidden = module(features[:, start : start + 365], station, hidden)
            chunks.append(heads.squeeze(0))
    heads_t = torch.cat(chunks).double()
    probability = torch.sigmoid(heads_t[:, 0]).numpy()
    wet = uniforms[:, 0] < probability
    parameters, continuous_start = core.amount_parameters(heads_t, "lognormal_wet_v2")
    amount = core.amount_quantile(parameters, "lognormal_wet_v2", torch.from_numpy(uniforms[:, 1])).numpy()
    heads = heads_t.numpy()
    locations = heads[:, continuous_start::2]
    scales = np.log1p(np.exp(heads[:, continuous_start + 1 :: 2])) + 1e-4
    normals = np.sqrt(-2.0 * np.log(uniforms[:, [1]])) * np.cos(
        2.0 * np.pi * (uniforms[:, [2]] + np.arange(6) / 7.0)
    )
    values = locations + scales * normals
    tmean, dtr = values[:, 0], np.exp(values[:, 1])
    output = np.column_stack(
        (
            wet * amount,
            tmean + dtr / 2,
            tmean - dtr / 2,
            np.exp(values[:, 2]),
            np.exp(values[:, 3]),
            np.exp(values[:, 4]),
            86400.0 / (1.0 + np.exp(-values[:, 5])),
            uniforms[:, 3],
        )
    ).astype("<f4")
    payload = output.tobytes()
    return output, hashlib.sha256(payload).hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    partial = path.with_suffix(path.suffix + ".part")
    with partial.open("w", encoding="utf-8") as stream_handle:
        json.dump(value, stream_handle, indent=2, sort_keys=True)
        stream_handle.write("\n")
    partial.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--row-id", required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--sites", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    contract = json.loads(options.contract.read_text(encoding="utf-8"))
    sites = json.loads(options.sites.read_text(encoding="utf-8"))["sites"]
    model = next((value for value in contract["models"] if value["row_id"] == options.row_id), None)
    if model is None:
        raise RuntimeError("row is not registered")
    export = options.output / "model-export.pt"
    export_sha = digest(export)
    if export.stat().st_size != model["export_bytes"] or export_sha != model["export_sha256"]:
        raise RuntimeError("accepted TorchScript export did not reproduce exactly")
    module = torch.jit.load(str(export), map_location="cpu").eval()
    generation = contract["generation"]
    date_axis = dates(generation["horizon_years"])
    records = []
    for site in sites:
        for member in generation["member_ids"]:
            values, payload_sha = stream(
                module,
                int(model["hidden_size"]),
                site["point_id"],
                float(site["latitude"]),
                float(site["longitude"]),
                float(site["elevation_m"]),
                int(generation["horizon_years"]),
                int(generation["neural_burn_id"]),
                int(member),
            )
            support = bool(
                np.isfinite(values).all()
                and np.all(values[:, 0] >= 0.0)
                and np.all(values[:, 1] >= values[:, 2])
                and np.all(values[:, 3:7] >= 0.0)
                and np.all(values[:, 6] <= 86400.0)
            )
            if not support:
                raise RuntimeError("generated stream support failure")
            records.append(
                {
                    "burn_id": generation["neural_burn_id"],
                    "member_id": member,
                    "metrics": realized_metrics(date_axis, values[:, 0], values[:, 1], values[:, 2]),
                    "point_id": site["point_id"],
                    "regime": site["regime"],
                    "row_count": len(values),
                    "stream_sha256": payload_sha,
                    "support": support,
                }
            )
    expected = len(sites) * len(generation["member_ids"])
    result = {
        "schema_version": 1,
        "capacity_id": model["capacity_id"],
        "export_sha256": export_sha,
        "row_id": options.row_id,
        "streams": records,
        "training_seed": model["training_seed"],
    }
    atomic_json(options.output / "streams.json", result)
    atomic_json(
        options.output / "evidence.json.part",
        {
            "classification": "a10m5r4r2-development-only-realized-temporal-streams",
            "gates": {
                "accepted_export_exact": True,
                "all_streams_support": all(record["support"] for record in records),
                "confirmation_sealed": True,
                "development_selection_sealed": True,
                "expected_stream_count": len(records) == expected,
                "finite_metrics": all(math.isfinite(value) for record in records for value in record["metrics"].values()),
            },
            "row_id": options.row_id,
            "stream_count": len(records),
        },
    )


if __name__ == "__main__":
    main()
