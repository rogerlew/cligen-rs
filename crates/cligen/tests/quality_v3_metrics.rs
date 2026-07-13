//! A5a metrics-v3 acceptance vectors.
//!
//! These fixtures are deliberately synthetic, contiguous Gregorian `.cli`
//! streams. Their expected values are hand-derived so this suite tests the
//! public quality-report surface independently of the observed-corpus builder.

use std::path::{Path, PathBuf};

use cligen::quality::{compute_report, QualityError, QualityReport};

const DAILY_HEADER: &str = " da mo year  prcp  dur   tp     ip  tmax  tmin  rad  w-vl w-dir  tdew\n             (mm)  (h)               (C)   (C) (l/d) (m/s)(Deg)   (C)\n";

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
struct Date {
    year: i32,
    month: i32,
    day: i32,
}

#[derive(Clone, Copy, Debug)]
struct Climate {
    precip_mm: f64,
    duration_h: f64,
    time_to_peak: f64,
    peak_intensity_ratio: f64,
    tmax_c: f64,
    tmin_c: f64,
}

impl Default for Climate {
    fn default() -> Self {
        Self {
            precip_mm: 0.0,
            duration_h: 1.0,
            time_to_peak: 0.5,
            peak_intensity_ratio: 2.0,
            tmax_c: 10.0,
            tmin_c: 2.0,
        }
    }
}

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .unwrap()
}

fn station_par() -> Vec<u8> {
    std::fs::read(repo_root().join("fixtures/new-meadows-id/id106388.par")).unwrap()
}

fn synthetic_cli(rows: &str) -> String {
    format!("5.32300\nA5a deterministic metric vector\n{DAILY_HEADER}{rows}")
}

fn render_row(date: Date, climate: Climate) -> String {
    format!(
        " {day:2} {month:2} {year:5} {precip:7.2} {duration:5.2} {time_to_peak:4.2} \
         {ratio:6.2} {tmax:6.2} {tmin:6.2} 200.0 3.0 180.0 0.0\n",
        day = date.day,
        month = date.month,
        year = date.year,
        precip = climate.precip_mm,
        duration = climate.duration_h,
        time_to_peak = climate.time_to_peak,
        ratio = climate.peak_intensity_ratio,
        tmax = climate.tmax_c,
        tmin = climate.tmin_c,
    )
}

fn rows_between(start: Date, end: Date, mut climate: impl FnMut(Date) -> Climate) -> String {
    let mut rows = String::new();
    let mut date = start;
    loop {
        rows.push_str(&render_row(date, climate(date)));
        if date == end {
            break;
        }
        date = next_date(date);
    }
    rows
}

fn next_date(date: Date) -> Date {
    let month_days = days_in_month(date.year, date.month);
    if date.day < month_days {
        return Date {
            day: date.day + 1,
            ..date
        };
    }
    if date.month < 12 {
        return Date {
            year: date.year,
            month: date.month + 1,
            day: 1,
        };
    }
    Date {
        year: date.year + 1,
        month: 1,
        day: 1,
    }
}

fn days_in_month(year: i32, month: i32) -> i32 {
    match month {
        2 => 28 + i32::from(year % 4 == 0 && (year % 100 != 0 || year % 400 == 0)),
        4 | 6 | 9 | 11 => 30,
        _ => 31,
    }
}

fn assert_close(actual: Option<f64>, expected: f64) {
    let actual = actual.expect("expected a finite metric");
    assert!(
        (actual - expected).abs() <= 1.0e-12,
        "expected {expected}, found {actual}"
    );
}

