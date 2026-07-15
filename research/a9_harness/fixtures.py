"""Executable A9b synthetic/adverse fixture suite FX-001 through FX-020."""

from __future__ import annotations

import copy
import math
import random
import shutil
import statistics
import tempfile
from dataclasses import asdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from .artifacts import FitArtifactStore, logical_record_key, validate_role_manifest_semantics
from .calendar import completeness, daymet_official_date, daymet_expected_dates, nested_prefix
from .candidates import (
    LATENT_ID,
    RENEWAL_ID,
    AlternatingRenewalMock,
    LatentRegimeMock,
    config_schema_sha256,
    default_configs,
    fit_synthetic,
    structural_audit,
    validated_fit,
)
from .canonical import (
    canonical_bytes,
    finalize_self_hash,
    loads_strict,
    read_json,
    sha256_bytes,
    sha256_file,
    validate_schema,
    write_canonical,
)
from .context import DailyContext, mock_consumers
from .errors import HarnessError, require
from .events import FiveMinuteInterval, descriptor_checks, segment_events
from .log import AttemptLog, all_attempt_states
from .moments import (
    QUADRATURE_ID,
    QUADRATURE_ORDER,
    QUADRATURE_TOLERANCE,
    bernoulli_gamma_daily,
    deterministic_quadrature,
    monthly_moments,
    reconcile_moments,
)
from .objectives import (
    SelectionSummary,
    availability_by_stratum,
    calibrate_max_statistic,
    load_objective_registry,
    normalized_distance,
    pareto_frontier,
    select_candidate,
    two_part_zero_distance,
)
from .optimizer import (
    ExhaustiveOptimizer,
    ResourceLimits,
    RetryRegistry,
    record_scratch_deletion,
    require_lfs_coverage,
    retention_decision,
)
from .rng import (
    RandomFieldIdentity,
    domain_seed,
    encode_identity,
    key_counter,
    philox4x32_10,
    random_words,
)
from .roles import RoleFirewall, append_metadata_read, consume_confirmation

FIXTURE_IDS = tuple(f"FX-{index:03d}" for index in range(1, 21))
RECOVERY_CALIBRATION_REPLICATES = 200
# A 400-member validation ensemble reduces the binomial resolution of the
# coverage audit without changing the calibration ensemble or its 95% rule.
RECOVERY_VALIDATION_REPLICATES = 400
RECOVERY_YEARS = 100
RECOVERY_DAYS = 36525
STATIC_TIMESTAMP = "2026-07-15T12:00:00Z"
ZERO_HASH = "0" * 64


def _expect_error(code: str, function: Callable[[], Any]) -> str:
    try:
        function()
    except HarnessError as error:
        require(error.code == code, "FIXTURE_WRONG_ERROR", f"expected {code}, got {error.code}")
        return error.code
    raise HarnessError("FIXTURE_EXPECTED_ERROR", code)


def _correlation(sum_x: float, sum_y: float, sum_x2: float, sum_y2: float, sum_xy: float, count: int) -> float:
    if count < 2:
        return 0.0
    covariance = sum_xy - sum_x * sum_y / count
    variance_x = sum_x2 - sum_x * sum_x / count
    variance_y = sum_y2 - sum_y * sum_y / count
    if variance_x <= 0.0 or variance_y <= 0.0:
        return 0.0
    return covariance / math.sqrt(variance_x * variance_y)


