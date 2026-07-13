//! The quality-report envelope (SPEC-QUALITY-REPORT §Report envelope).
//!
//! Serialization is byte-deterministic: serde emits struct fields in
//! declaration order, which **is** the schema order; every value is a
//! finite number, `null`, string, integer, or a fixed-shape
//! composite. No maps, no platform-dependent iteration anywhere.

use std::collections::HashSet;
use std::sync::OnceLock;

use serde::de::{self, MapAccess, SeqAccess, Visitor};
use serde::{Deserialize, Serialize};
use serde_json::Value as JsonValue;

use crate::provenance::{GenerationProfileV1, MediaTypeV1, QcPolicyV1, StationModelV1};

use super::QualityError;

/// The published metric-vector revision. Version 3 (A5a,
/// SPEC-QUALITY-REPORT rev 8) adds complete-period low-frequency,
/// precipitation-structure, event-descriptor, and winter climate metrics.
pub const METRICS_VERSION: u32 = 3;
/// Quality-report envelope revision. A1 changes identity/provenance without
/// changing the ADR-0002 metric vector.
pub const QUALITY_REPORT_SCHEMA_VERSION: u32 = 2;

/// Twelve calendar-month cells in schema order.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Months<T> {
    pub jan: T,
    pub feb: T,
    pub mar: T,
    pub apr: T,
    pub may: T,
    pub jun: T,
    pub jul: T,
    pub aug: T,
    pub sep: T,
    pub oct: T,
    pub nov: T,
    pub dec: T,
}

impl<T> Months<T> {
    /// Build from a 0-based month index function (0 = January).
    pub fn from_fn(mut cell: impl FnMut(usize) -> T) -> Self {
        Months {
            jan: cell(0),
            feb: cell(1),
            mar: cell(2),
            apr: cell(3),
            may: cell(4),
            jun: cell(5),
            jul: cell(6),
            aug: cell(7),
            sep: cell(8),
            oct: cell(9),
            nov: cell(10),
            dec: cell(11),
        }
    }
}

/// The complete report.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct QualityReport {
    pub quality_report_schema_version: u32,
    pub metrics_version: u32,
    pub identity: Identity,
    pub par_convergence: Option<ParConvergence>,
    pub interannual: Option<Interannual>,
    pub covariation: Option<Covariation>,
    pub tails: Tails,
    pub process: Option<ProcessMetrics>,
}

impl QualityReport {
    /// Null every run-only surface (SPEC-QUALITY-REPORT §Acceptance,
    /// rev 3): group P, `identity.provenance`, and
    /// `par_convergence.observed_passthrough`. After this, a
    /// run-emitted report byte-equals its post-hoc counterpart.
    pub fn null_run_only_surfaces(&mut self) {
        self.identity.provenance = None;
        self.process = None;
        if let Some(par_convergence) = &mut self.par_convergence {
            par_convergence.observed_passthrough = None;
        }
    }

    /// Parse and validate one complete envelope-2/metrics-3 JSON document.
    ///
    /// Validation runs against the published Draft 2020-12 combination
    /// schema before typed deserialization, so unknown nested members fail
    /// closed. The schema's provenance reference is resolved exclusively from
    /// the vendored schema registered in memory; this method performs no file
    /// or network retrieval.
    ///
    /// # Errors
    ///
    /// Returns a JSON intake error, a published-schema violation, or a typed
    /// relational validation error.
    pub fn parse_json(bytes: &[u8]) -> Result<Self, QualityError> {
        let value = serde_json::from_slice::<StrictJsonValue>(bytes)
            .map_err(QualityError::Deserialize)?
            .0;
        validate_json_schema(&value)?;
        let report: Self = serde_json::from_value(value).map_err(QualityError::Deserialize)?;
        report.validate()?;
        Ok(report)
    }

    /// Validate the published schema and cross-field metric invariants.
    ///
    /// This also rejects non-finite numbers introduced through the public
    /// mutable DTO before `serde_json` can coerce them to `null`.
    ///
    /// # Errors
    ///
    /// Returns the first provenance, schema, non-finite, or relational
    /// contract violation.
    pub fn validate(&self) -> Result<(), QualityError> {
        reject_nonfinite(self)?;
        if let Some(provenance) = &self.identity.provenance {
            provenance.validate().map_err(QualityError::Provenance)?;
        }
        let value = serde_json::to_value(self).map_err(QualityError::Serialize)?;
        validate_json_schema(&value)?;
        validate_report_relations(self)
    }

    /// Deterministic serialization: pretty JSON, schema-ordered keys,
    /// trailing newline. A given report value has exactly one byte
    /// rendering.
    ///
    /// # Errors
    ///
    /// Returns a validation or serializer error.
    pub fn to_json_bytes(&self) -> Result<Vec<u8>, QualityError> {
        self.validate()?;
        let mut bytes = serde_json::to_vec_pretty(self).map_err(QualityError::Serialize)?;
        bytes.push(b'\n');
        Ok(bytes)
    }
}

struct StrictJsonValue(JsonValue);

impl<'de> Deserialize<'de> for StrictJsonValue {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        deserializer
            .deserialize_any(StrictJsonVisitor)
            .map(StrictJsonValue)
    }
}

struct StrictJsonVisitor;

impl<'de> Visitor<'de> for StrictJsonVisitor {
    type Value = JsonValue;

    fn expecting(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter.write_str("a JSON value without duplicate object keys")
    }

    fn visit_bool<E>(self, value: bool) -> Result<Self::Value, E> {
        Ok(JsonValue::Bool(value))
    }

    fn visit_i64<E>(self, value: i64) -> Result<Self::Value, E> {
        Ok(JsonValue::Number(value.into()))
    }

    fn visit_u64<E>(self, value: u64) -> Result<Self::Value, E> {
        Ok(JsonValue::Number(value.into()))
    }

    fn visit_f64<E>(self, value: f64) -> Result<Self::Value, E>
    where
        E: de::Error,
    {
        serde_json::Number::from_f64(value)
            .map(JsonValue::Number)
            .ok_or_else(|| E::custom("non-finite JSON number"))
    }

    fn visit_str<E>(self, value: &str) -> Result<Self::Value, E>
    where
        E: de::Error,
    {
        Ok(JsonValue::String(value.to_owned()))
    }

    fn visit_string<E>(self, value: String) -> Result<Self::Value, E> {
        Ok(JsonValue::String(value))
    }

    fn visit_none<E>(self) -> Result<Self::Value, E> {
        Ok(JsonValue::Null)
    }

    fn visit_unit<E>(self) -> Result<Self::Value, E> {
        Ok(JsonValue::Null)
    }

    fn visit_seq<A>(self, mut sequence: A) -> Result<Self::Value, A::Error>
    where
        A: SeqAccess<'de>,
    {
        let mut values = Vec::new();
        while let Some(value) = sequence.next_element::<StrictJsonValue>()? {
            values.push(value.0);
        }
        Ok(JsonValue::Array(values))
    }

    fn visit_map<A>(self, mut object: A) -> Result<Self::Value, A::Error>
    where
        A: MapAccess<'de>,
    {
        let mut values = serde_json::Map::new();
        while let Some(key) = object.next_key::<String>()? {
            if values.contains_key(&key) {
                return Err(de::Error::custom(format!("duplicate object key {key:?}")));
            }
            let value = object.next_value::<StrictJsonValue>()?;
            values.insert(key, value.0);
        }
        Ok(JsonValue::Object(values))
    }
}

const PROVENANCE_SCHEMA_URI: &str = "https://raw.githubusercontent.com/rogerlew/cligen-rs/main/docs/specifications/provenance-v1.schema.json";

fn quality_schema_validator() -> Result<&'static jsonschema::Validator, QualityError> {
    static VALIDATOR: OnceLock<Result<jsonschema::Validator, String>> = OnceLock::new();
    VALIDATOR
        .get_or_init(build_quality_schema_validator)
        .as_ref()
        .map_err(|message| invalid("schema", message))
}

fn build_quality_schema_validator() -> Result<jsonschema::Validator, String> {
    let schema: JsonValue = serde_json::from_str(include_str!(
        "../../schemas/quality-report-s2-m3.schema.json"
    ))
    .map_err(|error| format!("invalid embedded quality-report schema: {error}"))?;
    let provenance: JsonValue =
        serde_json::from_str(include_str!("../../schemas/provenance-v1.schema.json"))
            .map_err(|error| format!("invalid embedded provenance schema: {error}"))?;
    let registry = jsonschema::Registry::new()
        .add(PROVENANCE_SCHEMA_URI, provenance)
        .map_err(|error| format!("cannot register provenance schema: {error}"))?
        .prepare()
        .map_err(|error| format!("cannot prepare local schema registry: {error}"))?;
    jsonschema::draft202012::options()
        .with_registry(&registry)
        .build(&schema)
        .map_err(|error| format!("cannot compile quality-report schema: {error}"))
}

fn validate_json_schema(value: &JsonValue) -> Result<(), QualityError> {
    quality_schema_validator()?
        .validate(value)
        .map_err(|error| {
            invalid(
                &format!("schema{}", error.instance_path()),
                &error.to_string(),
            )
        })
}

fn reject_nonfinite(report: &QualityReport) -> Result<(), QualityError> {
    let value = serde_value::to_value(report).map_err(|error| {
        invalid(
            "document",
            &format!("cannot inspect numeric values: {error}"),
        )
    })?;
    ensure(
        !contains_nonfinite(&value),
        "document",
        "contains a non-finite floating-point value",
    )
}

fn contains_nonfinite(value: &serde_value::Value) -> bool {
    match value {
        serde_value::Value::F32(value) => !value.is_finite(),
        serde_value::Value::F64(value) => !value.is_finite(),
        serde_value::Value::Option(Some(value)) | serde_value::Value::Newtype(value) => {
            contains_nonfinite(value)
        }
        serde_value::Value::Seq(values) => values.iter().any(contains_nonfinite),
        serde_value::Value::Map(values) => values
            .iter()
            .any(|(key, value)| contains_nonfinite(key) || contains_nonfinite(value)),
        _ => false,
    }
}

fn invalid(path: &str, message: &str) -> QualityError {
    QualityError::Validation(format!("{path}: {message}"))
}

fn ensure(condition: bool, path: &str, message: &str) -> Result<(), QualityError> {
    if condition {
        Ok(())
    } else {
        Err(invalid(path, message))
    }
}

fn checked_count_add(left: u64, right: u64, path: &str) -> Result<u64, QualityError> {
    left.checked_add(right)
        .ok_or_else(|| invalid(path, "count overflow"))
}

