"""Single command surface for the synthetic-only A9 research harness."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Set as AbstractSet
from pathlib import Path
from typing import Any

from .artifacts import FitArtifactStore, validate_role_manifest_semantics
from .candidates import config_schema_sha256, fit_synthetic, plugin_registry
from .canonical import canonical_bytes, read_json, sha256_file, validate_schema, write_canonical
from .errors import HarnessError, require
from .fixtures import FixtureRunner
from .log import AttemptLog
from .objectives import calibrate_max_statistic, load_objective_registry, pareto_frontier
from .optimizer import ExhaustiveOptimizer, ResourceLimits
from .roles import RoleFirewall, consume_confirmation


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_firewall(manifest_path: str, schema_path: str) -> tuple[dict[str, Any], RoleFirewall]:
    manifest = read_json(manifest_path)
    schema = read_json(schema_path)
    validate_schema(manifest, schema)
    validate_role_manifest_semantics(manifest)
    return manifest, RoleFirewall(manifest, schema)


def _strict_input_fields(
    payload: dict[str, Any], required: set[str], optional: AbstractSet[str] = frozenset()
) -> None:
    fields = set(payload)
    require(required <= fields, "COMMAND_INPUT_FIELDS", f"missing={sorted(required-fields)}")
    require(fields <= required | optional, "COMMAND_INPUT_FIELDS", f"unknown={sorted(fields-required-optional)}")


def _record_key(value: list[Any]) -> tuple[Any, ...]:
    require(len(value) == 8 and isinstance(value[3], list), "COMMAND_RECORD_KEY", repr(value))
    return (
        value[0],
        value[1],
        value[2],
        tuple(sorted(value[3])),
        value[4],
        value[5],
        value[6],
        value[7],
    )


def command_validate(args: argparse.Namespace) -> dict[str, Any]:
    if args.kind == "fit":
        artifact = FitArtifactStore(args.schema).read(args.artifact)
    elif args.kind == "role":
        artifact = read_json(args.artifact)
        schema = read_json(args.schema)
        validate_schema(artifact, schema)
        validate_role_manifest_semantics(artifact)
    elif args.kind == "objective":
        artifact = load_objective_registry(args.artifact, args.schema)
    else:
        artifact = read_json(args.artifact)
        validate_schema(artifact, read_json(args.schema))
    return {"status": "valid", "kind": args.kind, "artifact_sha256": sha256_file(args.artifact), "top_level_type": type(artifact).__name__}


def command_fit(args: argparse.Namespace) -> dict[str, Any]:
    _, firewall = _load_firewall(args.role_manifest, args.role_schema)
    exposure = read_json(args.exposures)
    _strict_input_fields(
        exposure,
        {"synthetic_only", "effective_exposures", "fit_artifact_template"},
        {"object_hashes", "logical_hashes", "record_keys"},
    )
    require(exposure.get("synthetic_only") is True, "OBSERVED_INPUT_PROHIBITED_A9B", args.exposures)
    artifact = exposure["fit_artifact_template"]
    require(isinstance(artifact, dict), "FIT_ARTIFACT_TEMPLATE", "object required")
    source_object_hashes = [source["object_sha256"] for source in artifact.get("sources", [])]
    source_logical_hashes = [source["logical_sha256"] for source in artifact.get("sources", [])]
    source_record_keys = [
        (
            source["source_id"],
            source["version"],
            source["station_id"],
            tuple(sorted(source["variables"])),
            source["calendar"],
            source["day_boundary"],
            source["period_start"],
            source["period_end"],
        )
        for source in artifact.get("sources", [])
    ]
    firewall.authorize(
        "fit",
        paths=[args.exposures],
        object_hashes=[*exposure.get("object_hashes", []), *source_object_hashes],
        logical_hashes=[*exposure.get("logical_hashes", []), *source_logical_hashes],
        record_keys=[*[_record_key(item) for item in exposure.get("record_keys", [])], *source_record_keys],
    )
    result = fit_synthetic(args.candidate_plugin, exposure["effective_exposures"])
    artifact["fit_status"] = result["fit_status"]
    artifact["status_reason"] = result["status_reason"]
    artifact["candidate_class"]["id"] = args.candidate_plugin
    artifact["candidate_class"]["schema_sha256"] = config_schema_sha256(args.candidate_plugin)
    artifact["candidate_class"]["source_sha256"] = sha256_file(Path(__file__).with_name("candidates.py"))
    artifact["diagnostics"]["effective_exposures"] = result["effective_exposures"]
    if result["fit_status"] == "fit_valid":
        fit_parameters = result["parameters"]
        if not isinstance(fit_parameters, dict):
            raise HarnessError("FIT_PARAMETER_RESULT", "object required")
        artifact["parameters"] = [
            {
                "name": name,
                "value": value,
                "unit": "research_parameter",
                "support": "candidate_config_schema_v1",
            }
            for name, value in sorted(fit_parameters.items())
        ]
    else:
        artifact["parameters"] = []
    return FitArtifactStore(args.fit_schema).write(args.output, artifact)


def command_evaluate(args: argparse.Namespace) -> dict[str, Any]:
    _, firewall = _load_firewall(args.role_manifest, args.role_schema)
    require(args.role in {"development", "gate_calibration"}, "EVALUATION_ROLE", args.role)
    payload = read_json(args.input)
    _strict_input_fields(payload, {"synthetic_only", "objectives"}, {"object_hashes", "logical_hashes"})
    require(payload.get("synthetic_only") is True, "OBSERVED_INPUT_PROHIBITED_A9B", args.input)
    firewall.authorize(
        "evaluate",
        paths=[args.input],
        object_hashes=payload.get("object_hashes", []),
        logical_hashes=payload.get("logical_hashes", []),
    )
    objectives = payload.get("objectives", {})
    require(isinstance(objectives, dict), "OBJECTIVE_VECTOR", "object required")
    output = {"schema_version": 1, "command": "evaluate", "role": args.role, "status": "evaluation_complete", "objectives": objectives}
    write_canonical(args.output, output, immutable=True)
    return output


def command_optimize(args: argparse.Namespace) -> dict[str, Any]:
    _, firewall = _load_firewall(args.role_manifest, args.role_schema)
    payload = read_json(args.proposals)
    _strict_input_fields(payload, {"synthetic_only", "proposals"}, {"object_hashes", "logical_hashes"})
    require(payload.get("synthetic_only") is True, "OBSERVED_INPUT_PROHIBITED_A9B", args.proposals)
    firewall.authorize("optimize", paths=[args.proposals], object_hashes=payload.get("object_hashes", []), logical_hashes=payload.get("logical_hashes", []))
    proposals = payload["proposals"]
    require(isinstance(proposals, list), "OPTIMIZER_PROPOSALS", "list required")
    log = AttemptLog(args.log_directory)
    limits = ResourceLimits(args.evaluations, args.wall_seconds, args.memory_bytes, args.retained_bytes, args.workers)

    def evaluator(proposal: dict[str, Any]) -> dict[str, Any]:
        if proposal.get("hard_feasible") is False:
            return {"state": "hard_infeasible", "failed_constraints": proposal.get("failed_constraints", ["synthetic"])}
        return {"state": "evaluation_complete", "objectives": proposal.get("objectives", {})}

    records = ExhaustiveOptimizer().run(proposals, evaluator, log, limits)
    vectors = [
        {"id": record["payload"]["proposal_sha256"], "objectives": record["payload"]["objectives"]}
        for record in records
        if record["payload"]["state"] == "evaluation_complete" and record["payload"].get("objectives")
    ]
    metric_ids = sorted(vectors[0]["objectives"]) if vectors else []
    frontier = pareto_frontier(vectors, metric_ids) if metric_ids else []
    return {"status": "complete", "attempts": len(records), "pareto_frontier": frontier}


def command_calibrate(args: argparse.Namespace) -> dict[str, Any]:
    _, firewall = _load_firewall(args.role_manifest, args.role_schema)
    payload = read_json(args.replicates)
    _strict_input_fields(payload, {"synthetic_only", "replicates", "floors"}, {"object_hashes", "logical_hashes"})
    require(payload.get("synthetic_only") is True, "OBSERVED_INPUT_PROHIBITED_A9B", args.replicates)
    firewall.authorize("calibrate-gates", paths=[args.replicates], object_hashes=payload.get("object_hashes", []), logical_hashes=payload.get("logical_hashes", []))
    replicates = []
    for replicate in payload["replicates"]:
        converted = {}
        for key, values in replicate.items():
            family, horizon = key.rsplit(":", 1)
            converted[(family, int(horizon))] = values
        replicates.append(converted)
    floors = {}
    for key, value in payload["floors"].items():
        family, horizon = key.rsplit(":", 1)
        floors[(family, int(horizon))] = value
    output = {"schema_version": 1, "method": "paired_max_statistic_quantile", "candidate_access_prohibited": True, "thresholds": calibrate_max_statistic(replicates, floors)}
    write_canonical(args.output, output, immutable=True)
    return output


def command_confirm(args: argparse.Namespace) -> dict[str, Any]:
    result = consume_confirmation(
        args.sealed_freeze,
        args.role_schema,
        args.freeze_sha256,
        args.actor,
        args.access_log_directory,
    )
    return {"status": "consumed", "manifest_id": result["manifest_id"], "freeze_sha256": result["freeze_sha256"]}


def command_verify_log(args: argparse.Namespace) -> dict[str, Any]:
    records = AttemptLog(args.log_directory).verify()
    return {"status": "valid", "attempts": len(records), "head_sha256": records[-1]["record_sha256"] if records else "0" * 64}


def command_run_fixtures(args: argparse.Namespace) -> dict[str, Any]:
    runner = FixtureRunner(_repo_root())
    hashes = runner.write_evidence(args.output_directory)
    return {"status": "PASS", "artifacts": hashes}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="a9-harness", description="Synthetic-only A9 calibration research harness")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate")
    validate.add_argument("artifact")
    validate.add_argument("--schema", required=True)
    validate.add_argument("--kind", choices=("fit", "role", "objective", "generic"), default="generic")
    validate.set_defaults(function=command_validate)

    fit = subparsers.add_parser("fit")
    fit.add_argument("--role-manifest", required=True)
    fit.add_argument("--role-schema", required=True)
    fit.add_argument("--fit-schema", required=True)
    fit.add_argument("--candidate-plugin", choices=tuple(plugin_registry()), required=True)
    fit.add_argument("--exposures", required=True)
    fit.add_argument("--output", required=True)
    fit.set_defaults(function=command_fit)

    evaluate = subparsers.add_parser("evaluate")
    evaluate.add_argument("--role-manifest", required=True)
    evaluate.add_argument("--role-schema", required=True)
    evaluate.add_argument("--role", choices=("development", "gate_calibration"), required=True)
    evaluate.add_argument("--input", required=True)
    evaluate.add_argument("--output", required=True)
    evaluate.set_defaults(function=command_evaluate)

    optimize = subparsers.add_parser("optimize")
    optimize.add_argument("--role-manifest", required=True)
    optimize.add_argument("--role-schema", required=True)
    optimize.add_argument("--proposals", required=True)
    optimize.add_argument("--log-directory", required=True)
    optimize.add_argument("--evaluations", type=int, default=256)
    optimize.add_argument("--wall-seconds", type=float, default=86400.0)
    optimize.add_argument("--memory-bytes", type=int, default=12 * 1024**3)
    optimize.add_argument("--retained-bytes", type=int, default=50 * 1024**3)
    optimize.add_argument("--workers", type=int, default=8)
    optimize.set_defaults(function=command_optimize)

    calibrate = subparsers.add_parser("calibrate-gates")
    calibrate.add_argument("--role-manifest", required=True)
    calibrate.add_argument("--role-schema", required=True)
    calibrate.add_argument("--replicates", required=True)
    calibrate.add_argument("--output", required=True)
    calibrate.set_defaults(function=command_calibrate)

    confirm = subparsers.add_parser("confirm")
    confirm.add_argument("--sealed-freeze", required=True)
    confirm.add_argument("--role-schema", required=True)
    confirm.add_argument("--freeze-sha256", required=True)
    confirm.add_argument("--actor", required=True)
    confirm.add_argument("--access-log-directory", required=True)
    confirm.set_defaults(function=command_confirm)

    verify_log = subparsers.add_parser("verify-log")
    verify_log.add_argument("log_directory")
    verify_log.set_defaults(function=command_verify_log)

    run_fixtures = subparsers.add_parser("run-fixtures")
    run_fixtures.add_argument("--output-directory", required=True)
    run_fixtures.set_defaults(function=command_run_fixtures)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = args.function(args)
        sys.stdout.buffer.write(canonical_bytes(result))
        return 0
    except HarnessError as error:
        print(f"{error.code}: {error.message}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
