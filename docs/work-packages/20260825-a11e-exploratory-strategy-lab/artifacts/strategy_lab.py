#!/usr/bin/env python3
"""Research-only numerical core for the A11 exploratory strategy lab."""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from statistics import NormalDist
from typing import Any, Iterable

import numpy as np


STRATEGY_IDS = {
    "gaussian_latent_scalar_ar1_v1",
    "circular_fixed_block_bootstrap_v1",
}
CAPABILITIES = {
    "annual_monthly_targets",
    "core_daily",
    "storm_descriptors",
    "secondary_context",
    "wepp",
}
EVALUATION_STAGES = {
    "synthetic",
    "candidate_fit_cross_validation",
    "held_out_development",
    "wepp_diagnostic",
}
RNG_DOMAINS = {
    "annual_target",
    "wet_count",
    "occurrence",
    "amount",
    "temperature",
    "range",
}
NORMAL = NormalDist()
CORE_CAPABILITIES = ["annual_monthly_targets", "core_daily"]
CORE_STAGES = ["synthetic", "candidate_fit_cross_validation", "held_out_development"]
EVALUATOR_ID = "a11e_core_diagnostics_v1"
METRIC_SET_ID = "a11e_core_metrics_v1"
UNCERTAINTY_ID = "a11e_descriptive_bootstrap_v1"


class ContractError(ValueError):
    """A strict exploratory strategy contract was violated."""


@dataclass(frozen=True)
class DomainRng:
    """A Philox stream carrying the domain identity required by the contract."""

    experiment_id: str
    strategy_id: str
    member: int
    domain: str
    generator: np.random.Generator
    stream_key: tuple[int, ...]

    def random(self, *args: Any, **kwargs: Any) -> Any:
        return self.generator.random(*args, **kwargs)

    def integers(self, *args: Any, **kwargs: Any) -> Any:
        return self.generator.integers(*args, **kwargs)

    def standard_normal(self, *args: Any, **kwargs: Any) -> Any:
        return self.generator.standard_normal(*args, **kwargs)


def _require_rng(value: Any, domain: str, strategy_id: str | None = None) -> DomainRng:
    expected_key = None
    if isinstance(value, DomainRng):
        expected_key = _philox_key(_domain_seed(value.experiment_id, value.strategy_id, value.member, value.domain))
    if (
        not isinstance(value, DomainRng)
        or value.domain != domain
        or (strategy_id is not None and value.strategy_id != strategy_id)
        or not isinstance(value.generator.bit_generator, np.random.Philox)
        or value.stream_key != expected_key
        or _current_philox_key(value.generator) != expected_key
    ):
        raise ContractError(f"{domain} requires its registered Philox domain stream")
    return value