/// Report identity: recoverable content vs run-only provenance.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Identity {
    pub content: IdentityContent,
    pub provenance: Option<crate::provenance::ArtifactProvenanceV1>,
}

/// Recoverable from the inputs alone; present in every report.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct IdentityContent {
    pub tool: String,
    pub station_model: String,
    pub station_parameter_set_sha256: String,
    pub station_source_sha256: String,
    pub cli_sha256: String,
    pub days: u64,
    pub years: u32,
    pub span: [i32; 2],
}

/// One generated-vs-target comparison cell.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ParCell {
    pub target: Option<f64>,
    pub generated: Option<f64>,
    pub abs_err: Option<f64>,
    pub rel_err: Option<f64>,
    /// Sample size behind `generated` (wet days for wet-day metrics,
    /// all days otherwise, transition pairs for the Markov terms).
    pub n: u64,
}

impl ParCell {
    /// Build a cell; `abs_err = |generated − target|`,
    /// `rel_err = abs_err / |target|` (`null` when target is 0).
    #[must_use]
    pub fn new(target: Option<f64>, generated: Option<f64>, n: u64) -> Self {
        let abs_err = match (target, generated) {
            (Some(t), Some(g)) => crate::quality::estimators::finite((g - t).abs()),
            _ => None,
        };
        let rel_err = match (abs_err, target) {
            (Some(a), Some(t)) if t != 0.0 => crate::quality::estimators::finite(a / t.abs()),
            _ => None,
        };
        ParCell {
            target,
            generated,
            abs_err,
            rel_err,
            n,
        }
    }
}

/// One group A parameter: whole-run months plus per-decade blocks.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ParParameter {
    #[serde(flatten)]
    pub months: Months<ParCell>,
    pub by_decade: Vec<ParDecade>,
}

/// A fixed 10-year block of group A month cells.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ParDecade {
    pub decade: u32,
    pub start_year: i32,
    pub n_years: u32,
    pub months: Months<ParCell>,
}

/// Group A — convergence to the `.par` contract.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ParConvergence {
    /// True when the run mode is known to be observed (`iopt = 6`),
    /// false when known otherwise, `null` post-hoc: group A errors
    /// under observed mode measure data-vs-parameter consistency,
    /// not generator quality.
    pub observed_passthrough: Option<bool>,
    pub precip_wet_mean_mm: ParParameter,
    pub precip_wet_sd_mm: ParParameter,
    pub precip_wet_skew: ParParameter,
    pub wet_day_fraction: ParParameter,
    pub p_ww: ParParameter,
    pub p_wd: ParParameter,
    pub tmax_mean_c: ParParameter,
    pub tmax_sd_c: ParParameter,
    pub tmin_mean_c: ParParameter,
    pub tmin_sd_c: ParParameter,
    pub radiation_mean_ly: ParParameter,
    pub dewpoint_mean_c: ParParameter,
    pub wind_speed_mean_ms: ParParameter,
}

/// Mean/SD/CV of an annual statistic across years.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Dispersion {
    pub mean: Option<f64>,
    pub sd: Option<f64>,
    pub cv: Option<f64>,
    pub n_years: u32,
}

/// Mean/SD of a signed statistic across years. Temperature CV is
/// deliberately absent because a Celsius mean can be zero or negative.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct LocationDispersion {
    pub mean: Option<f64>,
    pub sd: Option<f64>,
    pub n_years: u32,
}

/// The annual statistics group B disperses across years.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AnnualStats {
    pub precip_total_mm: Dispersion,
    pub trace_wet_day_count: Dispersion,
    pub r1mm_wet_day_count: Dispersion,
    pub max_daily_precip_mm: Dispersion,
    pub tmax_mean_c: LocationDispersion,
    pub tmin_mean_c: LocationDispersion,
}

/// Interannual statistics for one calendar month.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MonthlyClimate {
    pub precip_total_mm: Dispersion,
    pub trace_wet_day_count: Dispersion,
    pub r1mm_wet_day_count: Dispersion,
    pub trace_wet_day_mean_amount_mm: Dispersion,
    pub r1mm_wet_day_mean_amount_mm: Dispersion,
    pub tmax_mean_c: LocationDispersion,
    pub tmin_mean_c: LocationDispersion,
}

/// Pairwise-complete month × month dependence matrix. Both axes use
/// January-through-December index order.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MonthDependenceMatrix {
    pub covariance: Vec<Vec<Option<f64>>>,
    pub pearson_correlation: Vec<Vec<Option<f64>>>,
    pub n_pairs: Vec<Vec<u32>>,
}

/// Same-calendar-month interannual anomaly correlations.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ClimateAnomalyCorrelations {
    pub precip_tmax: CorrPair,
    pub precip_tmin: CorrPair,
    pub tmax_tmin: CorrPair,
}

/// Serial and low-frequency diagnostics for one complete annual series.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SeriesDependence {
    pub lag_one: CorrPair,
    pub period_ge_4y_power_fraction: Option<f64>,
    pub n_years: u32,
}

/// Annual dependence for precipitation and mean temperatures.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AnnualDependence {
    pub precip_total_mm: SeriesDependence,
    pub tmax_mean_c: SeriesDependence,
    pub tmin_mean_c: SeriesDependence,
}

/// Whole-run interannual dependence surfaces.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct InterannualDependence {
    pub precip_cross_month: MonthDependenceMatrix,
    pub tmax_cross_month: MonthDependenceMatrix,
    pub tmin_cross_month: MonthDependenceMatrix,
    pub cross_variable_by_month: Months<ClimateAnomalyCorrelations>,
    pub annual: AnnualDependence,
}

/// Group B — interannual dispersion.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Interannual {
    pub annual: AnnualStats,
    pub monthly: Months<MonthlyClimate>,
    pub dependence: InterannualDependence,
    pub by_decade: Vec<InterannualDecade>,
}

/// A fixed 10-year block of group B statistics.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct InterannualDecade {
    pub decade: u32,
    pub start_year: i32,
    pub n_years: u32,
    pub annual: AnnualStats,
    pub monthly: Months<MonthlyClimate>,
}

/// Paired wet-day correlations for one variable pair.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct CorrPair {
    pub pearson: Option<f64>,
    pub spearman: Option<f64>,
    pub n: u64,
}

/// The three group C wet-day correlation pairs.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct CorrSet {
    pub amount_duration: CorrPair,
    pub amount_peak_intensity_ratio: CorrPair,
    pub duration_radiation: CorrPair,
}

/// Wet/dry mean-radiation contrast for one scope.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ContrastCell {
    /// Mean radiation on wet days ÷ mean radiation on dry days;
    /// `null` when either side is empty or the dry mean is zero.
    pub contrast: Option<f64>,
    pub wet_n: u64,
    pub dry_n: u64,
}

/// Group C — covariation structure (wet-day correlations, radiation
/// contrast, daily-range sanity surface).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Covariation {
    pub whole_run: CorrSet,
    pub months: Months<CorrSet>,
    pub radiation_wet_dry_contrast: Months<ContrastCell>,
    pub daily_range_mean_c: DailyRangeMean,
    pub winter_air_temperature_proxies: WinterAirTemperatureProxies,
    pub by_decade: Vec<CovariationDecade>,
}

/// Fraction of precipitation falling on mean-air-temperature `<= 0 °C`
/// days. This is a climate proxy, not a physical phase partition.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FreezingPrecipitationFraction {
    pub fraction: Option<f64>,
    pub precipitation_on_freezing_air_days_mm: Option<f64>,
    pub total_precipitation_mm: Option<f64>,
    pub freezing_air_day_count: u64,
    pub n_days: u64,
}

/// One calendar year's winter air-temperature proxy diagnostics.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct YearWinterAirTemperatureProxy {
    pub year: i32,
    pub n_days: u32,
    pub complete_year: bool,
    pub precipitation_on_freezing_air_days: FreezingPrecipitationFraction,
    pub freeze_thaw_air_temperature_proxy_cycles: u32,
}

/// Explicit climate-only winter proxy vector.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct WinterAirTemperatureProxies {
    pub precipitation_on_freezing_air_days: FreezingPrecipitationFraction,
    pub by_month: Months<FreezingPrecipitationFraction>,
    pub djf_r1mm_precip_mean_air_temperature: CorrPair,
    pub freeze_thaw_air_temperature_proxy_cycles: Dispersion,
    pub per_year: Vec<YearWinterAirTemperatureProxy>,
}

/// tmax − tmin daily-range means.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DailyRangeMean {
    pub whole_run: Option<f64>,
    pub months: Months<Option<f64>>,
}

/// A decade-level group C block (rev 3: decade-level, not
/// month × decade — those cells are statistically empty at n ≈ 10 yr).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct CovariationDecade {
    pub decade: u32,
    pub start_year: i32,
    pub n_years: u32,
    pub pairs: CorrSet,
    pub radiation_wet_dry_contrast: ContrastCell,
    pub daily_range_mean_c: Option<f64>,
}

/// Group D — tails, precipitation structure, and event descriptors.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Tails {
    pub per_year: Vec<YearTails>,
    pub top_events: Vec<TopEvent>,
    pub precipitation_structure: PrecipitationStructure,
    pub storm_descriptors: StormDescriptors,
}

/// One simulated year's tail statistics. `n_days` makes partial years
/// (observed-mode truncation) visible.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct YearTails {
    pub year: i32,
    pub n_days: u32,
    pub complete_year: bool,
    pub max_1_day_precip_mm: Option<f64>,
    pub max_3_day_precip_mm: Option<f64>,
    pub max_5_day_precip_mm: Option<f64>,
    pub wet_event_day_count: u32,
    pub max_peak_intensity_ratio: Option<f64>,
    pub longest_wet_spell_days: u32,
    pub longest_dry_spell_days: u32,
}

/// One of the whole-run top-five daily events, depth-ordered with the
/// pinned tie-break (earlier date, then lower row index).
///
/// Descriptor fields preserve the raw finite `.cli` values. Their validity
/// bounds apply only to [`StormDescriptors`], whose included and excluded
/// counts expose that filtering.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct TopEvent {
    pub rank: u32,
    pub year: i32,
    pub month: i32,
    pub day: i32,
    /// 1-based index into the parsed daily table.
    pub row_index: u64,
    pub precip_mm: f64,
    pub duration_h: f64,
    pub time_to_peak_fraction: f64,
    pub peak_intensity_ratio: f64,
}

