//! Explicit climate-only winter proxy metrics (quality metrics v3).
//!
//! These fields use daily mean air temperature and precipitation only. They
//! are intentionally named as proxies and never represent snowpack, melt,
//! runoff, frost depth, or soil freeze/thaw state.

use crate::quality::aggregation::year_slices;
use crate::quality::estimators::{cv, finite, mean, sample_sd};
use crate::quality::groups::corr_pair;
use crate::quality::intake::DailyValue;
use crate::quality::report::{
    Dispersion, FreezingPrecipitationFraction, Months, WinterAirTemperatureProxies,
    YearWinterAirTemperatureProxy,
};

/// Compute Group C winter air-temperature/precipitation proxies.
#[must_use]
pub(crate) fn compute(rows: &[DailyValue]) -> WinterAirTemperatureProxies {
    let per_year = yearly_proxies(rows);
    let complete_cycle_counts: Vec<f64> = per_year
        .iter()
        .filter(|year| year.complete_year)
        .map(|year| f64::from(year.freeze_thaw_air_temperature_proxy_cycles))
        .collect();
    WinterAirTemperatureProxies {
        precipitation_on_freezing_air_days: freezing_precipitation_fraction(rows),
        by_month: Months::from_fn(|month| {
            let selected: Vec<DailyValue> = rows
                .iter()
                .filter(|row| row.month as usize == month + 1)
                .copied()
                .collect();
            freezing_precipitation_fraction(&selected)
        }),
        djf_r1mm_precip_mean_air_temperature: winter_precip_temperature(rows),
        freeze_thaw_air_temperature_proxy_cycles: count_dispersion(&complete_cycle_counts),
        per_year,
    }
}

fn freezing_precipitation_fraction(rows: &[DailyValue]) -> FreezingPrecipitationFraction {
    if rows.is_empty() {
        return FreezingPrecipitationFraction {
            fraction: None,
            precipitation_on_freezing_air_days_mm: None,
            total_precipitation_mm: None,
            freezing_air_day_count: 0,
            n_days: 0,
        };
    }
    let total = rows.iter().map(|row| row.precip_mm).sum::<f64>();
    let freezing_rows = rows
        .iter()
        .filter(|row| row.mean_air_temperature_c() <= 0.0);
    let mut freezing_air_day_count = 0u64;
    let mut freezing_precip = 0.0f64;
    for row in freezing_rows {
        freezing_air_day_count += 1;
        freezing_precip += row.precip_mm;
    }
    FreezingPrecipitationFraction {
        fraction: (total != 0.0)
            .then(|| finite(freezing_precip / total))
            .flatten(),
        precipitation_on_freezing_air_days_mm: finite(freezing_precip),
        total_precipitation_mm: finite(total),
        freezing_air_day_count,
        n_days: rows.len() as u64,
    }
}

fn winter_precip_temperature(rows: &[DailyValue]) -> crate::quality::report::CorrPair {
    let winter: Vec<&DailyValue> = rows
        .iter()
        .filter(|row| matches!(row.month, 12 | 1 | 2) && row.is_r1mm())
        .collect();
    let precip: Vec<f64> = winter.iter().map(|row| row.precip_mm).collect();
    let temperature: Vec<f64> = winter
        .iter()
        .map(|row| row.mean_air_temperature_c())
        .collect();
    corr_pair(&precip, &temperature)
}

fn yearly_proxies(rows: &[DailyValue]) -> Vec<YearWinterAirTemperatureProxy> {
    year_slices(rows)
        .into_iter()
        .map(|slice| YearWinterAirTemperatureProxy {
            year: slice.year,
            n_days: slice.rows.len() as u32,
            complete_year: slice.complete,
            precipitation_on_freezing_air_days: freezing_precipitation_fraction(slice.rows),
            freeze_thaw_air_temperature_proxy_cycles: transitions_attributed_to_year(
                rows, slice.year,
            ),
        })
        .collect()
}

fn transitions_attributed_to_year(rows: &[DailyValue], year: i32) -> u32 {
    rows.windows(2)
        .filter(|pair| pair[1].year == year)
        .filter(|pair| freezing_state(&pair[0]) != freezing_state(&pair[1]))
        .count() as u32
}

fn freezing_state(row: &DailyValue) -> bool {
    row.mean_air_temperature_c() <= 0.0
}

fn count_dispersion(values: &[f64]) -> Dispersion {
    let mean_value = mean(values);
    let sd_value = sample_sd(values);
    Dispersion {
        mean: mean_value,
        sd: sd_value,
        cv: cv(mean_value, sd_value),
        n_years: values.len() as u32,
    }
}
