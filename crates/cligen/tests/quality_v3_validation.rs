//! Metrics-v3 quality-report schema and public-DTO fail-closed gates.

use std::path::{Path, PathBuf};
use std::sync::OnceLock;

use cligen::quality::report::{CapGiveUp, CounterfactualMetrics, Months};
use cligen::quality::{compute_report, QualityError, QualityReport};
use cligen::runspec::RunspecDocument;
use serde_json::Value;

const DAILY_HEADER: &str = " da mo year  prcp  dur   tp     ip  tmax  tmin  rad  w-vl w-dir  tdew\n             (mm)  (h)               (C)   (C) (l/d) (m/s)(Deg)   (C)\n";

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .unwrap()
}

fn par_bytes() -> Vec<u8> {
    std::fs::read(repo_root().join("fixtures/new-meadows-id/id106388.par")).unwrap()
}

fn two_day_report() -> QualityReport {
    static REPORT: OnceLock<QualityReport> = OnceLock::new();
    REPORT
        .get_or_init(|| {
            let cli = format!(
                "5.32300\nquality validation vector\n{DAILY_HEADER}\
                  1  1  2001   1.0  1.00 0.25   1.50  10.0   0.0 200.  3.0  180.   0.0\n\
                  2  1  2001   2.0  2.00 0.75   2.50  11.0   1.0 200.  3.0  180.   0.0\n"
            );
            compute_report(&cli, &par_bytes(), None, None).unwrap()
        })
        .clone()
}

fn qc_off_report() -> QualityReport {
    static REPORT: OnceLock<QualityReport> = OnceLock::new();
    REPORT
        .get_or_init(|| {
            let document = RunspecDocument::parse(
                "cligen_runspec: 1\n\
                 station: { par: fixtures/new-meadows-id/id106388.par }\n\
                 mode: continuous\n\
                 simulation: { begin_year: 1, years: 1 }\n\
                 qc_filter: off\n\
                 output: { cli: target/a5a-counterfactual-vector.cli }\n",
            )
            .unwrap();
            document
                .resolve(&repo_root())
                .unwrap()
                .generate_quality_report()
                .unwrap()
        })
        .clone()
}

fn faithful_report() -> QualityReport {
    static REPORT: OnceLock<QualityReport> = OnceLock::new();
    REPORT
        .get_or_init(|| {
            let document = RunspecDocument::parse(
                "cligen_runspec: 1\n\
                 station: { par: fixtures/new-meadows-id/id106388.par }\n\
                 mode: continuous\n\
                 simulation: { begin_year: 1, years: 1 }\n\
                 output: { cli: target/a5a-faithful-validation.cli }\n",
            )
            .unwrap();
            document
                .resolve(&repo_root())
                .unwrap()
                .generate_quality_report()
                .unwrap()
        })
        .clone()
}

fn two_year_report() -> QualityReport {
    static REPORT: OnceLock<QualityReport> = OnceLock::new();
    REPORT
        .get_or_init(|| {
            let document = RunspecDocument::parse(
                "cligen_runspec: 1\n\
                 station: { par: fixtures/new-meadows-id/id106388.par }\n\
                 mode: continuous\n\
                 simulation: { begin_year: 1, years: 2 }\n\
                 qc_filter: off\n\
                 output: { cli: target/a5a-two-year-validation.cli }\n",
            )
            .unwrap();
            document
                .resolve(&repo_root())
                .unwrap()
                .generate_quality_report()
                .unwrap()
        })
        .clone()
}

fn four_year_report() -> QualityReport {
    static REPORT: OnceLock<QualityReport> = OnceLock::new();
    REPORT
        .get_or_init(|| {
            let document = RunspecDocument::parse(
                "cligen_runspec: 1\n\
                 station: { par: fixtures/new-meadows-id/id106388.par }\n\
                 mode: continuous\n\
                 simulation: { begin_year: 1, years: 4 }\n\
                 qc_filter: off\n\
                 output: { cli: target/a5a-four-year-validation.cli }\n",
            )
            .unwrap();
            document
                .resolve(&repo_root())
                .unwrap()
                .generate_quality_report()
                .unwrap()
        })
        .clone()
}