/// Deterministic scalar distribution summary.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ScalarDistribution {
    pub n: u64,
    pub mean: Option<f64>,
    pub sd: Option<f64>,
    pub p50: Option<f64>,
    pub p90: Option<f64>,
    pub p95: Option<f64>,
    pub p99: Option<f64>,
    pub max: Option<f64>,
}

/// Whole-stream spell distribution plus spell-start-month distributions.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SpellDistribution {
    pub whole_run: ScalarDistribution,
    pub by_start_month: Months<ScalarDistribution>,
}

/// Precipitation structure under one named wet-day predicate.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ThresholdPrecipitationStructure {
    pub wet_spells_days: SpellDistribution,
    pub dry_spells_days: SpellDistribution,
    pub wet_day_amount_mm: ScalarDistribution,
    pub adjacent_wet_day_amount: CorrPair,
    pub annual_max_1_day_mm: ScalarDistribution,
    pub annual_max_3_day_mm: ScalarDistribution,
    pub annual_max_5_day_mm: ScalarDistribution,
}

/// Legacy trace-positive and observed-comparable R1mm structure surfaces.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct PrecipitationStructure {
    pub trace_positive: ThresholdPrecipitationStructure,
    pub r1mm: ThresholdPrecipitationStructure,
}

/// Event-descriptor marginal distributions.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StormDescriptorDistributions {
    pub depth_mm: ScalarDistribution,
    pub duration_h: ScalarDistribution,
    pub time_to_peak_fraction: ScalarDistribution,
    pub peak_intensity_ratio: ScalarDistribution,
}

/// All six pairwise relationships among depth, duration, time-to-peak, and
/// peak/mean intensity ratio.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StormDescriptorDependence {
    pub depth_duration: CorrPair,
    pub depth_time_to_peak: CorrPair,
    pub depth_peak_intensity_ratio: CorrPair,
    pub duration_time_to_peak: CorrPair,
    pub duration_peak_intensity_ratio: CorrPair,
    pub time_to_peak_peak_intensity_ratio: CorrPair,
}

/// Whole-run event-descriptor quality surface.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StormDescriptors {
    pub wet_event_days: u64,
    pub included_event_days: u64,
    pub excluded_event_days: u64,
    pub distributions: StormDescriptorDistributions,
    pub dependence: StormDescriptorDependence,
}

/// Group P — run-emitted, observation-only process metrics.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ProcessMetrics {
    /// The conditioning policy the counters describe: `"faithful"`
    /// for the faithful backend today; `null` for `fast_batch_v0`
    /// (pre-knob, unconditioned).
    pub qc_filter: Option<String>,
    /// Per parameter (1..=9, source numbering) × month retry counts.
    pub retries: Vec<ParameterRetries>,
    /// Final statistics for every batch that exits `ranset`, in
    /// occurrence order. The three statistics are `null` for observed-mode
    /// parameter 9, whose source path bypasses quality evaluation.
    pub acceptance_statistics: Vec<AcceptanceStatistics>,
    /// Retry-cap give-up events (`iredo` reached 10,000,
    /// cligen.f:4302-4332): the still-failing batch was accepted.
    pub cap_give_ups: Vec<CapGiveUp>,
    /// `qc_filter: off` only: the faithful K-S / mean / variance
    /// verdicts evaluated diagnostically over the produced
    /// (unconditioned) batches — the would-have-been-rejected price of
    /// removing the conditioner. `null` under `faithful` and for
    /// `fast_batch_v0` (whose batch stream lacks the source
    /// predecessor chain the verdicts are defined over — SPEC rev 5).
    pub counterfactual: Option<CounterfactualMetrics>,
    /// `bk7.v7 == 0.0` band-aid draws (cligen.f:1253).
    pub v7_recovery_count: u64,
    /// Tdew low-range corrections (cligen.f:1464-1467).
    pub tdew_rangecheck_count: u64,
    /// Uniform draws consumed per stream k1..k10 over the run.
    pub randn_draws: [u64; 10],
}

/// Existing quality levels at the point a `ranset` batch is accepted.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AcceptanceStatistics {
    pub parameter: u32,
    pub month: u32,
    pub year: i32,
    /// K-S level returned by `ks_tst`, or `null` on the observed bypass.
    pub ks_level: Option<i32>,
    /// Mean-confidence level returned by `conflm`; `null` when not
    /// applicable or when K-S failed before this statistic was computed.
    pub mean_level: Option<f32>,
    /// Variance-confidence level returned by `confls`; `null` under the
    /// same conditions as `mean_level`.
    pub variance_level: Option<f32>,
}

/// The `qc_filter: off` diagnostic verdict counts.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct CounterfactualMetrics {
    /// Batches evaluated (parameter × month refills, minus the
    /// observed-mode parameter-9 bypass).
    pub batches: u64,
    /// Batches the faithful conditioner would have rejected.
    pub would_reject: u64,
    pub by_parameter: Vec<ParameterCounterfactual>,
}

/// Per-parameter counterfactual verdicts across months.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ParameterCounterfactual {
    /// Source parameter number (1..=9).
    pub parameter: u32,
    pub batches: Months<u64>,
    pub would_reject: Months<u64>,
}

/// Retry counts for one source parameter across months.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ParameterRetries {
    /// Source parameter number (1..=9).
    pub parameter: u32,
    /// Rejected attempts per calendar month over the run.
    pub rejected_attempts: Months<u64>,
    /// Accepted batches per calendar month over the run.
    pub accepted_batches: Months<u64>,
}

/// One retry-cap give-up event.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct CapGiveUp {
    pub parameter: u32,
    pub month: u32,
    pub year: i32,
}

const MONTH_NAMES: [&str; 12] = [
    "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec",
];

fn month_refs<T>(months: &Months<T>) -> [&T; 12] {
    [
        &months.jan,
        &months.feb,
        &months.mar,
        &months.apr,
        &months.may,
        &months.jun,
        &months.jul,
        &months.aug,
        &months.sep,
        &months.oct,
        &months.nov,
        &months.dec,
    ]
}

fn validate_report_relations(report: &QualityReport) -> Result<(), QualityError> {
    ensure(
        report.quality_report_schema_version == QUALITY_REPORT_SCHEMA_VERSION,
        "quality_report_schema_version",
        "does not match the supported envelope revision",
    )?;
    ensure(
        report.metrics_version == METRICS_VERSION,
        "metrics_version",
        "does not match the supported metric-vector revision",
    )?;
    validate_identity_and_years(report)?;
    validate_identity_provenance(report)?;
    validate_group_presence(report)?;
    if let Some(group) = &report.par_convergence {
        validate_par_convergence(group, &report.identity.content)?;
    }
    if let Some(group) = &report.interannual {
        validate_interannual(group, report)?;
    }
    if let Some(group) = &report.covariation {
        validate_covariation(group, report)?;
    }
    validate_tails(&report.tails, &report.identity.content)?;
    if let Some(process) = &report.process {
        validate_process(process, report)?;
    }
    Ok(())
}

fn validate_group_presence(report: &QualityReport) -> Result<(), QualityError> {
    let expected = report.identity.content.days > 1;
    ensure(
        report.par_convergence.is_some() == expected
            && report.interannual.is_some() == expected
            && report.covariation.is_some() == expected,
        "document",
        "groups A/B/C must be present exactly when the report has more than one day",
    )
}

fn validate_identity_and_years(report: &QualityReport) -> Result<(), QualityError> {
    let content = &report.identity.content;
    let years = &report.tails.per_year;
    let expected_years = usize::try_from(content.years).map_err(|_| {
        invalid(
            "identity.content.years",
            "does not fit this platform's vector length",
        )
    })?;
    ensure(
        years.len() == expected_years,
        "identity.content.years",
        "must equal tails.per_year length",
    )?;
    let first = years
        .first()
        .ok_or_else(|| invalid("tails.per_year", "must not be empty"))?;
    let last = years
        .last()
        .ok_or_else(|| invalid("tails.per_year", "must not be empty"))?;
    ensure(
        content.span == [first.year, last.year],
        "identity.content.span",
        "must equal the first and last per-year tail years",
    )?;
    let inclusive_years = i64::from(last.year) - i64::from(first.year) + 1;
    ensure(
        inclusive_years == i64::from(content.years),
        "identity.content",
        "years and span must describe consecutive calendar years",
    )?;
    let mut total_days = 0u64;
    for (index, year) in years.iter().enumerate() {
        ensure(
            year.n_days > 0,
            &format!("tails.per_year[{index}].n_days"),
            "must be positive",
        )?;
        total_days = total_days
            .checked_add(u64::from(year.n_days))
            .ok_or_else(|| invalid("tails.per_year", "day-count sum overflow"))?;
        if index > 0 {
            ensure(
                years[index - 1].year.checked_add(1) == Some(year.year),
                &format!("tails.per_year[{index}].year"),
                "must follow the preceding year",
            )?;
        }
        let complete = year.n_days == gregorian_year_days(year.year);
        ensure(
            year.complete_year == complete,
            &format!("tails.per_year[{index}].complete_year"),
            "must agree with the Gregorian day count",
        )?;
    }
    ensure(
        total_days == content.days,
        "identity.content.days",
        "must equal the sum of tails.per_year day counts",
    )
}

fn validate_identity_provenance(report: &QualityReport) -> Result<(), QualityError> {
    let Some(provenance) = &report.identity.provenance else {
        return Ok(());
    };
    let content = &report.identity.content;
    ensure(
        provenance.artifact.media_type == MediaTypeV1::CliText,
        "identity.provenance.artifact.media_type",
        "a quality report must describe the CLI text artifact it measures",
    )?;
    ensure(
        provenance.artifact.content_sha256.as_deref() == Some(content.cli_sha256.as_str()),
        "identity.content.cli_sha256",
        "must equal provenance.artifact.content_sha256",
    )?;
    ensure(
        content.station_parameter_set_sha256 == provenance.station.parameter_set_sha256,
        "identity.content.station_parameter_set_sha256",
        "must equal provenance.station.parameter_set_sha256",
    )?;
    ensure(
        content.station_source_sha256 == provenance.station.legacy_source_sha256,
        "identity.content.station_source_sha256",
        "must equal provenance.station.legacy_source_sha256",
    )?;
    ensure(
        content.station_model == "fixed_monthly_5_32_3"
            && provenance.station.model == StationModelV1::FixedMonthly5323,
        "identity.content.station_model",
        "must agree with provenance.station.model",
    )?;
    ensure(
        content.days == provenance.actual.emitted_day_count,
        "identity.content.days",
        "must equal provenance.actual.emitted_day_count",
    )?;
    let first_year = provenance
        .actual
        .first_date
        .ok_or_else(|| invalid("identity.provenance.actual.first_date", "must be present"))?
        .year;
    let last_year = provenance
        .actual
        .last_date
        .ok_or_else(|| invalid("identity.provenance.actual.last_date", "must be present"))?
        .year;
    ensure(
        content.span == [first_year, last_year],
        "identity.content.span",
        "must equal the year span in provenance.actual",
    )?;
    ensure(
        content.tool
            == format!(
                "{} {}",
                provenance.producer.name, provenance.producer.version
            ),
        "identity.content.tool",
        "must identify the provenance producer name and version",
    )
}

