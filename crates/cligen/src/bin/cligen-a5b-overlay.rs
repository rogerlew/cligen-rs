#![forbid(unsafe_code)]

//! Research-only A5b annual-state overlay.
//!
//! The executable obtains a faithful, QC-off, pre-format row stream through
//! the public revision-1 typed-output API, then applies an explicitly labeled
//! A5b candidate plan. It does not modify or feed values back into the
//! source-authority generator.

use std::fs::{self, File, OpenOptions};
use std::io::Write as _;
use std::path::{Path, PathBuf};
use std::process::ExitCode;

use clap::Parser;
use cligen::modes::DailyRow;
use cligen::output::{write_daily_row, write_run_end};
use cligen::profile::{GenerationProfile, QcFilter};
use cligen::runspec::load_runspec_file;
use cligen::typed_output::ClimateRowV1;
use serde::{Deserialize, Deserializer, Serialize};
use sha2::{Digest as _, Sha256};

const COUNTERFACTUAL_PROFILE: &str = "a5b_fourier_eof_precip_counterfactual_v1";
const DAILY_HEADER: &str = concat!(
    " da mo year  prcp  dur   tp     ip  tmax  tmin  rad  w-vl w-dir  tdew\n",
    "             (mm)  (h)               (C)   (C) (l/d) (m/s)(Deg)   (C)\n"
);
const BASE_COMMAND_ECHO_SUFFIX: &str = "--a5b-base faithful_5_32_3 --qc-filter off ";
// F5.1 can render 999.9 without asterisks. Keeping the arithmetic ceiling at
// that decimal value is deliberately conservative across the final f64->f32
// narrowing and exact ties-to-even formatter.
const MAX_RENDERABLE_PRECIP_MM: f32 = 999.9;

#[derive(Debug, Parser)]
#[command(name = "cligen-a5b-overlay")]
#[command(about = "Apply one frozen A5b candidate plan to faithful QC-off rows")]
struct Args {
    /// Continuous faithful/QC-off SPEC-RUNSPEC document.
    #[arg(long)]
    input: PathBuf,
    /// Realized annual-state overlay plan.
    #[arg(long)]
    plan: PathBuf,
    /// New legacy-CLI destination (must not exist).
    #[arg(long)]
    output: PathBuf,
    /// New deterministic diagnostics destination (must not exist).
    #[arg(long)]
    diagnostics: PathBuf,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct OverlayPlan {
    plan_schema_version: u32,
    station_id: String,
    station_model: String,
    candidate_profile: String,
    extension_seed: String,
    coefficient_payload_sha256: String,
    state_table_sha256: String,
    normalization: Normalization,
    annual_states: Vec<AnnualState>,
    #[serde(default)]
    counterfactual: Option<CounterfactualPlan>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct Normalization {
    fixed_years: u32,
    precipitation_clip_count: u64,
    temperature_centered: bool,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct AnnualState {
    simulation_year: i32,
    precip_factor: [f64; 12],
    tmax_delta_c: [f64; 12],
    tmin_delta_c: [f64; 12],
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct CounterfactualPlan {
    second_order_prob: [[f64; 4]; 12],
    amount_rank_rho: [f64; 12],
    #[serde(deserialize_with = "deserialize_hex_u64")]
    rng_state: u64,
}

#[derive(Debug, Deserialize)]
struct HexU64(String);

#[derive(Debug, Default)]
struct OverlayCounts {
    temperature_order_repairs: u64,
    dewpoint_caps: u64,
    wet_days_before: u64,
    wet_days_after: u64,
    relocated_wet_days: u64,
    reassigned_storm_tuples: u64,
    counterfactual_months: u64,
    counterfactual_rng_final_state: Option<u64>,
    precipitation_render_limit_adjustments: u64,
    precipitation_factor_adjustments: Vec<PrecipitationFactorAdjustmentV1>,
}

#[derive(Debug, Clone, Serialize)]
#[serde(deny_unknown_fields)]
struct PrecipitationFactorAdjustmentV1 {
    simulation_year: i32,
    month: i32,
    requested_factor: f64,
    effective_factor: f64,
    base_max_precip_mm: f64,
    render_limit_mm: f64,
    adjusted: bool,
}

#[derive(Debug, Serialize)]
#[serde(deny_unknown_fields)]
struct DiagnosticsV1<'a> {
    diagnostics_schema_version: u32,
    station_id: &'a str,
    station_model: &'a str,
    candidate_profile: &'a str,
    extension_seed: &'a str,
    coefficient_payload_sha256: &'a str,
    state_table_sha256: &'a str,
    input_runspec_sha256: String,
    plan_sha256: String,
    faithful_cli_sha256: String,
    output_cli_sha256: String,
    row_count: usize,
    plan_state_years: usize,
    consumed_prefix_years: usize,
    wet_days_before: u64,
    wet_days_after: u64,
    temperature_order_repairs: u64,
    dewpoint_caps: u64,
    counterfactual_applied: bool,
    counterfactual_months: u64,
    relocated_wet_days: u64,
    reassigned_storm_tuples: u64,
    counterfactual_rng_final_state: Option<String>,
    precipitation_render_limit_adjustments: u64,
    precipitation_factor_adjustments: &'a [PrecipitationFactorAdjustmentV1],
}

#[derive(Debug, Clone, Copy, PartialEq)]
struct StormTuple {
    xr: f32,
    dur: f32,
    tpr: f32,
    xmav: f32,
}

#[derive(Debug, Clone, Copy)]
struct IndexedStorm {
    original_order: usize,
    tuple: StormTuple,
}

#[derive(Debug, Clone, Copy)]
struct RankedPosition {
    row_index: usize,
    score: f64,
}

#[derive(Debug, Clone, Copy)]
struct SplitMix64 {
    state: u64,
}

impl SplitMix64 {
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

    fn open_unit_f64(&mut self) -> f64 {
        const SCALE: f64 = 1.0 / ((1u64 << 53) as f64);
        (((self.next_u64() >> 11) as f64) + 0.5) * SCALE
    }

    fn standard_normal(&mut self) -> f64 {
        let radius = libm::sqrt(-2.0 * libm::log(self.open_unit_f64()));
        let angle = std::f64::consts::TAU * self.open_unit_f64();
        radius * libm::cos(angle)
    }
}

fn main() -> ExitCode {
    match run(Args::parse()) {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("cligen-a5b-overlay: {error}");
            ExitCode::FAILURE
        }
    }
}

fn run(args: Args) -> Result<(), String> {
    preflight_destinations(&args.output, &args.diagnostics)?;
    let prepared = load_runspec_file(&args.input)
        .map_err(|error| format!("load runspec {}: {error}", args.input.display()))?;
    validate_runspec(&prepared)?;

    let plan_bytes = read_file(&args.plan, "overlay plan")?;
    let plan: OverlayPlan = serde_json::from_slice(&plan_bytes)
        .map_err(|error| format!("parse overlay plan {}: {error}", args.plan.display()))?;
    validate_plan_values(&plan)?;

    let generated = prepared
        .generate_climate_v1()
        .map_err(|error| format!("generate faithful typed climate: {error}"))?;
    let consumed_prefix_years = validate_year_coverage(&plan, &generated.rows)?;
    let mut rows = convert_rows(&generated.rows)?;
    let counts = apply_overlay(&mut rows, &plan)?;
    let output = render_cli(&generated.legacy_cli, &rows, &plan)?;

    let input_bytes = read_file(&args.input, "runspec")?;
    let diagnostics = build_diagnostics(
        &plan,
        &input_bytes,
        &plan_bytes,
        &generated.legacy_cli,
        &output,
        rows.len(),
        consumed_prefix_years,
        &counts,
    )?;
    publish_pair(
        &args.output,
        output.as_bytes(),
        &args.diagnostics,
        &diagnostics,
    )
}

fn validate_runspec(prepared: &cligen::runspec::PreparedRun) -> Result<(), String> {
    if prepared.iopt != 5 {
        return Err("input runspec mode must be continuous".to_owned());
    }
    if prepared.generation_profile != GenerationProfile::Faithful5323 {
        return Err("input generation_profile must be faithful_5_32_3".to_owned());
    }
    if prepared.qc_filter != QcFilter::Off {
        return Err("input qc_filter must be off".to_owned());
    }
    Ok(())
}

fn validate_plan_values(plan: &OverlayPlan) -> Result<(), String> {
    if plan.plan_schema_version != 1 {
        return Err("plan_schema_version must equal 1".to_owned());
    }
    if plan.candidate_profile.is_empty() {
        return Err("candidate_profile must not be empty".to_owned());
    }
    validate_station_id(&plan.station_id)?;
    validate_model_profile_pair(&plan.station_model, &plan.candidate_profile)?;
    validate_extension_seed(&plan.extension_seed)?;
    validate_sha256(
        "coefficient_payload_sha256",
        &plan.coefficient_payload_sha256,
    )?;
    validate_sha256("state_table_sha256", &plan.state_table_sha256)?;
    validate_normalization(&plan.normalization)?;
    if plan.annual_states.len() != 128 {
        return Err("annual_states must contain exactly 128 entries".to_owned());
    }
    validate_counterfactual_binding(plan)?;
    for state in &plan.annual_states {
        validate_state(state)?;
    }
    if let Some(counterfactual) = &plan.counterfactual {
        validate_counterfactual(counterfactual)?;
    }
    Ok(())
}

fn validate_extension_seed(seed: &str) -> Result<u64, String> {
    let digits = seed
        .strip_prefix("0x")
        .ok_or_else(|| "extension_seed must start with lowercase 0x".to_owned())?;
    if digits.len() != 16
        || !digits
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err("extension_seed must be 0x followed by 16 lowercase hex digits".to_owned());
    }
    u64::from_str_radix(digits, 16).map_err(|error| format!("parse extension_seed as u64: {error}"))
}

fn validate_station_id(station_id: &str) -> Result<(), String> {
    let bytes = station_id.as_bytes();
    if bytes.len() == 8
        && bytes[..2].iter().all(u8::is_ascii_lowercase)
        && bytes[2..].iter().all(u8::is_ascii_digit)
    {
        Ok(())
    } else {
        Err("station_id must contain two lowercase letters and six digits".to_owned())
    }
}

fn validate_model_profile_pair(station_model: &str, profile: &str) -> Result<(), String> {
    let expected_model = match profile {
        "a5b_rank_one_monthly_sd_v1" => "interannual_rank_one_monthly_sd_v1",
        "a5b_full_monthly_covariance_v1" => "interannual_full_monthly_covariance_v1",
        "a5b_fourier_eof_v1" => "interannual_fourier_eof_v1",
        "a5b_vector_ar_v1" => "interannual_fourier_eof_var1_v1",
        "a5b_gaussian_hmm_v1" => "interannual_fourier_eof_hmm2_v1",
        "a5b_spectral_random_phase_v1" => "interannual_fourier_eof_spectral_v1",
        COUNTERFACTUAL_PROFILE => "interannual_fourier_eof_precip_counterfactual_v1",
        _ => return Err(format!("unsupported candidate_profile {profile:?}")),
    };
    if station_model == expected_model {
        Ok(())
    } else {
        Err(format!(
            "station_model {station_model:?} does not match candidate_profile {profile:?}"
        ))
    }
}

fn validate_sha256(name: &str, value: &str) -> Result<(), String> {
    if value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        Ok(())
    } else {
        Err(format!(
            "{name} must contain 64 lowercase hexadecimal digits"
        ))
    }
}