fn month_mut<T>(months: &mut Months<T>, month: usize) -> &mut T {
    match month {
        0 => &mut months.jan,
        1 => &mut months.feb,
        2 => &mut months.mar,
        3 => &mut months.apr,
        4 => &mut months.may,
        5 => &mut months.jun,
        6 => &mut months.jul,
        7 => &mut months.aug,
        8 => &mut months.sep,
        9 => &mut months.oct,
        10 => &mut months.nov,
        11 => &mut months.dec,
        _ => panic!("month index out of range"),
    }
}

fn counterfactual(report: &mut QualityReport) -> &mut CounterfactualMetrics {
    report
        .process
        .as_mut()
        .unwrap()
        .counterfactual
        .as_mut()
        .unwrap()
}

fn validation_message(error: QualityError) -> String {
    match error {
        QualityError::Validation(message) => message,
        other => panic!("expected quality validation error, found {other}"),
    }
}

#[test]
fn valid_report_round_trips_through_published_schema() {
    let report = two_day_report();
    report.validate().unwrap();
    let bytes = report.to_json_bytes().unwrap();
    let reparsed = QualityReport::parse_json(&bytes).unwrap();
    assert_eq!(reparsed, report);
    assert_eq!(reparsed.to_json_bytes().unwrap(), bytes);
}

#[test]
fn parse_rejects_unknown_nested_members_and_duplicate_keys() {
    let report = two_day_report();
    let mut value = serde_json::to_value(&report).unwrap();
    value["tails"]["storm_descriptors"]["dependence"]
        .as_object_mut()
        .unwrap()
        .insert("unversioned_metric".to_owned(), Value::from(1));
    let message = validation_message(
        QualityReport::parse_json(&serde_json::to_vec(&value).unwrap()).unwrap_err(),
    );
    assert!(message.contains("storm_descriptors") || message.contains("unversioned_metric"));

    let bytes = report.to_json_bytes().unwrap();
    let text = String::from_utf8(bytes).unwrap();
    let duplicated = text.replacen(
        "  \"metrics_version\": 3,",
        "  \"metrics_version\": 3,\n  \"metrics_version\": 3,",
        1,
    );
    let error = QualityReport::parse_json(duplicated.as_bytes()).unwrap_err();
    assert!(matches!(error, QualityError::Deserialize(_)));
    assert!(error.to_string().contains("duplicate object key"));
}

#[test]
fn schema_rejects_versions_correlations_and_fraction_summaries() {
    let mut report = two_day_report();
    report.metrics_version += 1;
    assert!(validation_message(report.validate().unwrap_err()).contains("metrics_version"));

    let mut report = two_day_report();
    let pair = &mut report.tails.storm_descriptors.dependence.depth_duration;
    pair.pearson = Some(1.01);
    pair.spearman = Some(1.01);
    assert!(validation_message(report.validate().unwrap_err()).contains("depth_duration"));

    let mut report = two_day_report();
    report
        .tails
        .storm_descriptors
        .distributions
        .time_to_peak_fraction
        .max = Some(1.01);
    assert!(validation_message(report.validate().unwrap_err()).contains("time_to_peak_fraction"));
}

#[test]
fn mutable_dto_rejects_nonfinite_values_before_json_coercion() {
    let mut report = two_day_report();
    report.tails.top_events[0].precip_mm = f64::NAN;
    let message = validation_message(report.validate().unwrap_err());
    assert!(message.contains("non-finite"));
    assert!(matches!(
        report.to_json_bytes(),
        Err(QualityError::Validation(_))
    ));
}

#[test]
fn relational_validation_rejects_count_and_identity_mismatches() {
    let mut report = two_day_report();
    report.tails.storm_descriptors.excluded_event_days += 1;
    let message = validation_message(report.validate().unwrap_err());
    assert!(message.contains("included_event_days + excluded_event_days"));

    let mut report = two_day_report();
    report.identity.content.days += 1;
    let message = validation_message(report.validate().unwrap_err());
    assert!(message.contains("sum of tails.per_year day counts"));

    let mut report = two_day_report();
    report
        .covariation
        .as_mut()
        .unwrap()
        .winter_air_temperature_proxies
        .per_year[0]
        .n_days += 1;
    let message = validation_message(report.validate().unwrap_err());
    assert!(message.contains("must match tails.per_year"));
}