fn gregorian_year_days(year: i32) -> u32 {
    let leap = year % 4 == 0 && (year % 100 != 0 || year % 400 == 0);
    365 + u32::from(leap)
}

fn validate_tails(tails: &Tails, content: &IdentityContent) -> Result<(), QualityError> {
    let wet_days = validate_year_tails(&tails.per_year)?;
    validate_top_events(&tails.top_events, wet_days, content)?;
    let complete_years = tails
        .per_year
        .iter()
        .filter(|year| year.complete_year)
        .count();
    let complete_years = u64::try_from(complete_years)
        .map_err(|_| invalid("tails.per_year", "complete-year count does not fit u64"))?;
    validate_threshold_structure(
        &tails.precipitation_structure.trace_positive,
        wet_days,
        complete_years,
        "tails.precipitation_structure.trace_positive",
    )?;
    let r1mm_days = tails.precipitation_structure.r1mm.wet_day_amount_mm.n;
    ensure(
        r1mm_days <= wet_days,
        "tails.precipitation_structure.r1mm.wet_day_amount_mm.n",
        "cannot exceed the trace-positive wet-day count",
    )?;
    validate_threshold_structure(
        &tails.precipitation_structure.r1mm,
        r1mm_days,
        complete_years,
        "tails.precipitation_structure.r1mm",
    )?;
    validate_storm_descriptors(&tails.storm_descriptors, wet_days)
}

fn validate_year_tails(years: &[YearTails]) -> Result<u64, QualityError> {
    let mut wet_total = 0u64;
    for (index, year) in years.iter().enumerate() {
        let path = format!("tails.per_year[{index}]");
        ensure(
            year.max_1_day_precip_mm.is_some(),
            &format!("{path}.max_1_day_precip_mm"),
            "must be defined for every nonempty year slice",
        )?;
        ensure(
            year.wet_event_day_count <= year.n_days,
            &format!("{path}.wet_event_day_count"),
            "cannot exceed n_days",
        )?;
        ensure(
            year.max_peak_intensity_ratio.is_some() == (year.wet_event_day_count > 0),
            &format!("{path}.max_peak_intensity_ratio"),
            "definedness must agree with wet_event_day_count",
        )?;
        ensure(
            year.longest_wet_spell_days <= year.n_days
                && year.longest_dry_spell_days <= year.n_days,
            &path,
            "spell maxima cannot exceed n_days",
        )?;
        ensure(
            (year.longest_wet_spell_days > 0) == (year.wet_event_day_count > 0),
            &format!("{path}.longest_wet_spell_days"),
            "defined wet spells must agree with wet-event presence",
        )?;
        ensure(
            (year.longest_dry_spell_days > 0) == (year.wet_event_day_count < year.n_days),
            &format!("{path}.longest_dry_spell_days"),
            "defined dry spells must agree with dry-day presence",
        )?;
        wet_total = checked_count_add(
            wet_total,
            u64::from(year.wet_event_day_count),
            "tails.per_year",
        )?;
    }
    Ok(wet_total)
}

fn validate_top_events(
    events: &[TopEvent],
    wet_days: u64,
    content: &IdentityContent,
) -> Result<(), QualityError> {
    let event_count = u64::try_from(events.len())
        .map_err(|_| invalid("tails.top_events", "event count does not fit u64"))?;
    ensure(
        event_count == wet_days.min(5),
        "tails.top_events",
        "must contain min(wet_event_days, 5) entries",
    )?;
    let mut rows = HashSet::new();
    let mut dates = HashSet::new();
    for (index, event) in events.iter().enumerate() {
        let path = format!("tails.top_events[{index}]");
        let expected_rank = u32::try_from(index)
            .ok()
            .and_then(|value| value.checked_add(1))
            .ok_or_else(|| invalid(&path, "rank index does not fit u32"))?;
        ensure(
            event.rank == expected_rank,
            &format!("{path}.rank"),
            "ranks must be consecutive and ordered",
        )?;
        ensure(
            event.row_index <= content.days && rows.insert(event.row_index),
            &format!("{path}.row_index"),
            "must be in range and unique",
        )?;
        ensure(
            valid_report_date(content.days, event.year, event.month, event.day)
                && dates.insert((event.year, event.month, event.day)),
            &path,
            "event date must be valid and unique",
        )?;
        ensure(
            (content.span[0]..=content.span[1]).contains(&event.year),
            &format!("{path}.year"),
            "must lie within identity.content.span",
        )?;
        ensure(
            event.precip_mm > 0.0,
            &format!("{path}.precip_mm"),
            "top events must be wet",
        )?;
        if let Some(previous) = index.checked_sub(1).map(|prior| &events[prior]) {
            validate_top_event_order(previous, event, &path)?;
        }
    }
    Ok(())
}

fn valid_report_date(days: u64, year: i32, month: i32, day: i32) -> bool {
    if days == 1 {
        valid_source_date(year, month, day)
    } else {
        valid_gregorian_date(year, month, day)
    }
}

fn valid_source_date(year: i32, month: i32, day: i32) -> bool {
    let max_day = match month {
        2 => 28 + i32::from(year % 4 == 0),
        4 | 6 | 9 | 11 => 30,
        1 | 3 | 5 | 7 | 8 | 10 | 12 => 31,
        _ => return false,
    };
    (1..=max_day).contains(&day)
}

fn valid_gregorian_date(year: i32, month: i32, day: i32) -> bool {
    let leap = year % 4 == 0 && (year % 100 != 0 || year % 400 == 0);
    let max_day = match month {
        2 => 28 + i32::from(leap),
        4 | 6 | 9 | 11 => 30,
        1 | 3 | 5 | 7 | 8 | 10 | 12 => 31,
        _ => return false,
    };
    (1..=max_day).contains(&day)
}

fn validate_top_event_order(
    previous: &TopEvent,
    event: &TopEvent,
    path: &str,
) -> Result<(), QualityError> {
    ensure(
        previous.precip_mm >= event.precip_mm,
        path,
        "events must be ordered by nonincreasing precipitation",
    )?;
    if previous.precip_mm == event.precip_mm {
        ensure(
            (
                previous.year,
                previous.month,
                previous.day,
                previous.row_index,
            ) < (event.year, event.month, event.day, event.row_index),
            path,
            "equal-depth events must use the pinned date/row tie-break",
        )?;
    }
    Ok(())
}

fn validate_threshold_structure(
    structure: &ThresholdPrecipitationStructure,
    wet_days: u64,
    complete_years: u64,
    path: &str,
) -> Result<(), QualityError> {
    ensure(
        structure.wet_day_amount_mm.n == wet_days,
        &format!("{path}.wet_day_amount_mm.n"),
        "must equal the wet-day count for this threshold",
    )?;
    validate_distribution(
        &structure.wet_day_amount_mm,
        &format!("{path}.wet_day_amount_mm"),
    )?;
    validate_spell_distribution(
        &structure.wet_spells_days,
        &format!("{path}.wet_spells_days"),
    )?;
    validate_spell_distribution(
        &structure.dry_spells_days,
        &format!("{path}.dry_spells_days"),
    )?;
    let wet_spells = structure.wet_spells_days.whole_run.n;
    let dry_spells = structure.dry_spells_days.whole_run.n;
    ensure(
        wet_spells.abs_diff(dry_spells) <= 1 && (wet_spells != 0 || dry_spells != 0),
        path,
        "wet and dry spell counts must alternate across a nonempty stream",
    )?;
    ensure(
        structure.adjacent_wet_day_amount.n <= wet_days.saturating_sub(1),
        &format!("{path}.adjacent_wet_day_amount.n"),
        "cannot exceed wet_days - 1",
    )?;
    validate_corr_pair(
        &structure.adjacent_wet_day_amount,
        &format!("{path}.adjacent_wet_day_amount"),
    )?;
    for (name, distribution) in [
        ("annual_max_1_day_mm", &structure.annual_max_1_day_mm),
        ("annual_max_3_day_mm", &structure.annual_max_3_day_mm),
        ("annual_max_5_day_mm", &structure.annual_max_5_day_mm),
    ] {
        ensure(
            distribution.n == complete_years,
            &format!("{path}.{name}.n"),
            "must equal the number of complete years",
        )?;
        validate_distribution(distribution, &format!("{path}.{name}"))?;
    }
    Ok(())
}

fn validate_spell_distribution(spells: &SpellDistribution, path: &str) -> Result<(), QualityError> {
    validate_distribution(&spells.whole_run, &format!("{path}.whole_run"))?;
    let mut month_total = 0u64;
    for (month, distribution) in month_refs(&spells.by_start_month).into_iter().enumerate() {
        validate_distribution(
            distribution,
            &format!("{path}.by_start_month.{}", MONTH_NAMES[month]),
        )?;
        month_total = checked_count_add(month_total, distribution.n, path)?;
    }
    ensure(
        month_total == spells.whole_run.n,
        path,
        "start-month distribution counts must sum to whole_run.n",
    )
}

