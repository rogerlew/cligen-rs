//! Stable Group A and daily Group C quality metrics.
//!
//! Metrics v3 moves complete-period interannual, precipitation-structure,
//! event-descriptor, and winter calculations into focused modules so each
//! production function stays below the CRAP complexity cap.

use crate::quality::estimators::{adjusted_skew, finite, mean, pearson, sample_sd, spearman};
use crate::quality::intake::DailyValue;
use crate::quality::report::{
    ContrastCell, CorrPair, CorrSet, Covariation, CovariationDecade, DailyRangeMean, Months,
    ParCell, ParConvergence, ParDecade, ParParameter,
};
use crate::quality::targets::ParTargets;

/// One fixed 10-year block of contiguous rows.
pub struct DecadeSlice<'a> {
    pub decade: u32,
    pub start_year: i32,
    pub n_years: u32,
    pub rows: &'a [DailyValue],
}

/// Split the chronological row stream into fixed 10-year blocks from the
/// first simulated year.
#[must_use]
pub fn decade_slices(rows: &[DailyValue]) -> Vec<DecadeSlice<'_>> {
    let mut slices = Vec::new();
    if rows.is_empty() {
        return slices;
    }
    let origin = rows[0].year;
    let mut start = 0usize;
    while start < rows.len() {
        let decade = (rows[start].year - origin) / 10;
        let end = decade_end(rows, origin, decade, start);
        let block = &rows[start..end];
        slices.push(DecadeSlice {
            decade: u32::try_from(decade).expect("chronological intake keeps decades non-negative"),
            start_year: origin + decade * 10,
            n_years: distinct_years(block),
            rows: block,
        });
        start = end;
    }
    slices
}

fn decade_end(rows: &[DailyValue], origin: i32, decade: i32, start: usize) -> usize {
    let mut end = start + 1;
    while end < rows.len() && (rows[end].year - origin) / 10 == decade {
        end += 1;
    }
    end
}

/// Count distinct calendar years with at least one row.
#[must_use]
pub fn distinct_years(rows: &[DailyValue]) -> u32 {
    let mut count = 0u32;
    let mut current: Option<i32> = None;
    for row in rows {
        if current != Some(row.year) {
            count += 1;
            current = Some(row.year);
        }
    }
    count
}

// ---- group A ----

type MonthEstimate = dyn Fn(&[DailyValue], usize) -> (Option<f64>, u64);

fn month_values(rows: &[DailyValue], month: usize, value: fn(&DailyValue) -> f64) -> Vec<f64> {
    rows.iter()
        .filter(|row| row.month as usize == month + 1)
        .map(value)
        .collect()
}

fn wet_month_values(rows: &[DailyValue], month: usize) -> Vec<f64> {
    rows.iter()
        .filter(|row| row.month as usize == month + 1 && row.is_wet())
        .map(|row| row.precip_mm)
        .collect()
}

fn transition_rate(rows: &[DailyValue], month: usize, from_wet: bool) -> (Option<f64>, u64) {
    let mut opportunities = 0u64;
    let mut wet_outcomes = 0u64;
    for pair in rows.windows(2) {
        if pair[1].month as usize != month + 1 || pair[0].is_wet() != from_wet {
            continue;
        }
        opportunities += 1;
        wet_outcomes += u64::from(pair[1].is_wet());
    }
    if opportunities == 0 {
        return (None, 0);
    }
    (
        finite(wet_outcomes as f64 / opportunities as f64),
        opportunities,
    )
}

