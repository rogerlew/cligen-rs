"""Fail-closed A10M3 record and decision contracts.

This module is research-only.  It freezes interface checks and selector
arithmetic before any A10 neural candidate is trained or scored.
"""

from __future__ import annotations

import math
from typing import Any, Iterable, Mapping


CANONICAL_CONFIGURATION_ID = "lemhi-a10-py311-l40-v1"
CANONICAL_CONFIGURATION_SHA256 = (
    "0b1115a6801259c62d9550c877a3c49a897319348ba1c2027be0d9c4f77c1179"
)
HORIZONS = (30, 100)
REGIMES = (
    "hot_arid",
    "arid_boundary",
    "monsoonal_transition",
    "non_monsoonal_semi_arid",
    "humid",
    "cold",
)
MATERIAL_IMPROVEMENT = 0.10
MINIMUM_APPLICABLE_REGIMES = 4


class ContractError(ValueError):
    """A record is incomplete, malformed, or violates a frozen contract."""


def _object(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ContractError(f"{name} must be an object")
    return value


def _keys(record: Mapping[str, Any], required: set[str], name: str) -> None:
    actual = set(record)
    if actual != required:
        missing = sorted(required - actual)
        extra = sorted(actual - required)
        raise ContractError(f"{name} keys differ: missing={missing}, extra={extra}")


def _string(record: Mapping[str, Any], key: str) -> str:
    value = record[key]
    if not isinstance(value, str) or not value:
        raise ContractError(f"{key} must be a nonempty string")
    return value


def _integer(record: Mapping[str, Any], key: str, minimum: int = 0) -> int:
    value = record[key]
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ContractError(f"{key} must be an integer >= {minimum}")
    return value


def _finite(record: Mapping[str, Any], key: str) -> float:
    value = record[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractError(f"{key} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ContractError(f"{key} must be finite")
    return result


def _sha256(record: Mapping[str, Any], key: str) -> str:
    value = _string(record, key)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ContractError(f"{key} must be a lowercase SHA-256")
    return value


def validate_model_record(value: Any) -> None:
    record = _object(value, "model record")
    _keys(
        record,
        {
            "schema_version",
            "model_id",
            "family_id",
            "pooling_class",
            "configuration_id",
            "configuration_sha256",
            "parameter_count",
            "architecture",
            "corpus_manifest_sha256",
            "normalization_sha256",
        },
        "model record",
    )
    if record["schema_version"] != 1:
        raise ContractError("unsupported model schema_version")
    _string(record, "model_id")
    if record["family_id"] != "neural_point_weather_state_space_v1":
        raise ContractError("unsupported model family")
    if record["pooling_class"] not in {"N0_complete", "N1_partial"}:
        raise ContractError("unsupported pooling class")
    if record["configuration_id"] != CANONICAL_CONFIGURATION_ID:
        raise ContractError("noncanonical Lemhi configuration")
    if record["configuration_sha256"] != CANONICAL_CONFIGURATION_SHA256:
        raise ContractError("canonical configuration hash mismatch")
    if _integer(record, "parameter_count", 1) > 50_000_000:
        raise ContractError("parameter ceiling exceeded")
    architecture = _object(record["architecture"], "architecture")
    _keys(architecture, {"latent_dim", "width", "depth", "tail_head"}, "architecture")
    if _integer(architecture, "latent_dim", 1) not in {32, 64}:
        raise ContractError("latent_dim is outside the frozen grid")
    if _integer(architecture, "width", 1) != 128:
        raise ContractError("width is outside the frozen grid")
    if _integer(architecture, "depth", 1) not in {2, 3}:
        raise ContractError("depth is outside the frozen grid")
    if architecture["tail_head"] not in {"lognormal", "gpd"}:
        raise ContractError("tail_head is outside the frozen grid")
    _sha256(record, "corpus_manifest_sha256")
    _sha256(record, "normalization_sha256")


def validate_checkpoint_record(value: Any) -> None:
    record = _object(value, "checkpoint record")
    _keys(
        record,
        {
            "schema_version",
            "checkpoint_id",
            "model_id",
            "epoch",
            "global_step",
            "training_seed",
            "payload_sha256",
            "payload_bytes",
            "state",
            "corpus_cursor",
            "created_utc",
        },
        "checkpoint record",
    )
    if record["schema_version"] != 1:
        raise ContractError("unsupported checkpoint schema_version")
    for key in ("checkpoint_id", "model_id", "created_utc"):
        _string(record, key)
    for key in ("epoch", "global_step", "training_seed"):
        _integer(record, key)
    _integer(record, "payload_bytes", 1)
    _sha256(record, "payload_sha256")
    state = _object(record["state"], "checkpoint state")
    _keys(
        state,
        {"model", "optimizer", "scheduler", "scaler", "rng", "sampler"},
        "checkpoint state",
    )
    if not all(value is True for value in state.values()):
        raise ContractError("checkpoint state entries must be true")
    cursor = _object(record["corpus_cursor"], "corpus cursor")
    _keys(cursor, {"epoch_order_sha256", "next_batch"}, "corpus cursor")
    _sha256(cursor, "epoch_order_sha256")
    _integer(cursor, "next_batch")


def validate_generation_record(value: Any) -> None:
    record = _object(value, "generation record")
    _keys(
        record,
        {
            "schema_version",
            "stream_id",
            "model_id",
            "model_sha256",
            "station_id",
            "regime",
            "burn_id",
            "member_id",
            "horizon_years",
            "rng",
            "row_count",
            "stream_sha256",
            "prefix_30_sha256",
        },
        "generation record",
    )
    if record["schema_version"] != 1:
        raise ContractError("unsupported generation schema_version")
    for key in ("stream_id", "model_id", "station_id"):
        _string(record, key)
    for key in ("model_sha256", "stream_sha256", "prefix_30_sha256"):
        _sha256(record, key)
    if record["regime"] not in REGIMES:
        raise ContractError("unknown regime")
    _integer(record, "burn_id")
    _integer(record, "member_id")
    if record["horizon_years"] != 100:
        raise ContractError("only a 100-year stream with nested 30-year prefix is valid")
    if _integer(record, "row_count", 1) not in {36524, 36525}:
        raise ContractError("100-year Gregorian row count is invalid")
    rng = _object(record["rng"], "generation rng")
    _keys(rng, {"algorithm", "key", "counter_layout"}, "generation rng")
    if rng["algorithm"] != "random123_philox4x32_10":
        raise ContractError("unsupported generation RNG")
    _string(rng, "key")
    if rng["counter_layout"] != "station,burn,member,date,draw":
        raise ContractError("generation counter layout mismatch")


def classify_runtime(ratio: float) -> str:
    """Classify an unrounded warm-generation runtime ratio."""
    if isinstance(ratio, bool) or not isinstance(ratio, (int, float)):
        raise ContractError("runtime ratio must be numeric")
    ratio = float(ratio)
    if not math.isfinite(ratio) or ratio < 0:
        raise ContractError("runtime ratio must be finite and nonnegative")
    if ratio < 5.0:
        return "PASS"
    if ratio < 10.0:
        return "WARN"
    return "FAIL"


def regime_is_applicable(value: Any) -> bool:
    """Apply the frozen paired-comparator and noninferiority rule."""
    record = _object(value, "regime evidence")
    _keys(record, {"regime", "horizons"}, "regime evidence")
    if record["regime"] not in REGIMES:
        raise ContractError("unknown regime")
    horizons = record["horizons"]
    if not isinstance(horizons, list) or len(horizons) != 2:
        raise ContractError("both horizons are required")
    seen = set()
    for horizon in horizons:
        horizon = _object(horizon, "horizon evidence")
        _keys(horizon, {"years", "comparators", "guards"}, "horizon evidence")
        years = _integer(horizon, "years", 1)
        seen.add(years)
        comparators = horizon["comparators"]
        if not isinstance(comparators, list) or len(comparators) != 2:
            raise ContractError("B0 and B1 comparator evidence are required")
        comparator_ids = set()
        for comparator in comparators:
            comparator = _object(comparator, "comparator evidence")
            _keys(comparator, {"id", "available", "delta", "upper_95"}, "comparator evidence")
            comparator_ids.add(comparator["id"])
            if comparator["available"] is not True:
                return False
            if _finite(comparator, "delta") > -MATERIAL_IMPROVEMENT:
                return False
            if _finite(comparator, "upper_95") > 0.0:
                return False
        if comparator_ids != {"B0", "B1"}:
            raise ContractError("comparator identities must be B0 and B1")
        guards = horizon["guards"]
        if not isinstance(guards, list) or len(guards) != 4:
            raise ContractError("all four noninferiority guards are required")
        guard_ids = set()
        for guard in guards:
            guard = _object(guard, "guard evidence")
            _keys(guard, {"family", "available", "upper_95"}, "guard evidence")
            guard_ids.add(guard["family"])
            if guard["available"] is not True or _finite(guard, "upper_95") > 0.0:
                return False
        if guard_ids != {"occurrence_spell", "aggregate_extreme", "compound_context", "winter_proxy"}:
            raise ContractError("guard family set mismatch")
    if seen != set(HORIZONS):
        raise ContractError("horizons must be exactly 30 and 100 years")
    return True


def select_candidate(candidates: Iterable[Mapping[str, Any]]) -> str | None:
    """Select at most one development candidate under frozen tie breaks."""
    survivors: list[tuple[tuple[Any, ...], str]] = []
    for candidate in candidates:
        candidate = _object(candidate, "candidate")
        _keys(
            candidate,
            {
                "candidate_id",
                "hard_gates_pass",
                "regimes",
                "primary_score",
                "runtime_class",
                "training_seed_sd",
                "runtime_ratio",
                "model_bytes",
            },
            "candidate",
        )
        candidate_id = _string(candidate, "candidate_id")
        if candidate["hard_gates_pass"] is not True:
            continue
        regimes = candidate["regimes"]
        if not isinstance(regimes, list):
            raise ContractError("regimes must be a list")
        applicable = [row["regime"] for row in regimes if regime_is_applicable(row)]
        if len(set(applicable)) < MINIMUM_APPLICABLE_REGIMES:
            continue
        if not (set(applicable) & {"hot_arid", "arid_boundary", "monsoonal_transition", "non_monsoonal_semi_arid"}):
            continue
        if not (set(applicable) & {"humid", "cold"}):
            continue
        runtime_class = candidate["runtime_class"]
        if runtime_class not in {"PASS", "WARN", "FAIL"}:
            raise ContractError("invalid runtime class")
        ratio = _finite(candidate, "runtime_ratio")
        if classify_runtime(ratio) != runtime_class or runtime_class == "FAIL":
            continue
        rank = (
            -len(set(applicable)),
            _finite(candidate, "primary_score"),
            0 if runtime_class == "PASS" else 1,
            _finite(candidate, "training_seed_sd"),
            ratio,
            _integer(candidate, "model_bytes", 1),
            candidate_id,
        )
        survivors.append((rank, candidate_id))
    return min(survivors)[1] if survivors else None