def _validate_model_identity(model: Any, strategy_id: str) -> None:
    if (
        not isinstance(model, dict)
        or model.get("strategy_id") != strategy_id
        or model.get("fit_transform") != "within_site_sample_standardization"
        or not isinstance(model.get("region_id"), str)
        or not model["region_id"]
        or model.get("data_role") != "candidate_fit"
    ):
        raise ContractError("model provenance identity is invalid")


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def validate_manifest(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError("manifest must be an object")
    expected = {"schema_version", "manifest_id", "exploratory", "promotion_authority", "rng", "strategies"}
    if set(value) != expected:
        raise ContractError("manifest fields differ from revision 1")
    if (
        value["schema_version"] != 1
        or value["manifest_id"] != "a11e-strategy-manifest-v1"
        or value["exploratory"] is not True
        or value["promotion_authority"] is not False
    ):
        raise ContractError("manifest identity or authority is invalid")
    random = value["rng"]
    if not isinstance(random, dict) or set(random) != {"algorithm", "numpy_version", "domains"}:
        raise ContractError("rng record is not strict")
    if random["algorithm"] != "numpy_philox" or random["numpy_version"] != "2.3.5":
        raise ContractError("rng implementation identity differs")
    if not isinstance(random["domains"], list) or set(random["domains"]) != RNG_DOMAINS or len(random["domains"]) != len(RNG_DOMAINS):
        raise ContractError("rng domains are incomplete or duplicated")
    strategies = value["strategies"]
    if not isinstance(strategies, list) or not strategies:
        raise ContractError("at least one strategy is required")
    identifiers = []
    for strategy in strategies:
        if not isinstance(strategy, dict):
            raise ContractError("strategy must be an object")
        common = {
            "strategy_id", "fit_transform", "annual_law", "capabilities", "evaluation_stages",
            "evaluator_id", "metric_set_id", "uncertainty_id",
        }
        allowed = common | {"block_length_years"}
        if not common.issubset(strategy) or not set(strategy).issubset(allowed):
            raise ContractError("strategy fields are incomplete or unknown")
        identifier = strategy["strategy_id"]
        if identifier not in STRATEGY_IDS:
            raise ContractError("strategy identifier is not registered")
        if strategy["fit_transform"] != "within_site_sample_standardization":
            raise ContractError("fit transform differs")
        if not isinstance(strategy["annual_law"], str) or len(strategy["annual_law"]) < 16:
            raise ContractError("annual law is not descriptive")
        if strategy["capabilities"] != CORE_CAPABILITIES:
            raise ContractError("initial strategy capabilities differ from the implemented core")
        if strategy["evaluation_stages"] != CORE_STAGES:
            raise ContractError("initial strategy stages differ from the registered evaluator")
        if (
            strategy["evaluator_id"] != EVALUATOR_ID
            or strategy["metric_set_id"] != METRIC_SET_ID
            or strategy["uncertainty_id"] != UNCERTAINTY_ID
        ):
            raise ContractError("strategy evaluation identities differ")
        if identifier == "circular_fixed_block_bootstrap_v1":
            block = strategy.get("block_length_years")
            if not isinstance(block, int) or isinstance(block, bool) or not 2 <= block <= 30:
                raise ContractError("block strategy requires a 2..30 year block")
        elif "block_length_years" in strategy:
            raise ContractError("block length is valid only for block bootstrap")
        identifiers.append(identifier)
    if len(set(identifiers)) != len(identifiers) or set(identifiers) != STRATEGY_IDS:
        raise ContractError("revision 1 requires each initial strategy exactly once")
    return value


def _domain_seed(experiment_id: str, strategy_id: str, member: int, domain: str) -> int:
    payload = f"a11e-v1\0{experiment_id}\0{strategy_id}\0{member}\0{domain}".encode()
    return int.from_bytes(hashlib.blake2b(payload, digest_size=8).digest(), "little")


def _current_philox_key(generator: np.random.Generator) -> tuple[int, ...]:
    return tuple(int(value) for value in generator.bit_generator.state["state"]["key"])


def _philox_key(seed: int) -> tuple[int, ...]:
    return _current_philox_key(np.random.Generator(np.random.Philox(seed)))


def domain_rng(experiment_id: str, strategy_id: str, member: int, domain: str) -> DomainRng:
    if (
        not isinstance(experiment_id, str) or not experiment_id
        or strategy_id not in STRATEGY_IDS or domain not in RNG_DOMAINS
        or not isinstance(member, int) or isinstance(member, bool) or member < 0
    ):
        raise ContractError("invalid random-domain request")
    seed = _domain_seed(experiment_id, strategy_id, member, domain)
    generator = np.random.Generator(np.random.Philox(seed))
    return DomainRng(experiment_id, strategy_id, member, domain, generator, _current_philox_key(generator))


def domain_rngs(experiment_id: str, strategy_id: str, member: int) -> dict[str, DomainRng]:
    return {domain: domain_rng(experiment_id, strategy_id, member, domain) for domain in sorted(RNG_DOMAINS)}


def _finite_matrix(values: Any, name: str) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 2 or min(array.shape) < 1 or not np.isfinite(array).all():
        raise ContractError(f"{name} must be a nonempty finite matrix")
    return array


def within_site_standardize(
    site_ids: Iterable[str], years: Iterable[int], values: Any
) -> dict[str, Any]:
    matrix = _finite_matrix(values, "site-year values")
    sites = list(site_ids)
    year_values = list(years)
    if len(sites) != len(matrix) or len(year_values) != len(matrix):
        raise ContractError("site/year/value lengths differ")
    groups: dict[str, list[int]] = defaultdict(list)
    for index, (site, year) in enumerate(zip(sites, year_values)):
        if not isinstance(site, str) or not site or not isinstance(year, int) or isinstance(year, bool):
            raise ContractError("site and year identities are invalid")
        groups[site].append(index)
    anomalies = np.empty_like(matrix)
    summaries = {}
    sequences = {}
    for site in sorted(groups):
        indices = sorted(groups[site], key=lambda index: year_values[index])
        ordered_years = [year_values[index] for index in indices]
        if (
            len(indices) < 3
            or len(set(ordered_years)) != len(ordered_years)
            or ordered_years != list(range(ordered_years[0], ordered_years[0] + len(ordered_years)))
        ):
            raise ContractError("each site needs at least three unique years")
        rows = matrix[indices]
        means = np.mean(rows, axis=0, dtype=np.float64)
        scales = np.std(rows, axis=0, ddof=1, dtype=np.float64)
        if np.any(~np.isfinite(scales)) or np.any(scales <= 0.0):
            raise ContractError(f"site has constant or invalid fit field: {site}")
        standardized = (rows - means) / scales
        anomalies[indices] = standardized
        summaries[site] = {"means": means.tolist(), "sample_scales": scales.tolist()}
        sequences[site] = {"years": ordered_years, "values": standardized.tolist()}
    return {
        "anomalies": anomalies,
        "site_summaries": summaries,
        "sequences": sequences,
    }


def _validate_fit_cohort(site_ids: Iterable[str], years: Iterable[int], region_id: str, data_role: str) -> None:
    if not isinstance(region_id, str) or not region_id or data_role != "candidate_fit":
        raise ContractError("fit requires a registered region and candidate_fit role")
    groups: dict[str, list[int]] = defaultdict(list)
    for site, year in zip(site_ids, years):
        groups[site].append(year)
    if not groups or any(len(site_years) != 30 for site_years in groups.values()):
        raise ContractError("registered strategy fitting requires exactly 30 years per site")


def average_ranks(values: Any) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1 or not len(array) or not np.isfinite(array).all():
        raise ContractError("rank input must be a finite vector")
    order = np.argsort(array, kind="stable")
    ranks = np.empty(len(array), dtype=np.float64)
    start = 0
    while start < len(array):
        end = start + 1
        while end < len(array) and array[order[end]] == array[order[start]]:
            end += 1
        ranks[order[start:end]] = (start + 1 + end) / 2.0
        start = end
    return ranks


def rank_gaussian(values: Any) -> np.ndarray:
    matrix = _finite_matrix(values, "rank-Gaussian input")
    output = np.empty_like(matrix)
    count = len(matrix)
    for column in range(matrix.shape[1]):
        probabilities = (average_ranks(matrix[:, column]) - 0.5) / count
        output[:, column] = [NORMAL.inv_cdf(float(value)) for value in probabilities]
    return output


def nearest_correlation(values: Any, tolerance: float = 1e-10) -> tuple[np.ndarray, dict[str, float]]:
    matrix = _finite_matrix(values, "correlation")
    if matrix.shape[0] != matrix.shape[1] or tolerance <= 0.0:
        raise ContractError("correlation shape or tolerance is invalid")
    symmetric = (matrix + matrix.T) / 2.0
    requested_eigenvalues, eigenvectors = np.linalg.eigh(symmetric)
    clipped = np.maximum(requested_eigenvalues, tolerance)
    effective = (eigenvectors * clipped) @ eigenvectors.T
    diagonal = np.sqrt(np.diag(effective))
    if np.any(diagonal <= 0.0):
        raise ContractError("correlation projection has nonpositive diagonal")
    effective = effective / np.outer(diagonal, diagonal)
    effective = (effective + effective.T) / 2.0
    return effective, {
        "requested_min_eigenvalue": float(np.min(requested_eigenvalues)),
        "effective_min_eigenvalue": float(np.min(np.linalg.eigvalsh(effective))),
        "frobenius_adjustment": float(np.linalg.norm(effective - symmetric, ord="fro")),
    }


def _psd(matrix: np.ndarray, tolerance: float) -> bool:
    return float(np.min(np.linalg.eigvalsh((matrix + matrix.T) / 2.0))) >= -tolerance


def _boundary(diagonal: np.ndarray, off_diagonal: np.ndarray, direction: float, tolerance: float) -> float:
    feasible = 0.0
    candidate = direction
    while abs(candidate) <= 1e6 and _psd(diagonal + candidate * off_diagonal, tolerance):
        feasible = candidate
        candidate *= 2.0
    if abs(candidate) > 1e6:
        return candidate / 2.0
    infeasible = candidate
    for _ in range(100):
        midpoint = (feasible + infeasible) / 2.0
        if _psd(diagonal + midpoint * off_diagonal, tolerance):
            feasible = midpoint
        else:
            infeasible = midpoint
    return feasible


def reconcile_covariance(
    requested_covariance: Any,
    monthly_variances: Any,
    annual_weights: Any,
    requested_annual_variance: float,
    tolerance: float = 1e-10,
) -> tuple[np.ndarray, dict[str, Any]]:
    requested = _finite_matrix(requested_covariance, "requested covariance")
    variances = np.asarray(monthly_variances, dtype=np.float64)
    weights = np.asarray(annual_weights, dtype=np.float64)
    size = requested.shape[0]
    if (
        requested.shape != (size, size)
        or variances.shape != (size,)
        or weights.shape != (size,)
        or not np.isfinite(variances).all()
        or not np.isfinite(weights).all()
        or not np.any(weights != 0.0)
        or np.any(variances < 0.0)
        or not math.isfinite(requested_annual_variance)
        or requested_annual_variance < 0.0
        or tolerance <= 0.0
    ):
        raise ContractError("covariance reconciliation input is invalid")
    if not np.allclose(requested, requested.T, atol=tolerance, rtol=0.0):
        raise ContractError("requested covariance must be symmetric")
    if not np.allclose(np.diag(requested), variances, atol=tolerance, rtol=0.0):
        raise ContractError("requested covariance diagonal differs from monthly variances")
    symmetric = requested.copy()
    diagonal = np.diag(variances)
    off_diagonal = symmetric - np.diag(np.diag(symmetric))
    base_annual = float(weights @ diagonal @ weights)
    off_annual = float(weights @ off_diagonal @ weights)
    lower = _boundary(diagonal, off_diagonal, -1.0, tolerance)
    upper = _boundary(diagonal, off_diagonal, 1.0, tolerance)
    if lower > upper:
        raise ContractError("PSD interval is empty")
    if abs(off_annual) <= tolerance:
        requested_alpha = 1.0 if abs(requested_annual_variance - base_annual) <= tolerance else 0.0
    else:
        requested_alpha = (requested_annual_variance - base_annual) / off_annual
    effective_alpha = float(np.clip(requested_alpha, lower, upper))
    effective = diagonal + effective_alpha * off_diagonal
    effective = (effective + effective.T) / 2.0
    effective_annual = float(weights @ effective @ weights)
    if not _psd(effective, tolerance) or not np.allclose(np.diag(effective), variances, atol=tolerance, rtol=0.0):
        raise ContractError("reconciled covariance violates constraints")
    return effective, {
        "requested_alpha": requested_alpha,
        "effective_alpha": effective_alpha,
        "feasible_alpha_interval": [lower, upper],
        "requested_annual_variance": requested_annual_variance,
        "effective_annual_variance": effective_annual,
        "minimum_eigenvalue": float(np.min(np.linalg.eigvalsh(effective))),
        "projected_to_boundary": (
            effective_alpha != requested_alpha
            or abs(effective_annual - requested_annual_variance) > tolerance
        ),
        "annual_target_satisfied": abs(effective_annual - requested_annual_variance) <= tolerance,
        "tolerance": tolerance,
    }


def apply_location_scale(standardized_anomalies: Any, location: Any, scale: Any) -> np.ndarray:
    anomalies = _finite_matrix(standardized_anomalies, "standardized anomalies")
    locations = np.asarray(location, dtype=np.float64)
    scales = np.asarray(scale, dtype=np.float64)
    if (
        locations.shape != (anomalies.shape[1],)
        or scales.shape != (anomalies.shape[1],)
        or not np.isfinite(locations).all()
        or not np.isfinite(scales).all()
        or np.any(scales < 0.0)
    ):
        raise ContractError("location/scale forcing is invalid")
    return locations + anomalies * scales


def _estimate_scalar_persistence(
    site_ids: Iterable[str], years: Iterable[int], latent: np.ndarray
) -> float:
    sites = list(site_ids)
    year_values = list(years)
    groups: dict[str, list[int]] = defaultdict(list)
    for index, site in enumerate(sites):
        groups[site].append(index)
    numerator = 0.0
    denominator = 0.0
    for site in sorted(groups):
        indices = sorted(groups[site], key=lambda index: year_values[index])
        values = latent[indices]
        numerator += float(np.sum(values[:-1] * values[1:]))
        denominator += float(np.sum(values[:-1] * values[:-1]))
    if denominator <= 0.0:
        raise ContractError("persistence denominator is zero")
    return float(np.clip(numerator / denominator, -0.8, 0.8))


def fit_gaussian_ar1(
    site_ids: Iterable[str], years: Iterable[int], values: Any, region_id: str, data_role: str = "candidate_fit"
) -> dict[str, Any]:
    sites = list(site_ids)
    year_values = list(years)
    _validate_fit_cohort(sites, year_values, region_id, data_role)
    standardized = within_site_standardize(sites, year_values, values)
    anomalies = standardized["anomalies"]
    latent = rank_gaussian(anomalies)
    correlation, projection = nearest_correlation(np.corrcoef(latent, rowvar=False))
    return {
        "strategy_id": "gaussian_latent_scalar_ar1_v1",
        "correlation": correlation.tolist(),
        "scalar_persistence": _estimate_scalar_persistence(sites, year_values, latent),
        "projection_receipt": projection,
        "anomaly_correlation": correlation.tolist(),
        "generation_mean": np.zeros(correlation.shape[0], dtype=np.float64).tolist(),
        "generation_covariance": correlation.tolist(),
        "fit_transform": "within_site_sample_standardization",
        "region_id": region_id,
        "data_role": data_role,
    }


def generate_gaussian_ar1(model: dict[str, Any], years: int, generator: DomainRng) -> np.ndarray:
    _validate_model_identity(model, "gaussian_latent_scalar_ar1_v1")
    if not isinstance(years, int) or isinstance(years, bool) or years < 1:
        raise ContractError("Gaussian generation request is invalid")
    generator = _require_rng(generator, "annual_target", model.get("strategy_id"))
    correlation = _finite_matrix(model.get("correlation"), "model correlation")
    if (
        correlation.shape[0] != correlation.shape[1]
        or not _psd(correlation, 1e-10)
        or not np.allclose(np.diag(correlation), 1.0, atol=1e-10, rtol=0.0)
    ):
        raise ContractError("model correlation is invalid")
    phi = float(model.get("scalar_persistence"))
    if not math.isfinite(phi) or not -0.8 <= phi <= 0.8:
        raise ContractError("model persistence is invalid")
    eigenvalues, eigenvectors = np.linalg.eigh(correlation)
    root = eigenvectors @ np.diag(np.sqrt(np.maximum(eigenvalues, 0.0)))
    latent = np.empty((years, len(correlation)), dtype=np.float64)
    latent[0] = generator.standard_normal(len(correlation)) @ root.T
    innovation_scale = math.sqrt(1.0 - phi * phi)
    for year in range(1, years):
        innovation = generator.standard_normal(len(correlation)) @ root.T
        latent[year] = phi * latent[year - 1] + innovation_scale * innovation
    return latent


def fit_block_bootstrap(
    site_ids: Iterable[str], years: Iterable[int], values: Any, block_length_years: int,
    region_id: str, data_role: str = "candidate_fit",
) -> dict[str, Any]:
    if not isinstance(block_length_years, int) or isinstance(block_length_years, bool) or block_length_years < 2:
        raise ContractError("block length must be an integer of at least two")
    sites = list(site_ids)
    year_values = list(years)
    _validate_fit_cohort(sites, year_values, region_id, data_role)
    standardized = within_site_standardize(sites, year_values, values)
    minimum = min(len(value["values"]) for value in standardized["sequences"].values())
    if block_length_years > minimum:
        raise ContractError("block length exceeds a site sequence")
    generation_values = standardized["anomalies"]
    generation_mean = np.mean(generation_values, axis=0, dtype=np.float64)
    generation_covariance = np.cov(generation_values, rowvar=False, ddof=0)
    _covariance_root(generation_covariance, inverse=True)
    return {
        "strategy_id": "circular_fixed_block_bootstrap_v1",
        "block_length_years": block_length_years,
        "sequences": standardized["sequences"],
        "fit_transform": "within_site_sample_standardization",
        "anomaly_correlation": nearest_correlation(
            generation_covariance / np.sqrt(np.outer(np.diag(generation_covariance), np.diag(generation_covariance)))
        )[0].tolist(),
        "generation_mean": generation_mean.tolist(),
        "generation_covariance": generation_covariance.tolist(),
        "region_id": region_id,
        "data_role": data_role,
    }


def generate_block_bootstrap(model: dict[str, Any], years: int, generator: DomainRng) -> np.ndarray:
    _validate_model_identity(model, "circular_fixed_block_bootstrap_v1")
    if not isinstance(years, int) or isinstance(years, bool) or years < 1:
        raise ContractError("block-bootstrap generation request is invalid")
    generator = _require_rng(generator, "annual_target", model.get("strategy_id"))
    block = model.get("block_length_years")
    sequences = model.get("sequences")
    if (
        not isinstance(block, int) or isinstance(block, bool) or not 2 <= block <= 30
        or not isinstance(sequences, dict) or not sequences
    ):
        raise ContractError("block-bootstrap model is invalid")
    if any(not isinstance(value, dict) or block > len(value.get("values", [])) for value in sequences.values()):
        raise ContractError("block length exceeds a model sequence")
    sites = sorted(sequences)
    rows = []
    while len(rows) < years:
        site = sites[int(generator.integers(0, len(sites)))]
        values = _finite_matrix(sequences[site]["values"], "bootstrap sequence")
        start = int(generator.integers(0, len(values)))
        rows.extend(values[(start + offset) % len(values)] for offset in range(block))
    return np.asarray(rows[:years], dtype=np.float64)


def _covariance_root(covariance: np.ndarray, inverse: bool = False) -> np.ndarray:
    eigenvalues, eigenvectors = np.linalg.eigh((covariance + covariance.T) / 2.0)
    if float(np.min(eigenvalues)) < -1e-10:
        raise ContractError("covariance root input is not positive semidefinite")
    if inverse:
        if float(np.min(eigenvalues)) <= 1e-10:
            raise ContractError("generation covariance is not invertible")
        factors = 1.0 / np.sqrt(eigenvalues)
    else:
        factors = np.sqrt(np.maximum(eigenvalues, 0.0))
    return (eigenvectors * factors) @ eigenvectors.T


def generate_strategy_targets(
    model: dict[str, Any], years: int, generator: DomainRng, location: Any,
    monthly_variances: Any, annual_weights: Any, requested_annual_variance: float,
) -> tuple[np.ndarray, dict[str, Any]]:
    if not isinstance(model, dict):
        raise ContractError("target model must be an object")
    strategy_id = model.get("strategy_id")
    if strategy_id not in STRATEGY_IDS:
        raise ContractError("target strategy is not registered")
    _validate_model_identity(model, strategy_id)
    if not isinstance(years, int) or isinstance(years, bool) or years < 2:
        raise ContractError("target generation requires at least two years")
    correlation = _finite_matrix(model.get("anomaly_correlation"), "anomaly correlation")
    source_mean = np.asarray(model.get("generation_mean"), dtype=np.float64)
    source_covariance = _finite_matrix(model.get("generation_covariance"), "generation covariance")
    variances = np.asarray(monthly_variances, dtype=np.float64)
    locations = np.asarray(location, dtype=np.float64)
    dimensions = correlation.shape[0]
    if (
        correlation.shape != (dimensions, dimensions)
        or source_mean.shape != (dimensions,)
        or source_covariance.shape != (dimensions, dimensions)
        or variances.shape != (dimensions,)
        or locations.shape != (dimensions,)
        or not np.isfinite(source_mean).all()
        or not np.isfinite(locations).all()
        or np.any(variances <= 0.0)
    ):
        raise ContractError("monthly target variances are invalid")
    requested = correlation * np.sqrt(np.outer(variances, variances))
    effective, reconciliation = reconcile_covariance(
        requested, variances, annual_weights, requested_annual_variance
    )
    source_inverse_root = _covariance_root(source_covariance, inverse=True)
    effective_root = _covariance_root(effective)
    if strategy_id == "gaussian_latent_scalar_ar1_v1":
        anomalies = generate_gaussian_ar1(model, years, generator)
    else:
        anomalies = generate_block_bootstrap(model, years, generator)
    standardized = (anomalies - source_mean) @ source_inverse_root.T
    targets = standardized @ effective_root.T
    targets += locations
    realized_covariance = np.cov(targets, rowvar=False, ddof=1)
    covariance_error = float(np.max(np.abs(realized_covariance - effective))) if years > 1 else None
    return targets, {
        "strategy_id": strategy_id,
        "region_id": model.get("region_id"),
        "fit_data_role": model.get("data_role"),
        "reconciliation": reconciliation,
        "realized_covariance": realized_covariance.tolist(),
        "maximum_realized_covariance_error": covariance_error,
        "moment_semantics": "stationary_population_law; realized sample is diagnostic",
    }


def select_feasible_wet_count(
    total_mm: float,
    days: int,
    wet_threshold_mm: float,
    fitted_counts: Iterable[int],
    uniform: float,
) -> int:
    if (
        not math.isfinite(total_mm)
        or total_mm < 0.0
        or not isinstance(days, int)
        or isinstance(days, bool)
        or days < 1
        or not math.isfinite(wet_threshold_mm)
        or wet_threshold_mm <= 0.0
        or not 0.0 <= uniform < 1.0
    ):
        raise ContractError("wet-count request is invalid")
    counts = list(fitted_counts)
    if any(
        not isinstance(value, int) or isinstance(value, bool) or value < 0 or value > days
        for value in counts
    ):
        raise ContractError("fitted wet counts must be integers in the month support")
    if total_mm == 0.0:
        feasible = [value for value in counts if value == 0]
    else:
        maximum = min(days, int(math.floor(total_mm / wet_threshold_mm)))
        feasible = [value for value in counts if 1 <= value <= maximum]
    if not feasible:
        raise ContractError("no fitted wet count has conditional support")
    return sorted(feasible)[min(int(uniform * len(feasible)), len(feasible) - 1)]


def markov_bridge(
    days: int,
    wet_count: int,
    previous_wet: bool,
    p_wet_given_wet: float,
    p_wet_given_dry: float,
    generator: DomainRng,
) -> np.ndarray:
    generator = _require_rng(generator, "occurrence")
    if (
        not isinstance(days, int) or isinstance(days, bool) or days < 1
        or not isinstance(wet_count, int) or isinstance(wet_count, bool)
        or not isinstance(previous_wet, (bool, np.bool_))
        or not 0 <= wet_count <= days
        or not math.isfinite(p_wet_given_wet) or not math.isfinite(p_wet_given_dry)
        or not 0.0 < p_wet_given_wet < 1.0 or not 0.0 < p_wet_given_dry < 1.0
    ):
        raise ContractError("Markov bridge request is outside support")
    backward = np.zeros((days + 1, wet_count + 1, 2), dtype=np.float64)
    backward[days, 0, :] = 1.0
    for position in range(days - 1, -1, -1):
        remaining = days - position
        for needed in range(min(wet_count, remaining) + 1):
            for previous in (0, 1):
                probability = p_wet_given_wet if previous else p_wet_given_dry
                value = (1.0 - probability) * backward[position + 1, needed, 0]
                if needed:
                    value += probability * backward[position + 1, needed - 1, 1]
                backward[position, needed, previous] = value
    state = int(previous_wet)
    if backward[0, wet_count, state] <= 0.0:
        raise ContractError("conditional occurrence path has zero probability")
    output = np.zeros(days, dtype=bool)
    needed = wet_count
    for position in range(days):
        probability = p_wet_given_wet if state else p_wet_given_dry
        wet_weight = probability * backward[position + 1, needed - 1, 1] if needed else 0.0
        dry_weight = (1.0 - probability) * backward[position + 1, needed, 0]
        wet = generator.random() < wet_weight / (wet_weight + dry_weight)
        output[position] = wet
        needed -= int(wet)
        state = int(wet)
    if int(np.sum(output)) != wet_count:
        raise ContractError("conditional occurrence count was not exact")
    return output


def allocate_wet_amounts(
    total_mm: float,
    wet: Any,
    wet_threshold_mm: float,
    positive_weights: Any,
) -> np.ndarray:
    occurrence = np.asarray(wet)
    weights = np.asarray(positive_weights, dtype=np.float64)
    if occurrence.ndim != 1 or occurrence.dtype != np.bool_:
        raise ContractError("amount occurrence mask must be Boolean")
    count = int(np.sum(occurrence))
    if (
        not math.isfinite(total_mm)
        or total_mm < 0.0
        or not math.isfinite(wet_threshold_mm)
        or wet_threshold_mm <= 0.0
        or weights.shape != (count,)
        or not np.isfinite(weights).all()
        or np.any(weights <= 0.0)
    ):
        raise ContractError("amount weights are invalid")
    if count == 0:
        if total_mm != 0.0:
            raise ContractError("positive total requires a wet day")
        return np.zeros(len(occurrence), dtype=np.float64)
    minimum = count * wet_threshold_mm
    if not math.isfinite(total_mm) or total_mm < minimum:
        raise ContractError("total cannot support the registered wet count")
    output = np.zeros(len(occurrence), dtype=np.float64)
    output[occurrence] = wet_threshold_mm + (total_mm - minimum) * weights / float(np.sum(weights))
    if abs(float(np.sum(output)) - total_mm) > 1e-10:
        raise ContractError("amount allocation did not preserve total")
    return output


def condition_temperature_residuals(values: Any, target_sd: float) -> np.ndarray:
    residuals = np.asarray(values, dtype=np.float64)
    if residuals.ndim != 1 or len(residuals) < 2 or not np.isfinite(residuals).all() or not math.isfinite(target_sd) or target_sd <= 0.0:
        raise ContractError("temperature conditioning request is invalid")
    centered = residuals - float(np.mean(residuals))
    scale = float(np.std(centered, ddof=1))
    if scale <= 0.0:
        raise ContractError("temperature residual vector is constant")
    return centered * target_sd / scale


def condition_positive_ranges(values: Any, target_mean: float) -> np.ndarray:
    ranges = np.asarray(values, dtype=np.float64)
    if ranges.ndim != 1 or not len(ranges) or not np.isfinite(ranges).all() or np.any(ranges <= 0.0) or not math.isfinite(target_mean) or target_mean <= 0.0:
        raise ContractError("range conditioning request is invalid")
    return ranges * target_mean / float(np.mean(ranges))


def _ar1_standard_normal(length: int, phi: float, generator: DomainRng, domain: str) -> np.ndarray:
    generator = _require_rng(generator, domain)
    if (
        not isinstance(length, int) or isinstance(length, bool) or length < 1
        or not math.isfinite(phi) or not -0.95 <= phi <= 0.95
    ):
        raise ContractError("AR(1) request is invalid")
    output = np.empty(length, dtype=np.float64)
    output[0] = generator.standard_normal()
    innovation_scale = math.sqrt(1.0 - phi * phi)
    for index in range(1, length):
        output[index] = phi * output[index - 1] + innovation_scale * generator.standard_normal()
    return output


def generate_core_month(
    strategy_id: str, total_mm: float, days: int, fitted_wet_counts: Iterable[int],
    wet_threshold_mm: float, previous_wet: bool, p_wet_given_wet: float,
    p_wet_given_dry: float, temperature_mean: float, temperature_sd: float,
    range_mean: float, amount_phi: float, temperature_phi: float, range_phi: float,
    generators: dict[str, DomainRng],
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    required = {"wet_count", "occurrence", "amount", "temperature", "range"}
    if strategy_id not in STRATEGY_IDS or not isinstance(generators, dict) or set(generators) != required:
        raise ContractError("core month RNG domains are incomplete")
    forcing_scalars = (
        total_mm, wet_threshold_mm, p_wet_given_wet, p_wet_given_dry,
        temperature_mean, temperature_sd, range_mean, amount_phi, temperature_phi, range_phi,
    )
    if any(not isinstance(value, (int, float, np.integer, np.floating)) or not math.isfinite(float(value)) for value in forcing_scalars):
        raise ContractError("core month forcing scalars must be finite")
    if (
        not isinstance(days, int) or isinstance(days, bool) or days < 2
        or not isinstance(previous_wet, (bool, np.bool_))
        or total_mm < 0.0 or wet_threshold_mm <= 0.0
        or not 0.0 < p_wet_given_wet < 1.0 or not 0.0 < p_wet_given_dry < 1.0
        or temperature_sd <= 0.0 or range_mean <= 0.0
        or any(not -0.95 <= phi <= 0.95 for phi in (amount_phi, temperature_phi, range_phi))
    ):
        raise ContractError("core month forcing is outside registered support")
    counts = list(fitted_wet_counts)
    select_feasible_wet_count(total_mm, days, wet_threshold_mm, counts, 0.0)
    for domain in required:
        stream = _require_rng(generators[domain], domain, strategy_id)
        if stream.experiment_id != generators["wet_count"].experiment_id or stream.member != generators["wet_count"].member:
            raise ContractError("core month RNG streams do not share an execution identity")
    if len({id(generators[domain].generator) for domain in required}) != len(required):
        raise ContractError("core month RNG domains alias the same stream")
    wet_count_stream = generators["wet_count"]
    count = select_feasible_wet_count(
        total_mm, days, wet_threshold_mm, counts, float(wet_count_stream.random())
    )
    wet = markov_bridge(
        days, count, previous_wet, p_wet_given_wet, p_wet_given_dry, generators["occurrence"]
    )
    amount_latent = _ar1_standard_normal(max(count, 1), amount_phi, generators["amount"], "amount")
    amounts = allocate_wet_amounts(total_mm, wet, wet_threshold_mm, np.exp(amount_latent[:count]))
    temperature_latent = _ar1_standard_normal(days, temperature_phi, generators["temperature"], "temperature")
    residual = condition_temperature_residuals(temperature_latent, temperature_sd)
    temperature = temperature_mean + residual
    range_latent = _ar1_standard_normal(days, range_phi, generators["range"], "range")
    daily_range = condition_positive_ranges(np.exp(range_latent), range_mean)
    maximum = temperature + daily_range / 2.0
    minimum = temperature - daily_range / 2.0
    return {
        "wet": wet, "precipitation_mm": amounts, "temperature_mean": temperature,
        "temperature_range": daily_range, "temperature_max": maximum, "temperature_min": minimum,
    }, {
        "strategy_id": strategy_id,
        "wet_count": count,
        "precipitation_total_mm": float(np.sum(amounts)),
        "temperature_sample_sd": float(np.std(temperature, ddof=1)),
        "range_mean": float(np.mean(daily_range)),
    }