fn validate_normalization(normalization: &Normalization) -> Result<(), String> {
    if normalization.fixed_years != 128 {
        return Err("normalization.fixed_years must equal 128".to_owned());
    }
    if !normalization.temperature_centered {
        return Err("normalization.temperature_centered must be true".to_owned());
    }
    let _ = normalization.precipitation_clip_count;
    Ok(())
}

fn validate_counterfactual_binding(plan: &OverlayPlan) -> Result<(), String> {
    let is_profile = plan.candidate_profile == COUNTERFACTUAL_PROFILE;
    match (is_profile, plan.counterfactual.is_some()) {
        (true, false) => Err(format!(
            "candidate_profile {COUNTERFACTUAL_PROFILE} requires counterfactual"
        )),
        (false, true) => Err(format!(
            "counterfactual is permitted only for candidate_profile {COUNTERFACTUAL_PROFILE}"
        )),
        _ => Ok(()),
    }
}

fn validate_state(state: &AnnualState) -> Result<(), String> {
    if !(1..=99_999).contains(&state.simulation_year) {
        return Err("simulation_year must be in [1, 99999]".to_owned());
    }
    for (index, value) in state.precip_factor.iter().copied().enumerate() {
        finite_in_range(value, 0.05, 20.0, &format!("precip_factor[{index}]"))?;
    }
    for (name, values) in [
        ("tmax_delta_c", &state.tmax_delta_c),
        ("tmin_delta_c", &state.tmin_delta_c),
    ] {
        for (index, value) in values.iter().copied().enumerate() {
            finite_in_range(value, -30.0, 30.0, &format!("{name}[{index}]"))?;
        }
    }
    Ok(())
}

fn validate_counterfactual(plan: &CounterfactualPlan) -> Result<(), String> {
    for (month, probabilities) in plan.second_order_prob.iter().enumerate() {
        for (condition, value) in probabilities.iter().copied().enumerate() {
            finite_in_exclusive_range(
                value,
                0.0,
                1.0,
                &format!("second_order_prob[{month}][{condition}]"),
            )?;
        }
    }
    for (month, value) in plan.amount_rank_rho.iter().copied().enumerate() {
        finite_in_range(value, -0.95, 0.95, &format!("amount_rank_rho[{month}]"))?;
    }
    Ok(())
}

