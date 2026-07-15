//! Experimental A5e0 direct annual-state research profile.
//!
//! This module implements only the package-local surface frozen by
//! SPEC-A5E0-PILOT. It is not a public generation-profile enum variant and it
//! never changes the faithful default path. The extension works in f64, uses
//! pinned `libm` transcendentals, and narrows once at the existing REAL*4
//! station-parameter boundary.

use std::fmt;

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use crate::cbk1::Cbk1State;
use crate::cbk7::Cbk7State;
use crate::modes::{DailyRow, ResolvedRunInputs, RunError};
use crate::profile::{GenerationProfile, QcFilter};
use crate::quality::report::ProcessMetrics;
use crate::rng::{advance_seed_raw, raw_updates_for_returned, seed_period, SeedState};

const PROFILE: &str = "a5e0_direct_annual_state_v1";
const COEFFICIENT_SCHEMA: &str = "a5e0_direct_annual_state_coefficients_v1";
const FIT_RECIPE: &str = "a5e0_direct_monthly_loading_fit_v1";
const SOURCE_COMMIT: &str = "27e5e7754bdfafcca649a71d0f5576910433d0d3";
const OBSERVED_SNAPSHOT: &str = "daymet_v4r1_a5a17_fit1980_2009_noleap_v1";
const CALENDAR: &str = "noleap_365_v1";
const DOMAIN: &[u8] = b"cligen-a5e0-annual-state-v1\0";
const SEGMENT_SIZE: u64 = 500_000;
const STATION_ORDER: [&str; 3] = ["ca042319", "co051660", "ms227840"];
const REGIME_ORDER: [&str; 3] = ["dry", "cold", "wet"];
const MASTER_SEEDS: [u64; 8] = [
    0x0c88_62ed_55f2_1e2e,
    0x0c26_8832_6839_59b1,
    0x1a23_7b20_16b9_5a3f,
    0x9132_8e5f_a9a0_e916,
    0x0ee4_5605_e7d3_62c3,
    0xc59c_0654_75f3_21a3,
    0x9d9e_f1d0_97f8_66ab,
    0x5098_4769_b3e5_9a89,
];

/// A5e0 study arm. Both arms use the same segmented faithful stream; only the
/// candidate activates the independent annual state.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum A5e0Arm {
    ResearchBaseline,
    Candidate,
}

impl A5e0Arm {
    /// Parse the exact research-arm label.
    pub fn parse(value: &str) -> Result<Self, A5e0Error> {
        match value {
            "research_baseline" => Ok(Self::ResearchBaseline),
            "candidate" => Ok(Self::Candidate),
            _ => Err(A5e0Error::Invalid(format!(
                "arm must be research_baseline or candidate, got {value:?}"
            ))),
        }
    }

    fn label(self) -> &'static str {
        match self {
            Self::ResearchBaseline => "research_baseline",
            Self::Candidate => "candidate",
        }
    }
}

/// Inputs to one isolated A5e0 research execution.
pub struct A5e0RunInputs<'a> {
    pub par_bytes: &'a [u8],
    pub coefficient_bytes: &'a [u8],
    pub station_id: &'a str,
    pub arm: A5e0Arm,
    pub replicate: u8,
    pub years: i32,
}

/// One research execution's typed rows, text, and audit diagnostics.
#[derive(Debug, Clone)]
pub struct A5e0RunOutput {
    pub cli: String,
    pub rows: Vec<DailyRow>,
    pub diagnostics: A5e0Diagnostics,
}

/// Compact, run-local research provenance and RNG evidence.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct A5e0Diagnostics {
    pub research_profile: String,
    pub station_id: String,
    pub arm: A5e0Arm,
    pub replicate: u8,
    pub master_seed: String,
    pub coefficient_sha256: String,
    pub par_sha256: String,
    pub faithful_segment: u32,
    pub faithful_raw_skip: u64,
    pub faithful_partition: String,
    pub extension_prng: String,
    pub years: i32,
    pub annual_states: Vec<f64>,
    pub annual_state_sha256: Option<String>,
    pub initial_seed_states: [[i32; 4]; 10],
    pub final_seed_states: [[i32; 4]; 10],
    pub canonical_stream_periods: [u64; 10],
    pub actual_raw_updates: [u64; 10],
    pub process: ProcessMetrics,
}

impl A5e0Diagnostics {
    /// Deterministic compact JSON with one trailing line feed.
    pub fn to_json_bytes(&self) -> Result<Vec<u8>, A5e0Error> {
        let mut bytes = serde_json::to_vec(self).map_err(A5e0Error::Serialize)?;
        bytes.push(b'\n');
        Ok(bytes)
    }
}

/// Typed A5e0 intake or execution failure.
#[derive(Debug)]
pub enum A5e0Error {
    Parse(serde_json::Error),
    Serialize(serde_json::Error),
    Par(crate::par::ParError),
    Station(crate::station::StationDocumentError),
    Run(RunError),
    Invalid(String),
}