#[test]
fn multirow_requires_contiguous_gregorian_dates_but_single_storm_keeps_exception() {
    let par = station_par();

    let gap = render_row(
        Date {
            year: 2001,
            month: 1,
            day: 1,
        },
        Climate::default(),
    ) + &render_row(
        Date {
            year: 2001,
            month: 1,
            day: 3,
        },
        Climate::default(),
    );
    let error = compute_report(&synthetic_cli(&gap), &par, None, None).unwrap_err();
    assert!(matches!(error, QualityError::Cli(_)));
    assert!(error.to_string().contains("not the next calendar day"));

    // The source storm calendar admits 1900-02-29, while a multirow daily
    // stream uses the proleptic Gregorian calendar and rejects it.
    let february = render_row(
        Date {
            year: 1900,
            month: 2,
            day: 28,
        },
        Climate::default(),
    ) + &render_row(
        Date {
            year: 1900,
            month: 2,
            day: 29,
        },
        Climate::default(),
    );
    let error = compute_report(&synthetic_cli(&february), &par, None, None).unwrap_err();
    assert!(matches!(error, QualityError::Cli(_)));
    assert!(error.to_string().contains("not a Gregorian calendar date"));

    let single_storm = render_row(
        Date {
            year: 1900,
            month: 2,
            day: 29,
        },
        Climate {
            precip_mm: 1.0,
            ..Climate::default()
        },
    );
    let report = compute_report(&synthetic_cli(&single_storm), &par, None, None).unwrap();
    assert_eq!(report.identity.content.days, 1);
    assert_eq!(report.identity.content.span, [1900, 1900]);
    assert!(report.interannual.is_none());
    assert_eq!(report.tails.top_events.len(), 1);
}

#[test]
fn interannual_metrics_exclude_incomplete_months_and_years() {
    let rows = rows_between(
        Date {
            year: 1999,
            month: 12,
            day: 15,
        },
        Date {
            year: 2001,
            month: 1,
            day: 15,
        },
        |date| Climate {
            precip_mm: if date.year == 2000 { 2.0 } else { 9.0 },
            ..Climate::default()
        },
    );
    let report = compute_report(&synthetic_cli(&rows), &station_par(), None, None).unwrap();
    let interannual = report.interannual.as_ref().unwrap();

    assert_eq!(interannual.annual.precip_total_mm.n_years, 1);
    assert_close(interannual.annual.precip_total_mm.mean, 732.0);
    assert_eq!(interannual.annual.precip_total_mm.sd, None);
    assert_eq!(interannual.monthly.jan.precip_total_mm.n_years, 1);
    assert_close(interannual.monthly.jan.precip_total_mm.mean, 62.0);
    assert_eq!(interannual.monthly.dec.precip_total_mm.n_years, 1);
    assert_close(interannual.monthly.dec.precip_total_mm.mean, 62.0);

    assert_eq!(
        report
            .tails
            .per_year
            .iter()
            .map(|year| (year.year, year.n_days, year.complete_year))
            .collect::<Vec<_>>(),
        vec![(1999, 17, false), (2000, 366, true), (2001, 15, false)]
    );
}

#[test]
fn trace_positive_and_r1mm_surfaces_remain_distinct() {
    let rows = rows_between(
        Date {
            year: 2001,
            month: 1,
            day: 1,
        },
        Date {
            year: 2001,
            month: 1,
            day: 31,
        },
        |date| Climate {
            precip_mm: match date.day {
                1 => 0.5,
                2 => 1.0,
                _ => 0.0,
            },
            ..Climate::default()
        },
    );
    let report = compute_report(&synthetic_cli(&rows), &station_par(), None, None).unwrap();
    let january = &report.interannual.as_ref().unwrap().monthly.jan;

    assert_eq!(january.trace_wet_day_count.n_years, 1);
    assert_close(january.trace_wet_day_count.mean, 2.0);
    assert_close(january.r1mm_wet_day_count.mean, 1.0);
    assert_close(january.trace_wet_day_mean_amount_mm.mean, 0.75);
    assert_close(january.r1mm_wet_day_mean_amount_mm.mean, 1.0);

    let structure = &report.tails.precipitation_structure;
    assert_eq!(structure.trace_positive.wet_day_amount_mm.n, 2);
    assert_close(structure.trace_positive.wet_day_amount_mm.mean, 0.75);
    assert_eq!(structure.r1mm.wet_day_amount_mm.n, 1);
    assert_close(structure.r1mm.wet_day_amount_mm.mean, 1.0);
    assert_close(structure.trace_positive.wet_spells_days.whole_run.max, 2.0);
    assert_close(structure.r1mm.wet_spells_days.whole_run.max, 1.0);
}