fn finite_in_exclusive_range(value: f64, low: f64, high: f64, field: &str) -> Result<(), String> {
    if value.is_finite() && value > low && value < high {
        Ok(())
    } else {
        Err(format!(
            "{field} must be finite and strictly between {low} and {high}"
        ))
    }
}

fn finite_in_range(value: f64, low: f64, high: f64, field: &str) -> Result<(), String> {
    if value.is_finite() && (low..=high).contains(&value) {
        Ok(())
    } else {
        Err(format!("{field} must be finite and in [{low}, {high}]"))
    }
}

fn validate_year_coverage(plan: &OverlayPlan, rows: &[ClimateRowV1]) -> Result<usize, String> {
    let years = complete_years(rows)?;
    if plan.annual_states.len() != 128 {
        return Err(format!(
            "annual_states length must equal 128, got {}",
            plan.annual_states.len()
        ));
    }
    let first_year = years[0];
    for (offset, state) in plan.annual_states.iter().enumerate() {
        let expected = first_year
            .checked_add(i32::try_from(offset).map_err(|error| error.to_string())?)
            .ok_or_else(|| "annual state year sequence overflows i32".to_owned())?;
        if state.simulation_year != expected {
            return Err(format!(
                "annual_states year mismatch: expected {expected}, got {}",
                state.simulation_year
            ));
        }
    }
    if years.len() > plan.annual_states.len() {
        return Err("generated run exceeds the 128-year state table".to_owned());
    }
    for (state, year) in plan.annual_states.iter().zip(&years) {
        if state.simulation_year != *year {
            return Err(format!(
                "annual_states year mismatch: expected {year}, got {}",
                state.simulation_year
            ));
        }
    }
    Ok(years.len())
}

fn complete_years(rows: &[ClimateRowV1]) -> Result<Vec<i32>, String> {
    let Some(first) = rows.first() else {
        return Err("generated typed row stream is empty".to_owned());
    };
    let mut years = Vec::new();
    let mut months = [false; 12];
    let mut current_year = first.year;
    for row in rows {
        if row.year != current_year {
            require_all_months(current_year, &months)?;
            years.push(current_year);
            current_year = row.year;
            months = [false; 12];
        }
        let month = month_index(row.month)?;
        months[month] = true;
    }
    require_all_months(current_year, &months)?;
    years.push(current_year);
    if years.windows(2).any(|pair| pair[1] != pair[0] + 1) {
        return Err("generated years are not continuous".to_owned());
    }
    Ok(years)
}

fn require_all_months(year: i32, months: &[bool; 12]) -> Result<(), String> {
    if months.iter().all(|present| *present) {
        Ok(())
    } else {
        Err(format!(
            "generated year {year} does not contain all 12 months"
        ))
    }
}

fn month_index(month: i8) -> Result<usize, String> {
    let zero_based = month
        .checked_sub(1)
        .ok_or_else(|| format!("invalid generated month {month}"))?;
    let index = usize::try_from(zero_based)
        .map_err(|error| format!("convert generated month {month}: {error}"))?;
    if index < 12 {
        Ok(index)
    } else {
        Err(format!("invalid generated month {month}"))
    }
}

fn convert_rows(rows: &[ClimateRowV1]) -> Result<Vec<DailyRow>, String> {
    rows.iter().map(convert_row).collect()
}

fn convert_row(row: &ClimateRowV1) -> Result<DailyRow, String> {
    Ok(DailyRow {
        jd: i32::from(row.day_of_month),
        mo: i32::from(row.month),
        iyear: row.year,
        xr: narrow(row.precip_mm, "precip_mm")?,
        dur: narrow(row.duration_h, "duration_h")?,
        tpr: narrow(row.time_to_peak_fraction, "time_to_peak_fraction")?,
        xmav: narrow(row.peak_intensity_ratio, "peak_intensity_ratio")?,
        tmxg: narrow(row.tmax_c, "tmax_c")?,
        tmng: narrow(row.tmin_c, "tmin_c")?,
        radg: narrow(row.solar_langley_day, "solar_langley_day")?,
        wv: narrow(row.wind_velocity_m_s, "wind_velocity_m_s")?,
        th: narrow(row.wind_direction_deg, "wind_direction_deg")?,
        tdp: narrow(row.tdew_c, "tdew_c")?,
    })
}

fn narrow(value: f64, field: &str) -> Result<f32, String> {
    let narrowed = value as f32;
    if value.is_finite() && narrowed.is_finite() {
        Ok(narrowed)
    } else {
        Err(format!("{field} is non-finite or overflows f32"))
    }
}

fn apply_overlay(rows: &mut [DailyRow], plan: &OverlayPlan) -> Result<OverlayCounts, String> {
    let mut counts = OverlayCounts {
        wet_days_before: count_wet(rows)?,
        ..OverlayCounts::default()
    };
    let effective = effective_precipitation_factors(rows, &plan.annual_states)?;
    counts.precipitation_render_limit_adjustments = effective
        .1
        .iter()
        .filter(|record| record.adjusted)
        .count()
        .try_into()
        .map_err(|error| format!("count precipitation render-limit adjustments: {error}"))?;
    counts.precipitation_factor_adjustments = effective.1;
    apply_annual_states(rows, &plan.annual_states, &effective.0, &mut counts)?;
    if let Some(counterfactual) = &plan.counterfactual {
        apply_counterfactual(rows, counterfactual, &mut counts)?;
    }
    counts.wet_days_after = count_wet(rows)?;
    if counts.wet_days_before != counts.wet_days_after {
        return Err("overlay changed the total wet-day count".to_owned());
    }
    Ok(counts)
}

fn apply_annual_states(
    rows: &mut [DailyRow],
    states: &[AnnualState],
    effective_precipitation: &[[f64; 12]],
    counts: &mut OverlayCounts,
) -> Result<(), String> {
    let mut state_index = 0usize;
    for row in rows {
        while states
            .get(state_index)
            .is_some_and(|state| state.simulation_year < row.iyear)
        {
            state_index += 1;
        }
        let state = states
            .get(state_index)
            .filter(|state| state.simulation_year == row.iyear)
            .ok_or_else(|| format!("no annual state for generated year {}", row.iyear))?;
        let month = daily_month_index(row.mo)?;
        let factor = effective_precipitation
            .get(state_index)
            .ok_or_else(|| format!("no effective precipitation state for year {}", row.iyear))?
            [month];
        apply_annual_state(row, state, month, factor, counts)?;
    }
    Ok(())
}