fn validate_storm_descriptors(
    descriptors: &StormDescriptors,
    wet_days: u64,
) -> Result<(), QualityError> {
    ensure(
        descriptors.wet_event_days == wet_days,
        "tails.storm_descriptors.wet_event_days",
        "must equal the per-year wet-event-day total",
    )?;
    ensure(
        descriptors
            .included_event_days
            .checked_add(descriptors.excluded_event_days)
            == Some(wet_days),
        "tails.storm_descriptors",
        "included_event_days + excluded_event_days must equal wet_event_days",
    )?;
    let distributions = &descriptors.distributions;
    for (name, distribution) in [
        ("depth_mm", &distributions.depth_mm),
        ("duration_h", &distributions.duration_h),
        (
            "time_to_peak_fraction",
            &distributions.time_to_peak_fraction,
        ),
        ("peak_intensity_ratio", &distributions.peak_intensity_ratio),
    ] {
        ensure(
            distribution.n == descriptors.included_event_days,
            &format!("tails.storm_descriptors.distributions.{name}.n"),
            "must equal included_event_days",
        )?;
        validate_distribution(
            distribution,
            &format!("tails.storm_descriptors.distributions.{name}"),
        )?;
    }
    let dependence = &descriptors.dependence;
    for (name, pair) in [
        ("depth_duration", &dependence.depth_duration),
        ("depth_time_to_peak", &dependence.depth_time_to_peak),
        (
            "depth_peak_intensity_ratio",
            &dependence.depth_peak_intensity_ratio,
        ),
        ("duration_time_to_peak", &dependence.duration_time_to_peak),
        (
            "duration_peak_intensity_ratio",
            &dependence.duration_peak_intensity_ratio,
        ),
        (
            "time_to_peak_peak_intensity_ratio",
            &dependence.time_to_peak_peak_intensity_ratio,
        ),
    ] {
        ensure(
            pair.n == descriptors.included_event_days,
            &format!("tails.storm_descriptors.dependence.{name}.n"),
            "must equal included_event_days",
        )?;
        validate_corr_pair(pair, &format!("tails.storm_descriptors.dependence.{name}"))?;
    }
    Ok(())
}

fn validate_distribution(
    distribution: &ScalarDistribution,
    path: &str,
) -> Result<(), QualityError> {
    let always_defined = [
        distribution.mean,
        distribution.p50,
        distribution.p90,
        distribution.p95,
        distribution.p99,
        distribution.max,
    ];
    match distribution.n {
        0 => ensure(
            always_defined.iter().all(Option::is_none) && distribution.sd.is_none(),
            path,
            "an empty distribution must contain only null statistics",
        )?,
        1 => ensure(
            always_defined.iter().all(Option::is_some) && distribution.sd.is_none(),
            path,
            "a singleton distribution has defined location/quantiles and null sample SD",
        )?,
        _ => ensure(
            always_defined.iter().all(Option::is_some) && distribution.sd.is_some(),
            path,
            "a multi-value distribution must define every statistic",
        )?,
    }
    if distribution.n > 0 {
        let ordered = [
            distribution.p50.unwrap(),
            distribution.p90.unwrap(),
            distribution.p95.unwrap(),
            distribution.p99.unwrap(),
            distribution.max.unwrap(),
        ];
        ensure(
            ordered.windows(2).all(|pair| pair[0] <= pair[1]),
            path,
            "quantiles and maximum must be nondecreasing",
        )?;
        ensure(
            distribution.mean.unwrap() <= distribution.max.unwrap(),
            path,
            "mean cannot exceed the observed maximum",
        )?;
    }
    Ok(())
}

fn validate_corr_pair(pair: &CorrPair, path: &str) -> Result<(), QualityError> {
    ensure(
        pair.pearson.is_some() == pair.spearman.is_some(),
        path,
        "Pearson and Spearman definedness must agree",
    )?;
    if pair.n < 2 {
        ensure(
            pair.pearson.is_none(),
            path,
            "correlations require at least two paired values",
        )?;
    }
    Ok(())
}

fn validate_par_convergence(
    group: &ParConvergence,
    content: &IdentityContent,
) -> Result<(), QualityError> {
    let parameters = [
        ("precip_wet_mean_mm", &group.precip_wet_mean_mm),
        ("precip_wet_sd_mm", &group.precip_wet_sd_mm),
        ("precip_wet_skew", &group.precip_wet_skew),
        ("wet_day_fraction", &group.wet_day_fraction),
        ("p_ww", &group.p_ww),
        ("p_wd", &group.p_wd),
        ("tmax_mean_c", &group.tmax_mean_c),
        ("tmax_sd_c", &group.tmax_sd_c),
        ("tmin_mean_c", &group.tmin_mean_c),
        ("tmin_sd_c", &group.tmin_sd_c),
        ("radiation_mean_ly", &group.radiation_mean_ly),
        ("dewpoint_mean_c", &group.dewpoint_mean_c),
        ("wind_speed_mean_ms", &group.wind_speed_mean_ms),
    ];
    for (name, parameter) in parameters {
        validate_par_parameter(parameter, content, &format!("par_convergence.{name}"))?;
    }
    Ok(())
}

fn validate_par_parameter(
    parameter: &ParParameter,
    content: &IdentityContent,
    path: &str,
) -> Result<(), QualityError> {
    for (month, cell) in month_refs(&parameter.months).into_iter().enumerate() {
        validate_par_cell(cell, &format!("{path}.{}", MONTH_NAMES[month]))?;
    }
    validate_decade_count(
        parameter.by_decade.len(),
        content,
        &format!("{path}.by_decade"),
    )?;
    for (index, block) in parameter.by_decade.iter().enumerate() {
        let block_path = format!("{path}.by_decade[{index}]");
        validate_decade_identity(
            block.decade,
            block.start_year,
            block.n_years,
            index,
            content,
            &block_path,
        )?;
        for (month, cell) in month_refs(&block.months).into_iter().enumerate() {
            validate_par_cell(cell, &format!("{block_path}.months.{}", MONTH_NAMES[month]))?;
        }
    }
    Ok(())
}

fn validate_decade_count(
    actual: usize,
    content: &IdentityContent,
    path: &str,
) -> Result<(), QualityError> {
    let expected_u32 = content.years.div_ceil(10);
    let expected = usize::try_from(expected_u32)
        .map_err(|_| invalid(path, "derived decade count does not fit this platform"))?;
    ensure(
        actual == expected,
        path,
        "must contain exactly the decade blocks derived from identity.content",
    )
}

fn validate_decade_identity(
    decade: u32,
    start_year: i32,
    n_years: u32,
    index: usize,
    content: &IdentityContent,
    path: &str,
) -> Result<(), QualityError> {
    let expected_decade = u32::try_from(index).map_err(|_| {
        invalid(
            path,
            "decade index does not fit the published integer width",
        )
    })?;
    let offset = expected_decade
        .checked_mul(10)
        .ok_or_else(|| invalid(path, "decade year offset overflow"))?;
    let expected_start = i32::try_from(i64::from(content.span[0]) + i64::from(offset))
        .map_err(|_| invalid(path, "derived decade start year is outside the i32 range"))?;
    let remaining = content
        .years
        .checked_sub(offset)
        .ok_or_else(|| invalid(path, "decade starts beyond identity.content.years"))?;
    let expected_n = remaining.min(10);
    ensure(
        decade == expected_decade,
        &format!("{path}.decade"),
        "must equal the zero-based block index",
    )?;
    ensure(
        start_year == expected_start,
        &format!("{path}.start_year"),
        "must be derived from identity.content.span",
    )?;
    ensure(
        n_years == expected_n,
        &format!("{path}.n_years"),
        "must equal the years represented by this identity-derived block",
    )
}

fn validate_par_cell(cell: &ParCell, path: &str) -> Result<(), QualityError> {
    let expected_abs = cell
        .target
        .zip(cell.generated)
        .map(|(target, generated)| (generated - target).abs());
    ensure_optional_approx(
        cell.abs_err,
        expected_abs,
        &format!("{path}.abs_err"),
        "must equal |generated - target|",
    )?;
    let expected_rel = expected_abs
        .zip(cell.target)
        .and_then(|(error, target)| (target != 0.0).then_some(error / target.abs()));
    ensure_optional_approx(
        cell.rel_err,
        expected_rel,
        &format!("{path}.rel_err"),
        "must equal abs_err / |target| and be null for a zero target",
    )
}

fn validate_interannual(group: &Interannual, report: &QualityReport) -> Result<(), QualityError> {
    let complete_years = report
        .tails
        .per_year
        .iter()
        .filter(|year| year.complete_year)
        .count();
    let complete_years = u32::try_from(complete_years).map_err(|_| {
        invalid(
            "interannual",
            "complete-year count does not fit the published integer width",
        )
    })?;
    validate_annual_stats(&group.annual, Some(complete_years), "interannual.annual")?;
    for (month, climate) in month_refs(&group.monthly).into_iter().enumerate() {
        validate_monthly_climate(
            climate,
            report.identity.content.years,
            &format!("interannual.monthly.{}", MONTH_NAMES[month]),
        )?;
    }
    validate_interannual_dependence(
        &group.dependence,
        complete_years,
        &group.annual,
        &group.monthly,
    )?;
    validate_decade_count(
        group.by_decade.len(),
        &report.identity.content,
        "interannual.by_decade",
    )?;
    for (index, block) in group.by_decade.iter().enumerate() {
        let path = format!("interannual.by_decade[{index}]");
        validate_decade_identity(
            block.decade,
            block.start_year,
            block.n_years,
            index,
            &report.identity.content,
            &path,
        )?;
        validate_annual_stats(&block.annual, None, &format!("{path}.annual"))?;
        validate_annual_stats_upper_bound(&block.annual, block.n_years, &format!("{path}.annual"))?;
        for (month, climate) in month_refs(&block.monthly).into_iter().enumerate() {
            validate_monthly_climate(
                climate,
                block.n_years,
                &format!("{path}.monthly.{}", MONTH_NAMES[month]),
            )?;
        }
    }
    Ok(())
}

fn validate_annual_stats(
    stats: &AnnualStats,
    expected_n: Option<u32>,
    path: &str,
) -> Result<(), QualityError> {
    let dispersions = [
        ("precip_total_mm", &stats.precip_total_mm),
        ("trace_wet_day_count", &stats.trace_wet_day_count),
        ("r1mm_wet_day_count", &stats.r1mm_wet_day_count),
        ("max_daily_precip_mm", &stats.max_daily_precip_mm),
    ];
    for (name, dispersion) in dispersions {
        validate_dispersion(dispersion, &format!("{path}.{name}"))?;
        if let Some(expected) = expected_n {
            ensure(
                dispersion.n_years == expected,
                &format!("{path}.{name}.n_years"),
                "must equal the number of complete years",
            )?;
        }
    }
    for (name, dispersion) in [
        ("tmax_mean_c", &stats.tmax_mean_c),
        ("tmin_mean_c", &stats.tmin_mean_c),
    ] {
        validate_location_dispersion(dispersion, &format!("{path}.{name}"))?;
        if let Some(expected) = expected_n {
            ensure(
                dispersion.n_years == expected,
                &format!("{path}.{name}.n_years"),
                "must equal the number of complete years",
            )?;
        }
    }
    Ok(())
}