#[test]
fn relational_validation_binds_content_identity_to_provenance() {
    let mut report = qc_off_report();
    report.identity.content.cli_sha256 = "0".repeat(64);
    let message = validation_message(report.validate().unwrap_err());
    assert!(message.contains("cli_sha256"), "{message}");
    assert!(message.contains("artifact.content_sha256"), "{message}");

    let mut report = qc_off_report();
    report.identity.content.station_parameter_set_sha256 = "0".repeat(64);
    let message = validation_message(report.validate().unwrap_err());
    assert!(
        message.contains("station_parameter_set_sha256"),
        "{message}"
    );

    let mut report = qc_off_report();
    report.identity.content.station_source_sha256 = "0".repeat(64);
    let message = validation_message(report.validate().unwrap_err());
    assert!(message.contains("station_source_sha256"), "{message}");

    let mut report = qc_off_report();
    report.identity.content.tool.push_str("-mutated");
    let message = validation_message(report.validate().unwrap_err());
    assert!(message.contains("identity.content.tool"), "{message}");
}

#[test]
fn relational_validation_derives_every_decade_vector_from_identity() {
    let mut report = two_day_report();
    report
        .par_convergence
        .as_mut()
        .unwrap()
        .precip_wet_mean_mm
        .by_decade
        .clear();
    let message = validation_message(report.validate().unwrap_err());
    assert!(message.contains("par_convergence.precip_wet_mean_mm.by_decade"));
    assert!(message.contains("exactly"), "{message}");

    let mut report = two_day_report();
    report.interannual.as_mut().unwrap().by_decade[0].start_year += 1;
    let message = validation_message(report.validate().unwrap_err());
    assert!(message.contains("interannual.by_decade[0].start_year"));
    assert!(message.contains("identity.content.span"), "{message}");

    let mut report = two_day_report();
    report.covariation.as_mut().unwrap().by_decade[0].n_years = 2;
    let message = validation_message(report.validate().unwrap_err());
    assert!(message.contains("covariation.by_decade[0].n_years"));
    assert!(message.contains("identity-derived"), "{message}");
}

#[test]
fn relational_validation_binds_month_matrices_to_monthly_sources() {
    let report = two_year_report();
    report.validate().unwrap();
    let monthly = &report.interannual.as_ref().unwrap().monthly;
    let sds = [
        monthly.jan.precip_total_mm.sd,
        monthly.feb.precip_total_mm.sd,
        monthly.mar.precip_total_mm.sd,
        monthly.apr.precip_total_mm.sd,
        monthly.may.precip_total_mm.sd,
        monthly.jun.precip_total_mm.sd,
        monthly.jul.precip_total_mm.sd,
        monthly.aug.precip_total_mm.sd,
        monthly.sep.precip_total_mm.sd,
        monthly.oct.precip_total_mm.sd,
        monthly.nov.precip_total_mm.sd,
        monthly.dec.precip_total_mm.sd,
    ];
    let positive_variance = sds
        .iter()
        .position(|sd| sd.is_some_and(|value| value > 0.0))
        .expect("two-year validation vector must contain precipitation variance");

    let mut mutated = report.clone();
    let matrix = &mut mutated
        .interannual
        .as_mut()
        .unwrap()
        .dependence
        .precip_cross_month;
    matrix.n_pairs[0][1] += 1;
    matrix.n_pairs[1][0] += 1;
    let message = validation_message(mutated.validate().unwrap_err());
    assert!(message.contains("off-diagonal count"), "{message}");

    let mut mutated = report.clone();
    let matrix = &mut mutated
        .interannual
        .as_mut()
        .unwrap()
        .dependence
        .precip_cross_month;
    matrix.covariance[positive_variance][positive_variance] = None;
    let message = validation_message(mutated.validate().unwrap_err());
    assert!(message.contains("defined exactly"), "{message}");

    let mut mutated = report.clone();
    let matrix = &mut mutated
        .interannual
        .as_mut()
        .unwrap()
        .dependence
        .precip_cross_month;
    matrix.covariance[positive_variance][positive_variance] =
        Some(matrix.covariance[positive_variance][positive_variance].unwrap() + 1.0);
    let message = validation_message(mutated.validate().unwrap_err());
    assert!(message.contains("SD squared"), "{message}");

    let mut mutated = report;
    mutated
        .interannual
        .as_mut()
        .unwrap()
        .dependence
        .precip_cross_month
        .pearson_correlation[positive_variance][positive_variance] = None;
    let message = validation_message(mutated.validate().unwrap_err());
    assert!(message.contains("one exactly"), "{message}");
}

