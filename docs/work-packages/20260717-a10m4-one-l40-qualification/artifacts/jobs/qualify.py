#!/usr/bin/env python3
"""A10M4 one-L40 training/restart/generation/benchmark qualification."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import random
import resource
import statistics
import struct
import subprocess
import sys
import tarfile
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np
import torch
from torch import nn


FIELDS = ("prcp", "tmax", "tmin", "srad", "vp", "swe", "dayl")
STATIONS = (
    ("hot_arid", "az026481"),
    ("arid_boundary", "nv262631"),
    ("monsoonal_transition", "az028820"),
    ("non_monsoonal_semi_arid", "id101022"),
    ("humid", "la160549"),
    ("cold", "me171175"),
)
MASK32 = np.uint64(0xFFFFFFFF)
PHILOX_M0 = np.uint64(0xD2511F53)
PHILOX_M1 = np.uint64(0xCD9E8D57)
PHILOX_W0 = np.uint64(0x9E3779B9)
PHILOX_W1 = np.uint64(0xBB67AE85)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".part")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def atomic_torch(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".part")
    torch.save(value, temporary)
    with temporary.open("rb") as stream:
        os.fsync(stream.fileno())
    os.replace(temporary, path)


class PointWeatherStateSpace(nn.Module):
    """Frozen N0-l32-w128-d2-lognormal qualification model."""

    def __init__(self) -> None:
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(7, 128), nn.ReLU(), nn.Linear(128, 128), nn.ReLU()
        )
        self.transition = nn.GRUCell(128, 32)
        self.head = nn.Linear(32, 8)

    def forward(
        self, values: torch.Tensor, state: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        outputs = []
        for index in range(values.shape[1]):
            encoded = self.encoder(values[:, index, :])
            state = self.transition(encoded, state)
            outputs.append(self.head(state))
        return torch.stack(outputs, dim=1), state


def configure_determinism(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
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
    observed_bytes = 0
    for record in transfer["objects"]:
        path = root / record["path"]
        if not path.is_file() or path.stat().st_size != record["bytes"] or sha256(path) != record["sha256"]:
            raise RuntimeError(f"transfer identity mismatch: {record['path']}")
        observed_bytes += record["bytes"]
    if len(transfer["objects"]) != 98 or observed_bytes != 223_799_545:
        raise RuntimeError("transfer aggregate mismatch")
    if normalization["fit_role_only"] != "candidate_fit":
        raise RuntimeError("normalization role mismatch")
    return transfer, normalized, normalization


def load_daymet_role(corpus: Path, normalized: dict[str, Any], role: str) -> dict[str, Any]:
    for shard in normalized["daymet_shards"]:
        path = corpus / shard["path"]
        with tarfile.open(path, "r:gz") as archive:
            for member in archive.getmembers():
                stream = archive.extractfile(member)
                if stream is None:
                    continue
                value = json.load(stream)
                if value["role"] == role:
                    return value
    raise RuntimeError(f"Daymet role absent: {role}")


def normalizers(normalization: dict[str, Any], regime: str) -> tuple[np.ndarray, np.ndarray]:
    rows = {
        row["field"]: row
        for row in normalization["rows"]
        if row["source_id"] == "daymet_v4r1_single_pixel" and row["regime"] == regime
    }
    if set(rows) != set(FIELDS):
        raise RuntimeError("normalization field mismatch")
    means = np.asarray([rows[field]["mean"] for field in FIELDS], dtype=np.float32)
    scales = np.asarray([rows[field]["standard_deviation"] for field in FIELDS], dtype=np.float32)
    if not np.all(np.isfinite(scales)) or np.any(scales <= 0):
        raise RuntimeError("invalid normalization scale")
    return means, scales


def first_complete_offset(value: dict[str, Any], length: int) -> int:
    observed = value["source_observed"]
    if len(observed) < length:
        raise RuntimeError("Daymet record is shorter than the training window")
    for offset in range(len(observed) - length + 1):
        stop = offset + length
        if not all(observed[offset:stop]):
            continue
        if all(
            all(item is not None and math.isfinite(item) for item in value["fields"][field][offset:stop])
            for field in FIELDS
        ):
            return offset
    raise RuntimeError("no fully observed Daymet training window")


def window(value: dict[str, Any], means: np.ndarray, scales: np.ndarray, offset: int) -> tuple[torch.Tensor, torch.Tensor]:
    raw = np.column_stack([value["fields"][field] for field in FIELDS]).astype(np.float32)
    normalized = (raw - means) / scales
    inputs = torch.from_numpy(normalized[offset : offset + 730]).unsqueeze(0)
    targets = torch.from_numpy(normalized[offset + 1 : offset + 731]).unsqueeze(0)
    if not bool(torch.isfinite(inputs).all()) or not bool(torch.isfinite(targets).all()):
        raise RuntimeError("training window includes masked or non-finite data")
    wet = torch.from_numpy((raw[offset + 1 : offset + 731, 0] >= 1.0).astype(np.float32)).reshape(1, 730, 1)
    return inputs, torch.cat((wet, targets), dim=-1)


def components(device: torch.device) -> tuple[PointWeatherStateSpace, Any, Any, Any]:
    model = PointWeatherStateSpace().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.0003, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lambda _: 1.0)
    scaler = torch.amp.GradScaler("cuda", enabled=False)
    return model, optimizer, scheduler, scaler


def update(model: nn.Module, optimizer: Any, scheduler: Any, values: torch.Tensor, targets: torch.Tensor) -> tuple[torch.Tensor, float]:
    optimizer.zero_grad(set_to_none=True)
    state = torch.zeros((values.shape[0], 32), device=values.device)
    with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
        outputs, _ = model(values, state)
        occurrence = nn.functional.binary_cross_entropy_with_logits(outputs[..., :1].float(), targets[..., :1])
        continuous = nn.functional.mse_loss(outputs[..., 1:].float(), targets[..., 1:])
        loss = occurrence + continuous
    loss.backward()
    gradient_finite = all(
        parameter.grad is None or bool(torch.isfinite(parameter.grad).all())
        for parameter in model.parameters()
    )
    if not math.isfinite(float(loss)) or not gradient_finite:
        raise RuntimeError("non-finite training state")
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    optimizer.step()
    scheduler.step()
    vector = torch.cat([parameter.detach().reshape(-1).cpu() for parameter in model.parameters()])
    return vector, float(loss.detach().cpu())


def rng_state() -> dict[str, Any]:
    return {
        "python": random.getstate(),
        "numpy": np.random.get_state(),
        "torch_cpu": torch.get_rng_state(),
        "torch_cuda": torch.cuda.get_rng_state_all(),
    }


def restore_rng(value: dict[str, Any]) -> None:
    random.setstate(value["python"])
    np.random.set_state(value["numpy"])
    torch.set_rng_state(value["torch_cpu"])
    torch.cuda.set_rng_state_all(value["torch_cuda"])


def run_train(options: argparse.Namespace) -> None:
    started = time.monotonic()
    configure_determinism(147031)
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1 or "L40" not in torch.cuda.get_device_name(0):
        raise RuntimeError("exactly one L40 is required")
    transfer, normalized, normalization = verify_corpus(options.corpus)
    fit = load_daymet_role(options.corpus, normalized, "candidate_fit")
    validation = load_daymet_role(options.corpus, normalized, "fit_validation")
    means, scales = normalizers(normalization, fit["regime"])
    window_offset = first_complete_offset(fit, 732)
    batch1 = window(fit, means, scales, window_offset)
    batch2 = window(fit, means, scales, window_offset + 1)
    device = torch.device("cuda:0")
    model, optimizer, scheduler, scaler = components(device)
    parameter_count = sum(parameter.numel() for parameter in model.parameters())
    before = torch.cat([parameter.detach().reshape(-1).cpu() for parameter in model.parameters()])
    _, first_loss = update(model, optimizer, scheduler, batch1[0].to(device), batch1[1].to(device))
    after = torch.cat([parameter.detach().reshape(-1).cpu() for parameter in model.parameters()])
    options.checkpoint.parent.mkdir(parents=True, exist_ok=True)
    checkpoint = {
        "schema_version": 1,
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "scheduler": scheduler.state_dict(),
        "scaler": scaler.state_dict(),
        "rng": rng_state(),
        "sampler": {"epoch_order_sha256": hashlib.sha256(b"a10m4-fixed-two-window-order").hexdigest()},
        "corpus_cursor": {"next_batch": 1, "window_offset": window_offset},
        "model_record": {
            "configuration_id": "N0-l32-w128-d2-lognormal",
            "latent_dim": 32,
            "width": 128,
            "depth": 2,
            "tail_head": "lognormal",
            "parameter_count": parameter_count,
        },
    }
    atomic_torch(options.checkpoint, checkpoint)
    expected_vector, second_loss = update(
        model, optimizer, scheduler, batch2[0].to(device), batch2[1].to(device)
    )
    atomic_torch(options.expected, {"vector": expected_vector, "loss": second_loss})
    result = {
        "aggregate_bytes": transfer["aggregate_bytes"],
        "fit_point_id": fit["point_id"],
        "fit_regime": fit["regime"],
        "fit_role": fit["role"],
        "first_loss": first_loss,
        "gpu_peak_bytes": int(torch.cuda.max_memory_allocated()),
        "normalization_role": normalization["fit_role_only"],
        "object_count": len(transfer["objects"]),
        "parameter_count": parameter_count,
        "parameter_updated": not torch.equal(before, after),
        "validation_point_id": validation["point_id"],
        "validation_role": validation["role"],
        "validation_used_for_gradient": False,
        "window_all_observed": True,
        "window_offset": window_offset,
        "wall_seconds": time.monotonic() - started,
    }
    atomic_json(options.train_result, result)


def philox_words(station: str, burn: int, member: int, days: int) -> np.ndarray:
    station_digest = hashlib.sha256(station.encode()).digest()
    key0, key1 = struct.unpack("<II", station_digest[:8])
    c0 = np.full(days, burn, dtype=np.uint64)
    c1 = np.full(days, member, dtype=np.uint64)
    c2 = np.arange(days, dtype=np.uint64)
    c3 = np.zeros(days, dtype=np.uint64)
    k0, k1 = np.uint64(key0), np.uint64(key1)
    for _ in range(10):
        product0 = PHILOX_M0 * c0
        product1 = PHILOX_M1 * c2
        high0, low0 = (product0 >> np.uint64(32)) & MASK32, product0 & MASK32
        high1, low1 = (product1 >> np.uint64(32)) & MASK32, product1 & MASK32
        c0, c1, c2, c3 = (
            (high1 ^ c1 ^ k0) & MASK32,
            low1,
            (high0 ^ c3 ^ k1) & MASK32,
            low0,
        )
        k0 = (k0 + PHILOX_W0) & MASK32
        k1 = (k1 + PHILOX_W1) & MASK32
    return np.column_stack((c0, c1, c2, c3)).astype(np.uint32)


def philox_known_vector() -> bool:
    words = philox_words("", 0, 0, 1)[0]
    # The station key is SHA-256-derived above, so test the round core directly.
    c0 = c1 = c2 = c3 = np.zeros(1, dtype=np.uint64)
    k0 = k1 = np.uint64(0)
    for _ in range(10):
        p0, p1 = PHILOX_M0 * c0, PHILOX_M1 * c2
        hi0, lo0 = (p0 >> np.uint64(32)) & MASK32, p0 & MASK32
        hi1, lo1 = (p1 >> np.uint64(32)) & MASK32, p1 & MASK32
        c0, c1, c2, c3 = (hi1 ^ c1 ^ k0) & MASK32, lo1, (hi0 ^ c3 ^ k1) & MASK32, lo0
        k0, k1 = (k0 + PHILOX_W0) & MASK32, (k1 + PHILOX_W1) & MASK32
    expected = np.asarray([0x6627E8D5, 0xE169C58D, 0xBC57AC4C, 0x9B00DBD8], dtype=np.uint32)
    return words.shape == (4,) and np.array_equal(np.asarray([c0[0], c1[0], c2[0], c3[0]], dtype=np.uint32), expected)


def days_for_years(years: int) -> int:
    start = dt.date(2001, 1, 1)
    end = dt.date(2001 + years, 1, 1)
    return (end - start).days


def candidate_stream(model: PointWeatherStateSpace, station: str, years: int) -> tuple[str, bytes, bool]:
    days = days_for_years(years)
    words = philox_words(station, 101, 0, days)
    uniforms = (words.astype(np.float64) + 0.5) / 4294967296.0
    descriptor = int.from_bytes(hashlib.sha256(station.encode()).digest()[:4], "little") / 2**32
    state = torch.zeros((1, 32), dtype=torch.float32)
    chunks: list[np.ndarray] = []
    with torch.no_grad():
        for start in range(0, days, 365):
            count = min(365, days - start)
            ordinal = np.arange(start, start + count, dtype=np.float32)
            phase = 2.0 * np.pi * (ordinal % 365.2425) / 365.2425
            features = np.column_stack(
                (
                    np.sin(phase), np.cos(phase),
                    np.full(count, descriptor), np.full(count, descriptor * 0.5),
                    np.full(count, descriptor * 0.25), np.zeros(count), np.ones(count),
                )
            ).astype(np.float32)
            heads, state = model(torch.from_numpy(features).unsqueeze(0), state)
            chunks.append(heads.squeeze(0).numpy())
    heads = np.concatenate(chunks, axis=0)
    wet = uniforms[:, 0] < (1.0 / (1.0 + np.exp(-np.clip(heads[:, 0], -20, 20))))
    precipitation = wet * np.exp(np.clip(heads[:, 1], -5, 5)) * uniforms[:, 1]
    mean_temperature = np.clip(heads[:, 2], -8, 8) * 5.0
    temperature_range = np.log1p(np.exp(np.clip(heads[:, 3], -20, 20))) + 0.1
    output = np.column_stack(
        (
            precipitation,
            mean_temperature + temperature_range / 2,
            mean_temperature - temperature_range / 2,
            np.log1p(np.exp(np.clip(heads[:, 5], -20, 20))) * 100,
            (1.0 / (1.0 + np.exp(-np.clip(heads[:, 4], -20, 20)))) * 100,
            np.log1p(np.exp(np.clip(heads[:, 6], -20, 20))),
            1.0 / (1.0 + np.exp(-np.clip(heads[:, 7], -20, 20))),
            uniforms[:, 2],
        )
    ).astype("<f4")
    support = bool(
        np.isfinite(output).all()
        and np.all(output[:, 0] >= 0)
        and np.all(output[:, 1] >= output[:, 2])
        and np.all((output[:, 4] >= 0) & (output[:, 4] <= 100))
        and np.all(output[:, 3] >= 0)
        and np.all(output[:, 5] >= 0)
        and np.all((output[:, 6] >= 0) & (output[:, 6] <= 1))
    )
    payload = output.tobytes()
    return hashlib.sha256(payload).hexdigest(), payload, support


def pin_one_cpu() -> list[int]:
    affinity = sorted(os.sched_getaffinity(0))
    os.sched_setaffinity(0, {affinity[0]})
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    return affinity


def faithful_call(binary: Path, parameters: Path, work: Path, station: str, years: int) -> tuple[str, bool]:
    run = work / f"faithful-{station}-{years}"
    run.mkdir(parents=True, exist_ok=True)
    cli = run / "output.cli"
    runspec = run / "inp.yaml"
    runspec.write_text(
        "\n".join(
            (
                "cligen_runspec: 1", f"station:\n  par: {parameters / (station + '.par')}",
                "mode: continuous", f"simulation:\n  begin_year: 1\n  years: {years}\n  interpolation: none",
                "rng:\n  burn: 0", "generation_profile: faithful_5_32_3", "qc_filter: faithful",
                f"output:\n  cli: {cli}\n  overwrite: true\n  quality: false",
            )
        ) + "\n",
        encoding="utf-8",
    )
    completed = subprocess.run([str(binary), "run", str(runspec)], capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"faithful generation failed: {station}/{years}: {completed.stderr[-500:]}")
    lines = cli.read_text(encoding="utf-8").splitlines()
    complete = len(lines) == 15 + years * 365
    return sha256(cli), complete


def timed_minimum(call: Callable[[], tuple[str, bool]]) -> tuple[float, int, str, bool]:
    start = time.perf_counter()
    repeats = 0
    identity = ""
    complete = True
    while time.perf_counter() - start < 1.0 or repeats == 0:
        current, valid = call()
        if identity and current != identity:
            raise RuntimeError("timed output is nondeterministic")
        identity = current
        complete = complete and valid
        repeats += 1
    return time.perf_counter() - start, repeats, identity, complete


def mad_ratio(values: list[float]) -> float:
    median = statistics.median(values)
    return statistics.median(abs(value - median) for value in values) / median


def benchmark(model: PointWeatherStateSpace, binary: Path, parameters: Path, work: Path) -> dict[str, Any]:
    rows = []
    for regime, station in STATIONS:
        for years in (30, 100):
            def candidate() -> tuple[str, bool]:
                identity, _, support = candidate_stream(model, station, years)
                return identity, support
            faithful = lambda: faithful_call(binary, parameters, work, station, years)
            for _ in range(2):
                candidate()
                faithful()
            candidate_samples: list[float] = []
            faithful_samples: list[float] = []
            candidate_repeats: list[int] = []
            faithful_repeats: list[int] = []
            candidate_identity = faithful_identity = ""
            complete = True
            for sample in range(9):
                order = (("candidate", candidate), ("faithful", faithful))
                if sample % 2:
                    order = tuple(reversed(order))
                for name, call in order:
                    elapsed, repeats, identity, valid = timed_minimum(call)
                    complete = complete and valid
                    if name == "candidate":
                        candidate_samples.append(elapsed / repeats)
                        candidate_repeats.append(repeats)
                        candidate_identity = identity
                    else:
                        faithful_samples.append(elapsed / repeats)
                        faithful_repeats.append(repeats)
                        faithful_identity = identity
            rerun = False
            if mad_ratio(candidate_samples) > 0.10 or mad_ratio(faithful_samples) > 0.10:
                rerun = True
                candidate_samples.clear(); faithful_samples.clear()
                candidate_repeats.clear(); faithful_repeats.clear()
                for sample in range(9):
                    order = (("candidate", candidate), ("faithful", faithful))
                    if sample % 2:
                        order = tuple(reversed(order))
                    for name, call in order:
                        elapsed, repeats, _, valid = timed_minimum(call)
                        complete = complete and valid
                        (candidate_samples if name == "candidate" else faithful_samples).append(elapsed / repeats)
                        (candidate_repeats if name == "candidate" else faithful_repeats).append(repeats)
            candidate_median = statistics.median(candidate_samples)
            faithful_median = statistics.median(faithful_samples)
            rows.append(
                {
                    "candidate_identity": candidate_identity,
                    "candidate_mad_over_median": mad_ratio(candidate_samples),
                    "candidate_median_seconds": candidate_median,
                    "candidate_repeat_counts": candidate_repeats,
                    "candidate_samples_seconds": candidate_samples,
                    "complete": complete,
                    "faithful_identity": faithful_identity,
                    "faithful_mad_over_median": mad_ratio(faithful_samples),
                    "faithful_median_seconds": faithful_median,
                    "faithful_repeat_counts": faithful_repeats,
                    "faithful_samples_seconds": faithful_samples,
                    "horizon_years": years,
                    "ratio_diagnostic_only": candidate_median / faithful_median,
                    "regime": regime,
                    "rerun_used": rerun,
                    "station_id": station,
                }
            )
    return {"classification": "qualification-diagnostic-only", "rows": rows}


def run_restart(options: argparse.Namespace) -> None:
    configure_determinism(147031)
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1 or "L40" not in torch.cuda.get_device_name(0):
        raise RuntimeError("fresh restart requires exactly one L40")
    _, normalized, normalization = verify_corpus(options.corpus)
    fit = load_daymet_role(options.corpus, normalized, "candidate_fit")
    means, scales = normalizers(normalization, fit["regime"])
    device = torch.device("cuda:0")
    checkpoint = torch.load(options.checkpoint, map_location="cpu", weights_only=False)
    batch2 = window(
        fit, means, scales, int(checkpoint["corpus_cursor"]["window_offset"]) + 1
    )
    model, optimizer, scheduler, scaler = components(device)
    model.load_state_dict(checkpoint["model"])
    optimizer.load_state_dict(checkpoint["optimizer"])
    scheduler.load_state_dict(checkpoint["scheduler"])
    scaler.load_state_dict(checkpoint["scaler"])
    restore_rng(checkpoint["rng"])
    resumed_vector, resumed_loss = update(
        model, optimizer, scheduler, batch2[0].to(device), batch2[1].to(device)
    )
    expected = torch.load(options.expected, map_location="cpu", weights_only=True)
    restart_exact = torch.equal(resumed_vector, expected["vector"]) and struct.pack(
        "!d", resumed_loss
    ) == struct.pack("!d", expected["loss"])
    model_state = {key: value.detach().cpu() for key, value in model.state_dict().items()}
    atomic_torch(
        options.resumed_state,
        {"model": model_state, "model_record": checkpoint["model_record"]},
    )
    result = {
        "checkpoint_bytes": options.checkpoint.stat().st_size,
        "checkpoint_sha256": sha256(options.checkpoint),
        "corpus_cursor": checkpoint["corpus_cursor"],
        "fresh_process_restart_exact": restart_exact,
        "required_state": sorted(
            key
            for key in (
                "model", "optimizer", "scheduler", "scaler", "rng", "sampler", "corpus_cursor"
            )
            if key in checkpoint
        ),
        "resumed_loss": resumed_loss,
    }
    atomic_json(options.checkpoint_result, result)
    if not restart_exact:
        raise RuntimeError("fresh-process checkpoint restart diverged")


def run_benchmark(options: argparse.Namespace) -> None:
    started = time.monotonic()
    affinity = pin_one_cpu()
    configure_determinism(147031)
    if torch.cuda.is_available() or os.environ.get("CUDA_VISIBLE_DEVICES") not in {"", "-1"}:
        raise RuntimeError("GPU must be hidden for resume/export/benchmark")
    train = json.loads(options.train_result.read_text())
    checkpoint_result = json.loads(options.checkpoint_result.read_text())
    resumed = torch.load(options.resumed_state, map_location="cpu", weights_only=True)
    model = PointWeatherStateSpace()
    model.load_state_dict(resumed["model"])
    model.eval()

    sample_values = torch.zeros((1, 1, 7), dtype=torch.float32)
    sample_state = torch.zeros((1, 32), dtype=torch.float32)
    traced = torch.jit.trace(model, (sample_values, sample_state), strict=True)
    traced.save(str(options.export))
    reloaded = torch.jit.load(str(options.export), map_location="cpu")
    original_output = model(sample_values, sample_state)
    exported_output = reloaded(sample_values, sample_state)
    export_exact = all(torch.equal(left, right) for left, right in zip(original_output, exported_output))

    smoke_hash, _, smoke_support = candidate_stream(model, STATIONS[0][1], 1)
    forward = {station: candidate_stream(model, station, 100) for _, station in STATIONS}
    reverse = {station: candidate_stream(model, station, 100) for _, station in reversed(STATIONS)}
    order_independent = all(forward[key][0] == reverse[key][0] for key in forward)
    prefix_exact = True
    supports = smoke_support
    generation_rows = []
    prefix_days = days_for_years(30)
    for regime, station in STATIONS:
        identity, payload, support = forward[station]
        prefix_identity = hashlib.sha256(payload[: prefix_days * 8 * 4]).hexdigest()
        direct_prefix = candidate_stream(model, station, 30)[1]
        exact = direct_prefix == payload[: len(direct_prefix)]
        prefix_exact = prefix_exact and exact
        supports = supports and support
        generation_rows.append(
            {"regime": regime, "station_id": station, "rows_100": days_for_years(100), "stream_sha256": identity, "prefix_30_sha256": prefix_identity, "prefix_exact": exact, "support": support}
        )

    cold_start = subprocess.run(
        [sys.executable, "-c", "import torch,sys; torch.jit.load(sys.argv[1], map_location='cpu')", str(options.export)],
        env={**os.environ, "CUDA_VISIBLE_DEVICES": "", "OMP_NUM_THREADS": "1"},
        capture_output=True,
        check=False,
    )
    cold_started = time.perf_counter()
    subprocess.run(
        [sys.executable, "-c", "import torch,sys; torch.jit.load(sys.argv[1], map_location='cpu')", str(options.export)],
        env={**os.environ, "CUDA_VISIBLE_DEVICES": "", "OMP_NUM_THREADS": "1"},
        capture_output=True,
        check=True,
    )
    cold_seconds = time.perf_counter() - cold_started
    if cold_start.returncode != 0:
        raise RuntimeError("CPU export cold load failed")

    benchmark_result = benchmark(model, options.faithful_binary, options.parameters, options.work)
    benchmark_result["affinity_before_pin"] = affinity
    benchmark_result["affinity_used"] = sorted(os.sched_getaffinity(0))
    benchmark_result["node_class"] = os.environ.get("SLURMD_NODENAME", "unknown")
    benchmark_result["warmups"] = 2
    benchmark_result["timed_samples"] = 9
    benchmark_result["minimum_timed_seconds"] = 1.0
    atomic_json(options.benchmark, benchmark_result)

    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    resource_result = {
        "cold_start_seconds": cold_seconds,
        "cpu_peak_rss_bytes": peak_rss,
        "export_bytes": options.export.stat().st_size,
        "gpu_peak_bytes": train["gpu_peak_bytes"],
        "projected_twelve_config_screen_gpu_hours": train["wall_seconds"] * 12 / 3600,
        "resume_generation_benchmark_wall_seconds": time.monotonic() - started,
        "train_wall_seconds": train["wall_seconds"],
    }
    atomic_json(options.resource_result, resource_result)
    rows = benchmark_result["rows"]
    gates = {
        "all_98_objects_verified": train["object_count"] == 98 and train["aggregate_bytes"] == 223_799_545,
        "benchmark_complete": len(rows) == 12 and all(row["complete"] for row in rows),
        "benchmark_dispersion": all(row["candidate_mad_over_median"] <= 0.10 and row["faithful_mad_over_median"] <= 0.10 for row in rows),
        "canonical_configuration": options.configuration_id == "lemhi-a10-py311-l40-v1" and options.configuration_sha256 == "0b1115a6801259c62d9550c877a3c49a897319348ba1c2027be0d9c4f77c1179",
        "checkpoint_complete": checkpoint_result["required_state"] == sorted(["model", "optimizer", "scheduler", "scaler", "rng", "sampler", "corpus_cursor"]),
        "cpu_export_exact": export_exact,
        "cpu_export_safeguards": resource_result["export_bytes"] <= 262_144_000 and resource_result["cpu_peak_rss_bytes"] <= 2_147_483_648 and cold_seconds <= 15.0,
        "fresh_process_restart_exact": checkpoint_result["fresh_process_restart_exact"],
        "generation_order_independent": order_independent,
        "generation_prefix_exact": prefix_exact,
        "generation_support": supports,
        "model_frozen": resumed["model_record"]["configuration_id"] == "N0-l32-w128-d2-lognormal" and resumed["model_record"]["parameter_count"] <= 50_000_000,
        "missingness_excluded": train["window_all_observed"] is True,
        "parameter_updated": train["parameter_updated"],
        "philox_known_vector": philox_known_vector(),
        "role_boundary": train["fit_role"] == "candidate_fit" and train["validation_role"] == "fit_validation" and train["validation_used_for_gradient"] is False and train["normalization_role"] == "candidate_fit",
        "smoke_generation": bool(smoke_hash) and smoke_support,
    }
    evidence = {
        "classification": "development-only-implementation-qualification",
        "configuration_id": options.configuration_id,
        "configuration_semantic_sha256": options.configuration_sha256,
        "gates": gates,
        "generation": generation_rows,
        "model_record": resumed["model_record"],
        "runtime_interpretation": "qualification-diagnostic-only-no-selector-classification",
        "verdict": "PASS" if all(gates.values()) else "FAIL",
    }
    atomic_json(options.evidence, evidence)
    if not all(gates.values()):
        raise RuntimeError("one or more A10M4 gates failed")


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser()
    value.add_argument("mode", choices=("train", "restart", "benchmark"))
    value.add_argument("--corpus", type=Path, required=True)
    value.add_argument("--checkpoint", type=Path, required=True)
    value.add_argument("--expected", type=Path, required=True)
    value.add_argument("--train-result", type=Path, required=True)
    value.add_argument("--resumed-state", type=Path)
    value.add_argument("--checkpoint-result", type=Path)
    value.add_argument("--benchmark", type=Path)
    value.add_argument("--resource-result", type=Path)
    value.add_argument("--evidence", type=Path)
    value.add_argument("--export", type=Path)
    value.add_argument("--faithful-binary", type=Path)
    value.add_argument("--parameters", type=Path)
    value.add_argument("--work", type=Path)
    value.add_argument("--configuration-id", default="lemhi-a10-py311-l40-v1")
    value.add_argument("--configuration-sha256", default="0b1115a6801259c62d9550c877a3c49a897319348ba1c2027be0d9c4f77c1179")
    return value


def main() -> None:
    options = parser().parse_args()
    if options.mode == "train":
        run_train(options)
    elif options.mode == "restart":
        if options.checkpoint_result is None or options.resumed_state is None:
            raise SystemExit("restart outputs are required")
        run_restart(options)
    else:
        required = (options.checkpoint_result, options.resumed_state, options.benchmark, options.resource_result, options.evidence, options.export, options.faithful_binary, options.parameters, options.work)
        if any(value is None for value in required):
            raise SystemExit("resume outputs and benchmark inputs are required")
        run_benchmark(options)


if __name__ == "__main__":
    main()
