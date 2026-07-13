#!/usr/bin/env python3
"""Reference implementation for the A5 observed-target bootstrap v1."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path
from typing import Any, Sequence

from jsonschema import Draft202012Validator


MASK64 = (1 << 64) - 1
UINT64_RANGE = 1 << 64
DOMAIN = b"cligen-a5-bootstrap-v1\0"
DEFAULT_GOLDEN = Path(__file__).with_name("observed-bootstrap-v1-golden.json")
EXPECTED_CANONICAL_HASH_ENCODING = "UTF-8 compact JSON via separators comma/colon, ensure_ascii true, no trailing newline"
EXPECTED_VECTOR_COLUMNS = [
    "year",
    "precipitation_total_integer_test_units",
    "tmax_integer_test_units",
    "tmin_integer_test_units",
]
EXPECTED_FIXED_GENERATED_MEANS = [40, 60, 80, 100, 120, 140, 160, 180]

GOLDEN_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "bootstrap_contract_version",
        "canonical_hash_encoding",
        "contract_id",
        "expected",
        "input",
        "parameters",
        "percentile",
        "prng",
        "seed_domain",
        "uncertainty_application",
    ],
    "properties": {
        "bootstrap_contract_version": {"const": 1},
        "canonical_hash_encoding": {"type": "string"},
        "contract_id": {
            "const": "cligen-a5-observed-circular-moving-block-bootstrap-v1"
        },
        "expected": {"$ref": "#/$defs/expected"},
        "input": {"$ref": "#/$defs/input"},
        "parameters": {"$ref": "#/$defs/parameters"},
        "percentile": {"$ref": "#/$defs/percentile"},
        "prng": {"$ref": "#/$defs/prng"},
        "seed_domain": {"$ref": "#/$defs/seed_domain"},
        "uncertainty_application": {"$ref": "#/$defs/uncertainty_application"},
    },
    "$defs": {
        "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "index_row": {
            "type": "array",
            "minItems": 16,
            "maxItems": 16,
            "items": {"type": "integer", "minimum": 0, "maximum": 15},
        },
        "expected": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "bootstrap_target_precipitation_mean_rationals_sha256",
                "crossed_eight_replicate_median_distance_nearest_rank_p025",
                "crossed_eight_replicate_median_distance_nearest_rank_p975",
                "crossed_eight_replicate_median_distance_rationals_sha256",
                "first_three_sampled_year_indices",
                "first_three_start_indices",
                "first_three_target_mean_and_crossed_distance_rationals",
                "replicate_precipitation_sum_nearest_rank_p025",
                "replicate_precipitation_sum_nearest_rank_p975",
                "replicate_precipitation_sums_sha256",
                "sampled_aligned_year_vectors_sha256",
                "sampled_year_indices_sha256",
                "seed_sha256",
                "seed_u64_big_endian",
                "seed_u64_hex",
                "source_aligned_year_vectors_sha256",
                "start_indices_sha256",
            ],
            "properties": {
                "bootstrap_target_precipitation_mean_rationals_sha256": {
                    "$ref": "#/$defs/sha256"
                },
                "crossed_eight_replicate_median_distance_nearest_rank_p025": {
                    "$ref": "#/$defs/rational"
                },
                "crossed_eight_replicate_median_distance_nearest_rank_p975": {
                    "$ref": "#/$defs/rational"
                },
                "crossed_eight_replicate_median_distance_rationals_sha256": {
                    "$ref": "#/$defs/sha256"
                },
                "first_three_sampled_year_indices": {
                    "type": "array",
                    "minItems": 3,
                    "maxItems": 3,
                    "items": {"$ref": "#/$defs/index_row"},
                },
                "first_three_start_indices": {
                    "type": "array",
                    "minItems": 3,
                    "maxItems": 3,
                    "items": {
                        "type": "array",
                        "minItems": 4,
                        "maxItems": 4,
                        "items": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 15,
                        },
                    },
                },
                "first_three_target_mean_and_crossed_distance_rationals": {
                    "type": "array",
                    "minItems": 3,
                    "maxItems": 3,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["crossed_distance", "target_mean"],
                        "properties": {
                            "crossed_distance": {"$ref": "#/$defs/rational"},
                            "target_mean": {"$ref": "#/$defs/rational"},
                        },
                    },
                },
                "replicate_precipitation_sum_nearest_rank_p025": {"type": "integer"},
                "replicate_precipitation_sum_nearest_rank_p975": {"type": "integer"},
                "replicate_precipitation_sums_sha256": {"$ref": "#/$defs/sha256"},
                "sampled_aligned_year_vectors_sha256": {"$ref": "#/$defs/sha256"},
                "sampled_year_indices_sha256": {"$ref": "#/$defs/sha256"},
                "seed_sha256": {"$ref": "#/$defs/sha256"},
                "seed_u64_big_endian": {
                    "type": "string",
                    "pattern": "^(0|[1-9][0-9]{0,19})$",
                },
                "seed_u64_hex": {
                    "type": "string",
                    "pattern": "^[0-9a-f]{16}$",
                },
                "source_aligned_year_vectors_sha256": {"$ref": "#/$defs/sha256"},
                "start_indices_sha256": {"$ref": "#/$defs/sha256"},
            },
        },
        "input": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "aligned_year_vector_columns",
                "aligned_year_vectors",
                "corpus_sha256",
                "fixed_generated_replicate_precipitation_means",
                "period_id",
                "source_id",
                "station_id",
            ],
            "properties": {
                "aligned_year_vector_columns": {
                    "type": "array",
                    "minItems": 4,
                    "maxItems": 4,
                    "items": {"type": "string"},
                },
                "aligned_year_vectors": {
                    "type": "array",
                    "minItems": 16,
                    "maxItems": 16,
                    "items": {
                        "type": "array",
                        "minItems": 4,
                        "maxItems": 4,
                        "items": {"type": "integer"},
                    },
                },
                "corpus_sha256": {"$ref": "#/$defs/sha256"},
                "fixed_generated_replicate_precipitation_means": {
                    "type": "array",
                    "minItems": 8,
                    "maxItems": 8,
                    "uniqueItems": True,
                    "items": {"type": "integer"},
                },
                "period_id": {"const": "evaluation"},
                "source_id": {"type": "string", "minLength": 1},
                "station_id": {
                    "type": "string",
                    "pattern": "^[a-z]{2}[0-9]{6}$",
                },
            },
        },
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "aligned_year_vector_unit",
                "block_length_years",
                "blocks_per_replicate",
                "replicates",
                "source_year_count",
                "starting_index_draw_order",
                "truncation",
            ],
            "properties": {
                "aligned_year_vector_unit": {"type": "string"},
                "block_length_years": {"const": 5},
                "blocks_per_replicate": {"const": 4},
                "replicates": {"const": 2000},
                "source_year_count": {"const": 16},
                "starting_index_draw_order": {"type": "string"},
                "truncation": {"type": "string"},
            },
        },
        "percentile": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "estimator",
                "formula",
                "p025_one_based_rank",
                "p975_one_based_rank",
            ],
            "properties": {
                "estimator": {"const": "empirical_inverse_cdf_nearest_rank_v1"},
                "formula": {"type": "string"},
                "p025_one_based_rank": {"const": 50},
                "p975_one_based_rank": {"const": 1950},
            },
        },
        "prng": {
            "type": "object",
            "additionalProperties": False,
            "required": ["bounded_integer", "initial_state", "next_u64", "prng_id"],
            "properties": {
                "bounded_integer": {"type": "string"},
                "initial_state": {"type": "string"},
                "next_u64": {"type": "string"},
                "prng_id": {"const": "splitmix64-v1"},
            },
        },
        "seed_domain": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "byte_concatenation",
                "domain_ascii_with_terminal_nul",
                "field_encoding",
                "hash",
                "seed_extraction",
            ],
            "properties": {
                "byte_concatenation": {"type": "string"},
                "domain_ascii_with_terminal_nul": {
                    "const": "cligen-a5-bootstrap-v1\\0"
                },
                "field_encoding": {"const": "ASCII bytes exactly as stored"},
                "hash": {"const": "SHA-256"},
                "seed_extraction": {"type": "string"},
            },
        },
        "rational": {
            "type": "array",
            "minItems": 2,
            "maxItems": 2,
            "prefixItems": [
                {"type": "integer"},
                {"type": "integer", "minimum": 1},
            ],
            "items": False,
        },
        "uncertainty_application": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "crossing",
                "decision_role",
                "distance",
                "generated_replicate_aggregation",
                "target_estimand",
                "year_relabeling",
            ],
            "properties": {
                "crossing": {"type": "string"},
                "decision_role": {"type": "string"},
                "distance": {"type": "string"},
                "generated_replicate_aggregation": {"type": "string"},
                "target_estimand": {"type": "string"},
                "year_relabeling": {"type": "string"},
            },
        },
    },
}

EXPECTED_PARAMETERS = {
    "aligned_year_vector_unit": "entire complete aligned year vector; components are never resampled separately",
    "block_length_years": 5,
    "blocks_per_replicate": 4,
    "replicates": 2000,
    "source_year_count": 16,
    "starting_index_draw_order": "replicate-major then block-major; draw four starts for replicate 0, then four for replicate 1, continuing through replicate 1999",
    "truncation": "concatenate four circular five-year blocks in draw order and retain the first 16 year vectors",
}
EXPECTED_PERCENTILE = {
    "estimator": "empirical_inverse_cdf_nearest_rank_v1",
    "formula": "sorted_values[ceil(p*n)-1] for 0 < p <= 1",
    "p025_one_based_rank": 50,
    "p975_one_based_rank": 1950,
}
EXPECTED_PRNG = {
    "bounded_integer": "draw u64 until u < 2^64 - (2^64 mod bound), then return u mod bound",
    "initial_state": "seed_u64_big_endian",
    "next_u64": "state=(state+0x9e3779b97f4a7c15) mod 2^64; z=state; z=((z xor (z>>30))*0xbf58476d1ce4e5b9) mod 2^64; z=((z xor (z>>27))*0x94d049bb133111eb) mod 2^64; return z xor (z>>31)",
    "prng_id": "splitmix64-v1",
}
EXPECTED_SEED_DOMAIN = {
    "byte_concatenation": "domain || corpus_sha256 || source_id || station_id || period_id with no separators after the domain NUL",
    "domain_ascii_with_terminal_nul": "cligen-a5-bootstrap-v1\\0",
    "field_encoding": "ASCII bytes exactly as stored",
    "hash": "SHA-256",
    "seed_extraction": "digest bytes 0 through 7 interpreted as an unsigned 64-bit big-endian integer",
}
EXPECTED_UNCERTAINTY_APPLICATION = {
    "crossing": "for each of 2000 target bootstrap indices, cross the resampled target with all eight fixed generated values before replicate aggregation",
    "decision_role": "report_only; endpoints cannot change deterministic promotion pass or fail",
    "distance": "absolute_relative abs(generated-target)/target",
    "generated_replicate_aggregation": "conventional median; arithmetic mean of the fourth and fifth sorted distances for eight values",
    "target_estimand": "mean of precipitation_total_integer_test_units across all 16 relabelled bootstrap positions",
    "year_relabeling": "sampled source years remain in draw order and are relabelled bootstrap positions 0 through 15; original year labels are not sorted or grouped",
}


class ContractError(ValueError):
    """The golden vector or contract is inconsistent."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def strict_json_loads(text: str) -> Any:
    def pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ContractError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def reject_constant(value: str) -> Any:
        raise ContractError(f"non-finite JSON token: {value}")

    def parse_finite_float(value: str) -> float:
        parsed = float(value)
        if not math.isfinite(parsed):
            raise ContractError(f"JSON float overflows finite range: {value}")
        return parsed

    return json.loads(
        text,
        object_pairs_hook=pairs_hook,
        parse_constant=reject_constant,
        parse_float=parse_finite_float,
    )


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def sha256_hex(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def seed_digest(
    corpus_sha256: str, source_id: str, station_id: str, period_id: str
) -> bytes:
    fields = (corpus_sha256, source_id, station_id, period_id)
    try:
        suffix = b"".join(field.encode("ascii") for field in fields)
    except UnicodeEncodeError as error:
        raise ContractError("seed fields must be ASCII") from error
    return hashlib.sha256(DOMAIN + suffix).digest()


class SplitMix64V1:
    """Pinned SplitMix64 transition and rejection-sampled bounded draw."""

    def __init__(self, seed: int) -> None:
        require(0 <= seed <= MASK64, "seed outside u64")
        self.state = seed

    def next_u64(self) -> int:
        self.state = (self.state + 0x9E3779B97F4A7C15) & MASK64
        value = self.state
        value = ((value ^ (value >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
        value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & MASK64
        return (value ^ (value >> 31)) & MASK64

    def bounded(self, bound: int) -> int:
        require(1 <= bound <= UINT64_RANGE, "bound outside 1..2^64")
        limit = UINT64_RANGE - (UINT64_RANGE % bound)
        while True:
            value = self.next_u64()
            if value < limit:
                return value % bound


def bootstrap_indices(
    seed: int, n_years: int, block_length: int, replicates: int
) -> tuple[list[list[int]], list[list[int]]]:
    require(n_years == 16, "v1 evaluation contract requires n=16")
    require(block_length == 5, "v1 evaluation contract requires L=5")
    require(replicates == 2000, "v1 evaluation contract requires 2,000 replicates")
    blocks = (n_years + block_length - 1) // block_length
    require(blocks == 4, "ceil(n/L) must equal four")
    generator = SplitMix64V1(seed)
    starts: list[list[int]] = []
    sampled: list[list[int]] = []
    for _replicate in range(replicates):
        replicate_starts = [generator.bounded(n_years) for _block in range(blocks)]
        indices = [
            (start + offset) % n_years
            for start in replicate_starts
            for offset in range(block_length)
        ][:n_years]
        starts.append(replicate_starts)
        sampled.append(indices)
    return starts, sampled


def nearest_rank(values: Sequence[Any], numerator: int, denominator: int) -> Any:
    require(values, "nearest-rank input is empty")
    require(0 < numerator <= denominator, "percentile outside (0,1]")
    ordered = sorted(values)
    rank = (numerator * len(ordered) + denominator - 1) // denominator
    return ordered[rank - 1]


def rational_pair(value: Fraction) -> list[int]:
    return [value.numerator, value.denominator]


def validate_golden(golden: dict[str, Any]) -> dict[str, Any]:
    Draft202012Validator.check_schema(GOLDEN_SCHEMA)
    errors = sorted(
        Draft202012Validator(GOLDEN_SCHEMA).iter_errors(golden),
        key=lambda error: list(error.path),
    )
    require(not errors, f"schema: {errors[0].message}" if errors else "")
    require(
        golden["canonical_hash_encoding"] == EXPECTED_CANONICAL_HASH_ENCODING,
        "canonical hash encoding changed",
    )
    require(golden["parameters"] == EXPECTED_PARAMETERS, "parameter contract changed")
    require(golden["percentile"] == EXPECTED_PERCENTILE, "percentile contract changed")
    require(golden["prng"] == EXPECTED_PRNG, "PRNG contract changed")
    require(golden["seed_domain"] == EXPECTED_SEED_DOMAIN, "seed domain changed")
    require(
        golden["uncertainty_application"] == EXPECTED_UNCERTAINTY_APPLICATION,
        "uncertainty application changed",
    )

    source = golden["input"]
    require(
        source["aligned_year_vector_columns"] == EXPECTED_VECTOR_COLUMNS,
        "aligned-year vector columns changed",
    )
    require(
        source["fixed_generated_replicate_precipitation_means"]
        == EXPECTED_FIXED_GENERATED_MEANS,
        "fixed generated replicate values changed",
    )
    expected = golden["expected"]
    digest = seed_digest(
        source["corpus_sha256"],
        source["source_id"],
        source["station_id"],
        source["period_id"],
    )
    seed = int.from_bytes(digest[:8], byteorder="big", signed=False)
    require(digest.hex() == expected["seed_sha256"], "seed digest mismatch")
    require(seed == int(expected["seed_u64_big_endian"]), "big-endian seed mismatch")
    require(f"{seed:016x}" == expected["seed_u64_hex"], "seed hexadecimal mismatch")

    starts, indices = bootstrap_indices(seed, 16, 5, 2000)
    vectors = source["aligned_year_vectors"]
    sampled_vectors = [[vectors[index] for index in row] for row in indices]
    precipitation_sums = [sum(vector[1] for vector in row) for row in sampled_vectors]
    target_means = [Fraction(value, 16) for value in precipitation_sums]
    crossed_distances = []
    for target in target_means:
        distances = sorted(
            abs(Fraction(generated) - target) / target
            for generated in EXPECTED_FIXED_GENERATED_MEANS
        )
        crossed_distances.append((distances[3] + distances[4]) / 2)
    target_mean_pairs = [rational_pair(value) for value in target_means]
    crossed_distance_pairs = [rational_pair(value) for value in crossed_distances]

    require(
        starts[:3] == expected["first_three_start_indices"], "start draw order mismatch"
    )
    require(
        indices[:3] == expected["first_three_sampled_year_indices"],
        "circular block/truncation mismatch",
    )
    checks = {
        "source_aligned_year_vectors_sha256": sha256_hex(vectors),
        "start_indices_sha256": sha256_hex(starts),
        "sampled_year_indices_sha256": sha256_hex(indices),
        "sampled_aligned_year_vectors_sha256": sha256_hex(sampled_vectors),
        "replicate_precipitation_sums_sha256": sha256_hex(precipitation_sums),
        "bootstrap_target_precipitation_mean_rationals_sha256": sha256_hex(
            target_mean_pairs
        ),
        "crossed_eight_replicate_median_distance_rationals_sha256": sha256_hex(
            crossed_distance_pairs
        ),
    }
    for field, actual in checks.items():
        require(actual == expected[field], f"{field} mismatch")
    require(
        nearest_rank(precipitation_sums, 1, 40)
        == expected["replicate_precipitation_sum_nearest_rank_p025"],
        "p025 nearest-rank mismatch",
    )
    require(
        nearest_rank(precipitation_sums, 39, 40)
        == expected["replicate_precipitation_sum_nearest_rank_p975"],
        "p975 nearest-rank mismatch",
    )
    first_three_application = [
        {"target_mean": target, "crossed_distance": distance}
        for target, distance in zip(
            target_mean_pairs[:3], crossed_distance_pairs[:3], strict=True
        )
    ]
    require(
        first_three_application
        == expected["first_three_target_mean_and_crossed_distance_rationals"],
        "target/generated crossing order mismatch",
    )
    require(
        rational_pair(nearest_rank(crossed_distances, 1, 40))
        == expected["crossed_eight_replicate_median_distance_nearest_rank_p025"],
        "crossed-distance p025 mismatch",
    )
    require(
        rational_pair(nearest_rank(crossed_distances, 39, 40))
        == expected["crossed_eight_replicate_median_distance_nearest_rank_p975"],
        "crossed-distance p975 mismatch",
    )
    return {"replicates": len(indices), "draws_without_rejection": len(starts) * 4}


def expect_rejected(name: str, golden: dict[str, Any], mutate: Any) -> str:
    candidate = copy.deepcopy(golden)
    mutate(candidate)
    try:
        validate_golden(candidate)
    except (ContractError, KeyError, TypeError) as error:
        return f"{name}: {error}"
    raise AssertionError(f"negative vector unexpectedly passed: {name}")


def mutation_tests(golden: dict[str, Any]) -> list[str]:
    tests = [
        (
            "wrong_seed_endianness",
            lambda item: item["expected"].__setitem__("seed_u64_big_endian", "1"),
        ),
        (
            "wrong_start_draw",
            lambda item: item["expected"]["first_three_start_indices"][0].__setitem__(
                0, 0
            ),
        ),
        (
            "wrong_block_truncation_hash",
            lambda item: item["expected"].__setitem__(
                "sampled_year_indices_sha256", "0" * 64
            ),
        ),
        (
            "split_aligned_vector",
            lambda item: item["input"]["aligned_year_vectors"][0].__setitem__(1, 2),
        ),
        (
            "wrong_percentile",
            lambda item: item["expected"].__setitem__(
                "replicate_precipitation_sum_nearest_rank_p025", 0
            ),
        ),
        (
            "wrong_prng",
            lambda item: item["prng"].__setitem__("prng_id", "unspecified"),
        ),
        (
            "wrong_block_count",
            lambda item: item["parameters"].__setitem__("blocks_per_replicate", 3),
        ),
        ("extra_field", lambda item: item.__setitem__("analyst_choice", True)),
        (
            "hash_encoding_label",
            lambda item: item.__setitem__("canonical_hash_encoding", "unspecified"),
        ),
        (
            "vector_column_labels",
            lambda item: item["input"].__setitem__(
                "aligned_year_vector_columns", ["a", "b", "c", "d"]
            ),
        ),
        (
            "uncertainty_crossing",
            lambda item: item["uncertainty_application"].__setitem__(
                "crossing", "pair_target_and_generated_by_modulo_index"
            ),
        ),
        (
            "uncertainty_decision_role",
            lambda item: item["uncertainty_application"].__setitem__(
                "decision_role", "changes_promotion"
            ),
        ),
        (
            "bootstrap_year_relabeling",
            lambda item: item["uncertainty_application"].__setitem__(
                "year_relabeling", "sort_original_year_labels"
            ),
        ),
        (
            "fixed_generated_replicates",
            lambda item: item["input"][
                "fixed_generated_replicate_precipitation_means"
            ].__setitem__(0, 41),
        ),
        (
            "crossed_distance_endpoint",
            lambda item: item["expected"].__setitem__(
                "crossed_eight_replicate_median_distance_nearest_rank_p025", [0, 1]
            ),
        ),
    ]
    return [expect_rejected(name, golden, mutate) for name, mutate in tests]


def parser_negative_tests() -> list[str]:
    inputs = {
        "duplicate_key": '{"a":1,"a":2}',
        "nan": '{"a":NaN}',
        "positive_infinity": '{"a":Infinity}',
        "negative_infinity": '{"a":-Infinity}',
        "positive_float_overflow": '{"a":1e400}',
        "negative_float_overflow": '{"a":-1e400}',
    }
    results: list[str] = []
    for name, text in inputs.items():
        try:
            strict_json_loads(text)
        except (ContractError, ValueError) as error:
            results.append(f"{name}: {error}")
            continue
        raise AssertionError(f"invalid JSON unexpectedly passed: {name}")
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--golden", type=Path, default=DEFAULT_GOLDEN)
    args = parser.parse_args()
    golden_bytes = args.golden.read_bytes()
    golden = strict_json_loads(golden_bytes.decode("utf-8"))
    summary = validate_golden(golden)
    negatives = mutation_tests(golden)
    parser_negatives = parser_negative_tests()
    print(
        json.dumps(
            {
                "golden_sha256": hashlib.sha256(golden_bytes).hexdigest(),
                "negative_vectors": len(negatives) + len(parser_negatives),
                "status": "pass",
                **summary,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
