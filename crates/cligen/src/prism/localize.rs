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
use super::{PrismError, PROFILE_ID};

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
    pub collection: String,
    pub selected_station_id: String,
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

/// Complete local preprocessing result ready for artifact publication.
#[derive(Debug)]
pub struct LocalizedPar {
    pub source_path: PathBuf,
    pub source_bytes: Vec<u8>,
    pub localized_bytes: Vec<u8>,
    pub selection: SelectionReceipt,
    pub localization: LocalizationReceipt,
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

/// Select a station and localize its monthly precipitation/temperature rows.
pub fn localize(cache_root: &Path, normals: &NormalsReceipt) -> Result<LocalizedPar, PrismError> {
    let (selected, selection) = select_station(cache_root, normals)?;
    localize_selected(selected, selection, normals)
}

fn localize_selected(
    selected: NearestRow,
    selection: SelectionReceipt,
    normals: &NormalsReceipt,
) -> Result<LocalizedPar, PrismError> {
    let source_bytes = fs::read(&selected.path)
        .map_err(|source| super::io_error("read selected station .par", source))?;
    let source = ParFile::parse(&source_bytes)
        .map_err(|error| PrismError::InvalidStation(error.to_string()))?;
    let (localized_bytes, ratios) = rewrite(&source_bytes, &source, normals)?;
    let encoded =
        ParFile::parse(&localized_bytes).map_err(|error| PrismError::Render(error.to_string()))?;
    validate_encoded(&encoded, normals)?;
    Ok(build_localized_result(
        selected,
        selection,
        source_bytes,
        localized_bytes,
        &encoded,
        normals,
        ratios,
    ))
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

fn select_station(
    cache_root: &Path,
    normals: &NormalsReceipt,
) -> Result<(NearestRow, SelectionReceipt), PrismError> {
    let rows = nearest(
        &Manifests::embedded(),
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
    if rows.len() != POOL_SIZE {
        return Err(PrismError::InvalidStation(format!(
            "selector requires {POOL_SIZE} candidates, found {}",
            rows.len()
        )));
    }
    let mut candidates = load_candidates(rows, normals)?;
    assign_ranks(&mut candidates);
    let receipts: Vec<CandidateReceipt> = candidates.iter().map(candidate_receipt).collect();
    let winner = winning_candidate(&candidates);
    let receipt = SelectionReceipt {
        schema_version: 1,
        profile_id: PROFILE_ID.to_owned(),
        collection: "us-2015@2026.07".to_owned(),
        selected_station_id: winner.id.clone(),
        candidates: receipts,
    };
    Ok((winner, receipt))
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
) -> Result<(Vec<u8>, [f64; 12]), PrismError> {
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
    let mut ratio = [0.0; 12];
    for month in 0..12 {
        let values = localize_month(par, month, target_ppt[month])?;
        mean[month] = values[0];
        pww[month] = values[1];
        pwd[month] = values[2];
        intensity[month] = values[3];
        ratio[month] = values[4];
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
    Ok((output, ratio))
}

fn localize_month(par: &ParFile, month: usize, target: f64) -> Result<[f64; 5], PrismError> {
    let model = par.fixed_monthly();
    let mean = f64::from(model.rst[month][0]);
    let old_pww = f64::from(model.prw[month][0]);
    let old_pwd = f64::from(model.prw[month][1]);
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
        Ok(result)
    } else {
        Err(PrismError::InvalidStation(format!(
            "month {} produced invalid localized values",
            month + 1
        )))
    }
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
        localize_month, localize_selected, render_monthly, rewrite, station_ppt, validate_encoded,
        SelectionReceipt,
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
    fn localization_rewrites_only_registered_rows_and_reparses() {
        let par = ParFile::parse(PAR).unwrap();
        let targets = normals(&par);
        let (bytes, ratios) = rewrite(PAR, &par, &targets).unwrap();
        assert!(ratios.iter().all(|ratio| *ratio > 1.0));
        let localized = ParFile::parse(&bytes).unwrap();
        validate_encoded(&localized, &targets).unwrap();
        for record in 1..=83 {
            if ![4, 7, 8, 9, 10, 15].contains(&record) {
                assert_eq!(
                    PAR.split(|byte| *byte == b'\n').nth(record - 1),
                    bytes.split(|byte| *byte == b'\n').nth(record - 1)
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
                path,
            },
            SelectionReceipt {
                schema_version: 1,
                profile_id: "stochastic_prism_localized_par_v1".to_owned(),
                collection: "us-2015@2026.07".to_owned(),
                selected_station_id: "id106388.par".to_owned(),
                candidates: Vec::new(),
            },
            &normals(&par),
        )
        .unwrap();
        assert_eq!(result.localization.source_station_id, "id106388.par");
    }
}
