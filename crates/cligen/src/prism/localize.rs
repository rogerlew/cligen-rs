//! Deterministic station selection and PRISM localization of six `.par` rows.
//!
//! Extension prior art: `wepppy` commit
//! `3ee74d02df445a30968ef92975e5e3e2f6084669`, reviewed and corrected in
//! A10M5R4R1 `artifacts/wepppy-sanity-review.md`. This module is not part of
//! the faithful source-authority port; it emits a localized input that the
//! unchanged faithful generator subsequently consumes.

use std::fs;
use std::path::{Path, PathBuf};

use serde::Serialize;

use crate::par::ParFile;
use crate::stations::query::{nearest, NearestQuery, NearestRow};
use crate::stations::Manifests;

use super::grid::NormalsReceipt;
use super::{PrismError, DEGENERATE_OCCURRENCE_REPAIR_PROFILE_ID, PROFILE_ID};

const DAYS: [f64; 12] = [
    31.0, 28.25, 31.0, 30.0, 31.0, 30.0, 31.0, 31.0, 30.0, 31.0, 30.0, 31.0,
];
const POOL_SIZE: usize = 10;

/// Auditable component values and ranks for one selector candidate.
#[derive(Debug, Clone, Serialize)]
pub struct CandidateReceipt {
    pub station_id: String,
    pub description: String,
    pub path: PathBuf,
    pub latitude: f64,
    pub longitude: f64,
    pub distance_km: f64,
    pub latitude_error: f64,
    pub ppt_error: f64,
    pub tmax_error: f64,
    pub tmin_error: f64,
    pub distance_rank: usize,
    pub latitude_rank: usize,
    pub ppt_rank: usize,
    pub tmax_rank: usize,
    pub tmin_rank: usize,
    pub score: f64,
}

/// Station-selection decision, including the complete ten-station pool.
#[derive(Debug, Clone, Serialize)]
pub struct SelectionReceipt {
    pub schema_version: u32,
    pub profile_id: String,
    pub selection_method_id: String,
    pub collection_name: String,
    pub collection_version: String,
    pub collection_archive_sha256: String,
    pub selected_station_id: String,
    pub selected_source_par_path: PathBuf,
    pub selected_source_par_sha256: String,
    pub cligen_binary_sha256: String,
    pub candidates: Vec<CandidateReceipt>,
}

/// Requested, calculated, and encoded monthly localization state.
#[derive(Debug, Clone, Serialize)]
pub struct LocalizationReceipt {
    pub schema_version: u32,
    pub profile_id: String,
    pub source_station_id: String,
    pub source_par_sha256: String,
    pub localized_par_sha256: String,
    pub requested_ppt_in: [f64; 12],
    pub requested_tmax_f: [f64; 12],
    pub requested_tmin_f: [f64; 12],
    pub precipitation_ratio: [f64; 12],
    pub encoded_mean_wet_day_in: [f32; 12],
    pub encoded_pww: [f32; 12],
    pub encoded_pwd: [f32; 12],
    pub encoded_tmax_f: [f32; 12],
    pub encoded_tmin_f: [f32; 12],
    pub encoded_intensity_in_per_hour: [f32; 12],
}

/// Revision-2 localization receipt for the explicit repair profile.
#[derive(Debug, Clone, Serialize)]
pub struct LocalizationReceiptV2 {
    pub schema_version: u32,
    pub profile_id: String,
    pub source_station_id: String,
    pub source_par_sha256: String,
    pub localized_par_sha256: String,
    pub requested_ppt_in: [f64; 12],
    pub requested_tmax_f: [f64; 12],
    pub requested_tmin_f: [f64; 12],
    pub precipitation_ratio: [Option<f64>; 12],
    pub encoded_mean_wet_day_in: [f32; 12],
    pub encoded_pww: [f32; 12],
    pub encoded_pwd: [f32; 12],
    pub encoded_tmax_f: [f32; 12],
    pub encoded_tmin_f: [f32; 12],
    pub encoded_intensity_in_per_hour: [f32; 12],
    pub degenerate_occurrence_repair_method_id: String,
    pub occurrence_repairs: Vec<OccurrenceRepairReceipt>,
}

/// Explicit repair choices. Disabled preserves the revision-1 behavior.
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub enum DegenerateOccurrenceRepair {
    #[default]
    Disabled,
    IndependentPrismV1,
}

impl DegenerateOccurrenceRepair {
    /// Stable method identifier written to receipts and warnings.
    #[must_use]
    pub const fn method_id(self) -> Option<&'static str> {
        match self {
            Self::Disabled => None,
            Self::IndependentPrismV1 => Some("degenerate_occurrence_independent_prism_v1"),
        }
    }

    #[must_use]
    const fn profile_id(self) -> &'static str {
        match self {
            Self::Disabled => PROFILE_ID,
            Self::IndependentPrismV1 => DEGENERATE_OCCURRENCE_REPAIR_PROFILE_ID,
        }
    }
}

/// Complete structured warning for one repaired month.
#[derive(Debug, Clone, Serialize)]
pub struct OccurrenceRepairReceipt {
    pub method_id: String,
    pub month: usize,
    pub original_pww: f32,
    pub original_pwd: f32,
    pub source_mean_wet_day_in: f32,
    pub prism_target_ppt_in: f64,
    pub precipitation_ratio_undefined_reason: String,
    pub continuous_limit_wet_day_count: f64,
    pub continuous_limit_wet_fraction: f64,
    pub derived_wet_day_count: f64,
    pub derived_wet_fraction: f64,
    pub persistence_assumption: String,
    pub encoded_mean_wet_day_in: f32,
    pub encoded_pww: f32,
    pub encoded_pwd: f32,
    pub encoded_intensity_in_per_hour: f32,
}

