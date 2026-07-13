//! Metrics-v3 complete-period interannual dispersion and dependence.

use crate::quality::aggregation::{year_aggregates, MonthAggregate, YearAggregate};
use crate::quality::estimators::{
    cv, low_frequency_power_fraction, mean, pearson, sample_covariance, sample_sd, spearman,
};
use crate::quality::groups::{corr_pair, DecadeSlice};
use crate::quality::intake::DailyValue;
use crate::quality::report::{
    AnnualDependence, AnnualStats, ClimateAnomalyCorrelations, CorrPair, Dispersion, Interannual,
    InterannualDecade, InterannualDependence, LocationDispersion, MonthDependenceMatrix,
    MonthlyClimate, Months, SeriesDependence,
};

type MonthValue = fn(&MonthAggregate) -> Option<f64>;
type YearValue = fn(&YearAggregate) -> Option<f64>;

/// Group B — complete-period dispersion and whole-run dependence.
#[must_use]
pub(crate) fn compute(rows: &[DailyValue], decades: &[DecadeSlice<'_>]) -> Interannual {
    let aggregates = year_aggregates(rows);
    Interannual {
        annual: annual_stats(&aggregates),
        monthly: monthly_climate(&aggregates),
        dependence: dependence(&aggregates),
        by_decade: decades.iter().map(|block| decade_metrics(block)).collect(),
    }
}

fn decade_metrics(block: &DecadeSlice<'_>) -> InterannualDecade {
    let aggregates = year_aggregates(block.rows);
    InterannualDecade {
        decade: block.decade,
        start_year: block.start_year,
        n_years: block.n_years,
        annual: annual_stats(&aggregates),
        monthly: monthly_climate(&aggregates),
    }
}

fn complete_year_values(aggregates: &[YearAggregate], value: YearValue) -> Vec<f64> {
    aggregates
        .iter()
        .filter(|aggregate| aggregate.complete)
        .filter_map(value)
        .collect()
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

fn location_dispersion(values: &[f64]) -> LocationDispersion {
    LocationDispersion {
        mean: mean(values),
        sd: sample_sd(values),
        n_years: values.len() as u32,
    }
}

fn annual_stats(aggregates: &[YearAggregate]) -> AnnualStats {
    AnnualStats {
        precip_total_mm: dispersion(&complete_year_values(aggregates, |a| {
            Some(a.precip_total_mm)
        })),
        trace_wet_day_count: dispersion(&complete_year_values(aggregates, |a| {
            Some(f64::from(a.trace_wet_day_count))
        })),
        r1mm_wet_day_count: dispersion(&complete_year_values(aggregates, |a| {
            Some(f64::from(a.r1mm_wet_day_count))
        })),
        max_daily_precip_mm: dispersion(&complete_year_values(aggregates, |a| {
            Some(a.max_daily_precip_mm)
        })),
        tmax_mean_c: location_dispersion(&complete_year_values(aggregates, |a| a.tmax_mean_c)),
        tmin_mean_c: location_dispersion(&complete_year_values(aggregates, |a| a.tmin_mean_c)),
    }
}

fn complete_month_values(
    aggregates: &[YearAggregate],
    month: usize,
    value: MonthValue,
) -> Vec<f64> {
    aggregates
        .iter()
        .filter_map(|aggregate| aggregate.months[month].as_ref())
        .filter(|aggregate| aggregate.complete)
        .filter_map(value)
        .collect()
}

fn monthly_climate(aggregates: &[YearAggregate]) -> Months<MonthlyClimate> {
    Months::from_fn(|month| MonthlyClimate {
        precip_total_mm: month_dispersion(aggregates, month, |m| Some(m.precip_total_mm)),
        trace_wet_day_count: month_dispersion(aggregates, month, |m| {
            Some(f64::from(m.trace_wet_day_count))
        }),
        r1mm_wet_day_count: month_dispersion(aggregates, month, |m| {
            Some(f64::from(m.r1mm_wet_day_count))
        }),
        trace_wet_day_mean_amount_mm: month_dispersion(aggregates, month, |m| {
            m.trace_wet_day_mean_amount_mm
        }),
        r1mm_wet_day_mean_amount_mm: month_dispersion(aggregates, month, |m| {
            m.r1mm_wet_day_mean_amount_mm
        }),
        tmax_mean_c: month_location(aggregates, month, |m| m.tmax_mean_c),
        tmin_mean_c: month_location(aggregates, month, |m| m.tmin_mean_c),
    })
}

fn month_dispersion(aggregates: &[YearAggregate], month: usize, value: MonthValue) -> Dispersion {
    dispersion(&complete_month_values(aggregates, month, value))
}

fn month_location(
    aggregates: &[YearAggregate],
    month: usize,
    value: MonthValue,
) -> LocationDispersion {
    location_dispersion(&complete_month_values(aggregates, month, value))
}

fn dependence(aggregates: &[YearAggregate]) -> InterannualDependence {
    InterannualDependence {
        precip_cross_month: month_matrix(aggregates, |m| Some(m.precip_total_mm)),
        tmax_cross_month: month_matrix(aggregates, |m| m.tmax_mean_c),
        tmin_cross_month: month_matrix(aggregates, |m| m.tmin_mean_c),
        cross_variable_by_month: Months::from_fn(|month| {
            cross_variable_correlations(aggregates, month)
        }),
        annual: AnnualDependence {
            precip_total_mm: series_dependence(aggregates, |a| Some(a.precip_total_mm)),
            tmax_mean_c: series_dependence(aggregates, |a| a.tmax_mean_c),
            tmin_mean_c: series_dependence(aggregates, |a| a.tmin_mean_c),
        },
    }
}

fn month_matrix(aggregates: &[YearAggregate], value: MonthValue) -> MonthDependenceMatrix {
    let pairs = |left, right| paired_month_values(aggregates, left, right, value);
    MonthDependenceMatrix {
        covariance: (0..12)
            .map(|left| {
                (0..12)
                    .map(|right| {
                        let (xs, ys) = pairs(left, right);
                        sample_covariance(&xs, &ys)
                    })
                    .collect()
            })
            .collect(),
        pearson_correlation: (0..12)
            .map(|left| {
                (0..12)
                    .map(|right| {
                        let (xs, ys) = pairs(left, right);
                        pearson(&xs, &ys)
                    })
                    .collect()
            })
            .collect(),
        n_pairs: (0..12)
            .map(|left| {
                (0..12)
                    .map(|right| pairs(left, right).0.len() as u32)
                    .collect()
            })
            .collect(),
    }
}

fn paired_month_values(
    aggregates: &[YearAggregate],
    left: usize,
    right: usize,
    value: MonthValue,
) -> (Vec<f64>, Vec<f64>) {
    let mut xs = Vec::new();
    let mut ys = Vec::new();
    for aggregate in aggregates {
        let pair = aggregate.months[left]
            .as_ref()
            .zip(aggregate.months[right].as_ref());
        if let Some((a, b)) = pair.filter(|(a, b)| a.complete && b.complete) {
            if let Some((x, y)) = value(a).zip(value(b)) {
                xs.push(x);
                ys.push(y);
            }
        }
    }
    (xs, ys)
}

fn cross_variable_correlations(
    aggregates: &[YearAggregate],
    month: usize,
) -> ClimateAnomalyCorrelations {
    let triples: Vec<(f64, f64, f64)> = aggregates
        .iter()
        .filter_map(|year| year.months[month].as_ref())
        .filter(|cell| cell.complete)
        .filter_map(|cell| Some((cell.precip_total_mm, cell.tmax_mean_c?, cell.tmin_mean_c?)))
        .collect();
    let precip: Vec<f64> = triples.iter().map(|triple| triple.0).collect();
    let tmax: Vec<f64> = triples.iter().map(|triple| triple.1).collect();
    let tmin: Vec<f64> = triples.iter().map(|triple| triple.2).collect();
    ClimateAnomalyCorrelations {
        precip_tmax: corr_pair(&precip, &tmax),
        precip_tmin: corr_pair(&precip, &tmin),
        tmax_tmin: corr_pair(&tmax, &tmin),
    }
}

fn series_dependence(aggregates: &[YearAggregate], value: YearValue) -> SeriesDependence {
    let complete: Vec<(i32, f64)> = aggregates
        .iter()
        .filter(|aggregate| aggregate.complete)
        .filter_map(|aggregate| value(aggregate).map(|v| (aggregate.year, v)))
        .collect();
    let values: Vec<f64> = complete.iter().map(|(_, value)| *value).collect();
    SeriesDependence {
        lag_one: lag_one(&complete),
        period_ge_4y_power_fraction: low_frequency_power_fraction(&values),
        n_years: values.len() as u32,
    }
}

fn lag_one(series: &[(i32, f64)]) -> CorrPair {
    let mut previous = Vec::new();
    let mut next = Vec::new();
    for pair in series.windows(2) {
        if pair[1].0 == pair[0].0 + 1 {
            previous.push(pair[0].1);
            next.push(pair[1].1);
        }
    }
    CorrPair {
        pearson: pearson(&previous, &next),
        spearman: spearman(&previous, &next),
        n: previous.len() as u64,
    }
}