#[test]
fn relational_validation_pins_interannual_sample_counts() {
    let report = two_year_report();

    let mut mutated = report.clone();
    mutated.interannual.as_mut().unwrap().by_decade[0]
        .annual
        .trace_wet_day_count
        .n_years = 3;
    let message = validation_message(mutated.validate().unwrap_err());
    assert!(
        message.contains("by_decade[0].annual.trace_wet_day_count.n_years"),
        "{message}"
    );
    assert!(message.contains("enclosing decade"), "{message}");

    let mut mutated = report.clone();
    mutated.interannual.as_mut().unwrap().by_decade[0]
        .annual
        .tmax_mean_c
        .n_years = 3;
    let message = validation_message(mutated.validate().unwrap_err());
    assert!(
        message.contains("by_decade[0].annual.tmax_mean_c.n_years"),
        "{message}"
    );
    assert!(message.contains("enclosing decade"), "{message}");

    let mut mutated = report.clone();
    mutated
        .interannual
        .as_mut()
        .unwrap()
        .monthly
        .jan
        .tmin_mean_c
        .n_years = 3;
    let message = validation_message(mutated.validate().unwrap_err());
    assert!(
        message.contains("interannual.monthly.jan.tmin_mean_c.n_years"),
        "{message}"
    );
    assert!(message.contains("represented years"), "{message}");

    let mut mutated = report.clone();
    let january = &mut mutated.interannual.as_mut().unwrap().monthly.jan;
    january.precip_total_mm.n_years = 1;
    january.precip_total_mm.sd = None;
    january.precip_total_mm.cv = None;
    let message = validation_message(mutated.validate().unwrap_err());
    assert!(
        message.contains("interannual.monthly.jan.trace_wet_day_count.n_years"),
        "{message}"
    );
    assert!(message.contains("complete-month source count"), "{message}");

    let mut mutated = report.clone();
    let trace_count = &mut mutated
        .interannual
        .as_mut()
        .unwrap()
        .monthly
        .jan
        .trace_wet_day_count;
    trace_count.n_years = 1;
    trace_count.sd = None;
    trace_count.cv = None;
    let message = validation_message(mutated.validate().unwrap_err());
    assert!(
        message.contains("interannual.monthly.jan.trace_wet_day_count.n_years"),
        "{message}"
    );
    assert!(message.contains("must equal"), "{message}");

    let mut mutated = report.clone();
    let tmax = &mut mutated
        .interannual
        .as_mut()
        .unwrap()
        .monthly
        .jan
        .tmax_mean_c;
    tmax.n_years = 1;
    tmax.sd = None;
    let message = validation_message(mutated.validate().unwrap_err());
    assert!(
        message.contains("interannual.monthly.jan.tmax_mean_c.n_years"),
        "{message}"
    );
    assert!(message.contains("must equal"), "{message}");

    let mut optional = report.clone();
    let wet_mean = &mut optional
        .interannual
        .as_mut()
        .unwrap()
        .monthly
        .jan
        .trace_wet_day_mean_amount_mm;
    assert_eq!(wet_mean.n_years, 2);
    wet_mean.n_years = 1;
    wet_mean.sd = None;
    wet_mean.cv = None;
    optional.validate().unwrap();

    let mut mutated = report;
    mutated.interannual.as_mut().unwrap().by_decade[0]
        .monthly
        .feb
        .trace_wet_day_count
        .n_years = 3;
    let message = validation_message(mutated.validate().unwrap_err());
    assert!(
        message.contains("by_decade[0].monthly.feb.trace_wet_day_count.n_years"),
        "{message}"
    );
    assert!(message.contains("represented years"), "{message}");
}