impl OccurrenceRepairReceipt {
    /// Human warning emitted by the CLI after atomic publication.
    #[must_use]
    pub fn warning(&self) -> String {
        format!(
            "applied {} to month {}: source PWW=0 PWD=0, PRISM ppt={:.8} in, encoded PWW=PWD={:.2}",
            self.method_id, self.month, self.prism_target_ppt_in, self.encoded_pww
        )
    }
}

/// Complete local preprocessing result ready for artifact publication.
#[derive(Debug)]
pub struct LocalizedPar {
    pub source_path: PathBuf,
    pub source_bytes: Vec<u8>,
    pub localized_bytes: Vec<u8>,
    pub selection: SelectionReceipt,
    pub localization: LocalizationReceipt,
}

/// Complete preprocessing result for the revision-2 repair profile.
#[derive(Debug)]
pub struct LocalizedParV2 {
    pub source_path: PathBuf,
    pub source_bytes: Vec<u8>,
    pub localized_bytes: Vec<u8>,
    pub selection: SelectionReceipt,
    pub localization: LocalizationReceiptV2,
}

#[derive(Debug)]
struct Candidate {
    row: NearestRow,
    ppt_error: f64,
    tmax_error: f64,
    tmin_error: f64,
    latitude_error: f64,
    ranks: [usize; 5],
}

#[derive(Debug, Clone, Copy)]
struct RepairEvent {
    month: usize,
    source_mean: f32,
    target: f64,
    continuous_count: f64,
    continuous_wet_fraction: f64,
    count: f64,
    wet_fraction: f64,
}

#[derive(Debug)]
struct RewriteResult {
    bytes: Vec<u8>,
    ratios: [Option<f64>; 12],
    repairs: Vec<RepairEvent>,
}

/// Select a station and localize its monthly precipitation/temperature rows.
pub fn localize(cache_root: &Path, normals: &NormalsReceipt) -> Result<LocalizedPar, PrismError> {
    let executable_path = std::env::current_exe()
        .map_err(|source| super::io_error("resolve current executable", source))?;
    let cligen_binary_sha256 = super::sha256_file(&executable_path)?;
    localize_with_binary_identity(cache_root, normals, &cligen_binary_sha256)
}

/// Select and localize with an explicitly declared degenerate-month policy.
pub fn localize_with_repair(
    cache_root: &Path,
    normals: &NormalsReceipt,
    repair: DegenerateOccurrenceRepair,
) -> Result<LocalizedParV2, PrismError> {
    if repair == DegenerateOccurrenceRepair::Disabled {
        return Err(PrismError::InvalidRequest(
            "localize_with_repair requires an explicit repair method".to_owned(),
        ));
    }
    let executable_path = std::env::current_exe()
        .map_err(|source| super::io_error("resolve current executable", source))?;
    let cligen_binary_sha256 = super::sha256_file(&executable_path)?;
    localize_v2_with_binary_identity(cache_root, normals, &cligen_binary_sha256, repair)
}

fn localize_with_binary_identity(
    cache_root: &Path,
    normals: &NormalsReceipt,
    cligen_binary_sha256: &str,
) -> Result<LocalizedPar, PrismError> {
    validate_binary_identity(cligen_binary_sha256)?;
    let (selected, selection) =
        select_station(cache_root, normals, cligen_binary_sha256, PROFILE_ID)?;
    localize_selected(selected, selection, normals)
}

fn localize_v2_with_binary_identity(
    cache_root: &Path,
    normals: &NormalsReceipt,
    cligen_binary_sha256: &str,
    repair: DegenerateOccurrenceRepair,
) -> Result<LocalizedParV2, PrismError> {
    validate_binary_identity(cligen_binary_sha256)?;
    let (selected, selection) = select_station(
        cache_root,
        normals,
        cligen_binary_sha256,
        repair.profile_id(),
    )?;
    localize_selected_v2(selected, selection, normals, repair)
}

fn validate_binary_identity(cligen_binary_sha256: &str) -> Result<(), PrismError> {
    if cligen_binary_sha256.len() != 64
        || !cligen_binary_sha256
            .bytes()
            .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase())
    {
        return Err(PrismError::InvalidRequest(
            "cligen binary SHA-256 must be 64 lowercase hex characters".to_owned(),
        ));
    }
    Ok(())
}

fn localize_selected(
    selected: NearestRow,
    selection: SelectionReceipt,
    normals: &NormalsReceipt,
) -> Result<LocalizedPar, PrismError> {
    let (source_bytes, rewritten, encoded) = prepare_selected(
        &selected,
        &selection,
        normals,
        DegenerateOccurrenceRepair::Disabled,
    )?;
    Ok(build_localized_result(
        selected,
        selection,
        source_bytes,
        rewritten.bytes,
        &encoded,
        normals,
        rewritten.ratios.map(|ratio| ratio.expect("ordinary ratio")),
    ))
}