fn apply_annual_state(
    row: &mut DailyRow,
    state: &AnnualState,
    month: usize,
    effective_precip_factor: f64,
    counts: &mut OverlayCounts,
) -> Result<(), String> {
    validate_base_row(row)?;
    let precip = f64::from(row.xr) * effective_precip_factor;
    let mut tmax = f64::from(row.tmxg) + state.tmax_delta_c[month];
    let mut tmin = f64::from(row.tmng) + state.tmin_delta_c[month];
    let mut dewpoint = f64::from(row.tdp) + state.tmin_delta_c[month];
    if tmax < tmin {
        repair_temperature_order(&mut tmax, &mut tmin);
        counts.temperature_order_repairs += 1;
    }
    if dewpoint > tmin {
        dewpoint = tmin;
        counts.dewpoint_caps += 1;
    }
    row.xr = narrow(precip, "precip_mm")?;
    row.tmxg = narrow(tmax, "tmax_c")?;
    row.tmng = narrow(tmin, "tmin_c")?;
    row.tdp = narrow(dewpoint, "tdew_c")?;
    validate_overlay_arithmetic(row)?;
    if row.xr > MAX_RENDERABLE_PRECIP_MM {
        return Err("overlay precipitation exceeds the pinned F5.1 render limit".to_owned());
    }
    Ok(())
}

fn effective_precipitation_factors(
    rows: &[DailyRow],
    states: &[AnnualState],
) -> Result<(Vec<[f64; 12]>, Vec<PrecipitationFactorAdjustmentV1>), String> {
    let consumed_years = rows
        .last()
        .and_then(|row| usize::try_from(row.iyear).ok())
        .ok_or_else(|| "cannot derive consumed years from generated rows".to_owned())?;
    let consumed_states = states
        .get(..consumed_years)
        .ok_or_else(|| "annual state table is shorter than generated rows".to_owned())?;
    let mut maxima = vec![[0.0_f64; 12]; consumed_states.len()];
    for row in rows {
        let state_index = usize::try_from(row.iyear - 1)
            .map_err(|error| format!("convert simulation year {}: {error}", row.iyear))?;
        let month = daily_month_index(row.mo)?;
        let slot = maxima
            .get_mut(state_index)
            .ok_or_else(|| format!("no precipitation state for generated year {}", row.iyear))?;
        slot[month] = slot[month].max(f64::from(row.xr));
    }
    let mut effective = Vec::with_capacity(consumed_states.len());
    let mut records = Vec::with_capacity(consumed_states.len() * 12);
    for (state_index, state) in consumed_states.iter().enumerate() {
        let mut year = [0.0; 12];
        for month in 0..12 {
            let requested = state.precip_factor[month];
            let base_max = maxima[state_index][month];
            let ceiling = if base_max > 0.0 {
                f64::from(MAX_RENDERABLE_PRECIP_MM) / base_max
            } else {
                requested
            };
            let selected = requested.min(ceiling);
            if !selected.is_finite() || selected <= 0.0 {
                return Err(format!(
                    "invalid effective precipitation factor for year {} month {}",
                    state.simulation_year,
                    month + 1
                ));
            }
            year[month] = selected;
            records.push(PrecipitationFactorAdjustmentV1 {
                simulation_year: state.simulation_year,
                month: i32::try_from(month + 1)
                    .map_err(|error| format!("convert adjustment month: {error}"))?,
                requested_factor: requested,
                effective_factor: selected,
                base_max_precip_mm: base_max,
                render_limit_mm: f64::from(MAX_RENDERABLE_PRECIP_MM),
                adjusted: selected < requested,
            });
        }
        effective.push(year);
    }
    Ok((effective, records))
}

fn validate_base_row(row: &DailyRow) -> Result<(), String> {
    if row.xr < 0.0 {
        return Err(format!(
            "negative generated precipitation at {}-{}-{}",
            row.iyear, row.mo, row.jd
        ));
    }
    validate_overlay_arithmetic(row)
}

fn validate_overlay_arithmetic(row: &DailyRow) -> Result<(), String> {
    for (name, value) in [
        ("precip_mm", row.xr),
        ("duration_h", row.dur),
        ("time_to_peak_fraction", row.tpr),
        ("peak_intensity_ratio", row.xmav),
        ("tmax_c", row.tmxg),
        ("tmin_c", row.tmng),
        ("solar_langley_day", row.radg),
        ("wind_velocity_m_s", row.wv),
        ("wind_direction_deg", row.th),
        ("tdew_c", row.tdp),
    ] {
        if !value.is_finite() {
            return Err(format!("overlay produced non-finite f32 field {name}"));
        }
    }
    if row.xr < 0.0 {
        return Err("overlay produced negative precipitation".to_owned());
    }
    Ok(())
}

fn repair_temperature_order(tmax: &mut f64, tmin: &mut f64) {
    let midpoint = *tmax * 0.5 + *tmin * 0.5;
    *tmax = midpoint + 0.05;
    *tmin = midpoint - 0.05;
}

fn count_wet(rows: &[DailyRow]) -> Result<u64, String> {
    let mut count = 0u64;
    for row in rows {
        if !row.xr.is_finite() || row.xr < 0.0 {
            return Err("cannot classify a non-finite or negative precipitation row".to_owned());
        }
        count += u64::from(row.xr > 0.0);
    }
    Ok(count)
}

fn apply_counterfactual(
    rows: &mut [DailyRow],
    plan: &CounterfactualPlan,
    counts: &mut OverlayCounts,
) -> Result<(), String> {
    let mut rng = SplitMix64::new(plan.rng_state);
    let mut start = 0usize;
    while start < rows.len() {
        let year = rows[start].iyear;
        let month = rows[start].mo;
        let end = month_group_end(rows, start, year, month);
        let month_index = daily_month_index(month)?;
        let changes = relocate_month(
            &mut rows[start..end],
            &plan.second_order_prob[month_index],
            plan.amount_rank_rho[month_index],
            &mut rng,
        )?;
        counts.relocated_wet_days += changes.0;
        counts.reassigned_storm_tuples += changes.1;
        counts.counterfactual_months += 1;
        start = end;
    }
    counts.counterfactual_rng_final_state = Some(rng.state);
    Ok(())
}

fn month_group_end(rows: &[DailyRow], start: usize, year: i32, month: i32) -> usize {
    rows[start..]
        .iter()
        .position(|row| row.iyear != year || row.mo != month)
        .map_or(rows.len(), |offset| start + offset)
}

fn relocate_month(
    rows: &mut [DailyRow],
    probabilities: &[f64; 4],
    rho: f64,
    rng: &mut SplitMix64,
) -> Result<(u64, u64), String> {
    let before = rows.iter().map(storm_tuple).collect::<Vec<_>>();
    let events = collect_wet_events(&before)?;
    let selected = select_wet_positions(rows.len(), events.len(), probabilities, rng);
    clear_storm_tuples(rows);
    assign_ranked_events(rows, &selected, events, rho, rng);
    compare_storm_assignments(&before, rows)
}

fn storm_tuple(row: &DailyRow) -> StormTuple {
    StormTuple {
        xr: row.xr,
        dur: row.dur,
        tpr: row.tpr,
        xmav: row.xmav,
    }
}

