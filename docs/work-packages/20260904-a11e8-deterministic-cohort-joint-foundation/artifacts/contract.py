#!/usr/bin/env python3
"""Deterministic reference semantics for the A11E8 scaffold."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "execution-manifest-v1.json"
SCHEMA = HERE / "execution-manifest-v1.schema.json"
DOMAIN = b"cligen-rs/a11e8/thermal-state-v1\0"
MODEL_ORDER = ("faithful_5_32_3", "a11_joint_residual_thermal_rank1_v1")
MASK64 = 0xFFFF_FFFF_FFFF_FFFF
SELECTOR_FIELDS = (
    "annual_temperature_dispersion_error_q",
    "temperature_cross_month_correlation_rmse_q",
    "annual_temperature_lag1_error_q",
    "annual_temperature_low_frequency_error_q",
    "model_ordinal",
    "candidate_index",
)


class ContractError(ValueError):
    """A malformed deterministic cohort contract or score."""


class SplitMix64BoxMullerV1:
    """Frozen SplitMix64 transition with one cosine normal per two draws."""

    def __init__(self, state: int):
        if type(state) is not int or not 0 <= state <= MASK64:
            raise ContractError("SplitMix64 state is outside u64")
        self.state = state

    def next_u64(self) -> int:
        self.state = (self.state + 0x9E37_79B9_7F4A_7C15) & MASK64
        value = self.state
        value = ((value ^ (value >> 30)) * 0xBF58_476D_1CE4_E5B9) & MASK64
        value = ((value ^ (value >> 27)) * 0x94D0_49BB_1331_11EB) & MASK64
        return (value ^ (value >> 31)) & MASK64

    def open_unit(self) -> float:
        return ((self.next_u64() >> 11) + 0.5) * (1.0 / float(1 << 53))

    def standard_normal(self) -> float:
        first = self.open_unit()
        second = self.open_unit()
        return math.sqrt(-2.0 * math.log(first)) * math.cos(math.tau * second)


def annual_states(seed: int, years: int = 16) -> list[float]:
    if type(years) is not int or years <= 0:
        raise ContractError("year count must be positive")
    generator = SplitMix64BoxMullerV1(seed)
    return [generator.standard_normal() for _ in range(years)]


def canonical_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def validate_manifest(value: Any) -> dict[str, Any]:
    schema = json.loads(SCHEMA.read_text())
    if not isinstance(value, dict) or set(value) != set(schema["required"]):
        raise ContractError("manifest fields differ from the strict contract")
    for name, rule in schema["properties"].items():
        if "const" in rule and value[name] != rule["const"]:
            raise ContractError(f"manifest constant differs: {name}")
    dependencies = value["dependencies"]
    dependency_rule = schema["properties"]["dependencies"]
    if not isinstance(dependencies, dict) or set(dependencies) != set(
        dependency_rule["required"]
    ):
        raise ContractError("dependency fields differ from the strict contract")
    for name, rule in dependency_rule["properties"].items():
        if dependencies[name] != rule["const"]:
            raise ContractError(f"dependency digest differs: {name}")
    cohorts = value["cohorts"]
    if len(cohorts) != 4 or [row.get("cohort_id") for row in cohorts] != list(range(4)):
        raise ContractError("cohorts must be ordered 0 through 3")
    burns: list[int] = []
    for row in cohorts:
        root = row.get("root_seed_hex")
        member_burns = row.get("burns")
        if not isinstance(root, str) or len(root) != 18 or not root.startswith("0x"):
            raise ContractError("root seed must be 0x plus sixteen lowercase hex digits")
        try:
            parsed_root = int(root[2:], 16)
        except ValueError as error:
            raise ContractError("root seed is not hexadecimal") from error
        if root != f"0x{parsed_root:016x}":
            raise ContractError("root seed spelling is not canonical")
        if not isinstance(member_burns, list) or len(member_burns) != value["cohort_size"]:
            raise ContractError("cohort burn count differs")
        if any(type(burn) is not int or not 0 <= burn <= 2_147_483_647 for burn in member_burns):
            raise ContractError("burn is outside the faithful signed-32-bit domain")
        burns.extend(member_burns)
    if len(burns) != 32 or len(set(burns)) != 32:
        raise ContractError("the complete burn schedule must contain 32 unique values")
    if value["thermal_state_seed_domain"] != DOMAIN[:-1].decode() + "\\0":
        raise ContractError("seed-domain display spelling differs")
    return value


def derive_thermal_seed(
    station_id: str, model_id: str, root_seed_hex: str, candidate_index: int
) -> int:
    if not station_id or not station_id.isascii() or "\0" in station_id:
        raise ContractError("station ID must be nonempty NUL-free ASCII")
    if model_id != MODEL_ORDER[1]:
        raise ContractError("thermal seed is defined only for the candidate model")
    if type(candidate_index) is not int or not 0 <= candidate_index <= 0xFFFF_FFFF:
        raise ContractError("candidate index is outside u32")
    try:
        root_seed = int(root_seed_hex.removeprefix("0x"), 16)
    except ValueError as error:
        raise ContractError("root seed is not hexadecimal") from error
    if root_seed_hex != f"0x{root_seed:016x}":
        raise ContractError("root seed spelling is not canonical u64")
    preimage = (
        DOMAIN
        + station_id.encode("ascii")
        + b"\0"
        + model_id.encode("ascii")
        + b"\0"
        + root_seed.to_bytes(8, "big")
        + candidate_index.to_bytes(4, "big")
    )
    return int.from_bytes(hashlib.sha256(preimage).digest()[:8], "big")


def quantize_score(value: float, units_per_one: int = 1_000_000_000) -> int:
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0.0:
        raise ContractError("score input must be finite and nonnegative")
    if type(units_per_one) is not int or units_per_one <= 0:
        raise ContractError("quantization scale must be a positive integer")
    scaled = Decimal.from_float(float(value)) * Decimal(units_per_one)
    result = int(scaled.to_integral_value(rounding=ROUND_HALF_EVEN))
    if result > 0x7FFF_FFFF_FFFF_FFFF:
        raise ContractError("quantized score exceeds signed 64-bit range")
    return result


def select_candidate(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        raise ContractError("candidate cohort is empty")
    identities: set[tuple[int, int]] = set()
    for record in records:
        required = {
            "model_id",
            "model_ordinal",
            "candidate_index",
            "physical_failure_count",
            "monthly_temperature_mean_error_q",
            *SELECTOR_FIELDS[:-2],
        }
        if not isinstance(record, dict) or set(record) != required:
            raise ContractError("candidate score fields differ")
        ordinal = record["model_ordinal"]
        index = record["candidate_index"]
        if type(ordinal) is not int or not 0 <= ordinal < len(MODEL_ORDER):
            raise ContractError("model ordinal is invalid")
        if record["model_id"] != MODEL_ORDER[ordinal]:
            raise ContractError("model ID and ordinal disagree")
        if type(index) is not int or not 0 <= index < 8:
            raise ContractError("candidate index is outside the frozen cohort")
        identity = (ordinal, index)
        if identity in identities:
            raise ContractError("candidate identity is duplicated")
        identities.add(identity)
        integer_fields = required - {"model_id"}
        if any(type(record[name]) is not int or record[name] < 0 for name in integer_fields):
            raise ContractError("candidate scores must be nonnegative integers")
    expected_identities = (
        {(0, index) for index in range(8)}
        if len(records) == 8
        else {(ordinal, index) for ordinal in range(2) for index in range(8)}
        if len(records) == 16
        else set()
    )
    if identities != expected_identities:
        raise ContractError("candidate cohort is incomplete or has the wrong model composition")
    faithful_monthly = sorted(
        record["monthly_temperature_mean_error_q"]
        for record in records
        if record["model_ordinal"] == 0
    )
    faithful_median = Decimal(faithful_monthly[3] + faithful_monthly[4]) / 2
    monthly_threshold_q = int(
        (faithful_median * Decimal(105) / 100).to_integral_value(
            rounding=ROUND_HALF_EVEN
        )
    )
    eligible = [
        record
        for record in records
        if record["physical_failure_count"] == 0
        and record["monthly_temperature_mean_error_q"] <= monthly_threshold_q
    ]
    if not eligible:
        raise ContractError("cohort contains no eligible candidate")
    return min(eligible, key=lambda row: tuple(row[name] for name in SELECTOR_FIELDS))


def vectors() -> dict[str, Any]:
    manifest = validate_manifest(json.loads(MANIFEST.read_text()))
    cohort = manifest["cohorts"][0]
    first_seed = derive_thermal_seed(
        "az026481", MODEL_ORDER[1], cohort["root_seed_hex"], 0
    )
    states = annual_states(first_seed)
    return {
        "manifest_sha256": canonical_digest(manifest),
        "thermal_seed_station_az026481_candidate_0": first_seed,
        "thermal_seed_station_az026481_candidate_7": derive_thermal_seed(
            "az026481", MODEL_ORDER[1], cohort["root_seed_hex"], 7
        ),
        "thermal_state_candidate_0_first": states[0],
        "thermal_state_candidate_0_last": states[-1],
        "thermal_state_candidate_0_sha256": canonical_digest(states),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-manifest", action="store_true")
    parser.add_argument("--vectors", action="store_true")
    args = parser.parse_args()
    if args.validate_manifest:
        print(canonical_digest(validate_manifest(json.loads(MANIFEST.read_text()))))
        return
    if args.vectors:
        print(json.dumps(vectors(), indent=2, sort_keys=True))
        return
    parser.error("choose --validate-manifest or --vectors")


if __name__ == "__main__":
    main()