fn localize_selected_v2(
    selected: NearestRow,
    selection: SelectionReceipt,
    normals: &NormalsReceipt,
    repair: DegenerateOccurrenceRepair,
) -> Result<LocalizedParV2, PrismError> {
    let (source_bytes, rewritten, encoded) =
        prepare_selected(&selected, &selection, normals, repair)?;
    Ok(build_localized_result_v2(
        selected,
        selection,
        source_bytes,
        rewritten.bytes,
        &encoded,
        normals,
        rewritten.ratios,
        repair,
        rewritten.repairs,
    ))
}

fn prepare_selected(
    selected: &NearestRow,
    selection: &SelectionReceipt,
    normals: &NormalsReceipt,
    repair: DegenerateOccurrenceRepair,
) -> Result<(Vec<u8>, RewriteResult, ParFile), PrismError> {
    let source_bytes = fs::read(&selected.path)
        .map_err(|source| super::io_error("read selected station .par", source))?;
    if crate::quality::sha256_hex(&source_bytes) != selection.selected_source_par_sha256 {
        return Err(PrismError::InvalidStation(
            "selected source .par changed after selection".to_owned(),
        ));
    }
    let source = ParFile::parse(&source_bytes)
        .map_err(|error| PrismError::InvalidStation(error.to_string()))?;
    let rewritten = rewrite(&source_bytes, &source, normals, repair)?;
    let encoded =
        ParFile::parse(&rewritten.bytes).map_err(|error| PrismError::Render(error.to_string()))?;
    validate_encoded(&encoded, normals)?;
    Ok((source_bytes, rewritten, encoded))
}

#[allow(clippy::too_many_arguments)]
fn build_localized_result(
    selected: NearestRow,
    selection: SelectionReceipt,
    source_bytes: Vec<u8>,
    localized_bytes: Vec<u8>,
    encoded: &ParFile,
    normals: &NormalsReceipt,
    ratios: [f64; 12],
) -> LocalizedPar {
    let model = encoded.fixed_monthly();
    let localization = LocalizationReceipt {
        schema_version: 1,
        profile_id: PROFILE_ID.to_owned(),
        source_station_id: selected.id,
        source_par_sha256: crate::quality::sha256_hex(&source_bytes),
        localized_par_sha256: crate::quality::sha256_hex(&localized_bytes),
        requested_ppt_in: normals.monthly_ppt_in(),
        requested_tmax_f: normals.monthly_tmax_f(),
        requested_tmin_f: normals.monthly_tmin_f(),
        precipitation_ratio: ratios,
        encoded_mean_wet_day_in: std::array::from_fn(|month| model.rst[month][0]),
        encoded_pww: std::array::from_fn(|month| model.prw[month][0]),
        encoded_pwd: std::array::from_fn(|month| model.prw[month][1]),
        encoded_tmax_f: model.obmx,
        encoded_tmin_f: model.obmn,
        encoded_intensity_in_per_hour: model.wi_raw,
    };
    LocalizedPar {
        source_path: selected.path,
        source_bytes,
        localized_bytes,
        selection,
        localization,
    }
}

#[allow(clippy::too_many_arguments)]
fn build_localized_result_v2(
    selected: NearestRow,
    selection: SelectionReceipt,
    source_bytes: Vec<u8>,
    localized_bytes: Vec<u8>,
    encoded: &ParFile,
    normals: &NormalsReceipt,
    ratios: [Option<f64>; 12],
    repair: DegenerateOccurrenceRepair,
    repairs: Vec<RepairEvent>,
) -> LocalizedParV2 {
    let model = encoded.fixed_monthly();
    let occurrence_repairs = repairs
        .into_iter()
        .map(|event| OccurrenceRepairReceipt {
            method_id: repair
                .method_id()
                .expect("repair event has method")
                .to_owned(),
            month: event.month + 1,
            original_pww: 0.0,
            original_pwd: 0.0,
            source_mean_wet_day_in: event.source_mean,
            prism_target_ppt_in: event.target,
            precipitation_ratio_undefined_reason: "source_expected_monthly_precipitation_is_zero"
                .to_owned(),
            continuous_limit_wet_day_count: event.continuous_count,
            continuous_limit_wet_fraction: event.continuous_wet_fraction,
            derived_wet_day_count: event.count,
            derived_wet_fraction: event.wet_fraction,
            persistence_assumption: "independent_days_pww_equals_pwd_equals_q".to_owned(),
            encoded_mean_wet_day_in: model.rst[event.month][0],
            encoded_pww: model.prw[event.month][0],
            encoded_pwd: model.prw[event.month][1],
            encoded_intensity_in_per_hour: model.wi_raw[event.month],
        })
        .collect();
    let localization = LocalizationReceiptV2 {
        schema_version: 2,
        profile_id: repair.profile_id().to_owned(),
        source_station_id: selected.id,
        source_par_sha256: crate::quality::sha256_hex(&source_bytes),
        localized_par_sha256: crate::quality::sha256_hex(&localized_bytes),
        requested_ppt_in: normals.monthly_ppt_in(),
        requested_tmax_f: normals.monthly_tmax_f(),
        requested_tmin_f: normals.monthly_tmin_f(),
        precipitation_ratio: ratios,
        encoded_mean_wet_day_in: std::array::from_fn(|month| model.rst[month][0]),
        encoded_pww: std::array::from_fn(|month| model.prw[month][0]),
        encoded_pwd: std::array::from_fn(|month| model.prw[month][1]),
        encoded_tmax_f: model.obmx,
        encoded_tmin_f: model.obmn,
        encoded_intensity_in_per_hour: model.wi_raw,
        degenerate_occurrence_repair_method_id: repair
            .method_id()
            .expect("v2 result has repair method")
            .to_owned(),
        occurrence_repairs,
    };
    LocalizedParV2 {
        source_path: selected.path,
        source_bytes,
        localized_bytes,
        selection,
        localization,
    }
}