fn collect_wet_events(tuples: &[StormTuple]) -> Result<Vec<IndexedStorm>, String> {
    let mut events = Vec::new();
    for (index, tuple) in tuples.iter().copied().enumerate() {
        for value in [tuple.xr, tuple.dur, tuple.tpr, tuple.xmav] {
            if !value.is_finite() {
                return Err("counterfactual received a non-finite storm tuple".to_owned());
            }
        }
        if tuple.xr < 0.0 {
            return Err("counterfactual received negative precipitation".to_owned());
        }
        if tuple.xr > 0.0 {
            events.push(IndexedStorm {
                original_order: index,
                tuple,
            });
        }
    }
    Ok(events)
}

fn select_wet_positions(
    day_count: usize,
    wet_count: usize,
    probabilities: &[f64; 4],
    rng: &mut SplitMix64,
) -> Vec<usize> {
    let mut selected = Vec::with_capacity(wet_count);
    let mut remaining_wet = wet_count;
    let mut history = 0usize;
    for day in 0..day_count {
        let remaining_days = day_count - day;
        let wet =
            choose_fixed_count_wet(remaining_wet, remaining_days, probabilities[history], rng);
        if wet {
            selected.push(day);
            remaining_wet -= 1;
        }
        history = ((history << 1) | usize::from(wet)) & 3;
    }
    selected
}

fn choose_fixed_count_wet(
    remaining_wet: usize,
    remaining_days: usize,
    guided_probability: f64,
    rng: &mut SplitMix64,
) -> bool {
    if remaining_wet == 0 {
        return false;
    }
    if remaining_wet == remaining_days {
        return true;
    }
    rng.open_unit_f64() < guided_probability
}

fn clear_storm_tuples(rows: &mut [DailyRow]) {
    for row in rows {
        row.xr = 0.0;
        row.dur = 0.0;
        row.tpr = 0.0;
        row.xmav = 0.0;
    }
}

fn assign_ranked_events(
    rows: &mut [DailyRow],
    selected: &[usize],
    mut events: Vec<IndexedStorm>,
    rho: f64,
    rng: &mut SplitMix64,
) {
    let mut positions = ar1_ranked_positions(selected, rho, rng);
    positions.sort_by(|left, right| {
        left.score
            .total_cmp(&right.score)
            .then(left.row_index.cmp(&right.row_index))
    });
    events.sort_by(|left, right| {
        left.tuple
            .xr
            .total_cmp(&right.tuple.xr)
            .then(left.original_order.cmp(&right.original_order))
    });
    for (position, event) in positions.into_iter().zip(events) {
        set_storm_tuple(&mut rows[position.row_index], event.tuple);
    }
}

fn ar1_ranked_positions(selected: &[usize], rho: f64, rng: &mut SplitMix64) -> Vec<RankedPosition> {
    if selected.is_empty() {
        return Vec::new();
    }
    let innovation_scale = libm::sqrt(1.0 - rho * rho);
    let mut previous = rng.standard_normal();
    let mut positions = Vec::with_capacity(selected.len());
    positions.push(RankedPosition {
        row_index: selected[0],
        score: previous,
    });
    for row_index in selected.iter().copied().skip(1) {
        previous = rho * previous + innovation_scale * rng.standard_normal();
        positions.push(RankedPosition {
            row_index,
            score: previous,
        });
    }
    positions
}

fn set_storm_tuple(row: &mut DailyRow, tuple: StormTuple) {
    row.xr = tuple.xr;
    row.dur = tuple.dur;
    row.tpr = tuple.tpr;
    row.xmav = tuple.xmav;
}

fn compare_storm_assignments(
    before: &[StormTuple],
    rows: &[DailyRow],
) -> Result<(u64, u64), String> {
    let mut relocated = 0u64;
    let mut reassigned = 0u64;
    for (old, row) in before.iter().zip(rows) {
        let new = storm_tuple(row);
        relocated += u64::from((old.xr > 0.0) != (new.xr > 0.0));
        reassigned += u64::from(!storm_tuple_bits_equal(*old, new));
    }
    let mut old_wet = before
        .iter()
        .copied()
        .filter(|tuple| tuple.xr > 0.0)
        .collect::<Vec<_>>();
    let mut new_wet = rows
        .iter()
        .map(storm_tuple)
        .filter(|tuple| tuple.xr > 0.0)
        .collect::<Vec<_>>();
    sort_storm_tuples(&mut old_wet);
    sort_storm_tuples(&mut new_wet);
    if old_wet.len() != new_wet.len()
        || old_wet
            .iter()
            .zip(new_wet)
            .any(|(old, new)| !storm_tuple_bits_equal(*old, new))
    {
        return Err("counterfactual did not preserve the wet-event tuple multiset".to_owned());
    }
    Ok((relocated, reassigned))
}

fn sort_storm_tuples(tuples: &mut [StormTuple]) {
    tuples.sort_by(|left, right| {
        left.xr
            .total_cmp(&right.xr)
            .then(left.dur.total_cmp(&right.dur))
            .then(left.tpr.total_cmp(&right.tpr))
            .then(left.xmav.total_cmp(&right.xmav))
    });
}

fn storm_tuple_bits_equal(left: StormTuple, right: StormTuple) -> bool {
    left.xr.to_bits() == right.xr.to_bits()
        && left.dur.to_bits() == right.dur.to_bits()
        && left.tpr.to_bits() == right.tpr.to_bits()
        && left.xmav.to_bits() == right.xmav.to_bits()
}

fn daily_month_index(month: i32) -> Result<usize, String> {
    let zero_based = month
        .checked_sub(1)
        .ok_or_else(|| format!("invalid generated month {month}"))?;
    let index = usize::try_from(zero_based)
        .map_err(|error| format!("convert generated month {month}: {error}"))?;
    if index < 12 {
        Ok(index)
    } else {
        Err(format!("invalid generated month {month}"))
    }
}

fn candidate_command_echo_suffix(plan: &OverlayPlan) -> String {
    format!(
        "--a5b-profile {} --extension-seed {} --qc-filter off ",
        plan.candidate_profile, plan.extension_seed
    )
}

fn rewrite_header(base: &str, plan: &OverlayPlan, header_end: usize) -> Result<String, String> {
    let metadata_start = base
        .match_indices('\n')
        .nth(3)
        .map(|(index, _)| index + 1)
        .ok_or_else(|| "faithful CLI header is missing its metadata line".to_owned())?;
    let metadata_end = base[metadata_start..]
        .find('\n')
        .map(|offset| metadata_start + offset)
        .ok_or_else(|| "faithful CLI metadata line is unterminated".to_owned())?;
    if metadata_end >= header_end {
        return Err("faithful CLI metadata line is outside its header".to_owned());
    }
    let metadata_line = &base[metadata_start..metadata_end];
    let prefix = metadata_line
        .strip_suffix(BASE_COMMAND_ECHO_SUFFIX)
        .ok_or_else(|| {
            format!(
                "runspec output.command_echo must produce suffix {:?}",
                BASE_COMMAND_ECHO_SUFFIX.trim_end()
            )
        })?;
    let mut header = String::with_capacity(header_end + 64);
    header.push_str(&base[..metadata_start]);
    header.push_str(prefix);
    header.push_str(&candidate_command_echo_suffix(plan));
    header.push('\n');
    header.push_str(&base[metadata_end + 1..header_end]);
    Ok(header)
}