fn validate_annual_stats_upper_bound(
    stats: &AnnualStats,
    max_years: u32,
    path: &str,
) -> Result<(), QualityError> {
    for (name, n_years) in [
        ("precip_total_mm", stats.precip_total_mm.n_years),
        ("trace_wet_day_count", stats.trace_wet_day_count.n_years),
        ("r1mm_wet_day_count", stats.r1mm_wet_day_count.n_years),
        ("max_daily_precip_mm", stats.max_daily_precip_mm.n_years),
        ("tmax_mean_c", stats.tmax_mean_c.n_years),
        ("tmin_mean_c", stats.tmin_mean_c.n_years),
    ] {
        ensure(
            n_years <= max_years,
            &format!("{path}.{name}.n_years"),
            "cannot exceed the enclosing decade's year count",
        )?;
    }
    Ok(())
}

fn validate_monthly_climate(
    climate: &MonthlyClimate,
    represented_years: u32,
    path: &str,
) -> Result<(), QualityError> {
    let complete_month_years = climate.precip_total_mm.n_years;
    for (name, dispersion) in [
        ("precip_total_mm", &climate.precip_total_mm),
        ("trace_wet_day_count", &climate.trace_wet_day_count),
        ("r1mm_wet_day_count", &climate.r1mm_wet_day_count),
    ] {
        validate_dispersion(dispersion, &format!("{path}.{name}"))?;
        validate_required_monthly_n_years(
            dispersion.n_years,
            complete_month_years,
            represented_years,
            &format!("{path}.{name}.n_years"),
        )?;
    }
    for (name, dispersion) in [
        (
            "trace_wet_day_mean_amount_mm",
            &climate.trace_wet_day_mean_amount_mm,
        ),
        (
            "r1mm_wet_day_mean_amount_mm",
            &climate.r1mm_wet_day_mean_amount_mm,
        ),
    ] {
        validate_dispersion(dispersion, &format!("{path}.{name}"))?;
        validate_optional_monthly_n_years(
            dispersion.n_years,
            complete_month_years,
            represented_years,
            &format!("{path}.{name}.n_years"),
        )?;
    }
    for (name, dispersion) in [
        ("tmax_mean_c", &climate.tmax_mean_c),
        ("tmin_mean_c", &climate.tmin_mean_c),
    ] {
        validate_location_dispersion(dispersion, &format!("{path}.{name}"))?;
        validate_required_monthly_n_years(
            dispersion.n_years,
            complete_month_years,
            represented_years,
            &format!("{path}.{name}.n_years"),
        )?;
    }
    Ok(())
}

fn validate_required_monthly_n_years(
    n_years: u32,
    complete_month_years: u32,
    represented_years: u32,
    path: &str,
) -> Result<(), QualityError> {
    ensure(
        n_years <= represented_years,
        path,
        "cannot exceed the represented years available to this month",
    )?;
    ensure(
        n_years == complete_month_years,
        path,
        "must equal the complete-month source count",
    )
}

fn validate_optional_monthly_n_years(
    n_years: u32,
    complete_month_years: u32,
    represented_years: u32,
    path: &str,
) -> Result<(), QualityError> {
    ensure(
        n_years <= represented_years,
        path,
        "cannot exceed the represented years available to this month",
    )?;
    ensure(
        n_years <= complete_month_years,
        path,
        "cannot exceed the complete-month source count",
    )
}

fn validate_dispersion(dispersion: &Dispersion, path: &str) -> Result<(), QualityError> {
    match dispersion.n_years {
        0 => ensure(
            dispersion.mean.is_none() && dispersion.sd.is_none() && dispersion.cv.is_none(),
            path,
            "zero years requires null mean, SD, and CV",
        )?,
        1 => ensure(
            dispersion.mean.is_some() && dispersion.sd.is_none() && dispersion.cv.is_none(),
            path,
            "one year requires a mean and null sample SD/CV",
        )?,
        _ => ensure(
            dispersion.mean.is_some() && dispersion.sd.is_some(),
            path,
            "two or more years require mean and sample SD",
        )?,
    }
    if let (Some(mean), Some(sd)) = (dispersion.mean, dispersion.sd) {
        let expected = (mean != 0.0).then_some(sd / mean);
        ensure_optional_approx(
            dispersion.cv,
            expected,
            &format!("{path}.cv"),
            "must equal sd / mean and be null for a zero mean",
        )?;
    }
    Ok(())
}

fn validate_location_dispersion(
    dispersion: &LocationDispersion,
    path: &str,
) -> Result<(), QualityError> {
    match dispersion.n_years {
        0 => ensure(
            dispersion.mean.is_none() && dispersion.sd.is_none(),
            path,
            "zero years requires null mean and SD",
        ),
        1 => ensure(
            dispersion.mean.is_some() && dispersion.sd.is_none(),
            path,
            "one year requires a mean and null sample SD",
        ),
        _ => ensure(
            dispersion.mean.is_some() && dispersion.sd.is_some(),
            path,
            "two or more years require mean and sample SD",
        ),
    }
}

fn validate_interannual_dependence(
    dependence: &InterannualDependence,
    complete_years: u32,
    annual: &AnnualStats,
    monthly: &Months<MonthlyClimate>,
) -> Result<(), QualityError> {
    let monthly = month_refs(monthly);
    let precip_sources =
        monthly.map(|climate| (climate.precip_total_mm.n_years, climate.precip_total_mm.sd));
    let tmax_sources = monthly.map(|climate| (climate.tmax_mean_c.n_years, climate.tmax_mean_c.sd));
    let tmin_sources = monthly.map(|climate| (climate.tmin_mean_c.n_years, climate.tmin_mean_c.sd));
    validate_month_matrix(
        &dependence.precip_cross_month,
        &precip_sources,
        "interannual.dependence.precip_cross_month",
    )?;
    validate_month_matrix(
        &dependence.tmax_cross_month,
        &tmax_sources,
        "interannual.dependence.tmax_cross_month",
    )?;
    validate_month_matrix(
        &dependence.tmin_cross_month,
        &tmin_sources,
        "interannual.dependence.tmin_cross_month",
    )?;
    for (month, correlations) in month_refs(&dependence.cross_variable_by_month)
        .into_iter()
        .enumerate()
    {
        let path = format!(
            "interannual.dependence.cross_variable_by_month.{}",
            MONTH_NAMES[month]
        );
        for (name, pair, left_n, right_n) in [
            (
                "precip_tmax",
                &correlations.precip_tmax,
                precip_sources[month].0,
                tmax_sources[month].0,
            ),
            (
                "precip_tmin",
                &correlations.precip_tmin,
                precip_sources[month].0,
                tmin_sources[month].0,
            ),
            (
                "tmax_tmin",
                &correlations.tmax_tmin,
                tmax_sources[month].0,
                tmin_sources[month].0,
            ),
        ] {
            validate_corr_pair_with_sources(pair, left_n, right_n, &format!("{path}.{name}"))?;
        }
    }
    for (name, series, source_sd) in [
        (
            "precip_total_mm",
            &dependence.annual.precip_total_mm,
            annual.precip_total_mm.sd,
        ),
        (
            "tmax_mean_c",
            &dependence.annual.tmax_mean_c,
            annual.tmax_mean_c.sd,
        ),
        (
            "tmin_mean_c",
            &dependence.annual.tmin_mean_c,
            annual.tmin_mean_c.sd,
        ),
    ] {
        validate_series_dependence(
            series,
            complete_years,
            source_sd,
            &format!("interannual.dependence.annual.{name}"),
        )?;
    }
    Ok(())
}

fn validate_corr_pair_with_sources(
    pair: &CorrPair,
    left_n: u32,
    right_n: u32,
    path: &str,
) -> Result<(), QualityError> {
    ensure(
        left_n == right_n,
        path,
        "participating monthly source counts must be aligned",
    )?;
    ensure(
        pair.n == u64::from(left_n),
        &format!("{path}.n"),
        "must equal the aligned participating monthly source count",
    )?;
    validate_corr_pair(pair, path)
}

fn validate_month_matrix(
    matrix: &MonthDependenceMatrix,
    sources: &[(u32, Option<f64>); 12],
    path: &str,
) -> Result<(), QualityError> {
    ensure(
        matrix.covariance.len() == 12
            && matrix.pearson_correlation.len() == 12
            && matrix.n_pairs.len() == 12
            && matrix.covariance.iter().all(|row| row.len() == 12)
            && matrix.pearson_correlation.iter().all(|row| row.len() == 12)
            && matrix.n_pairs.iter().all(|row| row.len() == 12),
        path,
        "all dependence matrices must be 12 by 12",
    )?;
    for row in 0..12 {
        for column in 0..12 {
            let n = matrix.n_pairs[row][column];
            ensure(
                n == matrix.n_pairs[column][row],
                &format!("{path}.n_pairs[{row}][{column}]"),
                "pair counts must be symmetric",
            )?;
            ensure_optional_approx(
                matrix.covariance[row][column],
                matrix.covariance[column][row],
                &format!("{path}.covariance[{row}][{column}]"),
                "covariance definedness and values must be symmetric",
            )?;
            ensure_optional_approx(
                matrix.pearson_correlation[row][column],
                matrix.pearson_correlation[column][row],
                &format!("{path}.pearson_correlation[{row}][{column}]"),
                "correlation definedness and values must be symmetric",
            )?;
            validate_month_matrix_cell(matrix, sources, row, column, path)?;
        }
    }
    Ok(())
}

fn validate_month_matrix_cell(
    matrix: &MonthDependenceMatrix,
    sources: &[(u32, Option<f64>); 12],
    row: usize,
    column: usize,
    path: &str,
) -> Result<(), QualityError> {
    let n = matrix.n_pairs[row][column];
    let count_path = format!("{path}.n_pairs[{row}][{column}]");
    if row == column {
        ensure(
            n == sources[row].0,
            &count_path,
            "diagonal count must equal the corresponding monthly sample size",
        )?;
    } else {
        ensure(
            n <= sources[row].0.min(sources[column].0),
            &count_path,
            "off-diagonal count cannot exceed either monthly sample size",
        )?;
    }
    ensure(
        matrix.covariance[row][column].is_some() == (n >= 2),
        &format!("{path}.covariance[{row}][{column}]"),
        "covariance must be defined exactly when at least two pairs exist",
    )?;
    if n < 2 {
        ensure(
            matrix.pearson_correlation[row][column].is_none(),
            &format!("{path}.pearson_correlation[{row}][{column}]"),
            "correlation requires at least two pairs",
        )?;
    }
    if row == column {
        validate_month_matrix_diagonal(matrix, sources[row].1, row, path)?;
    }
    Ok(())
}

