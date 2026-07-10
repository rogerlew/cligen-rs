//! Metric groups A-D over the parsed daily table
//! (SPEC-QUALITY-REPORT §Metric groups).
//!
//! Every estimator accumulates in f64 in row order. Decades are fixed
//! 10-year blocks from the first simulated year; a trailing partial
//! decade reports its `n_years`. Markov transition estimates count
//! consecutive row pairs (the WEPP daily table is contiguous by
//! contract) attributed to the second row's calendar month; the first
//! row of a scope has no predecessor inside that scope.

use crate::quality::estimators::{adjusted_skew, cv, finite, mean, pearson, sample_sd, spearman};
use crate::quality::intake::DailyValue;
use crate::quality::report::{
    AnnualStats, ContrastCell, CorrPair, CorrSet, Covariation, CovariationDecade, DailyRangeMean,
    Dispersion, Interannual, InterannualDecade, MonthlySdCell, Months, ParCell, ParConvergence,
    ParDecade, ParParameter, Tails, TopEvent, YearTails,
};
use crate::quality::targets::ParTargets;

/// One fixed 10-year block of contiguous rows.
pub struct DecadeSlice<'a> {
    pub decade: u32,
    pub start_year: i32,
    pub n_years: u32,
    pub rows: &'a [DailyValue],
}

/// Split the chronological row stream into fixed 10-year blocks from
/// the first simulated year.
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
        let mut end = start;
        while end + 1 < rows.len() && (rows[end + 1].year - origin) / 10 == decade {
            end += 1;
        }
        let block = &rows[start..=end];
        slices.push(DecadeSlice {
            decade: u32::try_from(decade).expect("chronological intake keeps decades non-negative"),
            start_year: origin + decade * 10,
            n_years: distinct_years(block),
            rows: block,
        });
        start = end + 1;
    }
    slices
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

fn month_values(rows: &[DailyValue], month: usize, value: impl Fn(&DailyValue) -> f64) -> Vec<f64> {
    rows.iter()
        .filter(|row| row.month as usize == month + 1)
        .map(value)
        .collect()
}

fn wet_month_values(
    rows: &[DailyValue],
    month: usize,
    value: impl Fn(&DailyValue) -> f64,
) -> Vec<f64> {
    rows.iter()
        .filter(|row| row.month as usize == month + 1 && row.is_wet())
        .map(value)
        .collect()
}