fn render_cli(base: &str, rows: &[DailyRow], plan: &OverlayPlan) -> Result<String, String> {
    let header_start = base
        .find(DAILY_HEADER)
        .ok_or_else(|| "faithful CLI does not contain the exact daily column headers".to_owned())?;
    let header_end = header_start + DAILY_HEADER.len();
    let mut output = String::with_capacity(base.len());
    output.push_str(&rewrite_header(base, plan, header_end)?);
    for row in rows {
        let row_start = output.len();
        write_daily_row(&mut output, row);
        if output.as_bytes()[row_start..].contains(&b'*') {
            return Err(format!(
                "daily-row formatting overflow at {}-{}-{}",
                row.iyear, row.mo, row.jd
            ));
        }
    }
    write_run_end(&mut output);
    if output.contains('*') {
        return Err("rendered CLI contains a formatting asterisk".to_owned());
    }
    Ok(output)
}

#[allow(clippy::too_many_arguments)]
fn build_diagnostics(
    plan: &OverlayPlan,
    input_bytes: &[u8],
    plan_bytes: &[u8],
    faithful_cli: &str,
    output_cli: &str,
    row_count: usize,
    consumed_prefix_years: usize,
    counts: &OverlayCounts,
) -> Result<Vec<u8>, String> {
    let diagnostics = DiagnosticsV1 {
        diagnostics_schema_version: 1,
        station_id: &plan.station_id,
        station_model: &plan.station_model,
        candidate_profile: &plan.candidate_profile,
        extension_seed: &plan.extension_seed,
        coefficient_payload_sha256: &plan.coefficient_payload_sha256,
        state_table_sha256: &plan.state_table_sha256,
        input_runspec_sha256: sha256_hex(input_bytes),
        plan_sha256: sha256_hex(plan_bytes),
        faithful_cli_sha256: sha256_hex(faithful_cli.as_bytes()),
        output_cli_sha256: sha256_hex(output_cli.as_bytes()),
        row_count,
        plan_state_years: plan.annual_states.len(),
        consumed_prefix_years,
        wet_days_before: counts.wet_days_before,
        wet_days_after: counts.wet_days_after,
        temperature_order_repairs: counts.temperature_order_repairs,
        dewpoint_caps: counts.dewpoint_caps,
        counterfactual_applied: plan.counterfactual.is_some(),
        counterfactual_months: counts.counterfactual_months,
        relocated_wet_days: counts.relocated_wet_days,
        reassigned_storm_tuples: counts.reassigned_storm_tuples,
        counterfactual_rng_final_state: counts
            .counterfactual_rng_final_state
            .map(|state| format!("0x{state:016x}")),
        precipitation_render_limit_adjustments: counts.precipitation_render_limit_adjustments,
        precipitation_factor_adjustments: &counts.precipitation_factor_adjustments,
    };
    let mut bytes = serde_json::to_vec_pretty(&diagnostics)
        .map_err(|error| format!("serialize diagnostics: {error}"))?;
    bytes.push(b'\n');
    Ok(bytes)
}

fn sha256_hex(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

fn deserialize_hex_u64<'de, D>(deserializer: D) -> Result<u64, D::Error>
where
    D: Deserializer<'de>,
{
    let HexU64(value) = HexU64::deserialize(deserializer)?;
    validate_extension_seed(&value).map_err(serde::de::Error::custom)
}

fn preflight_destinations(output: &Path, diagnostics: &Path) -> Result<(), String> {
    if output == diagnostics {
        return Err("output and diagnostics destinations must differ".to_owned());
    }
    for (name, path) in [("output", output), ("diagnostics", diagnostics)] {
        if path.exists() {
            return Err(format!(
                "{name} destination already exists: {}",
                path.display()
            ));
        }
    }
    Ok(())
}

fn read_file(path: &Path, kind: &str) -> Result<Vec<u8>, String> {
    fs::read(path).map_err(|error| format!("read {kind} {}: {error}", path.display()))
}

fn create_new(path: &Path, kind: &str) -> Result<File, String> {
    OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)
        .map_err(|error| {
            format!(
                "create {kind} {} without overwrite: {error}",
                path.display()
            )
        })
}

fn publish_pair(
    output_path: &Path,
    output: &[u8],
    diagnostics_path: &Path,
    diagnostics: &[u8],
) -> Result<(), String> {
    let mut output_file = create_new(output_path, "output")?;
    let mut diagnostics_file = match create_new(diagnostics_path, "diagnostics") {
        Ok(file) => file,
        Err(error) => {
            drop(output_file);
            remove_new_file(output_path);
            return Err(error);
        }
    };
    let result = write_pair(&mut output_file, output, &mut diagnostics_file, diagnostics);
    drop(output_file);
    drop(diagnostics_file);
    if result.is_err() {
        remove_new_file(output_path);
        remove_new_file(diagnostics_path);
    }
    result
}

fn write_pair(
    output_file: &mut File,
    output: &[u8],
    diagnostics_file: &mut File,
    diagnostics: &[u8],
) -> Result<(), String> {
    output_file
        .write_all(output)
        .map_err(|error| format!("write output: {error}"))?;
    diagnostics_file
        .write_all(diagnostics)
        .map_err(|error| format!("write diagnostics: {error}"))?;
    output_file
        .sync_all()
        .map_err(|error| format!("sync output: {error}"))?;
    diagnostics_file
        .sync_all()
        .map_err(|error| format!("sync diagnostics: {error}"))?;
    Ok(())
}

fn remove_new_file(path: &Path) {
    let _ = fs::remove_file(path);
}

#[cfg(test)]
mod tests {
    use super::*;

    fn state(year: i32) -> AnnualState {
        AnnualState {
            simulation_year: year,
            precip_factor: [1.0; 12],
            tmax_delta_c: [0.0; 12],
            tmin_delta_c: [0.0; 12],
        }
    }

    fn plan() -> OverlayPlan {
        OverlayPlan {
            plan_schema_version: 1,
            station_id: "id106388".to_owned(),
            station_model: "interannual_rank_one_monthly_sd_v1".to_owned(),
            candidate_profile: "a5b_rank_one_monthly_sd_v1".to_owned(),
            extension_seed: "0x0c8862ed55f21e2e".to_owned(),
            coefficient_payload_sha256: "0".repeat(64),
            state_table_sha256: "1".repeat(64),
            normalization: Normalization {
                fixed_years: 128,
                precipitation_clip_count: 0,
                temperature_centered: true,
            },
            annual_states: (1..=128).map(state).collect(),
            counterfactual: None,
        }
    }

    fn row(day: i32, precip: f32) -> DailyRow {
        DailyRow {
            jd: day,
            mo: 1,
            iyear: 1,
            xr: precip,
            dur: if precip > 0.0 { precip + 0.25 } else { 0.0 },
            tpr: if precip > 0.0 { precip / 10.0 } else { 0.0 },
            xmav: if precip > 0.0 { precip * 2.0 } else { 0.0 },
            tmxg: 10.0,
            tmng: 5.0,
            radg: 100.0,
            wv: 2.0,
            th: 180.0,
            tdp: 4.0,
        }
    }

