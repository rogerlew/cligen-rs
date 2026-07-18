#!/usr/bin/env python3
"""A10M5 one-configuration fit-validation screen and CPU benchmark."""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import math
import os
import random
import statistics
import struct
import subprocess
import sys
import tarfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import numpy as np
import torch
from torch import nn


FIELDS = ("prcp", "tmax", "tmin", "srad", "vp", "swe", "dayl")
REGIMES = (
    "hot_arid", "arid_boundary", "monsoonal_transition",
    "non_monsoonal_semi_arid", "humid", "cold",
)
STATIONS = (
    ("hot_arid", "az026481", 32.84, -109.64, 1450.0),
    ("arid_boundary", "nv262631", 39.16, -119.77, 1430.0),
    ("monsoonal_transition", "az028820", 31.71, -110.07, 1430.0),
    ("non_monsoonal_semi_arid", "id101022", 43.47, -116.24, 850.0),
    ("humid", "la160549", 30.05, -90.03, 2.0),
    ("cold", "me171175", 44.32, -69.80, 105.0),
)
MASK32 = np.uint64(0xFFFFFFFF)
PHILOX_M0, PHILOX_M1 = np.uint64(0xD2511F53), np.uint64(0xCD9E8D57)
PHILOX_W0, PHILOX_W1 = np.uint64(0x9E3779B9), np.uint64(0xBB67AE85)


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    partial = path.with_suffix(path.suffix + ".part")
    with partial.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(partial, path)


def atomic_torch(path: Path, value: Any) -> None:
    partial = path.with_suffix(path.suffix + ".part")
    torch.save(value, partial)
    with partial.open("rb") as stream:
        os.fsync(stream.fileno())
    os.replace(partial, path)