impl fmt::Display for A5e0Error {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Parse(error) => write!(formatter, "coefficient JSON: {error}"),
            Self::Serialize(error) => write!(formatter, "diagnostic JSON: {error}"),
            Self::Par(error) => write!(formatter, "station par: {error}"),
            Self::Station(error) => write!(formatter, "station contract: {error}"),
            Self::Run(error) => write!(formatter, "generator: {error}"),
            Self::Invalid(message) => formatter.write_str(message),
        }
    }
}

impl std::error::Error for A5e0Error {}

/// Execute one 30- or 100-year A5e0 research arm.
///
/// # Errors
///
/// Fails closed on every malformed identity, coefficient, station mismatch,
/// unsupported horizon, or generator error.
pub fn run(inputs: &A5e0RunInputs<'_>) -> Result<A5e0RunOutput, A5e0Error> {
    validate_run_inputs(inputs)?;
    let coefficients = CoefficientBundle::parse(inputs.coefficient_bytes)?;
    let station_coefficients = coefficients.station(inputs.station_id)?.clone();
    let par_sha256 = sha256_hex(inputs.par_bytes);
    if station_coefficients.base_par_sha256 != par_sha256 {
        return Err(A5e0Error::Invalid(format!(
            "station par hash mismatch: expected {}, got {par_sha256}",
            station_coefficients.base_par_sha256
        )));
    }
    let par = crate::par::ParFile::parse(inputs.par_bytes).map_err(A5e0Error::Par)?;
    crate::station::StationDocumentV1::from_legacy_par(&par).map_err(A5e0Error::Station)?;
    validate_station_values(&station_coefficients, par.fixed_monthly())?;

    let mut runtime = A5e0Runtime::new(
        inputs.station_id,
        inputs.arm,
        inputs.replicate,
        station_coefficients,
    )?;
    let command_echo = format!(
        "cligen-a5e0 --profile {PROFILE} --arm {} --station {} --replicate {}",
        inputs.arm.label(),
        inputs.station_id,
        inputs.replicate
    );
    let generated = crate::modes::run_to_cli_resolved_a5e0(
        &ResolvedRunInputs {
            iopt: 5,
            interp: 0,
            burn: 0,
            generation_profile: GenerationProfile::Faithful5323,
            qc_filter: QcFilter::Off,
            begin_year: Some(1),
            years: Some(inputs.years),
            station: par.fixed_monthly(),
            prn_bytes: None,
            storm: None,
            version: 5.3230,
            command_echo: &command_echo,
        },
        &mut runtime,
    )
    .map_err(A5e0Error::Run)?;
    let cli = generated.render_cli();
    let rows = generated.rows.clone();
    let process = generated.process.clone();
    let diagnostics = runtime.diagnostics(
        inputs.years,
        sha256_hex(inputs.coefficient_bytes),
        par_sha256,
        process,
    )?;
    Ok(A5e0RunOutput {
        cli,
        rows,
        diagnostics,
    })
}