    fn climate_row(year: i32, month: i8) -> ClimateRowV1 {
        ClimateRowV1 {
            run_id: "0".repeat(64),
            generation_profile: "faithful_5_32_3".to_owned(),
            station_parameter_set_sha256: "1".repeat(64),
            sim_day_index: 1,
            year,
            month,
            day_of_month: 1,
            precip_mm: 0.0,
            duration_h: 0.0,
            time_to_peak_fraction: 0.0,
            peak_intensity_ratio: 0.0,
            tmax_c: 10.0,
            tmin_c: 5.0,
            solar_langley_day: 100.0,
            wind_velocity_m_s: 2.0,
            wind_direction_deg: 180.0,
            tdew_c: 4.0,
        }
    }

    #[test]
    fn plan_validation_is_strict_and_binds_candidate_seven() {
        let mut candidate = plan();
        assert!(validate_plan_values(&candidate).is_ok());
        candidate.extension_seed = "0x0C8862ED55F21E2E".to_owned();
        assert!(validate_plan_values(&candidate).is_err());

        candidate = plan();
        candidate.annual_states[0].precip_factor[3] = 0.0;
        assert!(validate_plan_values(&candidate).is_err());

        candidate = plan();
        candidate.candidate_profile = COUNTERFACTUAL_PROFILE.to_owned();
        candidate.station_model = "interannual_fourier_eof_precip_counterfactual_v1".to_owned();
        assert!(validate_plan_values(&candidate).is_err());
        candidate.counterfactual = Some(CounterfactualPlan {
            second_order_prob: [[0.5; 4]; 12],
            amount_rank_rho: [0.0; 12],
            rng_state: 17,
        });
        assert!(validate_plan_values(&candidate).is_ok());
    }

    #[test]
    fn every_frozen_profile_requires_its_station_model() {
        let pairs = [
            (
                "a5b_rank_one_monthly_sd_v1",
                "interannual_rank_one_monthly_sd_v1",
            ),
            (
                "a5b_full_monthly_covariance_v1",
                "interannual_full_monthly_covariance_v1",
            ),
            ("a5b_fourier_eof_v1", "interannual_fourier_eof_v1"),
            ("a5b_vector_ar_v1", "interannual_fourier_eof_var1_v1"),
            ("a5b_gaussian_hmm_v1", "interannual_fourier_eof_hmm2_v1"),
            (
                "a5b_spectral_random_phase_v1",
                "interannual_fourier_eof_spectral_v1",
            ),
            (
                COUNTERFACTUAL_PROFILE,
                "interannual_fourier_eof_precip_counterfactual_v1",
            ),
        ];
        for (profile, model) in pairs {
            assert!(validate_model_profile_pair(model, profile).is_ok());
            assert!(validate_model_profile_pair("wrong", profile).is_err());
        }
        assert!(validate_model_profile_pair("wrong", "unknown").is_err());
    }

    #[test]
    fn year_coverage_consumes_a_complete_prefix_of_the_128_year_plan() {
        let mut rows = Vec::new();
        for year in 1..=30 {
            for month in 1..=12 {
                rows.push(climate_row(year, month));
            }
        }
        let mut candidate = plan();
        assert_eq!(validate_year_coverage(&candidate, &rows).unwrap(), 30);
        candidate.annual_states[90].simulation_year += 1;
        assert!(validate_year_coverage(&candidate, &rows).is_err());
    }

    #[test]
    fn strict_json_rejects_unknown_fields_and_accepts_hex_rng_string() {
        let valid = format!(
            r#"{{"plan_schema_version":1,"station_id":"id106388","station_model":"interannual_fourier_eof_precip_counterfactual_v1","candidate_profile":"{COUNTERFACTUAL_PROFILE}","extension_seed":"0x0c8862ed55f21e2e","coefficient_payload_sha256":"{}","state_table_sha256":"{}","normalization":{{"fixed_years":128,"precipitation_clip_count":0,"temperature_centered":true}},"annual_states":[],"counterfactual":{{"second_order_prob":{},"amount_rank_rho":{},"rng_state":"0xffffffffffffffff"}}}}"#,
            "0".repeat(64),
            "1".repeat(64),
            serde_json::to_string(&[[0.5; 4]; 12]).unwrap(),
            serde_json::to_string(&[0.0; 12]).unwrap()
        );
        let parsed: OverlayPlan = serde_json::from_str(&valid).unwrap();
        assert_eq!(parsed.counterfactual.unwrap().rng_state, u64::MAX);
        let with_unknown = valid.replacen(
            "\"plan_schema_version\":1",
            "\"plan_schema_version\":1,\"unknown\":0",
            1,
        );
        assert!(serde_json::from_str::<OverlayPlan>(&with_unknown).is_err());
    }

    #[test]
    fn header_rewrite_binds_profile_and_extension_seed() {
        let candidate = plan();
        let header =
            format!("one\ntwo\nthree\nfour\nprefix {BASE_COMMAND_ECHO_SUFFIX}\n{DAILY_HEADER}");
        let rewritten = rewrite_header(&header, &candidate, header.len()).unwrap();
        assert!(rewritten.contains(&candidate_command_echo_suffix(&candidate)));
        assert!(!rewritten.contains(BASE_COMMAND_ECHO_SUFFIX));
        assert!(rewrite_header(
            &header.replace("--a5b-base", "--not-a5b-base"),
            &candidate,
            header.len()
        )
        .is_err());
    }

    #[test]
    fn annual_overlay_changes_only_declared_fields_and_repairs_temperatures() {
        let mut candidate = plan();
        candidate.annual_states[0].precip_factor[0] = 2.0;
        candidate.annual_states[0].tmax_delta_c[0] = -10.0;
        candidate.annual_states[0].tmin_delta_c[0] = 2.0;
        let mut rows = vec![row(1, 3.0)];
        rows[0].tdp = 4.5;
        let original_xmav = rows[0].xmav;
        let counts = apply_overlay(&mut rows, &candidate).unwrap();
        assert_eq!(rows[0].xr, 6.0);
        assert_eq!(rows[0].xmav.to_bits(), original_xmav.to_bits());
        assert_eq!(rows[0].tmxg, 3.55);
        assert_eq!(rows[0].tmng, 3.45);
        assert_eq!(rows[0].tdp, rows[0].tmng);
        assert_eq!(counts.temperature_order_repairs, 1);
        assert_eq!(counts.dewpoint_caps, 1);
    }