fn select_station(
    cache_root: &Path,
    normals: &NormalsReceipt,
    cligen_binary_sha256: &str,
    profile_id: &str,
) -> Result<(NearestRow, SelectionReceipt), PrismError> {
    let (collection, rows) = load_pool(cache_root, normals)?;
    let mut candidates = load_candidates(rows, normals)?;
    assign_ranks(&mut candidates);
    let receipts: Vec<CandidateReceipt> = candidates.iter().map(candidate_receipt).collect();
    let winner = winning_candidate(&candidates);
    let receipt = build_selection_receipt(
        &collection,
        &winner,
        receipts,
        cligen_binary_sha256,
        profile_id,
    )?;
    Ok((winner, receipt))
}

fn load_pool(
    cache_root: &Path,
    normals: &NormalsReceipt,
) -> Result<(crate::stations::Collection, Vec<NearestRow>), PrismError> {
    let manifests = Manifests::embedded();
    let collection = manifests
        .get("us-2015")
        .map_err(|error| PrismError::InvalidStation(error.to_string()))?
        .clone();
    let rows = nearest(
        &manifests,
        cache_root,
        &NearestQuery {
            latitude: normals.requested_latitude,
            longitude: normals.requested_longitude,
            count: POOL_SIZE,
            collection: Some("us-2015".to_owned()),
            min_years: None,
        },
    )
    .map_err(|error| PrismError::InvalidStation(error.to_string()))?;
    require_complete_pool(&rows)?;
    Ok((collection, rows))
}

fn require_complete_pool(rows: &[NearestRow]) -> Result<(), PrismError> {
    if rows.len() == POOL_SIZE {
        return Ok(());
    }
    Err(PrismError::InvalidStation(format!(
        "selector requires {POOL_SIZE} candidates, found {}",
        rows.len()
    )))
}

fn build_selection_receipt(
    collection: &crate::stations::Collection,
    winner: &NearestRow,
    candidates: Vec<CandidateReceipt>,
    cligen_binary_sha256: &str,
    profile_id: &str,
) -> Result<SelectionReceipt, PrismError> {
    let source_bytes = fs::read(&winner.path)
        .map_err(|source| super::io_error("hash selected station .par", source))?;
    Ok(SelectionReceipt {
        schema_version: 2,
        profile_id: profile_id.to_owned(),
        selection_method_id: "cligen_prism_rank_sum_v1".to_owned(),
        collection_name: collection.name.clone(),
        collection_version: collection.version.clone(),
        collection_archive_sha256: collection.archive.sha256.clone(),
        selected_station_id: winner.id.clone(),
        selected_source_par_path: winner.path.clone(),
        selected_source_par_sha256: crate::quality::sha256_hex(&source_bytes),
        cligen_binary_sha256: cligen_binary_sha256.to_owned(),
        candidates,
    })
}

fn load_candidates(
    rows: Vec<NearestRow>,
    normals: &NormalsReceipt,
) -> Result<Vec<Candidate>, PrismError> {
    let target_ppt = normals.monthly_ppt_in();
    let target_tmax = normals.monthly_tmax_f();
    let target_tmin = normals.monthly_tmin_f();
    rows.into_iter()
        .map(|row| {
            let bytes = fs::read(&row.path)
                .map_err(|source| super::io_error("read candidate station .par", source))?;
            let par = ParFile::parse(&bytes)
                .map_err(|error| PrismError::InvalidStation(error.to_string()))?;
            let model = par.fixed_monthly();
            let ppt = station_ppt(model)?;
            Ok(Candidate {
                latitude_error: (row.latitude - normals.requested_latitude).abs(),
                ppt_error: euclidean(&ppt, &target_ppt),
                tmax_error: euclidean_f32(&model.obmx, &target_tmax),
                tmin_error: euclidean_f32(&model.obmn, &target_tmin),
                row,
                ranks: [0; 5],
            })
        })
        .collect()
}

fn winning_candidate(candidates: &[Candidate]) -> NearestRow {
    candidates
        .iter()
        .min_by(|left, right| {
            score(left)
                .total_cmp(&score(right))
                .then_with(|| left.row.distance_km.total_cmp(&right.row.distance_km))
                .then_with(|| left.row.id.cmp(&right.row.id))
        })
        .expect("ten candidates")
        .row
        .clone()
}

fn station_ppt(model: &crate::station::FixedMonthly5323) -> Result<[f64; 12], PrismError> {
    let mut totals = [0.0; 12];
    for month in 0..12 {
        let pww = f64::from(model.prw[month][0]);
        let pwd = f64::from(model.prw[month][1]);
        let denominator = 1.0 - pww + pwd;
        if denominator <= 0.0 {
            return Err(PrismError::InvalidStation(format!(
                "month {} has invalid occurrence denominator",
                month + 1
            )));
        }
        totals[month] = f64::from(model.rst[month][0]) * DAYS[month] * pwd / denominator;
    }
    Ok(totals)
}

fn euclidean(left: &[f64; 12], right: &[f64; 12]) -> f64 {
    left.iter()
        .zip(right)
        .map(|(a, b)| (a - b) * (a - b))
        .sum::<f64>()
        .sqrt()
}