fn validate_run_inputs(inputs: &A5e0RunInputs<'_>) -> Result<(), A5e0Error> {
    if !STATION_ORDER.contains(&inputs.station_id) {
        return Err(A5e0Error::Invalid(format!(
            "station_id is not in the frozen A5e0 matrix: {:?}",
            inputs.station_id
        )));
    }
    if !(1..=8).contains(&inputs.replicate) {
        return Err(A5e0Error::Invalid("replicate must be in 1..=8".to_owned()));
    }
    if !matches!(inputs.years, 30 | 100) {
        return Err(A5e0Error::Invalid(
            "years must be the frozen 30 or 100 year horizon".to_owned(),
        ));
    }
    Ok(())
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct CoefficientBundle {
    coefficient_schema: String,
    identity: CoefficientIdentity,
    source: CoefficientSource,
    numerics: CoefficientNumerics,
    stations: Vec<StationCoefficients>,
}

impl CoefficientBundle {
    fn parse(bytes: &[u8]) -> Result<Self, A5e0Error> {
        let mut deserializer = serde_json::Deserializer::from_slice(bytes);
        let bundle = Self::deserialize(&mut deserializer).map_err(A5e0Error::Parse)?;
        deserializer.end().map_err(A5e0Error::Parse)?;
        bundle.validate()?;
        Ok(bundle)
    }

    fn validate(&self) -> Result<(), A5e0Error> {
        require_equal(
            "coefficient_schema",
            &self.coefficient_schema,
            COEFFICIENT_SCHEMA,
        )?;
        self.identity.validate()?;
        self.source.validate()?;
        self.numerics.validate()?;
        if self.stations.len() != STATION_ORDER.len() {
            return Err(A5e0Error::Invalid(
                "stations must contain exactly the three frozen stations".to_owned(),
            ));
        }
        for (index, station) in self.stations.iter().enumerate() {
            station.validate(STATION_ORDER[index], REGIME_ORDER[index])?;
        }
        Ok(())
    }

    fn station(&self, station_id: &str) -> Result<&StationCoefficients, A5e0Error> {
        self.stations
            .iter()
            .find(|station| station.station_id == station_id)
            .ok_or_else(|| A5e0Error::Invalid(format!("missing station {station_id}")))
    }
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct CoefficientIdentity {
    research_profile: String,
    fit_recipe: String,
    source_commit: String,
    fitter_sha256: String,
}

impl CoefficientIdentity {
    fn validate(&self) -> Result<(), A5e0Error> {
        require_equal("identity.research_profile", &self.research_profile, PROFILE)?;
        require_equal("identity.fit_recipe", &self.fit_recipe, FIT_RECIPE)?;
        require_equal("identity.source_commit", &self.source_commit, SOURCE_COMMIT)?;
        require_sha256("identity.fitter_sha256", &self.fitter_sha256)
    }
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct CoefficientSource {
    observed_snapshot: String,
    fit_years: [i32; 2],
    calendar: String,
    wet_threshold_mm: f64,
    station_order: [String; 3],
}

impl CoefficientSource {
    fn validate(&self) -> Result<(), A5e0Error> {
        require_equal(
            "source.observed_snapshot",
            &self.observed_snapshot,
            OBSERVED_SNAPSHOT,
        )?;
        if self.fit_years != [1980, 2009]
            || self.calendar != CALENDAR
            || self.wet_threshold_mm.to_bits() != 0.254f64.to_bits()
            || self.station_order != STATION_ORDER.map(str::to_owned)
        {
            return Err(A5e0Error::Invalid(
                "coefficient source contract differs from the frozen A5e0 source".to_owned(),
            ));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct CoefficientNumerics {
    python: String,
    numpy: String,
    scipy: String,
    quadrature_nodes: u32,
    root_method: String,
    root_xtol: f64,
    root_maxfev: u32,
}

impl CoefficientNumerics {
    fn validate(&self) -> Result<(), A5e0Error> {
        if self.python.is_empty()
            || self.numpy.is_empty()
            || self.scipy.is_empty()
            || self.quadrature_nodes != 32
            || self.root_method != "hybr"
            || self.root_xtol.to_bits() != 1.0e-12f64.to_bits()
            || self.root_maxfev != 20_000
        {
            return Err(A5e0Error::Invalid(
                "coefficient numerical contract differs from SPEC-A5E0-PILOT".to_owned(),
            ));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct ArtifactIdentity {
    path: String,
    sha256: String,
    bytes: u64,
}

impl ArtifactIdentity {
    fn validate(&self, field: &str) -> Result<(), A5e0Error> {
        if self.path.is_empty() || self.bytes == 0 {
            return Err(A5e0Error::Invalid(format!(
                "{field} must name a nonempty artifact"
            )));
        }
        require_sha256(&format!("{field}.sha256"), &self.sha256)
    }
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct StationCoefficients {
    station_id: String,
    regime: String,
    base_station: ArtifactIdentity,
    base_par_sha256: String,
    daymet: ArtifactIdentity,
    loadings: FourMonthlyArrays,
    derived: DerivedArrays,
    diagnostics: FitDiagnostics,
}

impl StationCoefficients {
    fn validate(&self, expected_id: &str, expected_regime: &str) -> Result<(), A5e0Error> {
        require_equal("station.station_id", &self.station_id, expected_id)?;
        require_equal("station.regime", &self.regime, expected_regime)?;
        self.base_station.validate("station.base_station")?;
        self.daymet.validate("station.daymet")?;
        require_sha256("station.base_par_sha256", &self.base_par_sha256)?;
        self.loadings.validate("station.loadings")?;
        self.derived.validate()?;
        self.diagnostics.validate()
    }

    fn all_zero(&self) -> bool {
        self.loadings.values().all(|value| value == 0.0)
    }

    fn occurrence_all_zero(&self) -> bool {
        self.loadings.occurrence.iter().all(|value| *value == 0.0)
    }
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct FourMonthlyArrays {
    occurrence: [f64; 12],
    amount: [f64; 12],
    tmax: [f64; 12],
    tmin: [f64; 12],
}

impl FourMonthlyArrays {
    fn values(&self) -> impl Iterator<Item = f64> + '_ {
        self.occurrence
            .iter()
            .chain(&self.amount)
            .chain(&self.tmax)
            .chain(&self.tmin)
            .copied()
    }

    fn validate(&self, field: &str) -> Result<(), A5e0Error> {
        if self.values().any(|value| !value.is_finite()) {
            return Err(A5e0Error::Invalid(format!(
                "{field} contains a nonfinite value"
            )));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct DerivedArrays {
    occurrence_intercepts: [f64; 12],
    amount_center: [f64; 12],
    amount_residual_sd_in: [f64; 12],
    tmax_residual_sd_f: [f64; 12],
    tmin_residual_sd_f: [f64; 12],
}

impl DerivedArrays {
    fn validate(&self) -> Result<(), A5e0Error> {
        let finite = self
            .occurrence_intercepts
            .iter()
            .chain(&self.amount_center)
            .chain(&self.amount_residual_sd_in)
            .chain(&self.tmax_residual_sd_f)
            .chain(&self.tmin_residual_sd_f)
            .all(|value| value.is_finite());
        let nonnegative = self
            .amount_residual_sd_in
            .iter()
            .chain(&self.tmax_residual_sd_f)
            .chain(&self.tmin_residual_sd_f)
            .all(|value| *value >= 0.0);
        if !finite || !nonnegative {
            return Err(A5e0Error::Invalid(
                "station.derived contains a nonfinite or negative residual value".to_owned(),
            ));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct FitDiagnostics {
    feature_sample_sd: FourMonthlyArrays,
    base_sampling_sd: FourMonthlyArrays,
    component_sign: FourSignArrays,
    occurrence_max_abs_count_error: f64,
    amount_max_relative_mean_error: f64,
    amount_max_relative_second_moment_error: f64,
    minimum_amount_residual_variance: f64,
    minimum_temperature_residual_variance: f64,
    minimum_occurrence_probability: f64,
    maximum_occurrence_probability: f64,
}

impl FitDiagnostics {
    fn validate(&self) -> Result<(), A5e0Error> {
        self.feature_sample_sd
            .validate("diagnostics.feature_sample_sd")?;
        self.base_sampling_sd
            .validate("diagnostics.base_sampling_sd")?;
        self.component_sign.validate()?;
        let values = [
            self.occurrence_max_abs_count_error,
            self.amount_max_relative_mean_error,
            self.amount_max_relative_second_moment_error,
            self.minimum_amount_residual_variance,
            self.minimum_temperature_residual_variance,
            self.minimum_occurrence_probability,
            self.maximum_occurrence_probability,
        ];
        if values.iter().any(|value| !value.is_finite())
            || self.occurrence_max_abs_count_error > 1.0e-10
            || self.amount_max_relative_mean_error > 1.0e-10
            || self.amount_max_relative_second_moment_error > 1.0e-10
            || self.minimum_amount_residual_variance < 0.0
            || self.minimum_temperature_residual_variance < 0.0
            || !(0.0 < self.minimum_occurrence_probability
                && self.minimum_occurrence_probability <= self.maximum_occurrence_probability
                && self.maximum_occurrence_probability < 1.0)
        {
            return Err(A5e0Error::Invalid(
                "station diagnostics fail the frozen H0 limits".to_owned(),
            ));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct FourSignArrays {
    occurrence: [i8; 12],
    amount: [i8; 12],
    tmax: [i8; 12],
    tmin: [i8; 12],
}

impl FourSignArrays {
    fn validate(&self) -> Result<(), A5e0Error> {
        if self
            .occurrence
            .iter()
            .chain(&self.amount)
            .chain(&self.tmax)
            .chain(&self.tmin)
            .any(|value| !matches!(value, -1 | 1))
        {
            return Err(A5e0Error::Invalid(
                "diagnostics.component_sign must contain only -1 or 1".to_owned(),
            ));
        }
        Ok(())
    }
}

fn validate_station_values(
    coefficients: &StationCoefficients,
    station: &crate::station::FixedMonthly5323,
) -> Result<(), A5e0Error> {
    for month in 0..12 {
        let pww = station.prw[month][0];
        let pwd = station.prw[month][1];
        if !(0.0 < pwd && pwd <= pww && pww < 1.0) {
            return Err(A5e0Error::Invalid(format!(
                "month {} occurrence base is outside the A5e0 domain",
                month + 1
            )));
        }
        validate_temperature_budget(
            month,
            "tmax",
            station.stdtx[month],
            coefficients.loadings.tmax[month],
            coefficients.derived.tmax_residual_sd_f[month],
        )?;
        validate_temperature_budget(
            month,
            "tmin",
            station.stdtm[month],
            coefficients.loadings.tmin[month],
            coefficients.derived.tmin_residual_sd_f[month],
        )?;
    }
    Ok(())
}

fn validate_temperature_budget(
    month: usize,
    variable: &str,
    base_sd: f32,
    loading_c: f64,
    residual_sd_f: f64,
) -> Result<(), A5e0Error> {
    let target = f64::from(base_sd) * f64::from(base_sd);
    let loading_f = 1.8 * loading_c;
    let reconstructed = loading_f * loading_f + residual_sd_f * residual_sd_f;
    let tolerance = 1.0e-10 * target.max(1.0);
    if (reconstructed - target).abs() > tolerance {
        return Err(A5e0Error::Invalid(format!(
            "month {} {variable} residual variance does not reconstruct the base budget",
            month + 1
        )));
    }
    Ok(())
}

fn require_equal(field: &str, value: &str, expected: &str) -> Result<(), A5e0Error> {
    if value == expected {
        Ok(())
    } else {
        Err(A5e0Error::Invalid(format!(
            "{field} must be {expected:?}, got {value:?}"
        )))
    }
}

fn require_sha256(field: &str, value: &str) -> Result<(), A5e0Error> {
    if value.len() == 64
        && value
            .as_bytes()
            .iter()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(byte))
    {
        Ok(())
    } else {
        Err(A5e0Error::Invalid(format!(
            "{field} must be a lowercase SHA-256"
        )))
    }
}

#[derive(Debug, Clone)]
struct BaseParameters {
    prw: [[f32; 2]; 12],
    amount_mean: [f32; 12],
    amount_sd: [f32; 12],
    tmax_mean: [f32; 12],
    tmin_mean: [f32; 12],
    tmax_sd: [f32; 12],
    tmin_sd: [f32; 12],
    dewpoint_mean: [f32; 12],
}

/// Mutable package-local hook threaded through the faithful year loop.
pub(crate) struct A5e0Runtime {
    station_id: String,
    arm: A5e0Arm,
    replicate: u8,
    master_seed: u64,
    segment: u32,
    raw_skip: u64,
    coefficients: StationCoefficients,
    annual_rng: SplitMix64BoxMuller,
    annual_states: Vec<f64>,
    base: Option<BaseParameters>,
    initial_seeds: Option<[SeedState; 10]>,
    final_seeds: Option<[SeedState; 10]>,
}

impl A5e0Runtime {
    fn new(
        station_id: &str,
        arm: A5e0Arm,
        replicate: u8,
        coefficients: StationCoefficients,
    ) -> Result<Self, A5e0Error> {
        let station_ordinal = STATION_ORDER
            .iter()
            .position(|candidate| *candidate == station_id)
            .ok_or_else(|| A5e0Error::Invalid("station is outside the frozen order".to_owned()))?;
        let segment = (8 * station_ordinal + usize::from(replicate - 1)) as u32;
        let master_seed = MASTER_SEEDS[usize::from(replicate - 1)];
        Ok(Self {
            station_id: station_id.to_owned(),
            arm,
            replicate,
            master_seed,
            segment,
            raw_skip: u64::from(segment) * SEGMENT_SIZE,
            coefficients,
            annual_rng: SplitMix64BoxMuller::new(derive_annual_seed(station_id, master_seed)),
            annual_states: Vec::new(),
            base: None,
            initial_seeds: None,
            final_seeds: None,
        })
    }

    pub(crate) fn partition_faithful_streams(&mut self, state: &mut Cbk7State) {
        for seed in seed_states_mut(state) {
            advance_seed_raw(seed, self.raw_skip);
        }
        self.initial_seeds = Some(seed_states(state));
    }

    pub(crate) fn bind_base(&mut self, bk1: &Cbk1State, bk7: &Cbk7State) {
        self.base = Some(BaseParameters {
            prw: bk7.prw,
            amount_mean: std::array::from_fn(|month| bk7.rst[month][0]),
            amount_sd: std::array::from_fn(|month| bk7.rst[month][1]),
            tmax_mean: bk7.obmx,
            tmin_mean: bk7.obmn,
            tmax_sd: bk7.stdtx,
            tmin_sd: bk7.stdtm,
            dewpoint_mean: bk1.rh,
        });
    }

    pub(crate) fn before_year(&mut self, bk1: &mut Cbk1State, bk7: &mut Cbk7State) {
        if self.arm == A5e0Arm::ResearchBaseline || self.coefficients.all_zero() {
            return;
        }
        let state = self.annual_rng.standard_normal();
        self.annual_states.push(state);
        let base = self
            .base
            .as_ref()
            .expect("A5e0 binds base before year loop");
        apply_occurrence(base, &self.coefficients, state, bk7);
        apply_amount(base, &self.coefficients, state, bk7);
        apply_temperature(base, &self.coefficients, state, bk1, bk7);
    }

    pub(crate) fn capture_final_seeds(&mut self, state: &Cbk7State) {
        self.final_seeds = Some(seed_states(state));
    }

    fn diagnostics(
        &self,
        years: i32,
        coefficient_sha256: String,
        par_sha256: String,
        process: ProcessMetrics,
    ) -> Result<A5e0Diagnostics, A5e0Error> {
        let initial = self
            .initial_seeds
            .ok_or_else(|| A5e0Error::Invalid("initial RNG state was not captured".to_owned()))?;
        let final_states = self
            .final_seeds
            .ok_or_else(|| A5e0Error::Invalid("final RNG state was not captured".to_owned()))?;
        let actual_raw_updates = std::array::from_fn(|stream| {
            raw_updates_for_returned(initial[stream], process.randn_draws[stream])
        });
        let annual_state_sha256 = if self.arm == A5e0Arm::Candidate && !self.coefficients.all_zero()
        {
            Some(sha256_hex(
                &serde_json::to_vec(&self.annual_states).expect("finite annual states serialize"),
            ))
        } else {
            None
        };
        let canonical = Cbk7State::default();
        let canonical_seeds = seed_states(&canonical);
        Ok(A5e0Diagnostics {
            research_profile: PROFILE.to_owned(),
            station_id: self.station_id.clone(),
            arm: self.arm,
            replicate: self.replicate,
            master_seed: format!("0x{:016x}", self.master_seed),
            coefficient_sha256,
            par_sha256,
            faithful_segment: self.segment,
            faithful_raw_skip: self.raw_skip,
            faithful_partition: "cbk7_skip_ahead_segments_v1".to_owned(),
            extension_prng: "splitmix64_box_muller_v1".to_owned(),
            years,
            annual_states: self.annual_states.clone(),
            annual_state_sha256,
            initial_seed_states: initial.map(|seed| seed.0),
            final_seed_states: final_states.map(|seed| seed.0),
            canonical_stream_periods: canonical_seeds.map(seed_period),
            actual_raw_updates,
            process,
        })
    }
}

fn apply_occurrence(
    base: &BaseParameters,
    coefficients: &StationCoefficients,
    state: f64,
    bk7: &mut Cbk7State,
) {
    if coefficients.occurrence_all_zero() {
        bk7.prw = base.prw;
        return;
    }
    for month in 0..12 {
        let pww = f64::from(base.prw[month][0]);
        let pwd = f64::from(base.prw[month][1]);
        let rho = pww - pwd;
        let linear = coefficients.derived.occurrence_intercepts[month]
            + coefficients.loadings.occurrence[month] * state;
        let wet_fraction = logistic(linear);
        let effective_pwd = (1.0 - rho) * wet_fraction;
        let effective_pww = rho + effective_pwd;
        bk7.prw[month] = [effective_pww as f32, effective_pwd as f32];
    }
}

fn apply_amount(
    base: &BaseParameters,
    coefficients: &StationCoefficients,
    state: f64,
    bk7: &mut Cbk7State,
) {
    for month in 0..12 {
        let loading = coefficients.loadings.amount[month];
        if loading == 0.0 {
            bk7.rst[month][0] = base.amount_mean[month];
            bk7.rst[month][1] = base.amount_sd[month];
        } else {
            let exponent = coefficients.derived.amount_center[month] + loading * state;
            bk7.rst[month][0] = (f64::from(base.amount_mean[month]) * libm::exp(exponent)) as f32;
            bk7.rst[month][1] = coefficients.derived.amount_residual_sd_in[month] as f32;
        }
    }
}

fn apply_temperature(
    base: &BaseParameters,
    coefficients: &StationCoefficients,
    state: f64,
    bk1: &mut Cbk1State,
    bk7: &mut Cbk7State,
) {
    for month in 0..12 {
        apply_temperature_month(
            base.tmax_mean[month],
            base.tmax_sd[month],
            coefficients.loadings.tmax[month],
            coefficients.derived.tmax_residual_sd_f[month],
            state,
            &mut bk7.obmx[month],
            &mut bk7.stdtx[month],
        );
        let tmin_loading = coefficients.loadings.tmin[month];
        apply_temperature_month(
            base.tmin_mean[month],
            base.tmin_sd[month],
            tmin_loading,
            coefficients.derived.tmin_residual_sd_f[month],
            state,
            &mut bk7.obmn[month],
            &mut bk7.stdtm[month],
        );
        bk1.rh[month] = if tmin_loading == 0.0 {
            base.dewpoint_mean[month]
        } else {
            (f64::from(base.dewpoint_mean[month]) + 1.8 * tmin_loading * state) as f32
        };
    }
}

#[allow(clippy::too_many_arguments)]
fn apply_temperature_month(
    base_mean: f32,
    base_sd: f32,
    loading_c: f64,
    residual_sd_f: f64,
    state: f64,
    output_mean: &mut f32,
    output_sd: &mut f32,
) {
    if loading_c == 0.0 {
        *output_mean = base_mean;
        *output_sd = base_sd;
    } else {
        *output_mean = (f64::from(base_mean) + 1.8 * loading_c * state) as f32;
        *output_sd = residual_sd_f as f32;
    }
}

fn logistic(value: f64) -> f64 {
    if value >= 0.0 {
        1.0 / (1.0 + libm::exp(-value))
    } else {
        let exponential = libm::exp(value);
        exponential / (1.0 + exponential)
    }
}

#[derive(Debug, Clone, Copy)]
struct SplitMix64BoxMuller {
    state: u64,
}

impl SplitMix64BoxMuller {
    fn new(state: u64) -> Self {
        Self { state }
    }

    fn next_u64(&mut self) -> u64 {
        self.state = self.state.wrapping_add(0x9e37_79b9_7f4a_7c15);
        let mut value = self.state;
        value = (value ^ (value >> 30)).wrapping_mul(0xbf58_476d_1ce4_e5b9);
        value = (value ^ (value >> 27)).wrapping_mul(0x94d0_49bb_1331_11eb);
        value ^ (value >> 31)
    }

    fn open_unit(&mut self) -> f64 {
        const SCALE: f64 = 1.0 / ((1u64 << 53) as f64);
        (((self.next_u64() >> 11) as f64) + 0.5) * SCALE
    }

    fn standard_normal(&mut self) -> f64 {
        let radius = libm::sqrt(-2.0 * libm::log(self.open_unit()));
        let angle = std::f64::consts::TAU * self.open_unit();
        radius * libm::cos(angle)
    }
}

fn derive_annual_seed(station_id: &str, master_seed: u64) -> u64 {
    let mut digest = Sha256::new();
    digest.update(DOMAIN);
    digest.update(station_id.as_bytes());
    digest.update([0]);
    digest.update(master_seed.to_be_bytes());
    let bytes: [u8; 8] = digest.finalize()[..8]
        .try_into()
        .expect("SHA-256 prefix is eight bytes");
    u64::from_be_bytes(bytes)
}

fn sha256_hex(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

fn seed_states(state: &Cbk7State) -> [SeedState; 10] {
    [
        state.k1, state.k2, state.k3, state.k4, state.k5, state.k6, state.k7, state.k8, state.k9,
        state.k10,
    ]
}

fn seed_states_mut(state: &mut Cbk7State) -> [&mut SeedState; 10] {
    [
        &mut state.k1,
        &mut state.k2,
        &mut state.k3,
        &mut state.k4,
        &mut state.k5,
        &mut state.k6,
        &mut state.k7,
        &mut state.k8,
        &mut state.k9,
        &mut state.k10,
    ]
}

#[cfg(test)]
mod tests {
    use super::*;

    const COEFFICIENTS: &[u8] = include_bytes!(
        "../../../docs/work-packages/20260714-a5e0-direct-annual-state-pilot/artifacts/a5e0-coefficients-v1.json"
    );

    fn coefficients() -> CoefficientBundle {
        CoefficientBundle::parse(COEFFICIENTS).unwrap()
    }

    #[test]
    fn frozen_bundle_passes_strict_runtime_intake() {
        let parsed = coefficients();
        assert_eq!(parsed.stations.len(), 3);
        assert_eq!(parsed.stations[0].station_id, "ca042319");
    }

    #[test]
    fn unknown_and_invalid_derived_fields_fail_closed() {
        let mut value: serde_json::Value = serde_json::from_slice(COEFFICIENTS).unwrap();
        value["unknown"] = serde_json::json!(true);
        assert!(CoefficientBundle::parse(&serde_json::to_vec(&value).unwrap()).is_err());

        let mut value: serde_json::Value = serde_json::from_slice(COEFFICIENTS).unwrap();
        value["stations"][0]["derived"]["amount_residual_sd_in"][0] = serde_json::json!(-1.0);
        assert!(CoefficientBundle::parse(&serde_json::to_vec(&value).unwrap()).is_err());
    }

    #[test]
    fn annual_state_rng_has_pinned_seed_and_normal_goldens() {
        let seed = derive_annual_seed("ca042319", MASTER_SEEDS[0]);
        assert_eq!(seed, 0x8a17_0b62_3da9_14bf);
        let mut rng = SplitMix64BoxMuller::new(seed);
        let values = std::array::from_fn::<_, 4, _>(|_| rng.standard_normal());
        assert_eq!(
            values.map(f64::to_bits),
            [
                (-0.8413057645171022f64).to_bits(),
                (-0.41934552207745696f64).to_bits(),
                (-0.7727070806584312f64).to_bits(),
                0.0842453585583669f64.to_bits(),
            ]
        );
    }

    #[test]
    fn all_zero_candidate_is_a_parameter_and_rng_bypass() {
        let mut station = coefficients().stations.remove(0);
        station.loadings = FourMonthlyArrays {
            occurrence: [0.0; 12],
            amount: [0.0; 12],
            tmax: [0.0; 12],
            tmin: [0.0; 12],
        };
        let mut baseline =
            A5e0Runtime::new("ca042319", A5e0Arm::ResearchBaseline, 1, station.clone()).unwrap();
        let mut candidate = A5e0Runtime::new("ca042319", A5e0Arm::Candidate, 1, station).unwrap();
        let mut baseline_bk7 = synthetic_bk7();
        let mut candidate_bk7 = baseline_bk7.clone();
        let mut baseline_bk1 = synthetic_bk1();
        let mut candidate_bk1 = baseline_bk1.clone();
        baseline.partition_faithful_streams(&mut baseline_bk7);
        candidate.partition_faithful_streams(&mut candidate_bk7);
        baseline.bind_base(&baseline_bk1, &baseline_bk7);
        candidate.bind_base(&candidate_bk1, &candidate_bk7);
        baseline.before_year(&mut baseline_bk1, &mut baseline_bk7);
        candidate.before_year(&mut candidate_bk1, &mut candidate_bk7);
        assert_eq!(seed_states(&baseline_bk7), seed_states(&candidate_bk7));
        assert_eq!(baseline_bk7.prw, candidate_bk7.prw);
        assert_eq!(baseline_bk7.rst, candidate_bk7.rst);
        assert_eq!(baseline_bk7.obmx, candidate_bk7.obmx);
        assert_eq!(baseline_bk7.obmn, candidate_bk7.obmn);
        assert_eq!(baseline_bk1.rh, candidate_bk1.rh);
        assert!(candidate.annual_states.is_empty());
    }

    #[test]
    fn active_year_routes_one_effective_occurrence_surface() {
        let station = coefficients().stations.remove(0);
        let mut runtime = A5e0Runtime::new("ca042319", A5e0Arm::Candidate, 1, station).unwrap();
        let mut bk7 = synthetic_bk7();
        let mut bk1 = synthetic_bk1();
        runtime.partition_faithful_streams(&mut bk7);
        runtime.bind_base(&bk1, &bk7);
        let base = bk7.prw;
        runtime.before_year(&mut bk1, &mut bk7);
        assert_eq!(runtime.annual_states.len(), 1);
        assert_ne!(bk7.prw, base);
        assert!(bk7
            .prw
            .iter()
            .flatten()
            .all(|probability| 0.0 < *probability && *probability < 1.0));
    }

    #[test]
    fn public_run_executes_all_zero_conformance_path() {
        const PAR: &[u8] = include_bytes!("../../../fixtures/new-meadows-id/id106388.par");

        let par = crate::par::ParFile::parse(PAR).unwrap();
        let station = par.fixed_monthly();
        let mut value: serde_json::Value = serde_json::from_slice(COEFFICIENTS).unwrap();
        value["stations"][0]["base_par_sha256"] = serde_json::json!(sha256_hex(PAR));
        for variable in ["occurrence", "amount", "tmax", "tmin"] {
            value["stations"][0]["loadings"][variable] = serde_json::to_value([0.0; 12]).unwrap();
        }
        value["stations"][0]["derived"]["amount_residual_sd_in"] =
            serde_json::json!(station.rst.map(|row| f64::from(row[1])));
        value["stations"][0]["derived"]["tmax_residual_sd_f"] =
            serde_json::json!(station.stdtx.map(f64::from));
        value["stations"][0]["derived"]["tmin_residual_sd_f"] =
            serde_json::json!(station.stdtm.map(f64::from));
        let zero_coefficients = serde_json::to_vec(&value).unwrap();

        let baseline = run(&A5e0RunInputs {
            par_bytes: PAR,
            coefficient_bytes: &zero_coefficients,
            station_id: "ca042319",
            arm: A5e0Arm::ResearchBaseline,
            replicate: 1,
            years: 30,
        })
        .unwrap();
        let candidate = run(&A5e0RunInputs {
            par_bytes: PAR,
            coefficient_bytes: &zero_coefficients,
            station_id: "ca042319",
            arm: A5e0Arm::Candidate,
            replicate: 1,
            years: 30,
        })
        .unwrap();

        assert_eq!(baseline.rows, candidate.rows);
        assert_eq!(
            baseline.diagnostics.final_seed_states,
            candidate.diagnostics.final_seed_states
        );
        assert!(candidate.diagnostics.annual_states.is_empty());
        assert!(candidate
            .diagnostics
            .to_json_bytes()
            .unwrap()
            .ends_with(b"\n"));
    }

    #[test]
    fn public_errors_are_typed_and_displayed() {
        assert_eq!(A5e0Arm::parse("candidate").unwrap(), A5e0Arm::Candidate);
        assert!(A5e0Arm::parse("unknown")
            .unwrap_err()
            .to_string()
            .contains("arm"));
        assert!(CoefficientBundle::parse(b"{")
            .unwrap_err()
            .to_string()
            .starts_with("coefficient JSON:"));
    }

    fn synthetic_bk7() -> Cbk7State {
        let mut state = Cbk7State::default();
        for month in 0..12 {
            state.prw[month] = [0.4, 0.1];
            state.rst[month] = [0.2, 0.3, 1.5];
            state.obmx[month] = 70.0;
            state.obmn[month] = 45.0;
            state.stdtx[month] = 8.0;
            state.stdtm[month] = 7.0;
        }
        state
    }

    fn synthetic_bk1() -> Cbk1State {
        Cbk1State {
            rh: [35.0; 12],
            ..Cbk1State::default()
        }
    }
}