#[test]
fn relational_validation_aligns_cross_variable_pair_counts() {
    let report = two_year_report();

    let mut mutated = report.clone();
    mutated
        .interannual
        .as_mut()
        .unwrap()
        .dependence
        .cross_variable_by_month
        .jan
        .precip_tmax
        .n = 3;
    let message = validation_message(mutated.validate().unwrap_err());
    assert!(message.contains("cross_variable_by_month.jan.precip_tmax.n"));
    assert!(
        message.contains("participating monthly source"),
        "{message}"
    );

    let mut mutated = report.clone();
    let pair = &mut mutated
        .interannual
        .as_mut()
        .unwrap()
        .dependence
        .cross_variable_by_month
        .jan
        .precip_tmax;
    pair.n = 1;
    pair.pearson = None;
    pair.spearman = None;
    let message = validation_message(mutated.validate().unwrap_err());
    assert!(message.contains("cross_variable_by_month.jan.precip_tmax.n"));
    assert!(message.contains("must equal"), "{message}");

    let mut mutated = report.clone();
    mutated
        .interannual
        .as_mut()
        .unwrap()
        .dependence
        .cross_variable_by_month
        .jan
        .precip_tmin
        .n = 3;
    let message = validation_message(mutated.validate().unwrap_err());
    assert!(message.contains("cross_variable_by_month.jan.precip_tmin.n"));
    assert!(
        message.contains("participating monthly source"),
        "{message}"
    );

    let mut mutated = report;
    mutated
        .interannual
        .as_mut()
        .unwrap()
        .dependence
        .cross_variable_by_month
        .jan
        .tmax_tmin
        .n = 3;
    let message = validation_message(mutated.validate().unwrap_err());
    assert!(message.contains("cross_variable_by_month.jan.tmax_tmin.n"));
    assert!(
        message.contains("participating monthly source"),
        "{message}"
    );
}

#[test]
fn relational_validation_pins_annual_dependence_samples_and_power() {
    let mut two_years = two_year_report();
    let lag_one = &mut two_years
        .interannual
        .as_mut()
        .unwrap()
        .dependence
        .annual
        .precip_total_mm
        .lag_one;
    assert_eq!(lag_one.n, 1);
    lag_one.n = 0;
    let message = validation_message(two_years.validate().unwrap_err());
    assert!(message.contains("annual.precip_total_mm.lag_one.n"));
    assert!(message.contains("must equal n_years - 1"), "{message}");

    let report = four_year_report();
    report.validate().unwrap();
    let interannual = report.interannual.as_ref().unwrap();
    assert!(interannual
        .annual
        .precip_total_mm
        .sd
        .is_some_and(|sd| sd > 0.0));
    assert!(interannual
        .dependence
        .annual
        .precip_total_mm
        .period_ge_4y_power_fraction
        .is_some());

    let mut missing_power = report.clone();
    missing_power
        .interannual
        .as_mut()
        .unwrap()
        .dependence
        .annual
        .precip_total_mm
        .period_ge_4y_power_fraction = None;
    let message = validation_message(missing_power.validate().unwrap_err());
    assert!(message.contains("period_ge_4y_power_fraction"));
    assert!(
        message.contains("positive annual-series variance"),
        "{message}"
    );

    let mut premature_power = two_year_report();
    premature_power
        .interannual
        .as_mut()
        .unwrap()
        .dependence
        .annual
        .precip_total_mm
        .period_ge_4y_power_fraction = Some(0.0);
    let message = validation_message(premature_power.validate().unwrap_err());
    assert!(message.contains("period_ge_4y_power_fraction"));
    assert!(message.contains("n_years >= 4"), "{message}");

    let mut spurious_power = report.clone();
    spurious_power
        .interannual
        .as_mut()
        .unwrap()
        .annual
        .tmax_mean_c
        .sd = Some(0.0);
    let message = validation_message(spurious_power.validate().unwrap_err());
    assert!(message.contains("annual.tmax_mean_c.period_ge_4y_power_fraction"));
    assert!(
        message.contains("positive annual-series variance"),
        "{message}"
    );

    let mut zero_variance = report;
    let interannual = zero_variance.interannual.as_mut().unwrap();
    interannual.annual.tmax_mean_c.sd = Some(0.0);
    let tmax_power = &mut interannual
        .dependence
        .annual
        .tmax_mean_c
        .period_ge_4y_power_fraction;
    assert!(tmax_power.is_some());
    *tmax_power = None;
    zero_variance.validate().unwrap();
}