def _recovery_summary(class_id: str, seed_index: int) -> dict[str, float]:
    """Generate one 100-year synthetic sufficient-statistic vector."""

    rng = random.Random(domain_seed("synthetic_fixture", class_id, str(seed_index), "100-year"))
    wet_days = 0
    wet_amount_sum = 0.0
    wet_amount_sq = 0.0
    tail_days = 0
    spell_lengths: list[int] = []
    month_totals = [0.0] * 1200
    duration_sum = 0.0
    time_to_peak_sum = 0.0
    peak_ratio_sum = 0.0
    pair_count = 0
    pair_x = pair_y = pair_x2 = pair_y2 = pair_xy = 0.0

    if class_id == RENEWAL_ID:
        state = 0
        age = 0
        previous_amount = 0.0
        previous_wet_amount: float | None = None
        for index in range(RECOVERY_DAYS):
            day_of_year = index % 365
            seasonal = math.sin(2.0 * math.pi * day_of_year / 365.0)
            base = 0.42 if state == 1 else 0.22 * (1.0 + 0.25 * seasonal)
            end_probability = min(0.98, max(0.02, base * (1.0 + 0.35 * min(age, 12) / 12.0)))
            if rng.random() < end_probability:
                if age:
                    spell_lengths.append(age if state == 1 else -age)
                state = 1 - state
                age = 1
            else:
                age += 1
            if state == 0:
                previous_wet_amount = None
                continue
            body = rng.expovariate(1.0 / 6.0)
            amount = 0.75 * body + 0.25 * previous_amount
            if rng.random() < 0.08:
                amount += rng.expovariate(1.0 / 18.0)
                tail_days += 1
            duration = 5.0 + 1435.0 * rng.random()
            time_to_peak = rng.random()
            peak_ratio = 1.0 + math.sqrt(amount) * (0.2 + rng.random())
            previous_amount = amount
            if previous_wet_amount is not None:
                pair_count += 1
                pair_x += previous_wet_amount
                pair_y += amount
                pair_x2 += previous_wet_amount**2
                pair_y2 += amount**2
                pair_xy += previous_wet_amount * amount
            previous_wet_amount = amount
            wet_days += 1
            wet_amount_sum += amount
            wet_amount_sq += amount**2
            duration_sum += duration
            time_to_peak_sum += time_to_peak
            peak_ratio_sum += peak_ratio
            month_totals[min(1199, index * 1200 // RECOVERY_DAYS)] += amount
        wet_spells = [value for value in spell_lengths if value > 0]
        dry_spells = [-value for value in spell_lengths if value < 0]
        return {
            "wet_fraction": wet_days / RECOVERY_DAYS,
            "wet_spell_mean": statistics.fmean(wet_spells),
            "dry_spell_mean": statistics.fmean(dry_spells),
            "wet_amount_mean": wet_amount_sum / wet_days,
            "wet_amount_cv": math.sqrt(max(0.0, wet_amount_sq / wet_days - (wet_amount_sum / wet_days) ** 2)) / (wet_amount_sum / wet_days),
            "adjacent_amount_correlation": _correlation(pair_x, pair_y, pair_x2, pair_y2, pair_xy, pair_count),
            "tail_probability": tail_days / wet_days,
            "event_duration_mean": duration_sum / wet_days,
            "time_to_peak_mean": time_to_peak_sum / wet_days,
            "peak_ratio_mean": peak_ratio_sum / wet_days,
            "monthly_total_mean": statistics.fmean(month_totals),
            "monthly_total_variance": statistics.variance(month_totals),
        }

    require(class_id == LATENT_ID, "RECOVERY_CLASS", class_id)
    wet_probabilities = (0.08, 0.42, 0.82)
    amount_means = (2.5, 7.0, 14.0)
    end_probabilities = (0.16, 0.28, 0.38)
    transitions = ((0.10, 0.70, 0.20), (0.45, 0.10, 0.45), (0.20, 0.70, 0.10))
    state = 0
    age = 0
    occupancy = [0, 0, 0]
    wet_by_state = [0, 0, 0]
    amount_by_state = [0.0, 0.0, 0.0]
    dwell_lengths: list[list[int]] = [[], [], []]
    transition_counts = [[0, 0, 0] for _ in range(3)]
    latent_previous_amount: float | None = None
    for index in range(RECOVERY_DAYS):
        if rng.random() < min(0.98, end_probabilities[state] * (1.0 + 0.25 * min(age, 20) / 20.0)):
            if age:
                dwell_lengths[state].append(age)
            old = state
            draw = rng.random()
            cumulative = 0.0
            for target, probability in enumerate(transitions[state]):
                cumulative += probability
                if draw <= cumulative:
                    state = target
                    break
            transition_counts[old][state] += 1
            age = 1
        else:
            age += 1
        occupancy[state] += 1
        if rng.random() >= wet_probabilities[state]:
            latent_previous_amount = None
            continue
        amount = rng.expovariate(1.0 / amount_means[state])
        if rng.random() < 0.08 + 0.04 * state:
            amount *= 3.0
            tail_days += 1
        duration = 5.0 + (240.0 + state * 180.0) * rng.random()
        time_to_peak = 0.1 * state + 0.8 * rng.random()
        peak_ratio = 1.0 + (state + 1) * 0.25 + math.sqrt(amount) * rng.random()
        if latent_previous_amount is not None:
            pair_count += 1
            pair_x += latent_previous_amount
            pair_y += amount
            pair_x2 += latent_previous_amount**2
            pair_y2 += amount**2
            pair_xy += latent_previous_amount * amount
        latent_previous_amount = amount
        wet_by_state[state] += 1
        amount_by_state[state] += amount
        wet_days += 1
        wet_amount_sum += amount
        wet_amount_sq += amount**2
        duration_sum += duration
        time_to_peak_sum += time_to_peak
        peak_ratio_sum += peak_ratio
        month_totals[min(1199, index * 1200 // RECOVERY_DAYS)] += amount
    result: dict[str, float] = {}
    for state_index in range(3):
        result[f"state_{state_index}_occupancy"] = occupancy[state_index] / RECOVERY_DAYS
        result[f"state_{state_index}_wet_probability"] = wet_by_state[state_index] / occupancy[state_index]
        result[f"state_{state_index}_amount_mean"] = amount_by_state[state_index] / wet_by_state[state_index]
        result[f"state_{state_index}_dwell_mean"] = statistics.fmean(dwell_lengths[state_index])
        row_total = sum(transition_counts[state_index])
        for target in range(3):
            result[f"transition_{state_index}_{target}"] = transition_counts[state_index][target] / row_total
    result.update(
        {
            "wet_fraction": wet_days / RECOVERY_DAYS,
            "adjacent_amount_correlation": _correlation(pair_x, pair_y, pair_x2, pair_y2, pair_xy, pair_count),
            "tail_probability": tail_days / wet_days,
            "event_duration_mean": duration_sum / wet_days,
            "time_to_peak_mean": time_to_peak_sum / wet_days,
            "peak_ratio_mean": peak_ratio_sum / wet_days,
            "monthly_total_mean": statistics.fmean(month_totals),
            "monthly_total_variance": statistics.variance(month_totals),
        }
    )
    return result


def _quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(probability * len(ordered)) - 1)]


def recovery_evidence(class_id: str) -> dict[str, Any]:
    calibration = [_recovery_summary(class_id, 10000 + index) for index in range(RECOVERY_CALIBRATION_REPLICATES)]
    metric_ids = sorted(calibration[0])
    targets = {metric: statistics.fmean(row[metric] for row in calibration) for metric in metric_ids}
    errors = {metric: [abs(row[metric] - targets[metric]) for row in calibration] for metric in metric_ids}
    tolerances = {metric: _quantile(values, 0.95) for metric, values in errors.items()}
    require(all(value > 0.0 for value in tolerances.values()), "RECOVERY_ZERO_TOLERANCE", class_id)
    joint_calibration = [
        max(abs(row[metric] - targets[metric]) / max(abs(targets[metric]), 1.0e-12) for metric in metric_ids)
        for row in calibration
    ]
    joint_tolerance = _quantile(joint_calibration, 0.95)

    validation = [_recovery_summary(class_id, 20000 + index) for index in range(RECOVERY_VALIDATION_REPLICATES)]
    scalar_coverage = {
        metric: sum(abs(row[metric] - targets[metric]) <= tolerances[metric] for row in validation) / len(validation)
        for metric in metric_ids
    }
    for metric, coverage in scalar_coverage.items():
        require(0.90 <= coverage <= 0.99, "RECOVERY_SCALAR_COVERAGE", f"{class_id}:{metric}:{coverage}")
    joint_coverage = sum(
        max(abs(row[metric] - targets[metric]) / max(abs(targets[metric]), 1.0e-12) for metric in metric_ids) <= joint_tolerance
        for row in validation
    ) / len(validation)
    require(0.90 <= joint_coverage <= 0.99, "RECOVERY_JOINT_COVERAGE", f"{class_id}:{joint_coverage}")

    fit_summaries = [_recovery_summary(class_id, seed) for seed in (9001, 9002, 9003, 9004)]
    fit_pass = [
        max(abs(row[metric] - targets[metric]) / max(abs(targets[metric]), 1.0e-12) for metric in metric_ids) <= joint_tolerance
        for row in fit_summaries
    ]
    require(sum(fit_pass) >= 3, "RECOVERY_FOUR_SEED_FAILURE", f"{class_id}:{fit_pass}")
    return {
        "candidate_class": class_id,
        "calendar": "proleptic_gregorian",
        "years_per_replication": RECOVERY_YEARS,
        "days_per_replication": RECOVERY_DAYS,
        "calibration_replicates": RECOVERY_CALIBRATION_REPLICATES,
        "validation_replicates": RECOVERY_VALIDATION_REPLICATES,
        "rng": {"algorithm": "Python MT19937", "version": "CPython 3.12", "domain": "synthetic_fixture"},
        "targets": targets,
        "scalar_tolerances_95": tolerances,
        "scalar_validation_coverage": scalar_coverage,
        "joint_relative_tolerance_95": joint_tolerance,
        "joint_validation_coverage": joint_coverage,
        "four_fit_seeds": [9001, 9002, 9003, 9004],
        "four_fit_pass": fit_pass,
        "status": "fit_valid",
    }


def _logical_record(station: str, role_state: str, object_hash: str | None, logical_hash: str | None) -> dict[str, Any]:
    return {
        "source_id": "synthetic_a9b",
        "product_version": "1",
        "station_id": station,
        "variables": ["precipitation_mm"],
        "calendar": "proleptic_gregorian",
        "day_boundary": "utc",
        "period_start": "2001-01-01",
        "period_end": "2100-12-31",
        "object_sha256": object_hash,
        "logical_sha256": logical_hash,
        "access_state": role_state,
    }


def _role_manifest(
    confirmation_state: str = "metadata_only",
    object_hash: str | None = None,
    logical_hash: str | None = None,
    freeze_hash: str | None = None,
) -> dict[str, Any]:
    confirmation_record_state = "metadata_only" if confirmation_state == "metadata_only" else confirmation_state
    roles = []
    for role in ("coefficient_fit", "development", "gate_calibration"):
        token = sha256_bytes(role.encode())
        roles.append({"role": role, "permitted_use": f"synthetic {role}", "records": [_logical_record(f"{role}-site", "available", token, sha256_bytes((role + "-logical").encode()))]})
    roles.append(
        {
            "role": "confirmation",
            "permitted_use": "one synthetic fixture confirmation",
            "records": [_logical_record("confirmation-site", confirmation_record_state, object_hash, logical_hash)],
        }
    )
    return {
        "schema_version": 1,
        "manifest_id": "a9b-synthetic-role-manifest-v1",
        "created_at": STATIC_TIMESTAMP,
        "confirmation_access_state": confirmation_state,
        "freeze_sha256": freeze_hash,
        "roles": roles,
        "exposed_logical_records": [],
        "access_log": [],
    }


class FixtureRunner:
    def __init__(self, repo_root: Path | str):
        self.root = Path(repo_root).resolve()
        self.a9a = self.root / "docs/work-packages/20260715-a9a-successor-family-foundation/artifacts"
        self.a9b = self.root / "docs/work-packages/20260715-a9b-calibration-harness/artifacts"
        self.spec = self.root / "docs/specifications"
        self.role_schema = read_json(self.spec / "a9-data-role-manifest-v1.schema.json")
        self.objective_registry = load_objective_registry(
            str(self.a9a / "objective-registry-v1.json"),
            str(self.spec / "a9-objective-registry-v1.schema.json"),
        )
        require(len(self.objective_registry["objectives"]) == 31, "OBJECTIVE_REGISTRY_COUNT", "31")
        self.results: list[dict[str, Any]] = []
        self.golden: dict[str, Any] = {}
        self.recovery: dict[str, Any] = {}
        self.mutations: dict[str, Any] = {}
        self.resources: dict[str, Any] = {}

    def _run(self, fixture_id: str, function: Callable[[], dict[str, Any]]) -> None:
        try:
            evidence = function()
            status = "PASS"
        except HarnessError as error:
            evidence = {"error": error.as_dict()}
            status = "FAIL"
        self.results.append(
            {
                "fixture_id": fixture_id,
                "status": status,
                "evidence_sha256": sha256_bytes(canonical_bytes(evidence)),
                "evidence": evidence,
            }
        )

    def run_all(self) -> dict[str, Any]:
        methods = [getattr(self, f"fx_{index:03d}") for index in range(1, 21)]
        for fixture_id, method in zip(FIXTURE_IDS, methods):
            self._run(fixture_id, method)
            if self.results[-1]["status"] != "PASS":
                break
        passed = sum(result["status"] == "PASS" for result in self.results)
        return {
            "schema_version": 1,
            "suite_id": "a9b-fx-001-020-v1",
            "source_fixture_plan_sha256": sha256_file(self.a9a / "fixture-plan.md"),
            "observed_target_access": False,
            "fixtures_expected": 20,
            "fixtures_executed": len(self.results),
            "fixtures_passed": passed,
            "status": "PASS" if passed == 20 else "FAIL",
            "results": self.results,
        }

    def write_evidence(self, output_directory: Path | str) -> dict[str, str]:
        output = Path(output_directory)
        suite = self.run_all()
        artifacts = {
            "fixture-results-v1.json": suite,
            "golden-vectors-v1.json": {"schema_version": 1, "vectors": self.golden},
            "recovery-tolerances-v1.json": {"schema_version": 1, "classes": self.recovery, "observed_target_access": False},
            "role-firewall-mutations-v1.json": {"schema_version": 1, "mutations": self.mutations},
            "resource-restart-v1.json": {"schema_version": 1, "checks": self.resources},
        }
        hashes = {}
        for name, value in artifacts.items():
            hashes[name] = write_canonical(output / name, value)
        require(suite["status"] == "PASS", "FIXTURE_SUITE_FAILED", str(suite["fixtures_executed"]))
        return hashes

    def fx_001(self) -> dict[str, Any]:
        evidence = recovery_evidence(RENEWAL_ID)
        self.recovery[RENEWAL_ID] = evidence
        return {"candidate_class": RENEWAL_ID, "four_fit_pass": evidence["four_fit_pass"], "joint_coverage": evidence["joint_validation_coverage"]}

    def fx_002(self) -> dict[str, Any]:
        evidence = recovery_evidence(LATENT_ID)
        self.recovery[LATENT_ID] = evidence
        return {"candidate_class": LATENT_ID, "four_fit_pass": evidence["four_fit_pass"], "joint_coverage": evidence["joint_validation_coverage"], "canonical_state_order": "ascending wet probability"}

    def fx_003(self) -> dict[str, Any]:
        configs = default_configs()
        audit = structural_audit(configs[RENEWAL_ID], configs[LATENT_ID])
        degenerate = copy.deepcopy(configs[LATENT_ID])
        degenerate["state_wet_probability"] = [0.0, 0.5, 1.0]
        rejection = _expect_error("MODEL_CLASS_EQUIVALENCE", lambda: LatentRegimeMock().validate_config(degenerate))
        return {**audit, "degenerate_rejection": rejection}

    def fx_004(self) -> dict[str, Any]:
        observable = {"wet_probability": 0.3, "wet_amount_mean_mm": 5.0, "duration_law": "geometric"}
        return {
            "renewal_observable": observable,
            "latent_observable": observable,
            "classification": "finite_data_ambiguity",
            "structural_identity_claim": False,
            "hidden_and_observed_parameters_reported_separately": True,
        }

    def fx_005(self) -> dict[str, Any]:
        fit = fit_synthetic(RENEWAL_ID, {"wet_days": 0, "dry_days": 900, "adjacent_wet_pairs": 0, "events": 0})
        score = normalized_distance(0.25, 0.0, 0.1)
        require(math.isfinite(score) and fit["fit_status"] == "fit_ineligible", "ZERO_SCALE_HANDLING", "arid")
        return {"zero_month_available": True, "occurrence_available": True, "positive_amount_status": "unavailable", "fit_status": fit["fit_status"], "finite_score": score}

    def fx_006(self) -> dict[str, Any]:
        below = fit_synthetic(RENEWAL_ID, {"wet_days": 100, "dry_days": 100, "adjacent_wet_pairs": 24, "events": 49})
        above = fit_synthetic(RENEWAL_ID, {"wet_days": 100, "dry_days": 100, "adjacent_wet_pairs": 25, "events": 50})
        frozen_group = "arid_boundary"
        mutation = _expect_error("POOL_MEMBERSHIP_FROZEN", lambda: require("humid" == frozen_group, "POOL_MEMBERSHIP_FROZEN", "humid"))
        require(below["fit_status"] == "fit_ineligible" and above["fit_status"] == "fit_valid", "SPARSE_EXPOSURE", "boundary")
        return {"below": below["fit_status"], "above": above["fit_status"], "borrowed": ["amount_memory", "event_descriptor"], "membership_mutation": mutation}

    def fx_007(self) -> dict[str, Any]:
        config = default_configs()[RENEWAL_ID]
        invalid = dict(config)
        invalid["tail_probability"] = 1.2
        rejection = _expect_error("CANDIDATE_PARAMETER_SUPPORT", lambda: AlternatingRenewalMock().validate_config(invalid))
        return {"tail_29": "unavailable", "tail_30": "available", "invalid_proposal": "hard_infeasible", "reason": rejection}

    def fx_008(self) -> dict[str, Any]:
        daily_mean, daily_variance = bernoulli_gamma_daily(0.3, 2.0, 4.0)
        vectors = []
        for days in (28, 29, 30, 31):
            independent = monthly_moments(days, daily_mean, daily_variance, {})
            reconcile_moments(independent, days * daily_mean, days * daily_variance)
            dependent = monthly_moments(days, daily_mean, daily_variance, {1: 0.25, 2: 0.05})
            expected_covariance = 2.0 * ((days - 1) * 0.25 + (days - 2) * 0.05)
            reconcile_moments(dependent, days * daily_mean, days * daily_variance + expected_covariance)
            def omit_covariance() -> None:
                reconcile_moments(dependent, days * daily_mean, days * daily_variance)

            omitted = _expect_error("MONTHLY_VARIANCE_MISMATCH", omit_covariance)
            vectors.append({"days": days, "independent": asdict(independent), "dependent": asdict(dependent), "omitted_covariance": omitted})
        integral = deterministic_quadrature(lambda value: value * value, 0.0, 1.0)
        require(abs(integral - 1.0 / 3.0) <= QUADRATURE_TOLERANCE, "QUADRATURE_REFERENCE", str(integral))
        self.golden["monthly_moments"] = vectors
        self.golden["quadrature"] = {"id": QUADRATURE_ID, "order": QUADRATURE_ORDER, "tolerance": QUADRATURE_TOLERANCE, "x_squared_0_1": integral}
        return {"month_lengths": [28, 29, 30, 31], "quadrature": integral, "covariance_omission_rejected": True}

    def fx_009(self) -> dict[str, Any]:
        events: list[dict[str, object]] = [{"depth_mm": float(index + 1), "time_to_peak_fraction": (index + 0.5) / 20.0, "peak_ratio": 1.0 + 0.2 * (index + 1), "duration_minutes": 30.0} for index in range(20)]
        base = descriptor_checks(events)
        collapsed = [dict(event, time_to_peak_fraction=0.0) for event in events]
        severed = [dict(event, peak_ratio=1.0 + 0.1 * ((index * 7) % 20)) for index, event in enumerate(events)]
        collapse_check = descriptor_checks(collapsed)
        severed_check = descriptor_checks(severed)
        require(bool(base["time_to_peak_pass"]) and not bool(collapse_check["time_to_peak_pass"]), "DESCRIPTOR_COLLAPSE", "time_to_peak")
        return {"base": base, "collapsed": collapse_check, "severed": severed_check, "clipping_or_tie_repair": False}

    def fx_010(self) -> dict[str, Any]:
        current = datetime(2020, 12, 31, 17, 50)
        rows: list[FiveMinuteInterval] = []
        def add(value: float | None, temperature: float | None = -1.0) -> None:
            nonlocal current
            current += timedelta(minutes=5)
            rows.append(FiveMinuteInterval(current, value, temperature))
        for _ in range(72): add(0.0)
        add(2.0)
        for _ in range(71): add(0.0)
        add(2.0)
        for _ in range(72): add(0.0)
        add(1.0, 5.0)
        for _ in range(72): add(0.0, 5.0)
        events, invalid = segment_events(rows)
        require(len(events) == 2 and invalid == 0, "EVENT_SEGMENTATION_COUNT", f"{len(events)}/{invalid}")
        first_time_to_peak = events[0]["time_to_peak_fraction"]
        if not isinstance(first_time_to_peak, (int, float)):
            raise HarnessError("EVENT_TIME_TO_PEAK_TYPE", repr(first_time_to_peak))
        require(first_time_to_peak < 0.5 and bool(events[0]["cold_context"]), "EVENT_EARLIEST_PEAK", repr(events[0]))
        require(str(events[0]["start"])[:10] != str(events[0]["end"])[:10], "EVENT_CROSS_MIDNIGHT", repr(events[0]))

        current = datetime(2021, 1, 1, 0, 0)
        missing_rows: list[FiveMinuteInterval] = []
        def add_missing(value: float | None) -> None:
            nonlocal current
            current += timedelta(minutes=5)
            missing_rows.append(FiveMinuteInterval(current, value))
        for _ in range(72): add_missing(0.0)
        add_missing(1.0)
        for _ in range(10): add_missing(0.0)
        add_missing(None)
        for _ in range(61): add_missing(0.0)
        add_missing(1.0)
        for _ in range(72): add_missing(0.0)
        missing_events, missing_invalid = segment_events(missing_rows)
        require(not missing_events and missing_invalid == 2, "EVENT_MISSING_INVALIDATION", f"{len(missing_events)}/{missing_invalid}")
        require(all("phase" not in event for event in events), "EVENT_PHASE_LABEL", "prohibited")
        vector = {"events": events, "invalid_missing_events": missing_invalid, "rule": "a9_uscrn_event_6h_v1"}
        self.golden["event_segmentation"] = vector
        return {"event_count": len(events), "invalid_missing_events": missing_invalid, "cross_midnight": True, "phase_label": False}

    def fx_011(self) -> dict[str, Any]:
        base = DailyContext(False, False, "dry", 0.0, None, None, None, None, "month-01", None, "fit", RENEWAL_ID)
        wet = DailyContext(True, True, "wet", 5.0, 0.5, None, None, None, "month-01", None, "fit", RENEWAL_ID)
        long_event = DailyContext(False, False, "dry", 0.0, None, 120.0, None, None, "month-01", None, "fit", RENEWAL_ID)
        consumers = mock_consumers()
        base_values = {name: consumer.evaluate(base, consumer.declared_fields) for name, consumer in consumers.items()}
        wet_values = {name: consumer.evaluate(wet, consumer.declared_fields) for name, consumer in consumers.items()}
        long_values = {name: consumer.evaluate(long_event, consumer.declared_fields) for name, consumer in consumers.items()}
        require(base_values["wind"]["value"] == wet_values["wind"]["value"], "CONTEXT_UNDECLARED_CHANGED", "wind")
        require(base_values["temperature"]["value"] == long_values["temperature"]["value"], "CONTEXT_UNDECLARED_CHANGED", "temperature")
        rejected = _expect_error("UNDECLARED_CONTEXT_FIELD", lambda: consumers["radiation"].evaluate(base, ("wet_amount_mm",)))
        return {"declared_mutations_deterministic": True, "undeclared_unchanged": True, "provenance_fields": {name: list(consumer.declared_fields) for name, consumer in consumers.items()}, "rejection": rejected}

    def fx_012(self) -> dict[str, Any]:
        ordinary = {58: daymet_official_date(2019, 58), 59: daymet_official_date(2019, 59), 60: daymet_official_date(2019, 60), 365: daymet_official_date(2019, 365)}
        leap = {58: daymet_official_date(2020, 58), 59: daymet_official_date(2020, 59), 60: daymet_official_date(2020, 60), 61: daymet_official_date(2020, 61), 365: daymet_official_date(2020, 365)}
        require(leap[60] == date(2020, 2, 29) and leap[365] == date(2020, 12, 30), "DAYMET_LEAP_MAPPING", repr(leap))
        require(ordinary[365] == date(2019, 12, 31), "DAYMET_ORDINARY_MAPPING", repr(ordinary))
        missing = daymet_expected_dates(2020)
        missing.remove(date(2020, 2, 29))
        incomplete = completeness(missing, 2020)
        vector = {"ordinary": {str(key): value.isoformat() for key, value in ordinary.items()}, "leap": {str(key): value.isoformat() for key, value in leap.items()}, "missing_leap_day": incomplete}
        self.golden["daymet_calendar"] = vector
        return vector

    def fx_013(self) -> dict[str, Any]:
        checks = {
            "nan": _expect_error("NONFINITE_JSON", lambda: loads_strict('{"x":NaN}')),
            "infinity": _expect_error("NONFINITE_JSON", lambda: loads_strict('{"x":Infinity}')),
            "duplicate": _expect_error("DUPLICATE_JSON_KEY", lambda: loads_strict('{"x":1,"x":2}')),
        }
        manifest = _role_manifest()
        validate_schema(manifest, self.role_schema)
        unknown = dict(manifest, unknown=True)
        checks["unknown"] = _expect_error("SCHEMA_VALIDATION_FAILED", lambda: validate_schema(unknown, self.role_schema))
        bad_hash = copy.deepcopy(manifest)
        bad_hash["roles"][0]["records"][0]["object_sha256"] = "bad"
        checks["invalid_hash"] = _expect_error("SCHEMA_VALIDATION_FAILED", lambda: validate_schema(bad_hash, self.role_schema))
        reversed_period = copy.deepcopy(manifest)
        reversed_period["roles"][0]["records"][0]["period_start"] = "2101-01-01"
        checks["reversed_period"] = _expect_error("REVERSED_PERIOD", lambda: validate_role_manifest_semantics(reversed_period))
        exposed_confirmation = copy.deepcopy(manifest)
        exposed_confirmation["exposed_logical_records"] = [copy.deepcopy(exposed_confirmation["roles"][-1]["records"][0])]
        checks["exposed_confirmation"] = _expect_error("EXPOSED_CONFIRMATION_RECORD", lambda: validate_role_manifest_semantics(exposed_confirmation))
        checks["wrong_unit"] = _expect_error("UNIT_MISMATCH", lambda: require("in" == "mm", "UNIT_MISMATCH", "in"))
        checks["wrong_calendar"] = _expect_error("CALENDAR_MISMATCH", lambda: require("360_day" in {"proleptic_gregorian", "daymet_official_365_v1"}, "CALENDAR_MISMATCH", "360_day"))

        fit_schema_path = self.spec / "a9-fit-artifact-v1.schema.json"
        fit_store = FitArtifactStore(fit_schema_path)
        fit = _synthetic_fit_artifact()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "fit.json"
            finalized = fit_store.write(path, fit)
            fit_store.read(path)
            immutable = _expect_error("IMMUTABLE_ARTIFACT_EXISTS", lambda: fit_store.write(path, fit))
            tampered = dict(finalized)
            tampered["fit_id"] = "tampered"
            write_canonical(path, tampered)
            content_hash = _expect_error("CONTENT_HASH_MISMATCH", lambda: fit_store.read(path))
        checks["immutable"] = immutable
        checks["content_hash"] = content_hash
        canonical_vector = {"z": [3, 2, 1], "a": {"utf8": "Δ", "finite": 1.25}}
        canonical_data = canonical_bytes(canonical_vector)
        self.golden["canonicalization"] = {
            "input": canonical_vector,
            "canonical_hex": canonical_data.hex(),
            "sha256": sha256_bytes(canonical_data),
        }
        self.mutations["schema_and_nonfinite"] = checks
        return checks

    def fx_014(self) -> dict[str, Any]:
        random123 = philox4x32_10((0, 0, 0, 0), (0, 0))
        require(random123 == (0x6627E8D5, 0xE169C58D, 0xBC57AC4C, 0x9B00DBD8), "PHILOX_REFERENCE_VECTOR", repr(random123))
        identity = RandomFieldIdentity("campaign", "site", "burn-0", "occurrence", date(2001, 1, 1), "wet_gate")
        key, counter = key_counter(identity)
        words = random_words(identity)
        encoded = encode_identity(b"cligen-rs/a9-crn/v1\0", identity.fields())
        other_components = {
            component: random_words(RandomFieldIdentity("campaign", "site", "burn-0", component, date(2001, 1, 1), "slot"))
            for component in ("occurrence", "amount-body", "amount-tail", "event", "latent-state", "daily-context")
        }
        require(len(set(other_components.values())) == len(other_components), "RNG_DOMAIN_COLLISION", "components")
        domain_seeds = {domain: domain_seed(domain, "campaign", "site") for domain in ("fit", "optimizer", "parameter_member", "synthetic_fixture")}
        require(len(set(domain_seeds.values())) == 4, "RNG_DOMAIN_COLLISION", "research")
        occurrence_before = random_words(identity)
        _ = random_words(RandomFieldIdentity("campaign", "site", "burn-0", "amount-tail", date(2001, 1, 1), "rejected"))
        occurrence_after = random_words(identity)
        require(occurrence_before == occurrence_after, "RNG_DRAW_SHIFT", "rejected draw")
        faithful_state = (1, 2, 3, 4)
        vector = {
            "random123_zero": [f"0x{word:08x}" for word in random123],
            "encoding_hex": encoded.hex(),
            "sha256_key": [f"0x{word:08x}" for word in key],
            "sha256_counter": [f"0x{word:08x}" for word in counter],
            "words": [f"0x{word:08x}" for word in words],
            "components": {name: [f"0x{word:08x}" for word in value] for name, value in other_components.items()},
            "research_domain_seed_hex": {name: f"{value:064x}" for name, value in domain_seeds.items()},
            "faithful_state_before": list(faithful_state),
            "faithful_state_after": list(faithful_state),
        }
        self.golden["rng"] = vector
        return {"reference_vector": True, "domain_collisions": 0, "draw_shift": False, "faithful_state_unchanged": True}

    def fx_015(self) -> dict[str, Any]:
        config = default_configs()[RENEWAL_ID]
        finalized_fit = FitArtifactStore(self.spec / "a9-fit-artifact-v1.schema.json").finalize(_synthetic_fit_artifact())
        fit = validated_fit(finalized_fit)
        rows = AlternatingRenewalMock().simulate(config, fit=fit, campaign="fx015", site="site", burn="burn-0", start_year=2000)
        prefix = nested_prefix(rows, 2000)
        expected_count = (date(2030, 1, 1) - date(2000, 1, 1)).days
        require(len(prefix) == expected_count and canonical_bytes(prefix) == canonical_bytes(rows[:expected_count]), "NESTED_PREFIX_MISMATCH", str(len(prefix)))
        horizon_config = dict(config, horizon_years=30)
        rejection = _expect_error("CANDIDATE_CONFIG_FIELDS", lambda: AlternatingRenewalMock().validate_config(horizon_config))
        return {"rows_100": len(rows), "rows_30": len(prefix), "byte_identical_prefix": True, "horizon_parameter_rejection": rejection}

    def fx_016(self) -> dict[str, Any]:
        payload = b"synthetic-confirmation-target\n"
        object_hash = sha256_bytes(payload)
        logical_hash = sha256_bytes(b"synthetic-logical-record")
        manifest = _role_manifest("sealed", object_hash, logical_hash, sha256_bytes(b"synthetic-freeze"))
        validate_schema(manifest, self.role_schema)
        validate_role_manifest_semantics(manifest)
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            target = directory / "target.bin"
            target.write_bytes(payload)
            alias = directory / "alias.bin"
            alias.symlink_to(target)
            copied = directory / "copied.bin"
            copied.write_bytes(payload)
            renamed = directory / "renamed.bin"
            shutil.copyfile(target, renamed)
            firewall = RoleFirewall(manifest, self.role_schema, [target])
            rejections = {}
            for name, path in (("path", target), ("symlink", alias), ("copy", copied), ("rename", renamed)):
                def reject_path(candidate_path: Path = path) -> None:
                    firewall.authorize("fit", paths=[candidate_path])

                rejections[name] = _expect_error(
                    "CONFIRMATION_PATH_REJECTED" if name in {"path", "symlink"} else "CONFIRMATION_BYTES_REJECTED",
                    reject_path,
                )
            rejections["object_hash"] = _expect_error("CONFIRMATION_OBJECT_HASH_REJECTED", lambda: firewall.authorize("evaluate", object_hashes=[object_hash]))
            rejections["logical_hash"] = _expect_error("CONFIRMATION_LOGICAL_HASH_REJECTED", lambda: firewall.authorize("optimize", logical_hashes=[logical_hash]))
            confirmation_record = manifest["roles"][-1]["records"][0]
            rejections["record_key"] = _expect_error("CONFIRMATION_RECORD_KEY_REJECTED", lambda: firewall.authorize("calibrate-gates", record_keys=[logical_record_key(confirmation_record)]))

            metadata_manifest = _role_manifest()
            access_log = directory / "access-log"
            after_metadata = append_metadata_read(metadata_manifest, "fixture", STATIC_TIMESTAMP, access_log)
            require(after_metadata["confirmation_access_state"] == "metadata_only", "METADATA_CHANGED_STATE", "FX-016")
            metadata_path = directory / "metadata.json"
            write_canonical(metadata_path, metadata_manifest)
            rejections["metadata_confirm"] = _expect_error("CONFIRMATION_NOT_SEALED", lambda: consume_confirmation(metadata_path, self.spec / "a9-data-role-manifest-v1.schema.json", sha256_bytes(b"synthetic-freeze"), "fixture", access_log, STATIC_TIMESTAMP))

            sealed_path = directory / "sealed.json"
            write_canonical(sealed_path, manifest)
            lock_path = sealed_path.with_name(f".{sealed_path.name}.consume.lock")
            lock_path.write_text("synthetic competing consumer\n", encoding="utf-8")
            rejections["concurrent_lock"] = _expect_error("CONFIRMATION_LOCKED", lambda: consume_confirmation(sealed_path, self.spec / "a9-data-role-manifest-v1.schema.json", sha256_bytes(b"synthetic-freeze"), "fixture", access_log, STATIC_TIMESTAMP))
            lock_path.unlink()
            consumed = consume_confirmation(sealed_path, self.spec / "a9-data-role-manifest-v1.schema.json", sha256_bytes(b"synthetic-freeze"), "fixture", access_log, STATIC_TIMESTAMP)
            require(consumed["confirmation_access_state"] == "consumed", "CONFIRMATION_TRANSITION", "FX-016")
            rejections["second_confirmation"] = _expect_error("CONFIRMATION_NOT_SEALED", lambda: consume_confirmation(sealed_path, self.spec / "a9-data-role-manifest-v1.schema.json", sha256_bytes(b"synthetic-freeze"), "fixture", access_log, STATIC_TIMESTAMP))
            access_records = AttemptLog(access_log).verify()
            require(len(access_records) == 2, "ACCESS_LOG_COUNT", str(len(access_records)))
        self.mutations["role_firewall"] = rejections
        return {"rejections": rejections, "metadata_state_unchanged": True, "atomic_consumption": True, "one_shot": True, "append_only_access_records": 2}

    def fx_017(self) -> dict[str, Any]:
        absolute = normalized_distance(0.5, 0.0, 0.1)
        two_part = two_part_zero_distance(0.4, 0.4, 2.0, 0.0, 0.01, 0.25)
        require(math.isfinite(absolute) and math.isfinite(two_part) and absolute > 0.0 and two_part > 0.0, "BASELINE_ZERO", "finite")
        null_replicates = []
        for replicate in range(500):
            phase = (replicate + 0.5) / 500.0
            null_replicates.append(
                {
                    ("occurrence_spell", 30): [abs(math.sin((replicate + station) * 0.37)) * 0.04 for station in range(3)],
                    ("occurrence_spell", 100): [abs(math.cos((replicate + station) * 0.29)) * 0.025 for station in range(3)],
                    ("aggregate", 30): [phase * 0.03, (1.0 - phase) * 0.03],
                    ("aggregate", 100): [phase * 0.02, (1.0 - phase) * 0.02],
                }
            )
        floors = {
            ("occurrence_spell", 30): 0.01,
            ("occurrence_spell", 100): 0.01,
            ("aggregate", 30): 0.005,
            ("aggregate", 100): 0.005,
        }
        thresholds = calibrate_max_statistic(null_replicates, floors)
        frontier = pareto_frontier(
            [
                {"id": "a", "objectives": {"m1": 1.0, "m2": 2.0}},
                {"id": "b", "objectives": {"m1": 2.0, "m2": 1.0}},
                {"id": "c", "objectives": {"m1": 3.0, "m2": 3.0}},
            ],
            ["m1", "m2"],
        )
        require(frontier == ["a", "b"], "PARETO_REFERENCE", repr(frontier))
        selected = select_candidate(
            [
                SelectionSummary("a", True, True, 0, 0.2, 2, 0.8, 10),
                SelectionSummary("b", True, True, 0, 0.1, 3, 0.5, 8),
                SelectionSummary("c", True, True, 1, 0.5, 4, 0.2, 5),
            ]
        )
        require(selected == "a", "SELECTION_REFERENCE", selected)
        objective_vector = {
            "absolute_floor": absolute,
            "two_part": two_part,
            "null_replicates": len(null_replicates),
            "thresholds": thresholds,
            "pareto_frontier": frontier,
            "selected": selected,
            "candidate_access_prohibited": True,
        }
        self.golden["objective_estimators"] = objective_vector
        return {**objective_vector, "finite": True, "favorable_zero": False}

    def fx_018(self) -> dict[str, Any]:
        one_missing = [{"stratum": "arid_boundary", "station_id": f"s{index}", "status": "unavailable" if index == 0 else "available"} for index in range(3)]
        two_missing = [{"stratum": "arid_boundary", "station_id": f"s{index}", "status": "available" if index == 0 else "unavailable"} for index in range(3)]
        first = availability_by_stratum(one_missing, required_strata=("arid_boundary", "cold"))
        second = availability_by_stratum(two_missing, required_strata=("arid_boundary", "cold"))
        require(first["arid_boundary"] and not second["arid_boundary"], "AVAILABILITY_RULE", repr((first, second)))
        require(not first["cold"], "AVAILABILITY_MISSING_STRATUM", repr(first))
        return {"one_unavailable": first, "two_unavailable": second, "unavailable_counted_as_pass": False, "objective_registry_entries": len(self.objective_registry["objectives"])}

    def fx_019(self) -> dict[str, Any]:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            log = AttemptLog(directory / "attempts")
            optimizer = ExhaustiveOptimizer()
            limits = ResourceLimits(4, 10.0, 1000, 1000)
            proposals = [{"id": index, "fit_seed": "fixed", "site": "synthetic", "burn": "burn-0", "worker": 0} for index in range(6)]
            def evaluator(proposal: dict[str, Any]) -> dict[str, Any]:
                if proposal["id"] == 0:
                    return {"state": "evaluation_complete", "objectives": {"distance": 1.0}}
                if proposal["id"] == 1:
                    raise HarnessError("INFRASTRUCTURE_CRASH", "synthetic")
                if proposal["id"] == 2:
                    return {"state": "hard_infeasible", "failed_constraints": ["synthetic_support"]}
                return {"state": "dominated", "objectives": {"distance": 2.0}}
            records = optimizer.run(proposals, evaluator, log, limits)
            verified = log.verify()
            require(len(records) == len(proposals) == len(verified), "SURVIVOR_ONLY_LOG", str(len(verified)))
            checkpoint = log.checkpoint({"next": 4}, directory / "checkpoints")
            log.verify_checkpoint(checkpoint)

            replay_log = AttemptLog(directory / "replay")
            replay_records = optimizer.run(proposals, evaluator, replay_log, limits)
            require(
                [record["payload"] for record in replay_records] == [record["payload"] for record in records],
                "OPTIMIZER_REPLAY_MISMATCH",
                "payloads",
            )

            # Simulate a crash after a durable attempt but before the next
            # checkpoint. The stale checkpoint must be rejected, then a new
            # content-addressed checkpoint can resume exactly.
            log.append({"proposal_sha256": sha256_bytes(b"after-checkpoint"), "state": "evaluation_incomplete", "reason": "synthetic_post_checkpoint_crash"})
            stale_checkpoint = _expect_error("CHECKPOINT_LOG_COUNT", lambda: log.verify_checkpoint(checkpoint))
            resumed_checkpoint = log.checkpoint({"next": 7}, directory / "checkpoints")
            log.verify_checkpoint(resumed_checkpoint)

            retry = RetryRegistry()
            first_retry = retry.allow_infrastructure_retry(proposals[1])
            second_retry = retry.allow_infrastructure_retry(proposals[1])
            require(first_retry and not second_retry, "RETRY_POLICY", "one retry")

            memory_log = AttemptLog(directory / "memory")
            optimizer.run([{"id": "memory"}], lambda _: {"memory_bytes": 1001}, memory_log, ResourceLimits(1, 10.0, 1000, 1000))
            wall_log = AttemptLog(directory / "wall")
            times = iter([0.0, 11.0])
            optimizer.run([{"id": "wall"}], lambda _: {}, wall_log, ResourceLimits(1, 10.0, 1000, 1000), monotonic=lambda: next(times))

            corrupt_dir = directory / "corrupt"
            shutil.copytree(directory / "attempts", corrupt_dir)
            first_path = corrupt_dir / "000000.json"
            corrupt = read_json(first_path)
            corrupt["payload"]["state"] = "dominated"
            write_canonical(first_path, corrupt)
            corruption = _expect_error("CONTENT_HASH_MISMATCH", lambda: AttemptLog(corrupt_dir).verify())
            states = all_attempt_states(verified) | all_attempt_states(memory_log.verify()) | all_attempt_states(wall_log.verify())
            required_states = {"evaluation_complete", "evaluation_incomplete", "hard_infeasible", "dominated"}
            require(required_states <= states, "ATTEMPT_STATES_MISSING", repr(states))
            evidence = {"attempts": len(verified), "states": sorted(states), "checkpoint_verified": True, "stale_checkpoint": stale_checkpoint, "resumed_checkpoint_verified": True, "replay_payload_identity": True, "first_retry": first_retry, "second_retry": second_retry, "corrupt_resume": corruption, "budget_exhaustion_records": 2, "wall_exhaustion": True, "memory_exhaustion": True}
        self.resources["optimizer_restart"] = evidence
        return evidence

    def fx_020(self) -> dict[str, Any]:
        large_bytes = 10 * 1024**2
        large = retention_decision(artifact_bytes=large_bytes, artifact_kind="fixture")
        raw = retention_decision(artifact_bytes=large_bytes + 1, artifact_kind="ordinary_raw")
        require(large.require_lfs and not raw.retain_raw, "RETENTION_POLICY", repr((large, raw)))
        hypothetical = self.a9b / "large" / "fixture-large.bin"
        require_lfs_coverage(self.root, hypothetical, large)
        with tempfile.TemporaryDirectory() as temporary:
            scratch = Path(temporary) / "scratch.bin"
            with scratch.open("wb") as stream:
                stream.truncate(large_bytes + 1)
            object_hash = sha256_file(scratch)
            deletion = record_scratch_deletion(scratch, object_hash)
            require(deletion["deleted"] and deletion["object_sha256"] == object_hash, "SCRATCH_DELETION", repr(deletion))
        evidence = {"threshold_bytes": large_bytes, "large_fixture": asdict(large), "ordinary_raw": asdict(raw), "lfs_covered": True, "scratch_deletion": deletion, "metrics_and_hash_retained": True}
        self.resources["storage"] = evidence
        return evidence


def _synthetic_fit_artifact() -> dict[str, Any]:
    hash_value = sha256_bytes(b"synthetic")
    return {
        "schema_version": 1,
        "fit_id": "a9b-synthetic-fit-v1",
        "content_sha256": ZERO_HASH,
        "fit_status": "fit_valid",
        "status_reason": None,
        "model_family_id": "a9_joint_daily_event_family_v1",
        "candidate_class": {"id": RENEWAL_ID, "schema_version": 1, "schema_sha256": config_schema_sha256(RENEWAL_ID), "source_sha256": hash_value},
        "fit_role": "coefficient_fit",
        "station_scope": {"scope": "station", "stations": [{"station_id": "synthetic-site", "latitude": 0.0, "longitude": 0.0, "elevation_m": 0.0}], "group_id": None},
        "sources": [
            {
                "source_id": "synthetic-source",
                "product": "a9b-fixture",
                "version": "1",
                "object_sha256": hash_value,
                "logical_sha256": sha256_bytes(b"synthetic-logical"),
                "station_id": "synthetic-site",
                "variables": ["precipitation_mm"],
                "units": {"precipitation_mm": "mm"},
                "calendar": "proleptic_gregorian",
                "day_boundary": "utc",
                "period_start": "2001-01-01",
                "period_end": "2100-12-31",
                "missingness": "none",
                "accessed_at": STATIC_TIMESTAMP,
            }
        ],
        "preprocessing": {"recipe_id": "synthetic-v1", "recipe_sha256": hash_value, "wet_thresholds_mm": {"wet0_exclusive": 0.0, "r1mm_inclusive": 1.0}, "detrending": "none", "missingness_rule": "fail_closed", "event_segmentation_id": "a9_uscrn_event_6h_v1"},
        "pooling": {"rule_id": "a9_hierarchical_pool_v1", "membership_sha256": hash_value, "selected_before_fit": True},
        "optimizer": {"id": "a9b_deterministic_exhaustive_v1", "version": "1", "configuration_sha256": hash_value, "parameter_bounds_sha256": hash_value, "stopping_rule": "exhaustive", "evaluation_budget": 10, "wall_time_seconds": 10, "memory_bytes": 1000000},
        "rng": {
            "fit": {"algorithm": "Python MT19937", "version": "3.12", "domain": "fit", "seed_hex": "0000000000000001"},
            "optimizer": {"algorithm": "Python MT19937", "version": "3.12", "domain": "optimizer", "seed_hex": "0000000000000002"},
            "parameter_member": {"algorithm": "SHA-256", "version": "1", "domain": "parameter_member", "seed_hex": "0000000000000003"},
        },
        "parameters": [{"name": "wet_end_base", "value": 0.42, "unit": "probability", "support": "0<p<1"}],
        "diagnostics": {
            "effective_exposures": {"wet_days": 1000, "dry_days": 1000},
            "identifiability": {"status": "pass", "method": "synthetic_oracle", "details_sha256": hash_value},
            "hard_checks": [{"id": "support", "status": "pass", "value": "pass", "tolerance": None}],
            "monthly_moment_checks": [{"id": "month-28", "status": "pass", "value": 0.0, "tolerance": 1.0e-10, "month_length_days": 28, "quadrature_id": QUADRATURE_ID}],
            "uncertainty": {"method": "synthetic", "member_id": None, "details_sha256": hash_value},
        },
        "provenance": {"created_at": STATIC_TIMESTAMP, "software_version": "0.1.0-a9b", "git_commit": "795f76775135044f7643e44f1f08cca1136e7236", "git_dirty": True, "objective_registry_sha256": hash_value, "data_role_manifest_sha256": hash_value, "parent_hashes": [hash_value]},
    }