/// Markov transition estimate: rate of wet second days among
/// consecutive row pairs whose first day matches `from_wet`,
/// attributed to the second day's month.
fn transition_rate(rows: &[DailyValue], month: usize, from_wet: bool) -> (Option<f64>, u64) {
    let mut opportunities = 0u64;
    let mut wet_outcomes = 0u64;
    for pair in rows.windows(2) {
        if pair[1].month as usize != month + 1 || pair[0].is_wet() != from_wet {
            continue;
        }
        opportunities += 1;
        if pair[1].is_wet() {
            wet_outcomes += 1;
        }
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

/// Group A — convergence to the `.par` contract.
#[must_use]
pub fn par_convergence(
    rows: &[DailyValue],
    decades: &[DecadeSlice<'_>],
    targets: &ParTargets,
    observed_passthrough: Option<bool>,
) -> ParConvergence {
    let wet_stat = |stat: fn(&[f64]) -> Option<f64>| {
        move |scope: &[DailyValue], month: usize| {
            let values = wet_month_values(scope, month, |row| row.precip_mm);
            (stat(&values), values.len() as u64)
        }
    };
    let day_mean = |value: fn(&DailyValue) -> f64| {
        move |scope: &[DailyValue], month: usize| {
            let values = month_values(scope, month, value);
            (mean(&values), values.len() as u64)
        }
    };
    let day_sd = |value: fn(&DailyValue) -> f64| {
        move |scope: &[DailyValue], month: usize| {
            let values = month_values(scope, month, value);
            (sample_sd(&values), values.len() as u64)
        }
    };
    let wet_fraction = |scope: &[DailyValue], month: usize| {
        let days = month_values(scope, month, |row| f64::from(u8::from(row.is_wet())));
        (mean(&days), days.len() as u64)
    };
    let build = |estimate: &MonthEstimate, targets_for: &[Option<f64>; 12]| {
        build_par_parameter(rows, decades, targets_for, estimate)
    };
    ParConvergence {
        observed_passthrough,
        precip_wet_mean_mm: build(&wet_stat(mean), &targets.precip_wet_mean_mm),
        precip_wet_sd_mm: build(&wet_stat(sample_sd), &targets.precip_wet_sd_mm),
        precip_wet_skew: build(&wet_stat(adjusted_skew), &targets.precip_wet_skew),
        wet_day_fraction: build(&wet_fraction, &targets.wet_day_fraction),
        p_ww: build(
            &|scope, month| transition_rate(scope, month, true),
            &targets.p_ww,
        ),
        p_wd: build(
            &|scope, month| transition_rate(scope, month, false),
            &targets.p_wd,
        ),
        tmax_mean_c: build(&day_mean(|row| row.tmax_c), &targets.tmax_mean_c),
        tmax_sd_c: build(&day_sd(|row| row.tmax_c), &targets.tmax_sd_c),
        tmin_mean_c: build(&day_mean(|row| row.tmin_c), &targets.tmin_mean_c),
        tmin_sd_c: build(&day_sd(|row| row.tmin_c), &targets.tmin_sd_c),
        radiation_mean_ly: build(
            &day_mean(|row| row.radiation_ly),
            &targets.radiation_mean_ly,
        ),
        dewpoint_mean_c: build(&day_mean(|row| row.dewpoint_c), &targets.dewpoint_mean_c),
        wind_speed_mean_ms: build(
            &day_mean(|row| row.wind_speed_ms),
            &targets.wind_speed_mean_ms,
        ),
    }
}

// ---- group B ----

struct YearAggregate {
    precip_total: f64,
    wet_days: u32,
    max_daily: f64,
    tmax_mean: Option<f64>,
    tmin_mean: Option<f64>,
    /// Monthly precipitation totals; `None` for months with no rows
    /// (partial years).
    monthly_precip: [Option<f64>; 12],
}

fn year_aggregates(rows: &[DailyValue]) -> Vec<YearAggregate> {
    let mut aggregates = Vec::new();
    let mut start = 0usize;
    while start < rows.len() {
        let mut end = start;
        while end + 1 < rows.len() && rows[end + 1].year == rows[start].year {
            end += 1;
        }
        aggregates.push(aggregate_year(&rows[start..=end]));
        start = end + 1;
    }
    aggregates
}

fn aggregate_year(rows: &[DailyValue]) -> YearAggregate {
    let mut monthly_precip: [Option<f64>; 12] = [None; 12];
    let mut precip_total = 0.0f64;
    let mut wet_days = 0u32;
    let mut max_daily = 0.0f64;
    let mut tmax_sum = 0.0f64;
    let mut tmin_sum = 0.0f64;
    for row in rows {
        precip_total += row.precip_mm;
        if row.is_wet() {
            wet_days += 1;
        }
        if row.precip_mm > max_daily {
            max_daily = row.precip_mm;
        }
        tmax_sum += row.tmax_c;
        tmin_sum += row.tmin_c;
        let month = (row.month - 1) as usize;
        monthly_precip[month] = Some(monthly_precip[month].unwrap_or(0.0) + row.precip_mm);
    }
    let n_days = rows.len() as f64;
    YearAggregate {
        precip_total,
        wet_days,
        max_daily,
        tmax_mean: finite(tmax_sum / n_days),
        tmin_mean: finite(tmin_sum / n_days),
        monthly_precip,
    }
}

fn dispersion(values: &[f64]) -> Dispersion {
    let mean_value = mean(values);
    let sd_value = sample_sd(values);
    Dispersion {
        mean: mean_value,
        sd: sd_value,
        cv: cv(mean_value, sd_value),
        n_years: values.len() as u32,
    }
}

fn annual_stats(aggregates: &[YearAggregate]) -> AnnualStats {
    let collect = |value: &dyn Fn(&YearAggregate) -> Option<f64>| -> Vec<f64> {
        aggregates.iter().filter_map(value).collect()
    };
    AnnualStats {
        precip_total_mm: dispersion(&collect(&|a| Some(a.precip_total))),
        wet_day_count: dispersion(&collect(&|a| Some(f64::from(a.wet_days)))),
        max_daily_precip_mm: dispersion(&collect(&|a| Some(a.max_daily))),
        tmax_mean_c: dispersion(&collect(&|a| a.tmax_mean)),
        tmin_mean_c: dispersion(&collect(&|a| a.tmin_mean)),
    }
}

fn monthly_precip_sd(aggregates: &[YearAggregate]) -> Months<MonthlySdCell> {
    Months::from_fn(|month| {
        let totals: Vec<f64> = aggregates
            .iter()
            .filter_map(|a| a.monthly_precip[month])
            .collect();
        MonthlySdCell {
            sd: sample_sd(&totals),
            n_years: totals.len() as u32,
        }
    })
}

/// Group B — interannual dispersion with per-decade blocks.
#[must_use]
pub fn interannual(rows: &[DailyValue], decades: &[DecadeSlice<'_>]) -> Interannual {
    let whole = year_aggregates(rows);
    Interannual {
        annual: annual_stats(&whole),
        monthly_precip_total_sd_mm: monthly_precip_sd(&whole),
        by_decade: decades
            .iter()
            .map(|block| {
                let aggregates = year_aggregates(block.rows);
                InterannualDecade {
                    decade: block.decade,
                    start_year: block.start_year,
                    n_years: block.n_years,
                    annual: annual_stats(&aggregates),
                    monthly_precip_total_sd_mm: monthly_precip_sd(&aggregates),
                }
            })
            .collect(),
    }
}

// ---- group C ----

fn corr_pair(xs: &[f64], ys: &[f64]) -> CorrPair {
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
    let intensity = column(|row| row.peak_intensity);
    let radiation = column(|row| row.radiation_ly);
    CorrSet {
        amount_duration: corr_pair(&amount, &duration),
        amount_peak_intensity: corr_pair(&amount, &intensity),
        duration_radiation: corr_pair(&duration, &radiation),
    }
}

fn radiation_contrast(rows: &[DailyValue], month: Option<usize>) -> ContrastCell {
    let mut wet = Vec::new();
    let mut dry = Vec::new();
    for row in rows {
        if month.is_some_and(|m| row.month as usize != m + 1) {
            continue;
        }
        if row.is_wet() {
            wet.push(row.radiation_ly);
        } else {
            dry.push(row.radiation_ly);
        }
    }
    let contrast = match (mean(&wet), mean(&dry)) {
        (Some(wet_mean), Some(dry_mean)) if dry_mean != 0.0 => finite(wet_mean / dry_mean),
        _ => None,
    };
    ContrastCell {
        contrast,
        wet_n: wet.len() as u64,
        dry_n: dry.len() as u64,
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

/// Group C — covariation. Per-decade blocks are decade-level
/// (SPEC-QUALITY-REPORT rev 3): month × decade wet-day cells are
/// statistically empty at n ≈ 10 years.
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

// ---- group D ----

fn year_tails(year_rows: &[DailyValue]) -> YearTails {
    let mut max_daily = 0.0f64;
    let mut storm_count = 0u32;
    let mut max_intensity: Option<f64> = None;
    let mut longest_wet = 0u32;
    let mut longest_dry = 0u32;
    let mut wet_run = 0u32;
    let mut dry_run = 0u32;
    for row in year_rows {
        if row.precip_mm > max_daily {
            max_daily = row.precip_mm;
        }
        if row.is_wet() {
            storm_count += 1;
            max_intensity = Some(match max_intensity {
                Some(current) if current >= row.peak_intensity => current,
                _ => row.peak_intensity,
            });
            wet_run += 1;
            dry_run = 0;
        } else {
            dry_run += 1;
            wet_run = 0;
        }
        longest_wet = longest_wet.max(wet_run);
        longest_dry = longest_dry.max(dry_run);
    }
    YearTails {
        year: year_rows[0].year,
        n_days: year_rows.len() as u32,
        max_daily_precip_mm: finite(max_daily),
        storm_count,
        max_peak_intensity: max_intensity,
        longest_wet_spell_days: longest_wet,
        longest_dry_spell_days: longest_dry,
    }
}

fn top_events(rows: &[DailyValue]) -> Vec<TopEvent> {
    let mut wet: Vec<(usize, &DailyValue)> = rows
        .iter()
        .enumerate()
        .filter(|(_, row)| row.is_wet())
        .collect();
    // Depth descending; ties break by earlier date, then lower row
    // index (SPEC-QUALITY-REPORT §Determinism).
    wet.sort_by(|(index_a, a), (index_b, b)| {
        b.precip_mm
            .partial_cmp(&a.precip_mm)
            .expect("intake guarantees finite values")
            .then_with(|| a.date_key().cmp(&b.date_key()))
            .then_with(|| index_a.cmp(index_b))
    });
    wet.iter()
        .take(5)
        .enumerate()
        .map(|(rank, (row_index, row))| TopEvent {
            rank: rank as u32 + 1,
            year: row.year,
            month: row.month,
            day: row.day,
            row_index: *row_index as u64 + 1,
            precip_mm: row.precip_mm,
            duration_h: row.duration_h,
            peak_intensity: row.peak_intensity,
        })
        .collect()
}

/// Group D — tails: per-year extremes and spells (spells are clipped
/// at year boundaries) plus the whole-run top five daily events.
#[must_use]
pub fn tails(rows: &[DailyValue]) -> Tails {
    let mut per_year = Vec::new();
    let mut start = 0usize;
    while start < rows.len() {
        let mut end = start;
        while end + 1 < rows.len() && rows[end + 1].year == rows[start].year {
            end += 1;
        }
        per_year.push(year_tails(&rows[start..=end]));
        start = end + 1;
    }
    Tails {
        per_year,
        top_events: top_events(rows),
    }
}
