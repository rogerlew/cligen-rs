"""Research-only mock candidate plugins for interface and fixture testing."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from datetime import date
from typing import Any, Protocol

from .calendar import gregorian_dates
from .context import DailyContext
from .errors import HarnessError, require
from .rng import RandomFieldIdentity, uniform

RENEWAL_ID = "alternating_renewal_marked_v1"
LATENT_ID = "latent_regime_marked_v1"
MODEL_FAMILY_ID = "a9_joint_daily_event_family_v1"


class CandidatePlugin(Protocol):
    class_id: str
    source_version: str

    def validate_config(self, config: dict[str, Any]) -> None: ...

    def simulate(
        self,
        config: dict[str, Any],
        *,
        fit: "ValidatedFit",
        campaign: str,
        site: str,
        burn: str,
        start_year: int,
        years: int = 100,
    ) -> list[dict[str, object]]: ...


@dataclass(frozen=True)
class ValidatedFit:
    """The only fit identity a candidate plugin is allowed to receive."""

    fit_id: str
    candidate_class: str
    config_schema_sha256: str
    content_sha256: str


def config_schema(class_id: str) -> dict[str, Any]:
    if class_id == RENEWAL_ID:
        required_fields = AlternatingRenewalMock.expected_fields
    elif class_id == LATENT_ID:
        required_fields = LatentRegimeMock.expected_fields
    else:
        raise HarnessError("UNKNOWN_CANDIDATE_PLUGIN", class_id)
    return {
        "schema_version": 1,
        "candidate_class": class_id,
        "additional_properties": False,
        "required_fields": sorted(required_fields),
    }


def config_schema_sha256(class_id: str) -> str:
    from .canonical import canonical_bytes, sha256_bytes

    return sha256_bytes(canonical_bytes(config_schema(class_id)))


def validated_fit(artifact: dict[str, Any]) -> ValidatedFit:
    from .canonical import verify_self_hash

    verify_self_hash(artifact, "content_sha256")
    require(artifact.get("fit_status") == "fit_valid", "FIT_NOT_VALID", str(artifact.get("fit_id")))
    candidate = artifact["candidate_class"]
    class_id = candidate["id"]
    expected = config_schema_sha256(class_id)
    require(candidate["schema_sha256"] == expected, "CANDIDATE_SCHEMA_HASH_MISMATCH", class_id)
    return ValidatedFit(artifact["fit_id"], class_id, expected, artifact["content_sha256"])


def _strict_keys(config: dict[str, Any], expected: set[str], class_id: str) -> None:
    require(set(config) == expected, "CANDIDATE_CONFIG_FIELDS", f"{class_id}:{sorted(set(config) ^ expected)}")
    require("horizon_years" not in config, "HORIZON_DEPENDENT_PARAMETER", class_id)


def _rng(
    campaign: str,
    site: str,
    burn: str,
    component: str,
    day: date,
    slot: str,
) -> float:
    return uniform(RandomFieldIdentity(campaign, site, burn, component, day, slot))


def _exponential(mean: float, u: float) -> float:
    return -mean * math.log(max(u, 2.0**-53))


class AlternatingRenewalMock:
    """Observable alternating wet/dry semi-Markov mock with conditional marks."""

    class_id = RENEWAL_ID
    source_version = "a9b-mock-renewal-v1"
    expected_fields = {
        "wet_end_base",
        "dry_end_base",
        "duration_age_slope",
        "seasonal_amplitude",
        "amount_mean_mm",
        "amount_memory",
        "tail_probability",
    }

    def validate_config(self, config: dict[str, Any]) -> None:
        _strict_keys(config, self.expected_fields, self.class_id)
        for field in ("wet_end_base", "dry_end_base", "tail_probability"):
            require(0.0 < float(config[field]) < 1.0, "CANDIDATE_PARAMETER_SUPPORT", field)
        require(0.0 <= float(config["duration_age_slope"]) <= 1.0, "CANDIDATE_PARAMETER_SUPPORT", "duration_age_slope")
        require(0.0 <= float(config["seasonal_amplitude"]) < 0.9, "CANDIDATE_PARAMETER_SUPPORT", "seasonal_amplitude")
        require(float(config["amount_mean_mm"]) > 0.0, "CANDIDATE_PARAMETER_SUPPORT", "amount_mean_mm")
        require(0.0 <= float(config["amount_memory"]) < 1.0, "CANDIDATE_PARAMETER_SUPPORT", "amount_memory")

    def simulate(
        self,
        config: dict[str, Any],
        *,
        fit: ValidatedFit,
        campaign: str,
        site: str,
        burn: str,
        start_year: int,
        years: int = 100,
    ) -> list[dict[str, object]]:
        self.validate_config(config)
        require(fit.candidate_class == self.class_id, "FIT_CANDIDATE_MISMATCH", fit.candidate_class)
        require(fit.config_schema_sha256 == config_schema_sha256(self.class_id), "CANDIDATE_SCHEMA_HASH_MISMATCH", self.class_id)
        require(years == 100, "CANDIDATE_HORIZON", "plugins emit one 100-year stream")
        state = "dry"
        age = 0
        previous_amount = 0.0
        rows: list[dict[str, object]] = []
        for day in gregorian_dates(start_year, years):
            seasonal = math.sin((2.0 * math.pi * (day.timetuple().tm_yday - 1)) / (366 if day.replace(month=12, day=31).timetuple().tm_yday == 366 else 365))
            base = float(config["wet_end_base"] if state == "wet" else config["dry_end_base"])
            modifier = 1.0 + float(config["duration_age_slope"]) * min(age, 12) / 12.0
            if state == "dry":
                modifier *= 1.0 + float(config["seasonal_amplitude"]) * seasonal
            end_probability = min(0.98, max(0.02, base * modifier))
            if _rng(campaign, site, burn, "occurrence", day, "spell_transition") < end_probability:
                state = "wet" if state == "dry" else "dry"
                age = 1
            else:
                age += 1
            wet = state == "wet"
            amount = 0.0
            duration = time_to_peak = peak_ratio = None
            if wet:
                body = _exponential(float(config["amount_mean_mm"]), _rng(campaign, site, burn, "amount-body", day, "body"))
                amount = (1.0 - float(config["amount_memory"])) * body + float(config["amount_memory"]) * previous_amount
                if _rng(campaign, site, burn, "amount-tail", day, "tail_gate") < float(config["tail_probability"]):
                    amount += _exponential(3.0 * float(config["amount_mean_mm"]), _rng(campaign, site, burn, "amount-tail", day, "tail_size"))
                duration = 5.0 + 1435.0 * _rng(campaign, site, burn, "event", day, "duration")
                time_to_peak = _rng(campaign, site, burn, "event", day, "time_to_peak")
                peak_ratio = 1.0 + math.sqrt(amount) * (0.2 + _rng(campaign, site, burn, "event", day, "peak_ratio"))
                previous_amount = amount
            context = DailyContext(
                wet0=wet,
                r1mm=amount >= 1.0,
                occurrence_state=state,
                wet_amount_mm=amount,
                amount_quantile=_rng(campaign, site, burn, "daily-context", day, "amount_quantile") if wet else None,
                event_duration_minutes=duration,
                time_to_peak_fraction=time_to_peak,
                peak_ratio=peak_ratio,
                seasonal_state=f"month-{day.month:02d}",
                latent_state=None,
                fit_id=fit.fit_id,
                candidate_class=self.class_id,
            )
            rows.append({"date": day.isoformat(), "precipitation_mm": amount, "context": asdict(context)})
        return rows


class LatentRegimeMock:
    """Hidden three-state semi-Markov mock with joint marked emissions."""

    class_id = LATENT_ID
    source_version = "a9b-mock-latent-v1"
    expected_fields = {
        "state_wet_probability",
        "state_amount_mean_mm",
        "state_end_base",
        "duration_age_slope",
        "transition_rows",
    }

    def validate_config(self, config: dict[str, Any]) -> None:
        _strict_keys(config, self.expected_fields, self.class_id)
        wet = config["state_wet_probability"]
        amounts = config["state_amount_mean_mm"]
        end = config["state_end_base"]
        transition = config["transition_rows"]
        require(len(wet) == len(amounts) == len(end) == len(transition) == 3, "LATENT_STATE_COUNT", "three")
        require(all(0.0 < float(value) < 1.0 for value in wet), "MODEL_CLASS_EQUIVALENCE", "latent wet probabilities must be interior")
        require(all(float(value) > 0.0 for value in amounts), "CANDIDATE_PARAMETER_SUPPORT", "amount means")
        require(all(0.0 < float(value) < 1.0 for value in end), "CANDIDATE_PARAMETER_SUPPORT", "end probabilities")
        require(0.0 <= float(config["duration_age_slope"]) <= 1.0, "CANDIDATE_PARAMETER_SUPPORT", "duration_age_slope")
        for row in transition:
            require(len(row) == 3 and all(float(value) >= 0.0 for value in row), "TRANSITION_SUPPORT", "row")
            require(abs(sum(float(value) for value in row) - 1.0) <= 1.0e-12, "TRANSITION_NORMALIZATION", repr(row))

    def simulate(
        self,
        config: dict[str, Any],
        *,
        fit: ValidatedFit,
        campaign: str,
        site: str,
        burn: str,
        start_year: int,
        years: int = 100,
    ) -> list[dict[str, object]]:
        self.validate_config(config)
        require(fit.candidate_class == self.class_id, "FIT_CANDIDATE_MISMATCH", fit.candidate_class)
        require(fit.config_schema_sha256 == config_schema_sha256(self.class_id), "CANDIDATE_SCHEMA_HASH_MISMATCH", self.class_id)
        require(years == 100, "CANDIDATE_HORIZON", "plugins emit one 100-year stream")
        state = 0
        age = 0
        rows: list[dict[str, object]] = []
        for day in gregorian_dates(start_year, years):
            end_probability = min(0.98, float(config["state_end_base"][state]) * (1.0 + float(config["duration_age_slope"]) * min(age, 20) / 20.0))
            if _rng(campaign, site, burn, "latent-state", day, "state_end") < end_probability:
                draw = _rng(campaign, site, burn, "latent-state", day, "state_transition")
                cumulative = 0.0
                for target, probability in enumerate(config["transition_rows"][state]):
                    cumulative += float(probability)
                    if draw <= cumulative:
                        state = target
                        break
                age = 1
            else:
                age += 1
            wet = _rng(campaign, site, burn, "occurrence", day, "wet_gate") < float(config["state_wet_probability"][state])
            amount = 0.0
            duration = time_to_peak = peak_ratio = None
            if wet:
                body = _exponential(float(config["state_amount_mean_mm"][state]), _rng(campaign, site, burn, "amount-body", day, "body"))
                high_gate = _rng(campaign, site, burn, "amount-tail", day, "joint_high_gate")
                amount = body * (3.0 if high_gate < (0.08 + state * 0.04) else 1.0)
                duration = 5.0 + (240.0 + state * 180.0) * _rng(campaign, site, burn, "event", day, "duration")
                time_to_peak = min(0.999999, max(0.000001, 0.1 * state + 0.8 * _rng(campaign, site, burn, "event", day, "time_to_peak")))
                peak_ratio = 1.0 + (state + 1) * 0.25 + math.sqrt(amount) * _rng(campaign, site, burn, "event", day, "peak_ratio")
            context = DailyContext(
                wet0=wet,
                r1mm=amount >= 1.0,
                occurrence_state="wet" if wet else "dry",
                wet_amount_mm=amount,
                amount_quantile=_rng(campaign, site, burn, "daily-context", day, "amount_quantile") if wet else None,
                event_duration_minutes=duration,
                time_to_peak_fraction=time_to_peak,
                peak_ratio=peak_ratio,
                seasonal_state=f"month-{day.month:02d}",
                latent_state=f"state-{state}",
                fit_id=fit.fit_id,
                candidate_class=self.class_id,
            )
            rows.append({"date": day.isoformat(), "precipitation_mm": amount, "context": asdict(context)})
        return rows


def plugin_registry() -> dict[str, CandidatePlugin]:
    return {RENEWAL_ID: AlternatingRenewalMock(), LATENT_ID: LatentRegimeMock()}


def structural_audit(
    renewal_config: dict[str, Any], latent_config: dict[str, Any]
) -> dict[str, object]:
    AlternatingRenewalMock().validate_config(renewal_config)
    LatentRegimeMock().validate_config(latent_config)
    wet_probabilities = [float(value) for value in latent_config["state_wet_probability"]]
    require(all(0.0 < value < 1.0 for value in wet_probabilities), "MODEL_CLASS_EQUIVALENCE", "interior emissions")
    return {
        "status": "non_isomorphic",
        "renewal_state": "observable alternating spell type; wet iff wet state; no hidden artifact",
        "latent_state": "hidden semi-Markov occupancy; wet and dry emissions in every state",
        "bijective_parameter_relabeling": False,
        "latent_occupancy_equals_observed_spell_type": False,
    }


def default_configs() -> dict[str, dict[str, Any]]:
    return {
        RENEWAL_ID: {
            "wet_end_base": 0.42,
            "dry_end_base": 0.22,
            "duration_age_slope": 0.35,
            "seasonal_amplitude": 0.25,
            "amount_mean_mm": 6.0,
            "amount_memory": 0.25,
            "tail_probability": 0.08,
        },
        LATENT_ID: {
            "state_wet_probability": [0.08, 0.42, 0.82],
            "state_amount_mean_mm": [2.5, 7.0, 14.0],
            "state_end_base": [0.16, 0.28, 0.38],
            "duration_age_slope": 0.25,
            "transition_rows": [
                [0.10, 0.70, 0.20],
                [0.45, 0.10, 0.45],
                [0.20, 0.70, 0.10],
            ],
        },
    }


def fit_synthetic(plugin_id: str, exposures: dict[str, int]) -> dict[str, object]:
    """Typed mock fit result used only to exercise the plugin boundary."""

    require(plugin_id in plugin_registry(), "UNKNOWN_CANDIDATE_PLUGIN", plugin_id)
    if exposures.get("wet_days", 0) < 50 or exposures.get("dry_days", 0) < 50:
        return {"fit_status": "fit_ineligible", "status_reason": "insufficient wet/dry exposure", "effective_exposures": exposures}
    if exposures.get("adjacent_wet_pairs", 0) < 25 or exposures.get("events", 0) < 50:
        return {"fit_status": "fit_ineligible", "status_reason": "insufficient memory/event exposure", "effective_exposures": exposures}
    return {"fit_status": "fit_valid", "status_reason": None, "effective_exposures": exposures, "parameters": default_configs()[plugin_id]}