fn euclidean_f32(left: &[f32; 12], right: &[f64; 12]) -> f64 {
    let converted = left.map(f64::from);
    euclidean(&converted, right)
}

fn assign_ranks(candidates: &mut [Candidate]) {
    for component in 0..5 {
        let mut order: Vec<usize> = (0..candidates.len()).collect();
        order.sort_by(|&left, &right| {
            component_value(&candidates[left], component)
                .total_cmp(&component_value(&candidates[right], component))
                .then_with(|| candidates[left].row.id.cmp(&candidates[right].row.id))
        });
        for (rank, index) in order.into_iter().enumerate() {
            candidates[index].ranks[component] = rank;
        }
    }
}

fn component_value(candidate: &Candidate, component: usize) -> f64 {
    [
        candidate.row.distance_km,
        candidate.latitude_error,
        candidate.ppt_error,
        candidate.tmax_error,
        candidate.tmin_error,
    ][component]
}

fn score(candidate: &Candidate) -> f64 {
    let ranks = candidate.ranks;
    ranks[0] as f64
        + ranks[1] as f64
        + 3.0 * ranks[2] as f64
        + 1.5 * ranks[3] as f64
        + 1.5 * ranks[4] as f64
}

fn candidate_receipt(candidate: &Candidate) -> CandidateReceipt {
    CandidateReceipt {
        station_id: candidate.row.id.clone(),
        description: candidate.row.desc.clone(),
        path: candidate.row.path.clone(),
        latitude: candidate.row.latitude,
        longitude: candidate.row.longitude,
        distance_km: candidate.row.distance_km,
        latitude_error: candidate.latitude_error,
        ppt_error: candidate.ppt_error,
        tmax_error: candidate.tmax_error,
        tmin_error: candidate.tmin_error,
        distance_rank: candidate.ranks[0],
        latitude_rank: candidate.ranks[1],
        ppt_rank: candidate.ranks[2],
        tmax_rank: candidate.ranks[3],
        tmin_rank: candidate.ranks[4],
        score: score(candidate),
    }
}

fn rewrite(
    bytes: &[u8],
    par: &ParFile,
    normals: &NormalsReceipt,
    repair: DegenerateOccurrenceRepair,
) -> Result<RewriteResult, PrismError> {
    let mut rows: Vec<String> = std::str::from_utf8(bytes)
        .map_err(|_| PrismError::Render("source .par is not UTF-8".to_owned()))?
        .lines()
        .map(str::to_owned)
        .collect();
    let trailing = bytes.ends_with(b"\n");
    let target_ppt = normals.monthly_ppt_in();
    let target_tmax = normals.monthly_tmax_f();
    let target_tmin = normals.monthly_tmin_f();
    let mut mean = [0.0; 12];
    let mut pww = [0.0; 12];
    let mut pwd = [0.0; 12];
    let mut intensity = [0.0; 12];
    let mut ratio = [None; 12];
    let mut repairs = Vec::new();
    for month in 0..12 {
        let localized = localize_month_with_repair(par, month, target_ppt[month], repair)?;
        let values = localized.values;
        mean[month] = values[0];
        pww[month] = values[1];
        pwd[month] = values[2];
        intensity[month] = values[3];
        ratio[month] = localized.repair.is_none().then_some(values[4]);
        if let Some(event) = localized.repair {
            repairs.push(event);
        }
    }
    for (record, values) in [
        (4, mean),
        (7, pww),
        (8, pwd),
        (9, target_tmax),
        (10, target_tmin),
        (15, intensity),
    ] {
        rows[record - 1] = render_monthly(&rows[record - 1], &values)?;
    }
    let mut output = rows.join("\n").into_bytes();
    if trailing {
        output.push(b'\n');
    }
    Ok(RewriteResult {
        bytes: output,
        ratios: ratio,
        repairs,
    })
}

#[cfg(test)]
fn localize_month(par: &ParFile, month: usize, target: f64) -> Result<[f64; 5], PrismError> {
    Ok(
        localize_month_with_repair(par, month, target, DegenerateOccurrenceRepair::Disabled)?
            .values,
    )
}

struct LocalizedMonth {
    values: [f64; 5],
    repair: Option<RepairEvent>,
}

fn localize_month_with_repair(
    par: &ParFile,
    month: usize,
    target: f64,
    repair: DegenerateOccurrenceRepair,
) -> Result<LocalizedMonth, PrismError> {
    let model = par.fixed_monthly();
    let mean = f64::from(model.rst[month][0]);
    let old_pww = f64::from(model.prw[month][0]);
    let old_pwd = f64::from(model.prw[month][1]);
    if repair == DegenerateOccurrenceRepair::IndependentPrismV1
        && old_pww == 0.0
        && old_pwd == 0.0
        && target.is_finite()
        && target > 0.0
        && mean.is_finite()
        && mean > 0.0
    {
        return repair_independent_month(model, month, target, mean);
    }
    let denominator = 1.0 - old_pww + old_pwd;
    let q = old_pwd / denominator;
    let current = DAYS[month] * q * mean;
    if !current.is_finite() || current <= 0.0 || !q.is_finite() || !(0.0..1.0).contains(&q) {
        return Err(PrismError::InvalidStation(format!(
            "month {} cannot be localized",
            month + 1
        )));
    }
    let delta = target / current;
    let active = target >= 0.05 && current >= 0.05;
    let old_count = DAYS[month] * q;
    let count = if active {
        (old_count * (1.0 + delta) / 2.0)
            .clamp(old_count / 2.0, old_count * 2.0)
            .clamp(0.1, DAYS[month] - 0.25)
    } else {
        old_count
    };
    let new_q = count / DAYS[month];
    let persistence = old_pwd / old_pww;
    let new_pww = 1.0 / (1.0 - persistence + persistence / new_q);
    let new_pwd = ((new_pww - 1.0) * new_q) / (new_q - 1.0);
    let new_mean = target / (DAYS[month] * new_q);
    let new_intensity =
        f64::from(model.wi_raw[month]) * if active { delta.clamp(0.5, 2.0) } else { 1.0 };
    let result = [new_mean, new_pww, new_pwd, new_intensity, delta];
    if result.iter().all(|value| value.is_finite())
        && new_mean >= 0.0
        && (0.0..1.0).contains(&new_pww)
        && (0.0..1.0).contains(&new_pwd)
    {
        Ok(LocalizedMonth {
            values: result,
            repair: None,
        })
    } else {
        Err(PrismError::InvalidStation(format!(
            "month {} produced invalid localized values",
            month + 1
        )))
    }
}