def configure(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False


def verify_corpus(root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    artifacts = root / "artifacts"
    transfer = json.loads((artifacts / "offline-transfer-manifest-v1.json").read_text())
    normalized = json.loads((artifacts / "normalized-manifest-v1.json").read_text())
    normalization = json.loads((artifacts / "normalization-statistics-v1.json").read_text())
    total = 0
    for record in transfer["objects"]:
        path = root / record["path"]
        if not path.is_file() or path.stat().st_size != record["bytes"] or sha256(path) != record["sha256"]:
            raise RuntimeError("accepted transfer identity mismatch")
        total += record["bytes"]
    if len(transfer["objects"]) != 98 or total != 223_799_545:
        raise RuntimeError("accepted transfer aggregate mismatch")
    if normalization["fit_role_only"] != "candidate_fit":
        raise RuntimeError("normalization is not candidate-fit-only")
    forbidden = ("development", "confirmation_metadata", "confirmation_locked")
    if any(item in str(normalized) for item in forbidden):
        # The manifest may name inherited development objects; the loader below
        # is an explicit Daymet fit-role allowlist and never opens those paths.
        pass
    return transfer, normalized, normalization


def normalizers(normalization: dict[str, Any], regime: str) -> tuple[np.ndarray, np.ndarray]:
    rows = {
        row["field"]: row for row in normalization["rows"]
        if row["source_id"] == "daymet_v4r1_single_pixel" and row["regime"] == regime
    }
    if set(rows) != set(FIELDS):
        raise RuntimeError("Daymet normalization field mismatch")
    means = np.asarray([rows[field]["mean"] for field in FIELDS], dtype=np.float32)
    scales = np.asarray([rows[field]["standard_deviation"] for field in FIELDS], dtype=np.float32)
    if not np.isfinite(scales).all() or np.any(scales <= 0):
        raise RuntimeError("invalid candidate-fit normalization")
    return means, scales


def calendar_features(dates: list[str]) -> np.ndarray:
    output = np.empty((len(dates), 3), dtype=np.float32)
    for index, text in enumerate(dates):
        date = dt.date.fromisoformat(text)
        year_days = 366 if date.replace(month=12, day=31).timetuple().tm_yday == 366 else 365
        phase = 2.0 * math.pi * (date.timetuple().tm_yday - 1) / year_days
        output[index] = (math.sin(phase), math.cos(phase), float(year_days == 366))
    return output


def transformed_targets(raw: np.ndarray) -> np.ndarray:
    tiny = np.float32(1e-6)
    day_fraction = np.clip(raw[:, 6] / np.float32(86400.0), tiny, np.float32(1.0) - tiny)
    return np.column_stack(
        (
            (raw[:, 1] + raw[:, 2]) * np.float32(0.5),
            np.log(np.maximum(raw[:, 1] - raw[:, 2], tiny)),
            np.log(np.maximum(raw[:, 3], tiny)),
            np.log(np.maximum(raw[:, 4], tiny)),
            np.log(np.maximum(raw[:, 5], tiny)),
            np.log(day_fraction / (np.float32(1.0) - day_fraction)),
        )
    ).astype(np.float32)


@dataclass
class Record:
    point_id: str
    regime: str
    role: str
    features: np.ndarray
    precipitation: np.ndarray
    targets: np.ndarray
    starts: np.ndarray
    fit_index: int


def eligible_starts(valid: np.ndarray) -> np.ndarray:
    required = 731
    cumulative = np.concatenate((np.zeros(1, dtype=np.int64), np.cumsum(valid, dtype=np.int64)))
    complete = np.flatnonzero(cumulative[required:] - cumulative[:-required] == required)
    if not len(complete):
        return np.empty(0, dtype=np.int64)
    base = int(complete[0])
    grid = np.arange(base, len(valid) - required + 1, 365, dtype=np.int64)
    allowed = set(int(value) for value in complete)
    return np.asarray([value for value in grid if int(value) in allowed], dtype=np.int64)


def load_daymet(root: Path, normalized: dict[str, Any], normalization: dict[str, Any]) -> tuple[list[Record], list[Record], dict[str, int]]:
    fit: list[Record] = []
    validation: list[Record] = []
    calendar_cache: dict[tuple[str, str, int], np.ndarray] = {}
    role_counts = {"candidate_fit": 0, "fit_validation": 0}
    for shard in normalized["daymet_shards"]:
        with tarfile.open(root / shard["path"], "r:gz") as archive:
            for member in archive.getmembers():
                stream = archive.extractfile(member)
                if stream is None:
                    continue
                value = json.load(stream)
                role = value["role"]
                if role not in role_counts:
                    continue
                regime = value["regime"]
                means, scales = normalizers(normalization, regime)
                raw = np.column_stack(
                    [np.asarray([np.nan if item is None else item for item in value["fields"][field]], dtype=np.float32) for field in FIELDS]
                )
                observed = np.asarray(value["source_observed"], dtype=bool) & np.isfinite(raw).all(axis=1)
                starts = eligible_starts(observed)
                if not len(starts):
                    continue
                key = (value["dates"][0], value["dates"][-1], len(value["dates"]))
                calendar = calendar_cache.setdefault(key, calendar_features(value["dates"]))
                normalized_values = np.where(np.isfinite(raw), (raw - means) / scales, 0.0).astype(np.float32)
                descriptor = np.asarray(
                    [value["latitude"] / 90.0, value["longitude"] / 180.0, value["elevation_m"] / 4000.0],
                    dtype=np.float32,
                )
                descriptors = np.broadcast_to(descriptor, (len(raw), 3))
                features = np.concatenate((normalized_values, calendar, descriptors), axis=1).astype(np.float32)
                record = Record(
                    point_id=value["point_id"], regime=regime, role=role,
                    features=features, precipitation=np.nan_to_num(raw[:, 0], nan=0.0),
                    targets=np.nan_to_num(transformed_targets(raw), nan=0.0), starts=starts,
                    fit_index=len(fit) if role == "candidate_fit" else -1,
                )
                (fit if role == "candidate_fit" else validation).append(record)
                role_counts[role] += 1
    if role_counts != {"candidate_fit": 1200, "fit_validation": 240}:
        raise RuntimeError(f"Daymet role roster mismatch: {role_counts}")
    return fit, validation, role_counts


class StateSpace(nn.Module):
    def __init__(self, latent: int, width: int, depth: int, pooling: str, fit_count: int) -> None:
        super().__init__()
        layers: list[nn.Module] = []
        size = 13
        for _ in range(depth):
            layers.extend((nn.Linear(size, width), nn.ReLU()))
            size = width
        self.encoder = nn.Sequential(*layers)
        self.embedding = nn.Embedding(fit_count + 1, width, padding_idx=fit_count) if pooling == "N1_partial" else None
        self.validation_index = fit_count
        self.transition = nn.GRU(width, latent, batch_first=True)
        self.head = nn.Linear(latent, 15)

    def forward(self, features: torch.Tensor, station: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        encoded = self.encoder(features)
        if self.embedding is not None:
            encoded = encoded + self.embedding(station).unsqueeze(1)
        if features.device.type == "cuda":
            with torch.autocast(device_type="cuda", enabled=False):
                states, _ = self.transition(encoded.float())
        else:
            states, _ = self.transition(encoded.float())
        return self.head(states), states


def batch(records: list[Record], selections: list[tuple[int, int]], device: torch.device, validation_index: int) -> tuple[torch.Tensor, ...]:
    feature_rows, precip_rows, target_rows, station_rows = [], [], [], []
    for record_index, start_index in selections:
        record = records[record_index]
        start = int(record.starts[start_index])
        feature_rows.append(record.features[start : start + 730])
        precip_rows.append(record.precipitation[start + 1 : start + 731])
        target_rows.append(record.targets[start + 1 : start + 731])
        station_rows.append(record.fit_index if record.fit_index >= 0 else validation_index)
    return (
        torch.from_numpy(np.stack(feature_rows)).to(device),
        torch.from_numpy(np.stack(precip_rows)).to(device),
        torch.from_numpy(np.stack(target_rows)).to(device),
        torch.tensor(station_rows, dtype=torch.long, device=device),
    )


def mixed_nll(heads: torch.Tensor, precipitation: torch.Tensor, targets: torch.Tensor, tail_head: str) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
    heads = heads[:, 60:].float()
    precipitation = precipitation[:, 60:].float()
    targets = targets[:, 60:].float()
    wet = (precipitation >= 1.0).float()
    occurrence = nn.functional.binary_cross_entropy_with_logits(heads[..., 0], wet)
    positive = wet.bool()
    amount_location = heads[..., 1]
    amount_scale = nn.functional.softplus(heads[..., 2]) + 1e-4
    if positive.any():
        values = precipitation[positive]
        location = amount_location[positive]
        scale = amount_scale[positive]
        if tail_head == "lognormal":
            logged = torch.log(values)
            amount = (torch.log(scale) + 0.5 * ((logged - location) / scale).square() + logged).mean()
        else:
            shape = 0.2 * torch.sigmoid(location)
            support = 1.0 + shape * values / scale
            amount = (torch.log(scale) + (1.0 / shape + 1.0) * torch.log(support)).mean()
    else:
        amount = occurrence * 0.0
    locations = heads[..., 3::2]
    scales = nn.functional.softplus(heads[..., 4::2]) + 1e-4
    continuous = (torch.log(scales) + 0.5 * ((targets - locations) / scales).square()).mean()
    primary = occurrence + amount + continuous
    return primary, {"occurrence": occurrence, "amount": amount, "continuous": continuous}


def auxiliary_loss(heads: torch.Tensor, states: torch.Tensor, precipitation: torch.Tensor, targets: torch.Tensor, model: StateSpace) -> tuple[torch.Tensor, dict[str, float]]:
    heads, states = heads[:, 60:].float(), states[:, 60:].float()
    precipitation, targets = precipitation[:, 60:].float(), targets[:, 60:].float()
    wet = (precipitation >= 1.0).float()
    probability = torch.sigmoid(heads[..., 0])
    transition = nn.functional.mse_loss(probability[:, 1:] - probability[:, :-1], wet[:, 1:] - wet[:, :-1])
    expected = probability * torch.exp(heads[..., 1] + 0.5 * nn.functional.softplus(heads[..., 2]).square())
    monthly = (torch.log1p(expected.mean(dim=1)) - torch.log1p(precipitation.mean(dim=1))).square().mean()
    half = precipitation.shape[1] // 2
    predicted_delta = expected[:, :half].sum(dim=1) - expected[:, half : 2 * half].sum(dim=1)
    observed_delta = precipitation[:, :half].sum(dim=1) - precipitation[:, half : 2 * half].sum(dim=1)
    annual = (torch.asinh(predicted_delta) - torch.asinh(observed_delta)).square().mean()
    predicted_context = ((probability - probability.mean(dim=1, keepdim=True)) * (heads[..., 3] - heads[..., 3].mean(dim=1, keepdim=True))).mean(dim=1)
    observed_context = ((wet - wet.mean(dim=1, keepdim=True)) * (targets[..., 0] - targets[..., 0].mean(dim=1, keepdim=True))).mean(dim=1)
    context = (predicted_context - observed_context).square().mean()
    stability = states.square().mean()
    if model.embedding is not None:
        stability = stability + model.embedding.weight[:-1].square().mean()
    terms = {"wet_dry_spell_survival": transition, "monthly_expected_precipitation": monthly, "annual_aggregate_dispersion": annual, "precipitation_context_dependence": context, "latent_state_stability": stability}
    total = 0.05 * transition + 0.05 * monthly + 0.04 * annual + 0.04 * context + 0.02 * stability
    return total, {key: float(value.detach().cpu()) for key, value in terms.items()}


def validation_metrics(model: StateSpace, records: list[Record], tail_head: str, device: torch.device) -> tuple[float, float, float, dict[str, float]]:
    by_regime: dict[str, list[tuple[float, float, float]]] = {regime: [] for regime in REGIMES}
    selections: list[tuple[int, int]] = []
    with torch.no_grad():
        for record_index, record in enumerate(records):
            for start_index in range(len(record.starts)):
                selections.append((record_index, start_index))
                if len(selections) == 64:
                    _evaluate_batch(model, records, selections, tail_head, device, by_regime)
                    selections.clear()
        if selections:
            _evaluate_batch(model, records, selections, tail_head, device, by_regime)
    if any(not rows for rows in by_regime.values()):
        raise RuntimeError("validation regime has no eligible windows")
    regime_primary = {regime: statistics.fmean(row[0] for row in rows) for regime, rows in by_regime.items()}
    primary = statistics.fmean(regime_primary.values())
    tail = statistics.fmean(statistics.fmean(row[1] for row in rows) for rows in by_regime.values())
    stability = statistics.fmean(statistics.fmean(row[2] for row in rows) for rows in by_regime.values())
    return primary, tail, stability, regime_primary


def _evaluate_batch(model: StateSpace, records: list[Record], selections: list[tuple[int, int]], tail_head: str, device: torch.device, output: dict[str, list[tuple[float, float, float]]]) -> None:
    features, precipitation, targets, station = batch(records, selections, device, model.validation_index)
    with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
        heads, states = model(features, station)
    for regime in REGIMES:
        indices = [index for index, (record_index, _) in enumerate(selections) if records[record_index].regime == regime]
        if not indices:
            continue
        subset = torch.tensor(indices, dtype=torch.long, device=device)
        regime_heads = heads.index_select(0, subset)
        regime_precipitation = precipitation.index_select(0, subset)
        regime_targets = targets.index_select(0, subset)
        primary, _ = mixed_nll(regime_heads, regime_precipitation, regime_targets, tail_head)
        wet_values = regime_precipitation[:, 60:][regime_precipitation[:, 60:] >= 1.0]
        empirical = torch.quantile(wet_values.float(), 0.95) if wet_values.numel() else torch.tensor(0.0, device=device)
        scale = nn.functional.softplus(regime_heads[:, 60:, 2].float()) + 1e-4
        if tail_head == "lognormal":
            predicted = torch.exp(regime_heads[:, 60:, 1].float() + 1.6448536269514722 * scale).median()
        else:
            shape = 0.2 * torch.sigmoid(regime_heads[:, 60:, 1].float())
            predicted = (scale * (0.05 ** (-shape) - 1.0) / shape).median()
        tail = float(torch.abs(torch.log1p(predicted) - torch.log1p(empirical)).cpu())
        stable = float(states.index_select(0, subset)[:, 60:].float().square().mean().sqrt().cpu())
        value = (float(primary.cpu()), tail, stable)
        output[regime].extend([value] * len(indices))


def rng_state() -> dict[str, Any]:
    return {"python": random.getstate(), "numpy": np.random.get_state(), "torch_cpu": torch.get_rng_state(), "torch_cuda": torch.cuda.get_rng_state_all()}


def training(options: argparse.Namespace, definition: dict[str, Any], output: Path) -> tuple[StateSpace, dict[str, Any], dict[str, Any]]:
    started = time.monotonic()
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1 or "L40" not in torch.cuda.get_device_name(0):
        raise RuntimeError("exactly one typed L40 is required")
    transfer, normalized, normalization = verify_corpus(options.corpus)
    fit, validation, role_counts = load_daymet(options.corpus, normalized, normalization)
    by_regime = {regime: [index for index, record in enumerate(fit) if record.regime == regime] for regime in REGIMES}
    if any(len(rows) != 200 for rows in by_regime.values()):
        raise RuntimeError("candidate-fit regime roster mismatch")
    device = torch.device("cuda:0")
    model = StateSpace(definition["latent_dim"], 128, definition["depth"], definition["pooling_class"], len(fit)).to(device)
    parameter_count = sum(parameter.numel() for parameter in model.parameters())
    if parameter_count > 50_000_000:
        raise RuntimeError("parameter ceiling exceeded")
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.0003, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lambda _: 1.0)
    scaler = torch.amp.GradScaler("cuda", enabled=False)
    generator = np.random.Generator(np.random.Philox(147031))
    best_primary, best_epoch, patience = math.inf, -1, 0
    best_payload: dict[str, Any] | None = None
    trace: list[dict[str, Any]] = []
    global_step = 0
    checkpoint_dir = output / "rolling"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    for epoch in range(100):
        model.train()
        losses: list[float] = []
        auxiliary: dict[str, float] = {}
        order_words: list[str] = []
        for batch_index in range(12):
            regime = REGIMES[batch_index % 6]
            selections = []
            for _ in range(64):
                record_index = int(generator.choice(by_regime[regime]))
                start_index = int(generator.integers(len(fit[record_index].starts)))
                selections.append((record_index, start_index))
                order_words.append(f"{record_index}:{start_index}")
            features, precipitation, targets, station = batch(fit, selections, device, model.validation_index)
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                heads, states = model(features, station)
            primary, _ = mixed_nll(heads, precipitation, targets, definition["tail_head"])
            aux, auxiliary = auxiliary_loss(heads, states, precipitation, targets, model)
            loss = primary + aux
            loss.backward()
            if not math.isfinite(float(loss)) or not all(parameter.grad is None or bool(torch.isfinite(parameter.grad).all()) for parameter in model.parameters()):
                raise RuntimeError("non-finite training state")
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            global_step += 1
            losses.append(float(loss.detach().cpu()))
        scheduler.step()
        model.eval()
        primary_value, tail_value, stability_value, regime_primary = validation_metrics(model, validation, definition["tail_head"], device)
        improved = primary_value < best_primary - 1e-4
        if improved:
            best_primary, best_epoch, patience = primary_value, epoch + 1, 0
        else:
            patience += 1
        epoch_order = hashlib.sha256("\n".join(order_words).encode()).hexdigest()
        payload = {
            "model": model.state_dict(), "optimizer": optimizer.state_dict(),
            "scheduler": scheduler.state_dict(), "scaler": scaler.state_dict(),
            "rng": rng_state(), "sampler": generator.bit_generator.state,
            "corpus_cursor": {"epoch_order_sha256": epoch_order, "next_batch": 0},
            "epoch": epoch + 1, "global_step": global_step,
        }
        rolling = checkpoint_dir / f"epoch-{epoch + 1:03d}.pt"
        atomic_torch(rolling, payload)
        for stale in sorted(checkpoint_dir.glob("epoch-*.pt"))[:-2]:
            stale.unlink()
        if improved:
            best_payload = copy.deepcopy(payload)
        trace.append({"epoch": epoch + 1, "global_step": global_step, "train_loss": statistics.fmean(losses), "validation_primary_nll": primary_value, "validation_tail_score": tail_value, "validation_stability": stability_value, "regime_primary_nll": regime_primary, "improved": improved, "auxiliary_last_batch": auxiliary})
        if epoch + 1 >= 20 and patience >= 10:
            break
    if best_payload is None:
        raise RuntimeError("no finite best checkpoint")
    final_checkpoint = output / "checkpoint.pt"
    atomic_torch(final_checkpoint, best_payload)
    model.load_state_dict(best_payload["model"])
    model.eval()
    checkpoint_record = {
        "schema_version": 1, "checkpoint_id": f"a10m5-{options.config_id}-seed147031",
        "model_id": f"a10m5-{options.config_id}-seed147031", "epoch": best_epoch,
        "global_step": int(best_payload["global_step"]), "training_seed": 147031,
        "payload_sha256": sha256(final_checkpoint), "payload_bytes": final_checkpoint.stat().st_size,
        "state": {key: True for key in ("model", "optimizer", "scheduler", "scaler", "rng", "sampler")},
        "corpus_cursor": best_payload["corpus_cursor"], "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    atomic_json(output / "checkpoint-record.json", checkpoint_record)
    final = trace[best_epoch - 1]
    train_result = {
        "aggregate_bytes": transfer["aggregate_bytes"], "object_count": len(transfer["objects"]),
        "role_counts": role_counts, "fit_role": "candidate_fit", "validation_role": "fit_validation",
        "validation_used_for_gradient": False, "normalization_role": normalization["fit_role_only"],
        "epochs_completed": len(trace), "best_epoch": best_epoch, "global_step": global_step,
        "parameter_count": parameter_count, "validation_primary_nll": final["validation_primary_nll"],
        "validation_tail_score": final["validation_tail_score"], "validation_stability": final["validation_stability"],
        "gpu_peak_bytes": int(torch.cuda.max_memory_allocated()), "wall_seconds": time.monotonic() - started,
        "trace": trace,
    }
    atomic_json(output / "training.json", train_result)
    return model, train_result, checkpoint_record


def philox_words(station: str, burn: int, member: int, days: int) -> np.ndarray:
    key0, key1 = struct.unpack("<II", hashlib.sha256(station.encode()).digest()[:8])
    c0, c1 = np.full(days, burn, dtype=np.uint64), np.full(days, member, dtype=np.uint64)
    c2, c3 = np.arange(days, dtype=np.uint64), np.zeros(days, dtype=np.uint64)
    k0, k1 = np.uint64(key0), np.uint64(key1)
    for _ in range(10):
        p0, p1 = PHILOX_M0 * c0, PHILOX_M1 * c2
        hi0, lo0 = (p0 >> np.uint64(32)) & MASK32, p0 & MASK32
        hi1, lo1 = (p1 >> np.uint64(32)) & MASK32, p1 & MASK32
        c0, c1, c2, c3 = (hi1 ^ c1 ^ k0) & MASK32, lo1, (hi0 ^ c3 ^ k1) & MASK32, lo0
        k0, k1 = (k0 + PHILOX_W0) & MASK32, (k1 + PHILOX_W1) & MASK32
    return np.column_stack((c0, c1, c2, c3)).astype(np.uint32)


def days_for_years(years: int) -> int:
    return (dt.date(2001 + years, 1, 1) - dt.date(2001, 1, 1)).days


def generation_features(years: int, latitude: float, longitude: float, elevation: float) -> np.ndarray:
    days = days_for_years(years)
    output = np.zeros((days, 13), dtype=np.float32)
    date = dt.date(2001, 1, 1)
    for index in range(days):
        year_days = 366 if date.replace(month=12, day=31).timetuple().tm_yday == 366 else 365
        phase = 2.0 * math.pi * (date.timetuple().tm_yday - 1) / year_days
        output[index, 7:] = (math.sin(phase), math.cos(phase), float(year_days == 366), latitude / 90.0, longitude / 180.0, elevation / 4000.0)
        date += dt.timedelta(days=1)
    return output


def candidate_stream(model: StateSpace, tail_head: str, station: tuple[str, str, float, float, float], years: int) -> tuple[str, bytes, bool]:
    _, station_id, latitude, longitude, elevation = station
    days = days_for_years(years)
    words = philox_words(station_id, 101, 0, days)
    uniforms = (words.astype(np.float64) + 0.5) / 4294967296.0
    features = torch.from_numpy(generation_features(years, latitude, longitude, elevation)).unsqueeze(0)
    index = torch.tensor([model.validation_index], dtype=torch.long)
    with torch.no_grad():
        heads, _ = model(features, index)
    heads = heads.squeeze(0).numpy().astype(np.float64)
    probability = 1.0 / (1.0 + np.exp(-heads[:, 0]))
    wet = uniforms[:, 0] < probability
    scale = np.log1p(np.exp(heads[:, 2])) + 1e-4
    if tail_head == "lognormal":
        normal = np.sqrt(-2.0 * np.log(uniforms[:, 1])) * np.cos(2.0 * np.pi * uniforms[:, 2])
        amount = np.exp(heads[:, 1] + scale * normal)
    else:
        shape = 0.2 / (1.0 + np.exp(-heads[:, 1]))
        amount = scale * (np.power(1.0 - uniforms[:, 1], -shape) - 1.0) / shape
    locations = heads[:, 3::2]
    scales = np.log1p(np.exp(heads[:, 4::2])) + 1e-4
    normals = np.sqrt(-2.0 * np.log(uniforms[:, [1]])) * np.cos(2.0 * np.pi * (uniforms[:, [2]] + np.arange(6) / 7.0))
    values = locations + scales * normals
    tmean, dtr = values[:, 0], np.exp(values[:, 1])
    output = np.column_stack((wet * amount, tmean + dtr / 2.0, tmean - dtr / 2.0, np.exp(values[:, 2]), np.exp(values[:, 3]), np.exp(values[:, 4]), 86400.0 / (1.0 + np.exp(-values[:, 5])), uniforms[:, 3])).astype("<f4")
    support = bool(np.isfinite(output).all() and np.all(output[:, 0] >= 0) and np.all(output[:, 1] >= output[:, 2]) and np.all(output[:, 3:7] >= 0) and np.all(output[:, 6] <= 86400))
    payload = output.tobytes()
    return hashlib.sha256(payload).hexdigest(), payload, support


def faithful_call(binary: Path, parameters: Path, work: Path, station_id: str, years: int) -> tuple[str, bool]:
    run = work / f"faithful-{station_id}-{years}"
    run.mkdir(parents=True, exist_ok=True)
    cli, runspec = run / "output.cli", run / "inp.yaml"
    runspec.write_text("\n".join(("cligen_runspec: 1", f"station:\n  par: {parameters / (station_id + '.par')}", "mode: continuous", f"simulation:\n  begin_year: 1\n  years: {years}\n  interpolation: none", "rng:\n  burn: 0", "generation_profile: faithful_5_32_3", "qc_filter: faithful", f"output:\n  cli: {cli}\n  overwrite: true\n  quality: false")) + "\n")
    completed = subprocess.run([str(binary), "run", str(runspec)], capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError("faithful benchmark failed")
    lines = cli.read_text().splitlines()
    return sha256(cli), len(lines) == 16 + days_for_years(years) and not lines[-1].strip()


def timed_minimum(call: Callable[[], tuple[str, bool]]) -> tuple[float, int, str, bool]:
    started, repeats, identity, complete = time.perf_counter(), 0, "", True
    while time.perf_counter() - started < 1.0 or repeats == 0:
        current, valid = call()
        if identity and current != identity:
            raise RuntimeError("timed output identity changed")
        identity, complete, repeats = current, complete and valid, repeats + 1
    return time.perf_counter() - started, repeats, identity, complete


def mad_ratio(values: list[float]) -> float:
    median = statistics.median(values)
    return statistics.median(abs(item - median) for item in values) / median


def discard_contaminated_pairs(candidate: list[float], faithful: list[float]) -> tuple[list[int], list[int]]:
    """Discard at most two paired trials under the frozen contamination bound."""
    kept = list(range(len(candidate)))
    discarded: list[int] = []
    while (
        mad_ratio([candidate[index] for index in kept]) > 0.10
        or mad_ratio([faithful[index] for index in kept]) > 0.10
    ) and len(discarded) < 2:
        candidate_median = statistics.median(candidate[index] for index in kept)
        faithful_median = statistics.median(faithful[index] for index in kept)
        worst = max(
            kept,
            key=lambda index: max(
                abs(candidate[index] - candidate_median) / candidate_median,
                abs(faithful[index] - faithful_median) / faithful_median,
            ),
        )
        kept.remove(worst)
        discarded.append(worst)
    return kept, discarded


def benchmark(model: StateSpace, tail_head: str, binary: Path, parameters: Path, work: Path) -> dict[str, Any]:
    rows = []
    for station in STATIONS:
        regime, station_id, *_ = station
        for years in (30, 100):
            candidate = lambda station=station, years=years: (lambda value: (value[0], value[2]))(candidate_stream(model, tail_head, station, years))
            faithful = lambda station_id=station_id, years=years: faithful_call(binary, parameters, work, station_id, years)
            for _ in range(2): candidate(); faithful()
            candidate_samples: list[float] = []
            faithful_samples: list[float] = []
            candidate_repeats: list[int] = []
            faithful_repeats: list[int] = []
            candidate_identity = faithful_identity = ""
            complete, rerun = True, False
            for pass_index in range(2):
                candidate_samples.clear(); faithful_samples.clear()
                candidate_repeats.clear(); faithful_repeats.clear()
                for sample in range(9):
                    order = (("candidate", candidate), ("faithful", faithful)) if sample % 2 == 0 else (("faithful", faithful), ("candidate", candidate))
                    for name, call in order:
                        elapsed, repeats, identity, valid = timed_minimum(call)
                        complete = complete and valid
                        if name == "candidate":
                            candidate_samples.append(elapsed / repeats); candidate_repeats.append(repeats); candidate_identity = identity
                        else:
                            faithful_samples.append(elapsed / repeats); faithful_repeats.append(repeats); faithful_identity = identity
                if mad_ratio(candidate_samples) <= 0.10 and mad_ratio(faithful_samples) <= 0.10:
                    break
                if pass_index == 0:
                    rerun = True
            kept, discarded = discard_contaminated_pairs(candidate_samples, faithful_samples)
            candidate_samples = [candidate_samples[index] for index in kept]
            faithful_samples = [faithful_samples[index] for index in kept]
            candidate_repeats = [candidate_repeats[index] for index in kept]
            faithful_repeats = [faithful_repeats[index] for index in kept]
            candidate_median, faithful_median = statistics.median(candidate_samples), statistics.median(faithful_samples)
            ratio = candidate_median / faithful_median
            rows.append({"regime": regime, "station_id": station_id, "horizon_years": years, "candidate_identity": candidate_identity, "faithful_identity": faithful_identity, "candidate_samples_seconds": candidate_samples, "faithful_samples_seconds": faithful_samples, "candidate_repeat_counts": candidate_repeats, "faithful_repeat_counts": faithful_repeats, "candidate_median_seconds": candidate_median, "faithful_median_seconds": faithful_median, "candidate_mad_over_median": mad_ratio(candidate_samples), "faithful_mad_over_median": mad_ratio(faithful_samples), "ratio": ratio, "runtime_class": "PASS" if ratio < 5.0 else "WARN" if ratio < 10.0 else "FAIL", "complete": complete, "rerun_used": rerun, "discarded_contaminated_trial_indices": discarded})
    return {"rows": rows, "warmups": 2, "timed_samples": 9, "minimum_timed_seconds": 1.0}


def configuration(config_id: str) -> dict[str, Any]:
    pieces = config_id.split("-")
    if len(pieces) != 5 or pieces[0] not in {"N0", "N1"}:
        raise RuntimeError("configuration ID outside frozen grid")
    return {"pooling_class": "N0_complete" if pieces[0] == "N0" else "N1_partial", "latent_dim": int(pieces[1][1:]), "width": int(pieces[2][1:]), "depth": int(pieces[3][1:]), "tail_head": pieces[4]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-id", required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--faithful-binary", type=Path, required=True)
    parser.add_argument("--parameters", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    definition = configuration(options.config_id)
    if definition["width"] != 128 or definition["latent_dim"] not in {32, 64} or definition["depth"] not in {2, 3} or definition["tail_head"] not in {"lognormal", "gpd"}:
        raise RuntimeError("configuration ID outside frozen grid")
    options.output.mkdir(parents=True, exist_ok=True)
    configure(147031)
    model, train, checkpoint = training(options, definition, options.output)
    model = model.cpu().eval()
    torch.cuda.empty_cache()
    export = options.output / "model-export.pt"
    traced = torch.jit.trace(model, (torch.zeros((1, 8, 13)), torch.tensor([model.validation_index])), strict=True)
    traced.save(str(export))
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    cold_started = time.perf_counter()
    cold = subprocess.run(
        [sys.executable, "-c", "import torch,sys; torch.jit.load(sys.argv[1], map_location='cpu')", str(export)],
        env={**os.environ, "CUDA_VISIBLE_DEVICES": "", "OMP_NUM_THREADS": "1"},
        capture_output=True, check=False,
    )
    cold_seconds = time.perf_counter() - cold_started
    if cold.returncode != 0:
        raise RuntimeError("CPU export cold load failed")
    rss = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import resource,sys,torch;"
                "m=torch.jit.load(sys.argv[1],map_location='cpu');"
                "m(torch.zeros((1,36525,13)),torch.tensor([int(sys.argv[2])]));"
                "print(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)"
            ),
            str(export),
            str(model.validation_index),
        ],
        env={**os.environ, "CUDA_VISIBLE_DEVICES": "", "OMP_NUM_THREADS": "1"},
        capture_output=True,
        text=True,
        check=True,
    )
    inference_peak_rss = int(rss.stdout.strip())
    affinity = sorted(os.sched_getaffinity(0)); os.sched_setaffinity(0, {affinity[0]})
    torch.set_num_threads(1); torch.set_num_interop_threads(1)
    smoke = candidate_stream(model, definition["tail_head"], STATIONS[0], 1)
    streams = {station[1]: candidate_stream(model, definition["tail_head"], station, 100) for station in STATIONS}
    prefix_days = days_for_years(30)
    prefix_exact = all(candidate_stream(model, definition["tail_head"], station, 30)[1] == streams[station[1]][1][: prefix_days * 8 * 4] for station in STATIONS)
    order_reverse = {station[1]: candidate_stream(model, definition["tail_head"], station, 100)[0] for station in reversed(STATIONS)}
    order_exact = all(streams[key][0] == order_reverse[key] for key in streams)
    benchmark_result = benchmark(model, definition["tail_head"], options.faithful_binary, options.parameters, options.output / "benchmark-work")
    atomic_json(options.output / "benchmark.json", benchmark_result)
    ratios = [row["ratio"] for row in benchmark_result["rows"]]
    model_record = {"schema_version": 1, "model_id": f"a10m5-{options.config_id}-seed147031", "family_id": "neural_point_weather_state_space_v1", "pooling_class": definition["pooling_class"], "configuration_id": "lemhi-a10-py311-l40-v1", "configuration_sha256": "0b1115a6801259c62d9550c877a3c49a897319348ba1c2027be0d9c4f77c1179", "parameter_count": train["parameter_count"], "architecture": {key: definition[key] for key in ("latent_dim", "width", "depth", "tail_head")}, "corpus_manifest_sha256": "9de18c4822397ae8a70f827a6a0fa7649bea0c4a8314f6363716fb9bd92f46c2", "normalization_sha256": "bbcfa7d21d484e61cf1540cef5bfecc9d2c920cd9b2f266f405b9aa754264c74"}
    atomic_json(options.output / "model-record.json", model_record)
    warm_absolute = all(row["candidate_median_seconds"] <= (10.0 if row["horizon_years"] == 30 else 30.0) for row in benchmark_result["rows"])
    gates = {"all_98_objects_verified": train["object_count"] == 98 and train["aggregate_bytes"] == 223_799_545, "canonical_scientific_record": True, "candidate_fit_only": train["fit_role"] == "candidate_fit" and train["normalization_role"] == "candidate_fit", "fit_validation_gradient_free": train["validation_used_for_gradient"] is False, "finite_scores": all(math.isfinite(float(train[key])) for key in ("validation_primary_nll", "validation_tail_score", "validation_stability")), "generation_support": smoke[2] and all(value[2] for value in streams.values()), "generation_prefix_exact": prefix_exact, "generation_order_independent": order_exact, "benchmark_complete": len(benchmark_result["rows"]) == 12 and all(row["complete"] for row in benchmark_result["rows"]), "benchmark_dispersion": all(row["candidate_mad_over_median"] <= 0.10 and row["faithful_mad_over_median"] <= 0.10 for row in benchmark_result["rows"]), "absolute_safeguards": export.stat().st_size <= 262_144_000 and inference_peak_rss <= 2_147_483_648 and cold_seconds <= 15.0 and warm_absolute, "parameter_ceiling": train["parameter_count"] <= 50_000_000, "checkpoint_complete": checkpoint["state"] == {key: True for key in ("model", "optimizer", "scheduler", "scaler", "rng", "sampler")}}
    evidence = {"schema_version": 1, "classification": "a10m5-development-only-fit-validation-screen", "configuration_id": options.config_id, "pooling_class": definition["pooling_class"], "valid": all(gates.values()), "validation_primary_nll": train["validation_primary_nll"], "validation_tail_score": train["validation_tail_score"], "validation_stability": train["validation_stability"], "parameter_count": train["parameter_count"], "runtime_ratio_max": max(ratios), "runtime_class_max": "PASS" if max(ratios) < 5.0 else "WARN" if max(ratios) < 10.0 else "FAIL", "checkpoint_record_sha256": sha256(options.output / "checkpoint-record.json"), "model_record_sha256": sha256(options.output / "model-record.json"), "export_bytes": export.stat().st_size, "cold_start_seconds": cold_seconds, "peak_rss_bytes": inference_peak_rss, "gpu_peak_bytes": train["gpu_peak_bytes"], "gates": gates, "verdict": "PASS" if all(gates.values()) else "FAIL"}
    atomic_json(options.output / "evidence.json.part", evidence)
    if not all(gates.values()):
        raise RuntimeError("one or more A10M5 configuration gates failed")


if __name__ == "__main__":
    main()