#[test]
fn spells_and_rolling_extremes_cross_the_year_boundary() {
    let rows = rows_between(
        Date {
            year: 2000,
            month: 12,
            day: 28,
        },
        Date {
            year: 2001,
            month: 1,
            day: 6,
        },
        |date| Climate {
            precip_mm: match (date.year, date.month, date.day) {
                (2000, 12, 30) => 1.0,
                (2000, 12, 31) => 2.0,
                (2001, 1, 1) => 3.0,
                (2001, 1, 2) => 4.0,
                (2001, 1, 4) => 5.0,
                _ => 0.0,
            },
            ..Climate::default()
        },
    );
    let report = compute_report(&synthetic_cli(&rows), &station_par(), None, None).unwrap();
    let wet_spells = &report
        .tails
        .precipitation_structure
        .trace_positive
        .wet_spells_days;
    assert_eq!(wet_spells.whole_run.n, 2);
    assert_close(wet_spells.whole_run.mean, 2.5);
    assert_close(wet_spells.whole_run.max, 4.0);
    assert_close(wet_spells.by_start_month.dec.max, 4.0);
    assert_close(wet_spells.by_start_month.jan.max, 1.0);

    let year_2000 = &report.tails.per_year[0];
    assert_close(year_2000.max_1_day_precip_mm, 2.0);
    assert_close(year_2000.max_3_day_precip_mm, 3.0);
    assert_eq!(year_2000.max_5_day_precip_mm, None);

    let year_2001 = &report.tails.per_year[1];
    assert_close(year_2001.max_1_day_precip_mm, 5.0);
    assert_close(year_2001.max_3_day_precip_mm, 9.0);
    assert_close(year_2001.max_5_day_precip_mm, 14.0);
}

#[test]
fn storm_descriptor_distributions_include_time_to_peak_and_peak_ratio() {
    let rows = rows_between(
        Date {
            year: 2001,
            month: 1,
            day: 1,
        },
        Date {
            year: 2001,
            month: 1,
            day: 5,
        },
        |date| match date.day {
            1 => Climate {
                precip_mm: 1.0,
                duration_h: 1.0,
                time_to_peak: 0.1,
                peak_intensity_ratio: 1.0,
                ..Climate::default()
            },
            2 => Climate {
                precip_mm: 2.0,
                duration_h: 2.0,
                time_to_peak: 0.2,
                peak_intensity_ratio: 2.0,
                ..Climate::default()
            },
            3 => Climate {
                precip_mm: 3.0,
                duration_h: 0.0,
                time_to_peak: 1.3,
                peak_intensity_ratio: -3.0,
                ..Climate::default()
            },
            4 => Climate {
                precip_mm: 4.0,
                duration_h: 4.0,
                time_to_peak: 0.4,
                peak_intensity_ratio: 4.0,
                ..Climate::default()
            },
            _ => Climate::default(),
        },
    );
    let report = compute_report(&synthetic_cli(&rows), &station_par(), None, None).unwrap();
    report.validate().unwrap();
    let reparsed = QualityReport::parse_json(&report.to_json_bytes().unwrap()).unwrap();
    assert_eq!(reparsed, report);
    let descriptors = &report.tails.storm_descriptors;

    assert_eq!(descriptors.wet_event_days, 4);
    assert_eq!(descriptors.included_event_days, 3);
    assert_eq!(descriptors.excluded_event_days, 1);
    assert_eq!(descriptors.distributions.time_to_peak_fraction.n, 3);
    assert_close(
        descriptors.distributions.time_to_peak_fraction.mean,
        0.7 / 3.0,
    );
    assert_close(descriptors.distributions.time_to_peak_fraction.p50, 0.2);
    assert_close(descriptors.distributions.time_to_peak_fraction.p90, 0.4);
    assert_close(
        descriptors.distributions.peak_intensity_ratio.mean,
        7.0 / 3.0,
    );
    assert_close(descriptors.distributions.peak_intensity_ratio.max, 4.0);
    assert_close(descriptors.dependence.depth_time_to_peak.pearson, 1.0);
    assert_close(
        descriptors
            .dependence
            .time_to_peak_peak_intensity_ratio
            .spearman,
        1.0,
    );
}

