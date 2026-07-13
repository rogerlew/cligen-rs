//! The quality-report envelope (SPEC-QUALITY-REPORT §Report envelope).
//!
//! Serialization is byte-deterministic: serde emits struct fields in
//! declaration order, which **is** the schema order; every value is a
//! finite number, `null`, string, integer, or a fixed-shape
//! composite. No maps, no platform-dependent iteration anywhere.

use serde::{Deserialize, Serialize};

use super::QualityError;

/// The published metric-vector revision. Version 2 (Q3,
/// SPEC-QUALITY-REPORT rev 5) adds `process.counterfactual` — the
/// `qc_filter: off` would-have-been QC verdicts.
pub const METRICS_VERSION: u32 = 2;
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

    /// Deterministic serialization: pretty JSON, schema-ordered keys,
    /// trailing newline. A given report value has exactly one byte
    /// rendering.
    ///
    /// # Errors
    ///
    /// Returns the underlying serializer error; unreachable for
    /// reports built by this module (no non-finite values, no maps).
    pub fn to_json_bytes(&self) -> Result<Vec<u8>, QualityError> {
        if let Some(provenance) = &self.identity.provenance {
            provenance.validate().map_err(QualityError::Provenance)?;
        }
        let mut bytes = serde_json::to_vec_pretty(self).map_err(QualityError::Serialize)?;
        bytes.push(b'\n');
        Ok(bytes)
    }
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

/// The annual statistics group B disperses across years.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AnnualStats {
    pub precip_total_mm: Dispersion,
    pub wet_day_count: Dispersion,
    pub max_daily_precip_mm: Dispersion,
    pub tmax_mean_c: Dispersion,
    pub tmin_mean_c: Dispersion,
}

/// Interannual SD of one calendar month's precipitation totals.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MonthlySdCell {
    pub sd: Option<f64>,
    pub n_years: u32,
}

/// Group B — interannual dispersion.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Interannual {
    pub annual: AnnualStats,
    pub monthly_precip_total_sd_mm: Months<MonthlySdCell>,
    pub by_decade: Vec<InterannualDecade>,
}

/// A fixed 10-year block of group B statistics.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct InterannualDecade {
    pub decade: u32,
    pub start_year: i32,
    pub n_years: u32,
    pub annual: AnnualStats,
    pub monthly_precip_total_sd_mm: Months<MonthlySdCell>,
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
    pub amount_peak_intensity: CorrPair,
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
    pub by_decade: Vec<CovariationDecade>,
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

/// Group D — tails.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Tails {
    pub per_year: Vec<YearTails>,
    pub top_events: Vec<TopEvent>,
}

/// One simulated year's tail statistics. `n_days` makes partial years
/// (observed-mode truncation) visible.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct YearTails {
    pub year: i32,
    pub n_days: u32,
    pub max_daily_precip_mm: Option<f64>,
    pub storm_count: u32,
    pub max_peak_intensity: Option<f64>,
    pub longest_wet_spell_days: u32,
    pub longest_dry_spell_days: u32,
}

/// One of the whole-run top-five daily events, depth-ordered with the
/// pinned tie-break (earlier date, then lower row index).
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
    pub peak_intensity: f64,
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