#[test]
fn schema_rejects_bad_distribution_state_and_matrix_shape() {
    let mut report = two_day_report();
    let distribution = &mut report.tails.storm_descriptors.distributions.depth_mm;
    distribution.n = 0;
    let message = validation_message(report.validate().unwrap_err());
    assert!(message.contains("depth_mm"));

    let mut report = two_day_report();
    report
        .interannual
        .as_mut()
        .unwrap()
        .dependence
        .precip_cross_month
        .covariance
        .pop();
    let message = validation_message(report.validate().unwrap_err());
    assert!(message.contains("precip_cross_month") || message.contains("covariance"));
}

#[test]
fn relational_validation_rejects_asymmetric_matrix_and_non_gregorian_event() {
    let mut report = two_day_report();
    let matrix = &mut report
        .interannual
        .as_mut()
        .unwrap()
        .dependence
        .precip_cross_month;
    matrix.n_pairs[0][1] = 2;
    matrix.n_pairs[1][0] = 2;
    matrix.covariance[0][1] = Some(1.0);
    matrix.covariance[1][0] = Some(2.0);
    let message = validation_message(report.validate().unwrap_err());
    assert!(message.contains("symmetric"));

    let mut report = two_day_report();
    report.tails.top_events[0].year = 2001;
    report.tails.top_events[0].month = 2;
    report.tails.top_events[0].day = 29;
    let message = validation_message(report.validate().unwrap_err());
    assert!(message.contains("event date must be valid"));

    let storm = format!(
        "5.32300\nsource-calendar storm vector\n{DAILY_HEADER}\
         29  2  1900   1.0  1.00 0.50   1.50  10.0   0.0 200.  3.0  180.   0.0\n"
    );
    let single_storm = compute_report(&storm, &par_bytes(), None, None).unwrap();
    single_storm.validate().unwrap();
}

#[test]
fn counterfactual_validation_accepts_generated_qc_off_counts() {
    let report = qc_off_report();
    report.validate().unwrap();

    let process = report.process.as_ref().unwrap();
    let counts = process.counterfactual.as_ref().unwrap();
    assert_eq!(counts.by_parameter.len(), 9);
    assert!(counts.would_reject <= counts.batches);
}

#[test]
fn process_validation_binds_acceptance_records_to_retry_cells() {
    let report = faithful_report();
    report.validate().unwrap();
    let first = report.process.as_ref().unwrap().acceptance_statistics[0].clone();
    let parameter = usize::try_from(first.parameter - 1).unwrap();
    let month = usize::try_from(first.month - 1).unwrap();
    let other_month = (month + 1) % 12;

    let mut mutated = report.clone();
    let retries = &mut mutated.process.as_mut().unwrap().retries[parameter];
    *month_mut(&mut retries.accepted_batches, month) -= 1;
    *month_mut(&mut retries.accepted_batches, other_month) += 1;
    let message = validation_message(mutated.validate().unwrap_err());
    assert!(message.contains("accepted_batches"), "{message}");
    assert!(message.contains("parameter and month"), "{message}");

    let mut mutated = report.clone();
    mutated
        .process
        .as_mut()
        .unwrap()
        .acceptance_statistics
        .pop();
    let message = validation_message(mutated.validate().unwrap_err());
    assert!(message.contains("accepted_batches total"), "{message}");

    let mut mutated = report;
    mutated.process.as_mut().unwrap().acceptance_statistics[0].year =
        mutated.identity.content.span[1] + 1;
    let message = validation_message(mutated.validate().unwrap_err());
    assert!(
        message.contains("acceptance_statistics[0].year"),
        "{message}"
    );
    assert!(message.contains("identity.content.span"), "{message}");
}