#[test]
fn winter_proxy_counts_zero_threshold_transitions_without_claiming_phase() {
    let rows = rows_between(
        Date {
            year: 2001,
            month: 1,
            day: 1,
        },
        Date {
            year: 2001,
            month: 12,
            day: 31,
        },
        |date| {
            let mean_air = match (date.month, date.day) {
                (1, 2) => 0.0,
                (12, 31) => -1.0,
                _ => 1.0,
            };
            Climate {
                precip_mm: 0.0,
                tmax_c: mean_air + 1.0,
                tmin_c: mean_air - 1.0,
                ..Climate::default()
            }
        },
    );
    let report = compute_report(&synthetic_cli(&rows), &station_par(), None, None).unwrap();
    let winter = &report
        .covariation
        .as_ref()
        .unwrap()
        .winter_air_temperature_proxies;

    assert_eq!(winter.precipitation_on_freezing_air_days.fraction, None);
    assert_close(
        winter
            .precipitation_on_freezing_air_days
            .precipitation_on_freezing_air_days_mm,
        0.0,
    );
    assert_close(
        winter
            .precipitation_on_freezing_air_days
            .total_precipitation_mm,
        0.0,
    );
    assert_eq!(
        winter
            .precipitation_on_freezing_air_days
            .freezing_air_day_count,
        2
    );
    assert_eq!(winter.by_month.jan.freezing_air_day_count, 1);
    assert_eq!(winter.by_month.dec.freezing_air_day_count, 1);
    assert_eq!(winter.per_year.len(), 1);
    assert!(winter.per_year[0].complete_year);
    assert_eq!(
        winter.per_year[0].freeze_thaw_air_temperature_proxy_cycles,
        3
    );
    assert_close(winter.freeze_thaw_air_temperature_proxy_cycles.mean, 3.0);
    assert_eq!(winter.freeze_thaw_air_temperature_proxy_cycles.n_years, 1);
    assert_eq!(winter.djf_r1mm_precip_mean_air_temperature.n, 0);
}

#[test]
fn four_year_vector_pins_dispersion_covariance_lag_and_spectral_power() {
    let rows = rows_between(
        Date {
            year: 2001,
            month: 1,
            day: 1,
        },
        Date {
            year: 2004,
            month: 12,
            day: 31,
        },
        |date| {
            let annual_state = if date.year % 2 == 1 { 1.0 } else { 2.0 };
            Climate {
                precip_mm: if date.month == 1 && date.day == 1 {
                    annual_state
                } else {
                    0.0
                },
                tmax_c: 10.0 + annual_state,
                tmin_c: annual_state,
                ..Climate::default()
            }
        },
    );
    let report = compute_report(&synthetic_cli(&rows), &station_par(), None, None).unwrap();
    assert_eq!(report.metrics_version, 3);
    let interannual = report.interannual.as_ref().unwrap();

    let expected_sd = (1.0f64 / 3.0).sqrt();
    assert_eq!(interannual.annual.precip_total_mm.n_years, 4);
    assert_close(interannual.annual.precip_total_mm.mean, 1.5);
    assert_close(interannual.annual.precip_total_mm.sd, expected_sd);
    assert_close(interannual.annual.precip_total_mm.cv, expected_sd / 1.5);
    assert_eq!(interannual.monthly.jan.tmax_mean_c.n_years, 4);
    assert_close(interannual.monthly.jan.tmax_mean_c.mean, 11.5);
    assert_close(interannual.monthly.jan.tmax_mean_c.sd, expected_sd);

    let precip_dependence = &interannual.dependence.annual.precip_total_mm;
    assert_eq!(precip_dependence.n_years, 4);
    assert_eq!(precip_dependence.lag_one.n, 3);
    assert_close(precip_dependence.lag_one.pearson, -1.0);
    assert_close(precip_dependence.lag_one.spearman, -1.0);
    assert_close(precip_dependence.period_ge_4y_power_fraction, 0.0);

    let january = &interannual.dependence.precip_cross_month;
    assert_eq!(january.n_pairs[0][0], 4);
    assert_close(january.covariance[0][0], 1.0 / 3.0);
    assert_close(january.pearson_correlation[0][0], 1.0);
}