fn build_par_parameter(
    rows: &[DailyValue],
    decades: &[DecadeSlice<'_>],
    targets: &[Option<f64>; 12],
    estimate: &MonthEstimate,
) -> ParParameter {
    let cells = |scope: &[DailyValue]| {
        Months::from_fn(|month| {
            let (generated, n) = estimate(scope, month);
            ParCell::new(targets[month], generated, n)
        })
    };
    ParParameter {
        months: cells(rows),
        by_decade: decades
            .iter()
            .map(|block| ParDecade {
                decade: block.decade,
                start_year: block.start_year,
                n_years: block.n_years,
                months: cells(block.rows),
            })
            .collect(),
    }
}

fn wet_statistic(
    scope: &[DailyValue],
    month: usize,
    statistic: fn(&[f64]) -> Option<f64>,
) -> (Option<f64>, u64) {
    let values = wet_month_values(scope, month);
    (statistic(&values), values.len() as u64)
}

fn daily_statistic(
    scope: &[DailyValue],
    month: usize,
    value: fn(&DailyValue) -> f64,
    statistic: fn(&[f64]) -> Option<f64>,
) -> (Option<f64>, u64) {
    let values = month_values(scope, month, value);
    (statistic(&values), values.len() as u64)
}

fn wet_fraction(scope: &[DailyValue], month: usize) -> (Option<f64>, u64) {
    let days = month_values(scope, month, |row| f64::from(u8::from(row.is_wet())));
    (mean(&days), days.len() as u64)
}

/// Group A — convergence to the fixed-monthly station contract. Metrics v3
/// deliberately retains the legacy positive-trace wet predicate here.
#[must_use]
pub fn par_convergence(
    rows: &[DailyValue],
    decades: &[DecadeSlice<'_>],
    targets: &ParTargets,
    observed_passthrough: Option<bool>,
) -> ParConvergence {
    let build = |estimate: &MonthEstimate, target: &[Option<f64>; 12]| {
        build_par_parameter(rows, decades, target, estimate)
    };
    ParConvergence {
        observed_passthrough,
        precip_wet_mean_mm: build(
            &|s, m| wet_statistic(s, m, mean),
            &targets.precip_wet_mean_mm,
        ),
        precip_wet_sd_mm: build(
            &|s, m| wet_statistic(s, m, sample_sd),
            &targets.precip_wet_sd_mm,
        ),
        precip_wet_skew: build(
            &|s, m| wet_statistic(s, m, adjusted_skew),
            &targets.precip_wet_skew,
        ),
        wet_day_fraction: build(&wet_fraction, &targets.wet_day_fraction),
        p_ww: build(&|s, m| transition_rate(s, m, true), &targets.p_ww),
        p_wd: build(&|s, m| transition_rate(s, m, false), &targets.p_wd),
        tmax_mean_c: build(
            &|s, m| daily_statistic(s, m, |row| row.tmax_c, mean),
            &targets.tmax_mean_c,
        ),
        tmax_sd_c: build(
            &|s, m| daily_statistic(s, m, |row| row.tmax_c, sample_sd),
            &targets.tmax_sd_c,
        ),
        tmin_mean_c: build(
            &|s, m| daily_statistic(s, m, |row| row.tmin_c, mean),
            &targets.tmin_mean_c,
        ),
        tmin_sd_c: build(
            &|s, m| daily_statistic(s, m, |row| row.tmin_c, sample_sd),
            &targets.tmin_sd_c,
        ),
        radiation_mean_ly: build(
            &|s, m| daily_statistic(s, m, |row| row.radiation_ly, mean),
            &targets.radiation_mean_ly,
        ),
        dewpoint_mean_c: build(
            &|s, m| daily_statistic(s, m, |row| row.dewpoint_c, mean),
            &targets.dewpoint_mean_c,
        ),
        wind_speed_mean_ms: build(
            &|s, m| daily_statistic(s, m, |row| row.wind_speed_ms, mean),
            &targets.wind_speed_mean_ms,
        ),
    }
}

// ---- group C ----

pub(crate) fn corr_pair(xs: &[f64], ys: &[f64]) -> CorrPair {
    CorrPair {
        pearson: pearson(xs, ys),
        spearman: spearman(xs, ys),
        n: xs.len() as u64,
    }
}

fn corr_set(rows: &[DailyValue], month: Option<usize>) -> CorrSet {
    let wet: Vec<&DailyValue> = rows
        .iter()
        .filter(|row| row.is_wet() && month.is_none_or(|m| row.month as usize == m + 1))
        .collect();
    let column =
        |value: fn(&DailyValue) -> f64| -> Vec<f64> { wet.iter().map(|row| value(row)).collect() };
    let amount = column(|row| row.precip_mm);
    let duration = column(|row| row.duration_h);
    let ratio = column(|row| row.peak_intensity_ratio);
    let radiation = column(|row| row.radiation_ly);
    CorrSet {
        amount_duration: corr_pair(&amount, &duration),
        amount_peak_intensity_ratio: corr_pair(&amount, &ratio),
        duration_radiation: corr_pair(&duration, &radiation),
    }
}

fn radiation_contrast(rows: &[DailyValue], month: Option<usize>) -> ContrastCell {
    let mut wet_values = Vec::new();
    let mut dry_values = Vec::new();
    for row in rows
        .iter()
        .filter(|row| month.is_none_or(|m| row.month as usize == m + 1))
    {
        if row.is_wet() {
            wet_values.push(row.radiation_ly);
        } else {
            dry_values.push(row.radiation_ly);
        }
    }
    let contrast = match (mean(&wet_values), mean(&dry_values)) {
        (Some(wet_mean), Some(dry_mean)) if dry_mean != 0.0 => finite(wet_mean / dry_mean),
        _ => None,
    };
    ContrastCell {
        contrast,
        wet_n: wet_values.len() as u64,
        dry_n: dry_values.len() as u64,
    }
}

fn daily_range_mean(rows: &[DailyValue], month: Option<usize>) -> Option<f64> {
    let ranges: Vec<f64> = rows
        .iter()
        .filter(|row| month.is_none_or(|m| row.month as usize == m + 1))
        .map(|row| row.tmax_c - row.tmin_c)
        .collect();
    mean(&ranges)
}

/// Group C — daily covariation plus explicit climate-only winter proxies.
#[must_use]
pub fn covariation(rows: &[DailyValue], decades: &[DecadeSlice<'_>]) -> Covariation {
    Covariation {
        whole_run: corr_set(rows, None),
        months: Months::from_fn(|month| corr_set(rows, Some(month))),
        radiation_wet_dry_contrast: Months::from_fn(|month| radiation_contrast(rows, Some(month))),
        daily_range_mean_c: DailyRangeMean {
            whole_run: daily_range_mean(rows, None),
            months: Months::from_fn(|month| daily_range_mean(rows, Some(month))),
        },
        winter_air_temperature_proxies: crate::quality::winter::compute(rows),
        by_decade: decades
            .iter()
            .map(|block| CovariationDecade {
                decade: block.decade,
                start_year: block.start_year,
                n_years: block.n_years,
                pairs: corr_set(block.rows, None),
                radiation_wet_dry_contrast: radiation_contrast(block.rows, None),
                daily_range_mean_c: daily_range_mean(block.rows, None),
            })
            .collect(),
    }
}