    #[test]
    fn monthly_effective_factor_prevents_f5_1_precipitation_overflow() {
        let mut candidate = plan();
        candidate.annual_states[0].precip_factor[0] = 20.0;
        let mut rows = vec![row(1, 100.0), row(2, 50.0)];
        let counts = apply_overlay(&mut rows, &candidate).unwrap();
        assert!(rows[0].xr <= MAX_RENDERABLE_PRECIP_MM);
        assert_eq!(rows[1].xr.to_bits(), (rows[0].xr * 0.5).to_bits());
        assert_eq!(counts.precipitation_render_limit_adjustments, 1);
        assert_eq!(counts.precipitation_factor_adjustments.len(), 12);
        let january = &counts.precipitation_factor_adjustments[0];
        assert_eq!(january.requested_factor, 20.0);
        assert_eq!(january.base_max_precip_mm, 100.0);
        assert!(january.effective_factor < january.requested_factor);
        assert!(january.adjusted);
        assert!(counts.precipitation_factor_adjustments[1..]
            .iter()
            .all(|record| !record.adjusted));
    }

    #[test]
    fn fixed_width_render_rejects_temperature_and_dewpoint_overflow() {
        let candidate = plan();
        let base =
            format!("one\ntwo\nthree\nfour\nprefix {BASE_COMMAND_ECHO_SUFFIX}\n{DAILY_HEADER}");
        for field in ["tmax", "tmin", "tdew"] {
            let mut generated = row(1, 1.0);
            match field {
                "tmax" => generated.tmxg = -100.0,
                "tmin" => generated.tmng = -100.0,
                "tdew" => generated.tdp = -100.0,
                _ => unreachable!(),
            }
            let error = render_cli(&base, &[generated], &candidate).unwrap_err();
            assert!(error.contains("daily-row formatting overflow"));
        }
    }

    #[test]
    fn counterfactual_is_deterministic_and_preserves_wet_tuple_multiset() {
        let original = vec![
            row(1, 1.0),
            row(2, 0.0),
            row(3, 4.0),
            row(4, 0.0),
            row(5, 2.0),
            row(6, 0.0),
            row(7, 7.0),
            row(8, 0.0),
        ];
        let before = original.iter().map(storm_tuple).collect::<Vec<_>>();
        let mut first = original.clone();
        let mut second = original;
        let probabilities = [0.85, 0.75, 0.25, 0.15];
        let mut first_rng = SplitMix64::new(123_456);
        let mut second_rng = SplitMix64::new(123_456);
        relocate_month(&mut first, &probabilities, 0.6, &mut first_rng).unwrap();
        relocate_month(&mut second, &probabilities, 0.6, &mut second_rng).unwrap();
        assert_eq!(first, second);
        assert_eq!(first_rng.state, second_rng.state);
        assert_eq!(first.iter().filter(|row| row.xr > 0.0).count(), 4);
        let mut expected = before
            .into_iter()
            .filter(|tuple| tuple.xr > 0.0)
            .collect::<Vec<_>>();
        let mut actual = first
            .iter()
            .map(storm_tuple)
            .filter(|tuple| tuple.xr > 0.0)
            .collect::<Vec<_>>();
        sort_storm_tuples(&mut expected);
        sort_storm_tuples(&mut actual);
        assert!(expected
            .iter()
            .zip(actual)
            .all(|(left, right)| storm_tuple_bits_equal(*left, right)));
        assert!(first.iter().filter(|row| row.xr == 0.0).all(|row| {
            row.dur.to_bits() == 0 && row.tpr.to_bits() == 0 && row.xmav.to_bits() == 0
        }));
    }

    #[test]
    fn fixed_count_selector_preserves_extreme_counts() {
        let mut rng = SplitMix64::new(0);
        assert!(select_wet_positions(31, 0, &[0.5; 4], &mut rng).is_empty());
        assert_eq!(
            select_wet_positions(31, 31, &[0.5; 4], &mut rng),
            (0..31).collect::<Vec<_>>()
        );
        assert_eq!(
            select_wet_positions(31, 11, &[0.0, 1.0, 0.0, 1.0], &mut rng).len(),
            11
        );
    }

    #[test]
    fn executable_runs_end_to_end_and_refuses_overwrite() {
        let nonce = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let root =
            std::env::temp_dir().join(format!("cligen-a5b-overlay-{}-{nonce}", std::process::id()));
        fs::create_dir(&root).unwrap();
        let station = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../../fixtures/new-meadows-id/id106388.par")
            .canonicalize()
            .unwrap();
        let runspec = root.join("run.yaml");
        let plan_path = root.join("plan.json");
        let output = root.join("candidate.cli");
        let diagnostics = root.join("candidate.diagnostics.json");
        let candidate = plan();
        let runspec_text = format!(
            "cligen_runspec: 1\nstation:\n  par: {}\nmode: continuous\nsimulation:\n  begin_year: 1\n  years: 1\ngeneration_profile: faithful_5_32_3\nqc_filter: off\noutput:\n  cli: {}\n  command_echo: {}\n",
            serde_json::to_string(station.to_str().unwrap()).unwrap(),
            serde_json::to_string(root.join("unused.cli").to_str().unwrap()).unwrap(),
            serde_json::to_string("--a5b-base faithful_5_32_3").unwrap()
        );
        fs::write(&runspec, runspec_text).unwrap();
        let ones = vec![1.0; 12];
        let zeros = vec![0.0; 12];
        let states = (1..=128)
            .map(|year| {
                serde_json::json!({
                    "simulation_year": year,
                    "precip_factor": ones,
                    "tmax_delta_c": zeros,
                    "tmin_delta_c": zeros
                })
            })
            .collect::<Vec<_>>();
        let plan_document = serde_json::json!({
            "plan_schema_version": 1,
            "station_id": candidate.station_id,
            "station_model": candidate.station_model,
            "candidate_profile": candidate.candidate_profile,
            "extension_seed": candidate.extension_seed,
            "coefficient_payload_sha256": candidate.coefficient_payload_sha256,
            "state_table_sha256": candidate.state_table_sha256,
            "normalization": {
                "fixed_years": 128,
                "precipitation_clip_count": 0,
                "temperature_centered": true
            },
            "annual_states": states
        });
        fs::write(
            &plan_path,
            serde_json::to_vec_pretty(&plan_document).unwrap(),
        )
        .unwrap();
        let args = Args {
            input: runspec,
            plan: plan_path,
            output: output.clone(),
            diagnostics: diagnostics.clone(),
        };
        run(args).unwrap();
        let output_text = fs::read_to_string(&output).unwrap();
        assert!(output_text.contains(DAILY_HEADER));
        assert!(output_text.contains(&candidate_command_echo_suffix(&candidate)));
        assert!(!output_text.contains(BASE_COMMAND_ECHO_SUFFIX));
        assert!(!output_text.contains('*'));
        let report: serde_json::Value =
            serde_json::from_slice(&fs::read(&diagnostics).unwrap()).unwrap();
        assert_eq!(report["consumed_prefix_years"], 1);
        assert_eq!(report["row_count"], 365);
        let second = Args {
            input: root.join("run.yaml"),
            plan: root.join("plan.json"),
            output,
            diagnostics,
        };
        assert!(run(second).is_err());
        fs::remove_dir_all(root).unwrap();
    }
}
