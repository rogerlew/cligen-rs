//! Complete-period aggregation shared by quality metrics v3.
//!
//! The rendered `.cli` intake is contiguous, but observed-mode EOF may leave
//! a trailing partial month/year. This module retains partial aggregates for
//! tail diagnostics while marking completeness so interannual estimators
//! never treat a truncated period as climate variation.

use crate::quality::estimators::mean;
use crate::quality::intake::{max_gregorian_day, DailyValue};

/// One calendar month's aggregate values.
#[derive(Debug, Clone)]
pub(crate) struct MonthAggregate {
    pub complete: bool,
    pub precip_total_mm: f64,
    pub trace_wet_day_count: u32,
    pub r1mm_wet_day_count: u32,
    pub trace_wet_day_mean_amount_mm: Option<f64>,
    pub r1mm_wet_day_mean_amount_mm: Option<f64>,
    pub tmax_mean_c: Option<f64>,
    pub tmin_mean_c: Option<f64>,
}

/// One calendar year's aggregate values and month cells.
#[derive(Debug, Clone)]
pub(crate) struct YearAggregate {
    pub year: i32,
    pub complete: bool,
    pub months: [Option<MonthAggregate>; 12],
    pub precip_total_mm: f64,
    pub trace_wet_day_count: u32,
    pub r1mm_wet_day_count: u32,
    pub max_daily_precip_mm: f64,
    pub tmax_mean_c: Option<f64>,
    pub tmin_mean_c: Option<f64>,
}

/// Contiguous rows for one printed calendar year.
pub(crate) struct YearSlice<'a> {
    pub year: i32,
    pub complete: bool,
    pub rows: &'a [DailyValue],
}

/// Split the row stream into calendar years and mark complete years.
#[must_use]
pub(crate) fn year_slices(rows: &[DailyValue]) -> Vec<YearSlice<'_>> {
    let mut slices = Vec::new();
    let mut start = 0usize;
    while start < rows.len() {
        let mut end = start + 1;
        while end < rows.len() && rows[end].year == rows[start].year {
            end += 1;
        }
        let year_rows = &rows[start..end];
        slices.push(YearSlice {
            year: year_rows[0].year,
            complete: is_complete_year(year_rows),
            rows: year_rows,
        });
        start = end;
    }
    slices
}

/// Aggregate every represented year; callers select `complete` rows for
/// dispersion/dependence and may retain partial rows for diagnostics.
#[must_use]
pub(crate) fn year_aggregates(rows: &[DailyValue]) -> Vec<YearAggregate> {
    year_slices(rows)
        .into_iter()
        .map(|slice| aggregate_year(slice.rows, slice.complete))
        .collect()
}

fn aggregate_year(rows: &[DailyValue], complete: bool) -> YearAggregate {
    let mut months: [Option<MonthAggregate>; 12] = std::array::from_fn(|_| None);
    let mut start = 0usize;
    while start < rows.len() {
        let month = rows[start].month;
        let mut end = start + 1;
        while end < rows.len() && rows[end].month == month {
            end += 1;
        }
        let aggregate = aggregate_month(&rows[start..end]);
        months[(month - 1) as usize] = Some(aggregate);
        start = end;
    }
    let precip_total_mm = rows.iter().map(|row| row.precip_mm).sum();
    let trace_wet_day_count = count_where(rows, DailyValue::is_wet);
    let r1mm_wet_day_count = count_where(rows, DailyValue::is_r1mm);
    let max_daily_precip_mm = rows.iter().map(|row| row.precip_mm).fold(0.0f64, f64::max);
    YearAggregate {
        year: rows[0].year,
        complete,
        months,
        precip_total_mm,
        trace_wet_day_count,
        r1mm_wet_day_count,
        max_daily_precip_mm,
        tmax_mean_c: mean_values(rows, |row| row.tmax_c),
        tmin_mean_c: mean_values(rows, |row| row.tmin_c),
    }
}

fn aggregate_month(rows: &[DailyValue]) -> MonthAggregate {
    let trace_amounts = selected_values(rows, DailyValue::is_wet, |row| row.precip_mm);
    let r1mm_amounts = selected_values(rows, DailyValue::is_r1mm, |row| row.precip_mm);
    MonthAggregate {
        complete: is_complete_month(rows),
        precip_total_mm: rows.iter().map(|row| row.precip_mm).sum(),
        trace_wet_day_count: trace_amounts.len() as u32,
        r1mm_wet_day_count: r1mm_amounts.len() as u32,
        trace_wet_day_mean_amount_mm: mean(&trace_amounts),
        r1mm_wet_day_mean_amount_mm: mean(&r1mm_amounts),
        tmax_mean_c: mean_values(rows, |row| row.tmax_c),
        tmin_mean_c: mean_values(rows, |row| row.tmin_c),
    }
}

fn selected_values(
    rows: &[DailyValue],
    predicate: fn(&DailyValue) -> bool,
    value: fn(&DailyValue) -> f64,
) -> Vec<f64> {
    rows.iter()
        .filter(|row| predicate(row))
        .map(value)
        .collect()
}

fn count_where(rows: &[DailyValue], predicate: fn(&DailyValue) -> bool) -> u32 {
    rows.iter().filter(|row| predicate(row)).count() as u32
}

fn mean_values(rows: &[DailyValue], value: fn(&DailyValue) -> f64) -> Option<f64> {
    mean(&rows.iter().map(value).collect::<Vec<_>>())
}

fn is_complete_month(rows: &[DailyValue]) -> bool {
    let first = &rows[0];
    let last = &rows[rows.len() - 1];
    first.day == 1
        && last.day == max_gregorian_day(first.month, first.year)
        && rows.len() == max_gregorian_day(first.month, first.year) as usize
}

fn is_complete_year(rows: &[DailyValue]) -> bool {
    let first = &rows[0];
    let last = &rows[rows.len() - 1];
    first.month == 1
        && first.day == 1
        && last.month == 12
        && last.day == 31
        && rows.len() == days_in_year(first.year)
}

fn days_in_year(year: i32) -> usize {
    (1..=12)
        .map(|month| max_gregorian_day(month, year) as usize)
        .sum()
}