fn validate_month_matrix_diagonal(
    matrix: &MonthDependenceMatrix,
    source_sd: Option<f64>,
    index: usize,
    path: &str,
) -> Result<(), QualityError> {
    ensure_optional_approx(
        matrix.covariance[index][index],
        source_sd.map(|sd| sd * sd),
        &format!("{path}.covariance[{index}][{index}]"),
        "diagonal covariance must equal the corresponding monthly SD squared",
    )?;
    let expected_correlation = source_sd.and_then(|sd| (sd > 0.0).then_some(1.0));
    ensure_optional_approx(
        matrix.pearson_correlation[index][index],
        expected_correlation,
        &format!("{path}.pearson_correlation[{index}][{index}]"),
        "diagonal correlation must be one exactly when monthly variance is positive",
    )
}

fn validate_series_dependence(
    series: &SeriesDependence,
    expected_n: u32,
    source_sd: Option<f64>,
    path: &str,
) -> Result<(), QualityError> {
    ensure(
        series.n_years == expected_n,
        &format!("{path}.n_years"),
        "must equal the complete-year count",
    )?;
    let expected_lag_n = u64::from(series.n_years.saturating_sub(1));
    ensure(
        series.lag_one.n == expected_lag_n,
        &format!("{path}.lag_one.n"),
        "must equal n_years - 1, saturating at zero",
    )?;
    validate_corr_pair(&series.lag_one, &format!("{path}.lag_one"))?;
    let expected_power = series.n_years >= 4 && source_sd.is_some_and(|sd| sd > 0.0);
    ensure(
        series.period_ge_4y_power_fraction.is_some() == expected_power,
        &format!("{path}.period_ge_4y_power_fraction"),
        "definedness must agree with n_years >= 4 and positive annual-series variance",
    )
}

fn validate_covariation(group: &Covariation, report: &QualityReport) -> Result<(), QualityError> {
    let wet_days = report.tails.storm_descriptors.wet_event_days;
    ensure(
        validate_corr_set(&group.whole_run, "covariation.whole_run")? == wet_days,
        "covariation.whole_run",
        "pair counts must equal the whole-run wet-day count",
    )?;
    let mut monthly_wet = 0u64;
    let mut monthly_dry = 0u64;
    let pair_months = month_refs(&group.months);
    let contrast_months = month_refs(&group.radiation_wet_dry_contrast);
    let range_months = month_refs(&group.daily_range_mean_c.months);
    for month in 0..12 {
        let path = format!("covariation.months.{}", MONTH_NAMES[month]);
        let wet = validate_corr_set(pair_months[month], &path)?;
        let contrast = contrast_months[month];
        validate_contrast_cell(
            contrast,
            &format!(
                "covariation.radiation_wet_dry_contrast.{}",
                MONTH_NAMES[month]
            ),
        )?;
        ensure(
            contrast.wet_n == wet,
            &format!(
                "covariation.radiation_wet_dry_contrast.{}.wet_n",
                MONTH_NAMES[month]
            ),
            "must equal the month correlation pair count",
        )?;
        ensure(
            range_months[month].is_some() == (contrast.wet_n != 0 || contrast.dry_n != 0),
            &format!(
                "covariation.daily_range_mean_c.months.{}",
                MONTH_NAMES[month]
            ),
            "definedness must agree with month day presence",
        )?;
        monthly_wet = checked_count_add(monthly_wet, contrast.wet_n, "covariation.months")?;
        monthly_dry = checked_count_add(monthly_dry, contrast.dry_n, "covariation.months")?;
    }
    let monthly_days = checked_count_add(monthly_wet, monthly_dry, "covariation")?;
    ensure(
        monthly_wet == wet_days && monthly_days == report.identity.content.days,
        "covariation",
        "monthly wet/dry counts must partition identity.content.days",
    )?;
    ensure(
        group.daily_range_mean_c.whole_run.is_some(),
        "covariation.daily_range_mean_c.whole_run",
        "must be defined for a nonempty report",
    )?;
    validate_decade_count(
        group.by_decade.len(),
        &report.identity.content,
        "covariation.by_decade",
    )?;
    for (index, block) in group.by_decade.iter().enumerate() {
        let path = format!("covariation.by_decade[{index}]");
        validate_decade_identity(
            block.decade,
            block.start_year,
            block.n_years,
            index,
            &report.identity.content,
            &path,
        )?;
        validate_corr_set(&block.pairs, &format!("{path}.pairs"))?;
        validate_contrast_cell(
            &block.radiation_wet_dry_contrast,
            &format!("{path}.radiation_wet_dry_contrast"),
        )?;
        ensure(
            block.daily_range_mean_c.is_some(),
            &format!("{path}.daily_range_mean_c"),
            "must be defined for a nonempty decade block",
        )?;
    }
    validate_winter_proxies(
        &group.winter_air_temperature_proxies,
        report,
        "covariation.winter_air_temperature_proxies",
    )
}

fn validate_corr_set(set: &CorrSet, path: &str) -> Result<u64, QualityError> {
    let pairs = [
        ("amount_duration", &set.amount_duration),
        (
            "amount_peak_intensity_ratio",
            &set.amount_peak_intensity_ratio,
        ),
        ("duration_radiation", &set.duration_radiation),
    ];
    let n = set.amount_duration.n;
    for (name, pair) in pairs {
        ensure(
            pair.n == n,
            &format!("{path}.{name}.n"),
            "all correlations in a set must use the same wet-day sample",
        )?;
        validate_corr_pair(pair, &format!("{path}.{name}"))?;
    }
    Ok(n)
}

fn validate_contrast_cell(cell: &ContrastCell, path: &str) -> Result<(), QualityError> {
    if cell.wet_n == 0 || cell.dry_n == 0 {
        ensure(
            cell.contrast.is_none(),
            &format!("{path}.contrast"),
            "requires nonempty wet and dry samples",
        )?;
    }
    Ok(())
}

fn validate_winter_proxies(
    winter: &WinterAirTemperatureProxies,
    report: &QualityReport,
    path: &str,
) -> Result<(), QualityError> {
    validate_freezing_fraction(
        &winter.precipitation_on_freezing_air_days,
        &format!("{path}.precipitation_on_freezing_air_days"),
    )?;
    ensure(
        winter.precipitation_on_freezing_air_days.n_days == report.identity.content.days,
        &format!("{path}.precipitation_on_freezing_air_days.n_days"),
        "must equal identity.content.days",
    )?;
    let mut monthly_days = 0u64;
    let mut monthly_freezing_days = 0u64;
    for (month, fraction) in month_refs(&winter.by_month).into_iter().enumerate() {
        validate_freezing_fraction(fraction, &format!("{path}.by_month.{}", MONTH_NAMES[month]))?;
        monthly_days =
            checked_count_add(monthly_days, fraction.n_days, &format!("{path}.by_month"))?;
        monthly_freezing_days = checked_count_add(
            monthly_freezing_days,
            fraction.freezing_air_day_count,
            &format!("{path}.by_month"),
        )?;
    }
    ensure(
        monthly_days == report.identity.content.days
            && monthly_freezing_days
                == winter
                    .precipitation_on_freezing_air_days
                    .freezing_air_day_count,
        &format!("{path}.by_month"),
        "monthly counts must sum to the whole-run winter proxy counts",
    )?;
    validate_corr_pair(
        &winter.djf_r1mm_precip_mean_air_temperature,
        &format!("{path}.djf_r1mm_precip_mean_air_temperature"),
    )?;
    validate_winter_per_year(winter, report, path)?;
    let complete_years = winter
        .per_year
        .iter()
        .filter(|year| year.complete_year)
        .count();
    let complete_years = u32::try_from(complete_years).map_err(|_| {
        invalid(
            path,
            "complete-year count does not fit the published integer width",
        )
    })?;
    validate_dispersion(
        &winter.freeze_thaw_air_temperature_proxy_cycles,
        &format!("{path}.freeze_thaw_air_temperature_proxy_cycles"),
    )?;
    ensure(
        winter.freeze_thaw_air_temperature_proxy_cycles.n_years == complete_years,
        &format!("{path}.freeze_thaw_air_temperature_proxy_cycles.n_years"),
        "must equal the complete-year count",
    )
}

fn validate_winter_per_year(
    winter: &WinterAirTemperatureProxies,
    report: &QualityReport,
    path: &str,
) -> Result<(), QualityError> {
    ensure(
        winter.per_year.len() == report.tails.per_year.len(),
        &format!("{path}.per_year"),
        "must align one-for-one with tails.per_year",
    )?;
    let mut total_days = 0u64;
    let mut freezing_days = 0u64;
    for (index, (proxy, tails)) in winter
        .per_year
        .iter()
        .zip(&report.tails.per_year)
        .enumerate()
    {
        let year_path = format!("{path}.per_year[{index}]");
        ensure(
            (proxy.year, proxy.n_days, proxy.complete_year)
                == (tails.year, tails.n_days, tails.complete_year),
            &year_path,
            "year identity, day count, and completeness must match tails.per_year",
        )?;
        validate_freezing_fraction(
            &proxy.precipitation_on_freezing_air_days,
            &format!("{year_path}.precipitation_on_freezing_air_days"),
        )?;
        ensure(
            proxy.precipitation_on_freezing_air_days.n_days == u64::from(proxy.n_days),
            &format!("{year_path}.precipitation_on_freezing_air_days.n_days"),
            "must equal the enclosing year's n_days",
        )?;
        ensure(
            proxy.freeze_thaw_air_temperature_proxy_cycles <= proxy.n_days,
            &format!("{year_path}.freeze_thaw_air_temperature_proxy_cycles"),
            "cannot exceed n_days",
        )?;
        total_days = checked_count_add(total_days, u64::from(proxy.n_days), &year_path)?;
        freezing_days = checked_count_add(
            freezing_days,
            proxy
                .precipitation_on_freezing_air_days
                .freezing_air_day_count,
            &year_path,
        )?;
    }
    ensure(
        total_days == winter.precipitation_on_freezing_air_days.n_days
            && freezing_days
                == winter
                    .precipitation_on_freezing_air_days
                    .freezing_air_day_count,
        &format!("{path}.per_year"),
        "per-year counts must sum to whole-run winter proxy counts",
    )
}