#[test]
fn process_validation_binds_profile_and_cap_event_span() {
    let mut report = qc_off_report();
    report.process.as_mut().unwrap().qc_filter = Some("faithful".to_owned());
    let message = validation_message(report.validate().unwrap_err());
    assert!(message.contains("qc"), "{message}");

    let mut report = qc_off_report();
    report.process.as_mut().unwrap().retries[0]
        .rejected_attempts
        .jan = 1;
    let message = validation_message(report.validate().unwrap_err());
    assert!(message.contains("unconditioned generation"), "{message}");

    let mut report = faithful_report();
    report
        .process
        .as_mut()
        .unwrap()
        .cap_give_ups
        .push(CapGiveUp {
            parameter: 1,
            month: 1,
            year: report.identity.content.span[1] + 1,
        });
    let message = validation_message(report.validate().unwrap_err());
    assert!(message.contains("cap_give_ups"), "{message}");
    assert!(message.contains("identity.content.span"), "{message}");
}

#[test]
fn public_count_sums_fail_closed_on_overflow() {
    let mut report = faithful_report();
    let retries = &mut report.process.as_mut().unwrap().retries[0];
    retries.accepted_batches = Months::from_fn(|_| 0);
    retries.accepted_batches.jan = u64::MAX;
    retries.accepted_batches.feb = 1;
    let message = validation_message(report.validate().unwrap_err());
    assert!(message.contains("process.retries[0]"), "{message}");
    assert!(message.contains("count overflow"), "{message}");

    let mut report = qc_off_report();
    let by_month = &mut report
        .covariation
        .as_mut()
        .unwrap()
        .winter_air_temperature_proxies
        .by_month;
    by_month.jan.n_days = u64::MAX;
    let message = validation_message(report.validate().unwrap_err());
    assert!(message.contains("winter_air_temperature_proxies.by_month"));
    assert!(message.contains("count overflow"), "{message}");
}

#[test]
fn counterfactual_validation_rejects_bad_parameter_order_and_month_count() {
    let mut report = qc_off_report();
    counterfactual(&mut report).by_parameter[0].parameter = 2;
    let message = validation_message(report.validate().unwrap_err());
    assert!(message.contains("by_parameter[0].parameter"), "{message}");

    let mut report = qc_off_report();
    let parameter = &mut counterfactual(&mut report).by_parameter[0];
    parameter.batches.jan = 0;
    parameter.would_reject.jan = 1;
    let message = validation_message(report.validate().unwrap_err());
    assert!(message.contains("would_reject.jan"), "{message}");
    assert!(message.contains("cannot exceed batches"), "{message}");
}

#[test]
fn counterfactual_validation_rejects_batch_overflow_and_stale_totals() {
    let mut report = qc_off_report();
    let counts = counterfactual(&mut report);
    for parameter in &mut counts.by_parameter {
        parameter.batches = Months::from_fn(|_| 0);
        parameter.would_reject = Months::from_fn(|_| 0);
    }
    counts.by_parameter[0].batches.jan = u64::MAX;
    counts.by_parameter[0].batches.feb = 1;
    let message = validation_message(report.validate().unwrap_err());
    assert!(message.contains("by_parameter[0]"), "{message}");
    assert!(message.contains("count overflow"), "{message}");

    let mut report = qc_off_report();
    let counts = counterfactual(&mut report);
    for parameter in &mut counts.by_parameter {
        parameter.batches = Months::from_fn(|_| 0);
        parameter.would_reject = Months::from_fn(|_| 0);
    }
    counts.by_parameter[0].batches.jan = u64::MAX;
    counts.by_parameter[1].batches.jan = 1;
    let message = validation_message(report.validate().unwrap_err());
    assert!(message.contains("by_parameter[1]"), "{message}");
    assert!(message.contains("batch count overflow"), "{message}");

    let mut report = qc_off_report();
    counterfactual(&mut report).batches += 1;
    let message = validation_message(report.validate().unwrap_err());
    assert!(message.contains("totals must equal"), "{message}");
}