fn repair_independent_month(
    model: &crate::station::FixedMonthly5323,
    month: usize,
    target: f64,
    source_mean: f64,
) -> Result<LocalizedMonth, PrismError> {
    let continuous_count = (target / (2.0 * source_mean)).clamp(0.1, DAYS[month] - 0.25);
    let continuous_wet_fraction = continuous_count / DAYS[month];
    let wet_fraction = f6_2_probability(continuous_wet_fraction);
    let count = DAYS[month] * wet_fraction;
    let new_mean = target / (DAYS[month] * wet_fraction);
    let new_intensity = f64::from(model.wi_raw[month]) * 2.0;
    let values = [new_mean, wet_fraction, wet_fraction, new_intensity, 0.0];
    if values.iter().all(|value| value.is_finite())
        && new_mean > 0.0
        && (0.0..1.0).contains(&wet_fraction)
    {
        Ok(LocalizedMonth {
            values,
            repair: Some(RepairEvent {
                month,
                source_mean: source_mean as f32,
                target,
                continuous_count,
                continuous_wet_fraction,
                count,
                wet_fraction,
            }),
        })
    } else {
        Err(PrismError::InvalidStation(format!(
            "month {} produced invalid independent occurrence repair",
            month + 1
        )))
    }
}

fn f6_2_probability(value: f64) -> f64 {
    format!("{value:.2}")
        .parse::<f64>()
        .expect("formatting a finite probability produces a number")
        .clamp(0.01, 0.99)
}

fn render_monthly(source: &str, values: &[f64; 12]) -> Result<String, PrismError> {
    if source.len() < 8 || !source.is_ascii() {
        return Err(PrismError::Render(
            "monthly row has no 8-byte label".to_owned(),
        ));
    }
    let mut output = source[..8].to_owned();
    for value in values {
        let mut rounded = format!("{value:.2}");
        if rounded == "-0.00" {
            rounded = "0.00".to_owned();
        }
        let suppressed = rounded
            .strip_prefix("0.")
            .map(|tail| format!(".{tail}"))
            .or_else(|| rounded.strip_prefix("-0.").map(|tail| format!("-.{tail}")))
            .unwrap_or(rounded);
        if suppressed.len() > 6 {
            return Err(PrismError::Render(format!(
                "value {value} does not fit F6.2"
            )));
        }
        output.push_str(&format!("{suppressed:>6}"));
    }
    Ok(output)
}