fn validate_freezing_fraction(
    fraction: &FreezingPrecipitationFraction,
    path: &str,
) -> Result<(), QualityError> {
    ensure(
        fraction.freezing_air_day_count <= fraction.n_days,
        &format!("{path}.freezing_air_day_count"),
        "cannot exceed n_days",
    )?;
    if fraction.n_days == 0 {
        return ensure(
            fraction.fraction.is_none()
                && fraction.precipitation_on_freezing_air_days_mm.is_none()
                && fraction.total_precipitation_mm.is_none(),
            path,
            "an empty sample requires null precipitation statistics",
        );
    }
    let freezing = fraction
        .precipitation_on_freezing_air_days_mm
        .ok_or_else(|| invalid(path, "freezing-air precipitation must be defined"))?;
    let total = fraction
        .total_precipitation_mm
        .ok_or_else(|| invalid(path, "total precipitation must be defined"))?;
    ensure(
        freezing <= total || approximately_equal(freezing, total),
        path,
        "freezing-air precipitation cannot exceed total precipitation",
    )?;
    let expected = (total != 0.0).then_some(freezing / total);
    ensure_optional_approx(
        fraction.fraction,
        expected,
        &format!("{path}.fraction"),
        "must equal freezing-air precipitation / total precipitation",
    )
}

fn validate_process(process: &ProcessMetrics, report: &QualityReport) -> Result<(), QualityError> {
    let unconditioned = validate_process_profile(process, report)?;
    let (expected_acceptances, accepted_total, retry_activity) = validate_retry_counters(process)?;
    let (actual_acceptances, recorded_total) =
        validate_acceptance_statistics(&process.acceptance_statistics, report)?;
    validate_acceptance_counts(
        &expected_acceptances,
        &actual_acceptances,
        accepted_total,
        recorded_total,
    )?;
    validate_cap_give_ups(&process.cap_give_ups, report)?;
    match process.qc_filter.as_deref() {
        Some("off") => ensure(
            process.counterfactual.is_some(),
            "process.counterfactual",
            "is required when qc_filter is off",
        )?,
        _ => ensure(
            process.counterfactual.is_none(),
            "process.counterfactual",
            "must be null unless qc_filter is off",
        )?,
    }
    if let Some(counterfactual) = &process.counterfactual {
        validate_counterfactual(counterfactual)?;
    }
    if unconditioned {
        ensure(
            retry_activity == 0
                && process.acceptance_statistics.is_empty()
                && process.cap_give_ups.is_empty(),
            "process",
            "unconditioned generation must not publish retry, acceptance, or cap-give-up activity",
        )?;
    }
    Ok(())
}

fn validate_process_profile(
    process: &ProcessMetrics,
    report: &QualityReport,
) -> Result<bool, QualityError> {
    let provenance = report.identity.provenance.as_ref().ok_or_else(|| {
        invalid(
            "process",
            "run-only process metrics require identity.provenance",
        )
    })?;
    let (expected_filter, unconditioned) = match (
        provenance.generation.profile,
        provenance.generation.qc_policy,
    ) {
        (GenerationProfileV1::Faithful5323, Some(QcPolicyV1::Faithful)) => {
            (Some("faithful"), false)
        }
        (GenerationProfileV1::Faithful5323, Some(QcPolicyV1::Off)) => (Some("off"), true),
        (GenerationProfileV1::FastBatchV0, None) => (None, true),
        _ => {
            return Err(invalid(
                "identity.provenance.generation",
                "generation profile and QC policy combination is unsupported",
            ));
        }
    };
    ensure(
        process.qc_filter.as_deref() == expected_filter,
        "process.qc_filter",
        "must agree with identity.provenance.generation",
    )?;
    Ok(unconditioned)
}

fn validate_retry_counters(
    process: &ProcessMetrics,
) -> Result<([[u64; 12]; 9], u64, u64), QualityError> {
    ensure(
        process.retries.len() == 9,
        "process.retries",
        "must contain parameters 1 through 9 exactly once",
    )?;
    let mut accepted_by_cell = [[0u64; 12]; 9];
    let mut accepted_total = 0u64;
    let mut retry_activity = 0u64;
    for (index, retries) in process.retries.iter().enumerate() {
        let expected_parameter = u32::try_from(index)
            .ok()
            .and_then(|value| value.checked_add(1))
            .ok_or_else(|| invalid("process.retries", "parameter index overflow"))?;
        let path = format!("process.retries[{index}]");
        ensure(
            retries.parameter == expected_parameter,
            &format!("{path}.parameter"),
            "parameters must be unique and ordered 1 through 9",
        )?;
        let rejected = sum_months_u64(&retries.rejected_attempts, &path)?;
        let accepted = sum_months_u64(&retries.accepted_batches, &path)?;
        accepted_total = checked_count_add(accepted_total, accepted, &path)?;
        retry_activity = checked_count_add(retry_activity, rejected, &path)?;
        retry_activity = checked_count_add(retry_activity, accepted, &path)?;
        for (month, value) in month_refs(&retries.accepted_batches)
            .into_iter()
            .enumerate()
        {
            accepted_by_cell[index][month] = *value;
        }
    }
    Ok((accepted_by_cell, accepted_total, retry_activity))
}

fn validate_acceptance_statistics(
    records: &[AcceptanceStatistics],
    report: &QualityReport,
) -> Result<([[u64; 12]; 9], u64), QualityError> {
    let mut by_cell = [[0u64; 12]; 9];
    let mut total = 0u64;
    for (index, record) in records.iter().enumerate() {
        let path = format!("process.acceptance_statistics[{index}]");
        let (parameter, month) = process_cell_indices(record.parameter, record.month, &path)?;
        ensure_year_in_report(record.year, report, &format!("{path}.year"))?;
        by_cell[parameter][month] = checked_count_add(
            by_cell[parameter][month],
            1,
            &format!("{path}.parameter_month_count"),
        )?;
        total = checked_count_add(total, 1, "process.acceptance_statistics")?;
    }
    let record_count = u64::try_from(records.len()).map_err(|_| {
        invalid(
            "process.acceptance_statistics",
            "record count does not fit the published integer width",
        )
    })?;
    ensure(
        total == record_count,
        "process.acceptance_statistics",
        "validated record count must equal the vector length",
    )?;
    Ok((by_cell, total))
}

fn validate_acceptance_counts(
    expected: &[[u64; 12]; 9],
    actual: &[[u64; 12]; 9],
    expected_total: u64,
    actual_total: u64,
) -> Result<(), QualityError> {
    ensure(
        expected_total == actual_total,
        "process.acceptance_statistics",
        "record count must equal the accepted_batches total",
    )?;
    for parameter in 0..9 {
        for month in 0..12 {
            ensure(
                expected[parameter][month] == actual[parameter][month],
                &format!(
                    "process.retries[{parameter}].accepted_batches.{}",
                    MONTH_NAMES[month]
                ),
                "must equal acceptance-statistics records for this parameter and month",
            )?;
        }
    }
    Ok(())
}

fn validate_cap_give_ups(events: &[CapGiveUp], report: &QualityReport) -> Result<(), QualityError> {
    for (index, event) in events.iter().enumerate() {
        let path = format!("process.cap_give_ups[{index}]");
        process_cell_indices(event.parameter, event.month, &path)?;
        ensure_year_in_report(event.year, report, &format!("{path}.year"))?;
    }
    Ok(())
}

fn process_cell_indices(
    parameter: u32,
    month: u32,
    path: &str,
) -> Result<(usize, usize), QualityError> {
    ensure(
        (1..=9).contains(&parameter),
        &format!("{path}.parameter"),
        "must be in 1 through 9",
    )?;
    ensure(
        (1..=12).contains(&month),
        &format!("{path}.month"),
        "must be in 1 through 12",
    )?;
    let parameter = usize::try_from(parameter - 1)
        .map_err(|_| invalid(path, "parameter index does not fit this platform"))?;
    let month = usize::try_from(month - 1)
        .map_err(|_| invalid(path, "month index does not fit this platform"))?;
    Ok((parameter, month))
}

fn ensure_year_in_report(
    year: i32,
    report: &QualityReport,
    path: &str,
) -> Result<(), QualityError> {
    ensure(
        (report.identity.content.span[0]..=report.identity.content.span[1]).contains(&year),
        path,
        "must fall within identity.content.span",
    )
}

fn validate_counterfactual(counterfactual: &CounterfactualMetrics) -> Result<(), QualityError> {
    let mut batches = 0u64;
    let mut rejected = 0u64;
    for (index, parameter) in counterfactual.by_parameter.iter().enumerate() {
        let path = format!("process.counterfactual.by_parameter[{index}]");
        let expected_parameter = u32::try_from(index)
            .ok()
            .and_then(|value| value.checked_add(1))
            .ok_or_else(|| invalid(&path, "parameter index does not fit u32"))?;
        ensure(
            parameter.parameter == expected_parameter,
            &format!("{path}.parameter"),
            "parameters must be unique and ordered 1 through 9",
        )?;
        let rejected_months = month_refs(&parameter.would_reject);
        let batch_months = month_refs(&parameter.batches);
        for (month, month_name) in MONTH_NAMES.iter().enumerate() {
            ensure(
                *rejected_months[month] <= *batch_months[month],
                &format!("{path}.would_reject.{month_name}"),
                "cannot exceed batches",
            )?;
        }
        batches = batches
            .checked_add(sum_months_u64(&parameter.batches, &path)?)
            .ok_or_else(|| invalid(&path, "batch count overflow"))?;
        rejected = rejected
            .checked_add(sum_months_u64(&parameter.would_reject, &path)?)
            .ok_or_else(|| invalid(&path, "rejection count overflow"))?;
    }
    ensure(
        (batches, rejected) == (counterfactual.batches, counterfactual.would_reject),
        "process.counterfactual",
        "totals must equal the sum of by-parameter month counts",
    )
}

fn sum_months_u64(months: &Months<u64>, path: &str) -> Result<u64, QualityError> {
    month_refs(months)
        .into_iter()
        .try_fold(0u64, |total, value| checked_count_add(total, *value, path))
}

fn ensure_optional_approx(
    actual: Option<f64>,
    expected: Option<f64>,
    path: &str,
    message: &str,
) -> Result<(), QualityError> {
    let matches = match (actual, expected) {
        (None, None) => true,
        (Some(actual), Some(expected)) => approximately_equal(actual, expected),
        _ => false,
    };
    ensure(matches, path, message)
}

fn approximately_equal(left: f64, right: f64) -> bool {
    let scale = 1.0f64.max(left.abs()).max(right.abs());
    (left - right).abs() <= f64::EPSILON * 8.0 * scale
}
