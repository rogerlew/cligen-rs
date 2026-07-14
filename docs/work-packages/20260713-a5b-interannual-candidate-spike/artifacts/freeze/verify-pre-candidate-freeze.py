#!/usr/bin/env python3
"""Freeze and verify every A5b contract before candidate output exists."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[5]
PACKAGE = Path(__file__).resolve().parents[2]
A5A = ROOT / "docs/work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts"

ANALYSIS_HELPER_SOURCES = (
    "Cargo.lock",
    "Cargo.toml",
    "rust-toolchain.toml",
    "crates/cligen/Cargo.toml",
    "crates/cligen/src/lib.rs",
    "crates/cligen/src/bin/cligen-quality-estimator.rs",
    "crates/cligen/src/quality/estimators.rs",
    "crates/cligen/src/quality/mod.rs",
    "docs/work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts/corpus/build_targets.py",
    "docs/work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts/corpus/corpus_common.py",
    "docs/work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts/corpus/corpus-config-v1.json",
)
RELEASE_ESTIMATOR = ROOT / "target/release/cligen-quality-estimator"
RELEASE_ESTIMATOR_BUILD_COMMAND = (
    "cargo",
    "build",
    "--locked",
    "--offline",
    "--release",
    "--bin",
    "cligen-quality-estimator",
)
RELEASE_ESTIMATOR_SHA256 = (
    "b2c9175101bcd109c52bc67b3e91c32fcffcf7b89ff543616376d6651b25b1ad"
)
RELEASE_ESTIMATOR_BYTES = 619_040
FORBIDDEN_ESTIMATOR_BUILD_ENV = (
    "RUSTFLAGS",
    "CARGO_ENCODED_RUSTFLAGS",
    "RUSTC_WRAPPER",
    "RUSTC_WORKSPACE_WRAPPER",
    "CARGO_TARGET_DIR",
    "CARGO_BUILD_TARGET",
)

PINNED_A5A = {
    "docs/specifications/a5-climate-gate-metrics-v1.json":
        "37d2e36fe84a7fafbc2dafdea553a5702fe94677de23a6ba45ac4a4946572d95",
    "docs/specifications/a5-climate-gate-metrics-v1.schema.json":
        "f17b6a3896df1226b60a6e1f181089568cab918488d6564caa4ec12baf83be2c",
    "docs/work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts/verify-a5-climate-gate-metrics-v1.py":
        "ae1ef7f06b4afef94910af656f2077ee2029698a42e9223f3a8099a61dac1ac0",
    "docs/work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts/observed-bootstrap-v1.py":
        "d154773bb8bd5265e8423360b69fc6acb0cec8cc64280cdee5c1ac705df8d649",
    "docs/work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts/observed-bootstrap-v1-golden.json":
        "d38a730371a847e78fb9563821ea7efffa24f364787f902f555634a32f8c2ec2",
    "docs/specifications/a5-wepp-response-v1.schema.json":
        "7d006023684f2079ce09e5ab1af21e1154a417eb4295ebf1a02c40d7f7a2e70d",
    "docs/work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts/wepp-response-protocol.md":
        "9cd770d18c04dfde877c91e03304697b107d117bf2e52cc94f1f83e3d99c5800",
    "docs/work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts/verify-wepp-response-schema.py":
        "05e7a085f146e264c3b34e3f7c04f498f0f4d3dd0c9b0cd17a0f8176221b683b",
    "docs/work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts/baseline-run-manifest-v1.json":
        "e6e12a08b7d552edd45481b929271af87530d2821b9b51d5cec066dc76867cbc",
    "docs/work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts/baseline-analysis-v1.json":
        "7892cc2d8931623154c33f854db1170e46749e741d08a3843205131329934733",
    "docs/work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts/baseline-evidence-v1.tar.gz":
        "2fca565b8c3f83632e73050984dce0c619352ac4bb76deed86fb3928f8de15fe",
    "docs/work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts/verify-baseline-evidence.py":
        "9a3fbdb4d35ec693db6bad916b1cb941c3c3ebec93340a05899f103f269b32f1",
    "docs/work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts/baseline-run-manifest-v1.schema.json":
        "54b2ac2a780efcde70c403d75a0a42899200c315a0d47dd6927959649f03c450",
    "docs/work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts/baseline-analysis-v1.schema.json":
        "0b0c1558f8bdc557855a7442315796d45bfddd56ff9528bd5d5d2905af0d50ba",
}

NEW_CONTRACTS = [
    "docs/work-packages/20260713-a5b-interannual-candidate-spike/package.md",
    "docs/work-packages/20260713-a5b-interannual-candidate-spike/artifacts/freeze/verify-pre-candidate-freeze.py",
    "docs/work-packages/20260713-a5b-interannual-candidate-spike/artifacts/freeze/verify-accepted-a5a-baseline.py",
    "docs/work-packages/20260713-a5b-coefficient-source-assessment/artifacts/daily-source-assessment.md",
    "docs/work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts/a5b-pre-registration.md",
    "docs/specifications/SPEC-A5-EVALUATION.md",
    "docs/specifications/SPEC-A5B-CANDIDATES.md",
    "docs/specifications/station-document.schema.json",
    "docs/specifications/a5b-augmented-station-v1.schema.json",
    "docs/specifications/a5b-overlay-plan-v1.schema.json",
    "docs/specifications/a5b-run-record-v1.schema.json",
    "docs/specifications/a5b-candidate-evidence-v1.schema.json",
    "docs/specifications/quality-report-s2-m3.schema.json",
    "docs/specifications/provenance-v1.schema.json",
    "crates/cligen/src/bin/cligen-a5b-overlay.rs",
    "docs/work-packages/20260713-a5b-interannual-candidate-spike/artifacts/fit/fit-a5b-models.py",
    "docs/work-packages/20260713-a5b-interannual-candidate-spike/artifacts/runtime/generate-a5b-plan.py",
    "docs/work-packages/20260713-a5b-interannual-candidate-spike/artifacts/runtime/run-a5b-matrix.py",
    "docs/work-packages/20260713-a5b-interannual-candidate-spike/artifacts/runtime/verify-a5b-evidence.py",
    "docs/work-packages/20260713-a5b-interannual-candidate-spike/artifacts/climate/analyze-a5b.py",
    "docs/work-packages/20260713-a5b-interannual-candidate-spike/artifacts/wepp/wepp-campaign-v1.md",
    "docs/work-packages/20260713-a5b-interannual-candidate-spike/artifacts/wepp/run-wepp-matrix.py",
    "docs/work-packages/20260713-a5b-interannual-candidate-spike/artifacts/wepp/analyze-wepp.py",
    "docs/work-packages/20260713-a5b-interannual-candidate-spike/artifacts/freeze/pre-output-amendments.md",
    *ANALYSIS_HELPER_SOURCES,
]

SCHEMAS = [
    "docs/specifications/a5b-augmented-station-v1.schema.json",
    "docs/specifications/a5b-overlay-plan-v1.schema.json",
    "docs/specifications/a5b-run-record-v1.schema.json",
    "docs/specifications/a5b-candidate-evidence-v1.schema.json",
]

VERIFIER_COMMANDS = [
    [sys.executable, str(A5A / "verify-a5-climate-gate-metrics-v1.py")],
    [sys.executable, str(A5A / "observed-bootstrap-v1.py")],
    [sys.executable, str(A5A / "verify-wepp-response-schema.py")],
    [
        sys.executable,
        str(PACKAGE / "artifacts/freeze/verify-accepted-a5a-baseline.py"),
        "--self-test",
    ],
    [sys.executable, str(A5A / "corpus/verify_offline.py")],
    [
        sys.executable,
        str(PACKAGE / "artifacts/fit/fit-a5b-models.py"),
        "--self-test",
    ],
    [
        sys.executable,
        str(PACKAGE / "artifacts/runtime/generate-a5b-plan.py"),
        "--self-test",
    ],
    [
        sys.executable,
        str(PACKAGE / "artifacts/runtime/run-a5b-matrix.py"),
        "--self-test",
    ],
    [
        sys.executable,
        str(PACKAGE / "artifacts/runtime/verify-a5b-evidence.py"),
        "--self-test",
    ],
    [
        sys.executable,
        str(PACKAGE / "artifacts/climate/analyze-a5b.py"),
        "--self-test",
    ],
    [
        sys.executable,
        str(PACKAGE / "artifacts/wepp/run-wepp-matrix.py"),
        "--self-test",
    ],
    [
        sys.executable,
        str(PACKAGE / "artifacts/wepp/analyze-wepp.py"),
        "--self-test",
    ],
    ["cargo", "test", "--bin", "cligen-a5b-overlay"],
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def strict_load(path: Path) -> Any:
    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in values:
            if key in result:
                raise ValueError(f"duplicate JSON key {key!r} in {path}")
            result[key] = value
        return result

    def nonfinite(token: str) -> None:
        raise ValueError(f"nonfinite JSON token {token!r} in {path}")

    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=pairs,
        parse_constant=nonfinite,
    )


def load_bootstrap_module() -> Any:
    path = A5A / "observed-bootstrap-v1.py"
    spec = importlib.util.spec_from_file_location("a5_bootstrap_v1", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def additional_bootstrap_vectors() -> dict[str, Any]:
    module = load_bootstrap_module()
    golden = strict_load(A5A / "observed-bootstrap-v1-golden.json")
    first = golden["expected"]["first_three_sampled_year_indices"][0]
    weighted_order_statistic = sum((index + 1) * value for index, value in enumerate(first))
    sorted_statistic = sum(
        (index + 1) * value for index, value in enumerate(sorted(first))
    )
    if weighted_order_statistic == sorted_statistic:
        raise AssertionError("order-sensitive bootstrap vector does not detect sorting")

    class Injected(module.SplitMix64V1):
        def __init__(self, values: list[int]) -> None:
            self.values = iter(values)
            self.state = 0

        def next_u64(self) -> int:
            return next(self.values)

    rejected = (1 << 64) - 1
    accepted = 7
    bounded = Injected([rejected, accepted]).bounded(10)
    modulo_only = rejected % 10
    if bounded != 7 or modulo_only == bounded:
        raise AssertionError("non-divisor vector does not distinguish rejection")
    return {
        "order_sensitive": {
            "sample_indices": first,
            "weighted_statistic": weighted_order_statistic,
            "sorted_weighted_statistic": sorted_statistic,
        },
        "non_divisor_bounded_draw": {
            "bound": 10,
            "injected_draws": [str(rejected), str(accepted)],
            "rejection_sampled_result": bounded,
            "modulo_first_draw_result": modulo_only,
        },
    }


def check_schemas() -> dict[str, str]:
    identities: dict[str, str] = {}
    for relative in SCHEMAS:
        path = ROOT / relative
        schema = strict_load(path)
        Draft202012Validator.check_schema(schema)
        identities[relative] = sha256(path)
    return identities


def run_verifiers() -> list[dict[str, Any]]:
    results = []
    for command in VERIFIER_COMMANDS:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"verifier failed: {command}\n{completed.stdout}\n{completed.stderr}"
            )
        output = (completed.stdout + completed.stderr).encode("utf-8")
        results.append(
            {
                "command": command,
                "returncode": completed.returncode,
                "output_sha256": hashlib.sha256(output).hexdigest(),
                "last_line": (completed.stdout + completed.stderr).strip().splitlines()[-1],
            }
        )
    return results


def command_output(command: list[str]) -> str:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"build-metadata command failed: {command}\n"
            f"{completed.stdout}\n{completed.stderr}"
        )
    return completed.stdout.strip()


def release_estimator_evidence() -> dict[str, Any]:
    present = [name for name in FORBIDDEN_ESTIMATOR_BUILD_ENV if os.environ.get(name)]
    if present:
        raise RuntimeError(
            f"release quality-estimator build environment is not clean: {present}"
        )
    completed = subprocess.run(
        list(RELEASE_ESTIMATOR_BUILD_COMMAND),
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "release quality-estimator build failed:\n"
            f"{completed.stdout}\n{completed.stderr}"
        )
    if not RELEASE_ESTIMATOR.is_file() or RELEASE_ESTIMATOR.is_symlink():
        raise RuntimeError(f"release quality estimator is missing: {RELEASE_ESTIMATOR}")
    actual_sha256 = sha256(RELEASE_ESTIMATOR)
    actual_bytes = RELEASE_ESTIMATOR.stat().st_size
    if (
        actual_sha256 != RELEASE_ESTIMATOR_SHA256
        or actual_bytes != RELEASE_ESTIMATOR_BYTES
    ):
        raise RuntimeError(
            "release quality-estimator identity differs: "
            f"{actual_sha256}/{actual_bytes} != "
            f"{RELEASE_ESTIMATOR_SHA256}/{RELEASE_ESTIMATOR_BYTES}"
        )
    sources = {}
    for relative in ANALYSIS_HELPER_SOURCES:
        path = ROOT / relative
        if not path.is_file() or path.is_symlink():
            raise RuntimeError(f"analysis helper source is missing: {path}")
        sources[relative] = {
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
        }
    return {
        "contract_id": "a5b-analysis-helper-release-v1",
        "built_before_candidate_output": True,
        "build": {
            "command": list(RELEASE_ESTIMATOR_BUILD_COMMAND),
            "cwd": ".",
            "profile": "release",
            "locked": True,
            "offline": True,
            "forbidden_environment_absent": list(FORBIDDEN_ESTIMATOR_BUILD_ENV),
            "cargo_version_verbose": command_output(
                ["cargo", "--version", "--verbose"]
            ),
            "rustc_version_verbose": command_output(
                ["rustc", "--version", "--verbose"]
            ),
        },
        "sources": sources,
        "binary": {
            "path": RELEASE_ESTIMATOR.relative_to(ROOT).as_posix(),
            "sha256": actual_sha256,
            "bytes": actual_bytes,
        },
    }


def assert_frozen_identities(
    pinned: dict[str, str],
    contracts: dict[str, str],
    helper: dict[str, Any],
) -> None:
    for inventory, label in ((pinned, "pinned A5a"), (contracts, "frozen A5b")):
        for relative, expected in inventory.items():
            path = ROOT / relative
            if not path.is_file() or path.is_symlink() or sha256(path) != expected:
                raise RuntimeError(f"{label} artifact changed during freeze: {relative}")
    binary = helper["binary"]
    if (
        not RELEASE_ESTIMATOR.is_file()
        or RELEASE_ESTIMATOR.is_symlink()
        or sha256(RELEASE_ESTIMATOR) != binary["sha256"]
        or RELEASE_ESTIMATOR.stat().st_size != binary["bytes"]
    ):
        raise RuntimeError("release quality estimator changed during freeze")
    for relative, identity in helper["sources"].items():
        path = ROOT / relative
        if (
            not path.is_file()
            or path.is_symlink()
            or sha256(path) != identity["sha256"]
            or path.stat().st_size != identity["bytes"]
            or contracts.get(relative) != identity["sha256"]
        ):
            raise RuntimeError(
                f"release quality-estimator source changed during freeze: {relative}"
            )


def forbidden_candidate_output_paths() -> tuple[Path, ...]:
    return (
        PACKAGE / "artifacts/fit/evidence-v1",
        PACKAGE / "artifacts/climate/candidate-evidence-manifest-v1.json",
        PACKAGE / "artifacts/climate/shared-base-evidence-v1.tar.gz",
        PACKAGE / "artifacts/climate/a5b-analysis-v1.json",
        PACKAGE / "artifacts/wepp/wepp-evidence-manifest-v1.json",
        PACKAGE / "artifacts/wepp/a5b-wepp-analysis-v1.json",
        PACKAGE / "artifacts/wepp/evidence-v1",
        ROOT / "target/a5a-baseline-v1",
        ROOT / "target/a5b-candidate-v1",
        ROOT / "target/a5b-candidate-v1.a5b-wepp-quarantine",
    )


def path_occupied(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def output_guard_self_test() -> None:
    required = {
        ROOT / "target/a5a-baseline-v1",
        ROOT / "target/a5b-candidate-v1",
        ROOT / "target/a5b-candidate-v1.a5b-wepp-quarantine",
    }
    if not required.issubset(forbidden_candidate_output_paths()):
        raise RuntimeError("candidate-output guard lacks a WEPP workspace")
    target = ROOT / "target"
    target.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="a5b-output-guard-", dir=target) as name:
        dangling = Path(name) / "dangling"
        dangling.symlink_to(Path(name) / "missing")
        if not path_occupied(dangling):
            raise RuntimeError("candidate-output guard accepted a dangling symlink")


def ensure_no_candidate_output(output: Path) -> None:
    output_guard_self_test()
    for path in forbidden_candidate_output_paths():
        if path_occupied(path):
            raise RuntimeError(f"candidate output already exists before freeze: {path}")
    for pattern in (
        "artifacts/climate/candidate-evidence-*-v1.tar.gz",
        "artifacts/wepp/**/wepp-response-*-v1.tar.gz",
        "artifacts/wepp/**/wepp-response-campaign-v1.json",
        "artifacts/wepp/**/a5b-wepp-analysis-v1.json",
    ):
        matches = sorted(PACKAGE.glob(pattern))
        if matches:
            raise RuntimeError(
                f"candidate output already exists before freeze: {matches[0]}"
            )
    if path_occupied(output):
        raise FileExistsError(output)


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            indent=2,
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    # Keep the final path component lexical until the occupancy guard has seen
    # it.  resolve() would replace a dangling output symlink with its missing
    # target and let the pre-output guard inspect the wrong path.
    output = args.output.absolute()
    ensure_no_candidate_output(output)

    pinned: dict[str, str] = {}
    for relative, expected in PINNED_A5A.items():
        path = ROOT / relative
        actual = sha256(path)
        if actual != expected:
            raise RuntimeError(f"pinned identity mismatch: {relative}: {actual}")
        pinned[relative] = actual

    contracts: dict[str, str] = {}
    for relative in NEW_CONTRACTS:
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(f"freeze input missing: {path}")
        contracts[relative] = sha256(path)

    helper = release_estimator_evidence()
    verifier_results = run_verifiers()
    bootstrap_vectors = additional_bootstrap_vectors()
    assert_frozen_identities(pinned, contracts, helper)
    result = {
        "pre_candidate_freeze_version": 1,
        "status": "passed",
        "candidate_output_absent": True,
        "a5a_pinned_artifacts": pinned,
        "a5b_frozen_artifacts": contracts,
        "schema_identities": check_schemas(),
        "analysis_helper_release": helper,
        "additional_bootstrap_vectors": bootstrap_vectors,
        "verifier_results": verifier_results,
        "matrix_contract": {
            "stations": 17,
            "horizons": [30, 100],
            "replicates": 8,
            "candidates": 7,
            "expected_runs": 1904,
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_bytes(result))
    print(output)


if __name__ == "__main__":
    main()