fn validate_encoded(par: &ParFile, normals: &NormalsReceipt) -> Result<(), PrismError> {
    let model = par.fixed_monthly();
    let ppt = normals.monthly_ppt_in();
    for (month, target) in ppt.iter().enumerate() {
        if *target > 0.0 && model.rst[month][0] <= 0.0 {
            return Err(PrismError::Render(format!(
                "positive precipitation is unrepresentable in month {}",
                month + 1
            )));
        }
        if !(0.0..1.0).contains(&model.prw[month][0])
            || !(0.0..1.0).contains(&model.prw[month][1])
            || model.obmx[month] < model.obmn[month]
        {
            return Err(PrismError::Render(format!(
                "encoded constraints fail in month {}",
                month + 1
            )));
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::{
        f6_2_probability, localize_month, localize_month_with_repair, localize_selected,
        localize_selected_v2, localize_with_binary_identity, render_monthly, rewrite, station_ppt,
        validate_encoded, DegenerateOccurrenceRepair, SelectionReceipt,
    };
    use crate::par::ParFile;
    use crate::prism::grid::NormalsReceipt;

    const PAR: &[u8] = include_bytes!("../../../../fixtures/new-meadows-id/id106388.par");

    fn normals(par: &ParFile) -> NormalsReceipt {
        let model = par.fixed_monthly();
        let ppt = station_ppt(model).unwrap();
        NormalsReceipt {
            schema_version: 1,
            bundle_id: "test".to_owned(),
            bundle_version: "test".to_owned(),
            grid_manifest_sha256: "0".repeat(64),
            source_manifest_sha256: "0".repeat(64),
            attribution: "test".to_owned(),
            requested_longitude: -116.0,
            requested_latitude: 45.0,
            row: 0,
            column: 0,
            cell_center_longitude: -116.0,
            cell_center_latitude: 45.0,
            monthly_ppt_mm: ppt.map(|value| (value * 1.2 * 25.4) as f32),
            monthly_tmax_c: model.obmx.map(|value| (value - 32.0) * 5.0 / 9.0),
            monthly_tmin_c: model.obmn.map(|value| (value - 32.0) * 5.0 / 9.0),
            monthly_ppt_in: ppt.map(|value| value * 1.2),
            monthly_tmax_f: model.obmx.map(f64::from),
            monthly_tmin_f: model.obmn.map(f64::from),
        }
    }

    fn par_with_month_six(pww: f64, pwd: f64, intensity: Option<f64>) -> Vec<u8> {
        let source = std::str::from_utf8(PAR).unwrap();
        let mut rows: Vec<String> = source.lines().map(str::to_owned).collect();
        for (record, month_six) in [(7, pww), (8, pwd)] {
            let mut values = [0.5; 12];
            values[5] = month_six;
            rows[record - 1] = render_monthly(&rows[record - 1], &values).unwrap();
        }
        if let Some(month_six) = intensity {
            let mut values = [0.5; 12];
            values[5] = month_six;
            rows[14] = render_monthly(&rows[14], &values).unwrap();
        }
        format!("{}\n", rows.join("\n")).into_bytes()
    }

    fn selection(path: std::path::PathBuf, bytes: &[u8], profile_id: &str) -> SelectionReceipt {
        SelectionReceipt {
            schema_version: 2,
            profile_id: profile_id.to_owned(),
            selection_method_id: "cligen_prism_rank_sum_v1".to_owned(),
            collection_name: "us-2015".to_owned(),
            collection_version: "2026.07".to_owned(),
            collection_archive_sha256: "0".repeat(64),
            selected_station_id: "test.par".to_owned(),
            selected_source_par_path: path,
            selected_source_par_sha256: crate::quality::sha256_hex(bytes),
            cligen_binary_sha256: "1".repeat(64),
            candidates: Vec::new(),
        }
    }

    #[test]
    fn canonical_monthly_row_suppresses_leading_zero() {
        let values = [
            0.26, -0.26, 12.34, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, -0.001,
        ];
        let row = render_monthly(" MEAN P anything", &values).unwrap();
        assert_eq!(&row[8..26], "   .26  -.26 12.34");
        assert!(row.ends_with("   .00"));
        assert_eq!(row.len(), 80);
    }

    #[test]
    fn probability_snap_uses_the_exact_f6_2_tie_rule() {
        assert_eq!(f6_2_probability(0.015), 0.01);
        assert_eq!(f6_2_probability(0.025), 0.03);
        assert_eq!(f6_2_probability(0.0001), 0.01);
    }

    #[test]
    fn localization_rewrites_only_registered_rows_and_reparses() {
        let par = ParFile::parse(PAR).unwrap();
        let targets = normals(&par);
        let rewritten = rewrite(PAR, &par, &targets, DegenerateOccurrenceRepair::Disabled).unwrap();
        assert!(rewritten
            .ratios
            .iter()
            .all(|ratio| ratio.is_some_and(|value| value > 1.0)));
        assert_eq!(
            crate::quality::sha256_hex(&rewritten.bytes),
            "abebcb6ad97979bee6fec2609729c6276a18117571119ed58a8c6b4fdae66120"
        );
        let localized = ParFile::parse(&rewritten.bytes).unwrap();
        validate_encoded(&localized, &targets).unwrap();
        for record in 1..=83 {
            if ![4, 7, 8, 9, 10, 15].contains(&record) {
                assert_eq!(
                    PAR.split(|byte| *byte == b'\n').nth(record - 1),
                    rewritten.bytes.split(|byte| *byte == b'\n').nth(record - 1)
                );
            }
        }
    }

    #[test]
    fn dry_threshold_preserves_occurrence_and_intensity() {
        let par = ParFile::parse(PAR).unwrap();
        let values = localize_month(&par, 0, 0.01).unwrap();
        assert_eq!(values[3], f64::from(par.fixed_monthly().wi_raw[0]));
        assert!(values[0] > 0.0);
    }

    #[test]
    fn selected_station_builds_complete_receipts() {
        let path = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../../fixtures/new-meadows-id/id106388.par");
        let par = ParFile::parse(PAR).unwrap();
        let result = localize_selected(
            crate::stations::query::NearestRow {
                collection: "us-2015".to_owned(),
                id: "id106388.par".to_owned(),
                desc: "test".to_owned(),
                latitude: 45.0,
                longitude: -116.0,
                years: 40.0,
                distance_km: 0.0,
                path: path.clone(),
            },
            SelectionReceipt {
                schema_version: 2,
                profile_id: "stochastic_prism_localized_par_v1".to_owned(),
                selection_method_id: "cligen_prism_rank_sum_v1".to_owned(),
                collection_name: "us-2015".to_owned(),
                collection_version: "2026.07".to_owned(),
                collection_archive_sha256: "0".repeat(64),
                selected_station_id: "id106388.par".to_owned(),
                selected_source_par_path: path,
                selected_source_par_sha256: crate::quality::sha256_hex(PAR),
                cligen_binary_sha256: "1".repeat(64),
                candidates: Vec::new(),
            },
            &normals(&par),
        )
        .unwrap();
        assert_eq!(result.localization.source_station_id, "id106388.par");
        assert_eq!(result.selection.schema_version, 2);
        assert_eq!(result.localization.schema_version, 1);
        let serialized = serde_json::to_value(&result.localization).unwrap();
        assert!(serialized
            .get("degenerate_occurrence_repair_method_id")
            .is_none());
        assert!(serialized.get("occurrence_repairs").is_none());
        assert_eq!(result.selection.selected_source_par_sha256.len(), 64);
        assert_eq!(result.selection.cligen_binary_sha256, "1".repeat(64));
    }

    #[test]
    fn selection_rejects_malformed_binary_identity_before_cache_access() {
        let par = ParFile::parse(PAR).unwrap();
        let error = localize_with_binary_identity(
            std::path::Path::new("missing"),
            &normals(&par),
            "not-a-hash",
        )
        .unwrap_err();
        assert!(error.to_string().contains("binary SHA-256"));
    }

    #[test]
    fn explicit_repair_revives_an_all_dry_month_from_prism() {
        let dry_bytes = par_with_month_six(0.0, 0.0, None);
        let dry = ParFile::parse(&dry_bytes).unwrap();
        let source_mean = f64::from(dry.fixed_monthly().rst[5][0]);
        let target = 0.126_385_83;

        assert!(localize_month(&dry, 5, target).is_err());
        let repaired = localize_month_with_repair(
            &dry,
            5,
            target,
            DegenerateOccurrenceRepair::IndependentPrismV1,
        )
        .unwrap();
        let continuous_count = target / (2.0 * source_mean);
        let continuous_q = continuous_count / 30.0;
        let expected_q = 0.01;
        assert_eq!(repaired.values[0], target / (30.0 * expected_q));
        assert_eq!(repaired.values[1], expected_q);
        assert_eq!(repaired.values[2], expected_q);
        let event = repaired.repair.unwrap();
        assert_eq!(event.continuous_count, continuous_count);
        assert_eq!(event.continuous_wet_fraction, continuous_q);
        assert_eq!(event.count, 0.3);
        assert_eq!(event.wet_fraction, expected_q);
    }

    #[test]
    fn v2_receipt_marks_ratio_undefined_and_reports_encoded_repair() {
        let dry_bytes = par_with_month_six(0.0, 0.0, None);
        let dry = ParFile::parse(&dry_bytes).unwrap();
        let mut targets = normals(&dry);
        targets.monthly_ppt_in[5] = 0.063_192_910_096_776_77;
        targets.monthly_ppt_mm[5] = (targets.monthly_ppt_in[5] * 25.4) as f32;
        let root = std::env::temp_dir().join(format!(
            "cligen-a12r1-v2-{}-{:?}",
            std::process::id(),
            std::thread::current().id()
        ));
        std::fs::create_dir(&root).unwrap();
        let path = root.join("test.par");
        std::fs::write(&path, &dry_bytes).unwrap();
        let result = localize_selected_v2(
            crate::stations::query::NearestRow {
                collection: "us-2015".to_owned(),
                id: "test.par".to_owned(),
                desc: "test".to_owned(),
                latitude: 33.25,
                longitude: -116.5,
                years: 40.0,
                distance_km: 0.0,
                path: path.clone(),
            },
            selection(
                path,
                &dry_bytes,
                "stochastic_prism_localized_par_degenerate_occurrence_independent_v1",
            ),
            &targets,
            DegenerateOccurrenceRepair::IndependentPrismV1,
        )
        .unwrap();
        assert_eq!(result.localization.schema_version, 2);
        assert_eq!(result.localization.precipitation_ratio[5], None);
        let repair = &result.localization.occurrence_repairs[0];
        assert_eq!(
            repair.precipitation_ratio_undefined_reason,
            "source_expected_monthly_precipitation_is_zero"
        );
        assert_eq!(repair.encoded_pww, 0.01);
        assert_eq!(repair.encoded_pwd, 0.01);
        assert!(
            (30.0 * 0.01 * f64::from(repair.encoded_mean_wet_day_in) - repair.prism_target_ppt_in)
                .abs()
                < 0.001
        );
        assert!(repair.warning().contains("month 6"));
        std::fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn repair_rejects_other_degenerate_states_and_unrepresentable_targets() {
        let partial = ParFile::parse(&par_with_month_six(0.0, 0.1, None)).unwrap();
        assert!(localize_month_with_repair(
            &partial,
            5,
            0.1,
            DegenerateOccurrenceRepair::IndependentPrismV1,
        )
        .is_err());

        let dry_bytes = par_with_month_six(0.0, 0.0, None);
        let dry = ParFile::parse(&dry_bytes).unwrap();
        let mut targets = normals(&dry);
        targets.monthly_ppt_in[5] = 0.000_001;
        let rewritten = rewrite(
            &dry_bytes,
            &dry,
            &targets,
            DegenerateOccurrenceRepair::IndependentPrismV1,
        )
        .unwrap();
        let encoded = ParFile::parse(&rewritten.bytes).unwrap();
        assert!(validate_encoded(&encoded, &targets).is_err());
    }

    #[test]
    fn repair_fails_closed_when_doubled_intensity_cannot_render() {
        let dry_bytes = par_with_month_six(0.0, 0.0, Some(600.0));
        let dry = ParFile::parse(&dry_bytes).unwrap();
        let mut targets = normals(&dry);
        targets.monthly_ppt_in[5] = 0.063_192_910_096_776_77;
        let error = rewrite(
            &dry_bytes,
            &dry,
            &targets,
            DegenerateOccurrenceRepair::IndependentPrismV1,
        )
        .unwrap_err();
        assert!(error.to_string().contains("does not fit F6.2"));
    }
}
