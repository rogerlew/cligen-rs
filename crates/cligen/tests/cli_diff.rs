use std::error::Error;

use cligen::cli_diff::{
    diff_cli_files, diff_cli_text, CliDiff, CliDiffError, CliField, Divergence,
};

const BASE_CLI: &str = "\
5.32300
   1   0   0
  Station:  TEST
 Latitude Longitude Elevation (m) Obs. Years   Beginning year  Years simulated Command Line:
     1.00     2.00         100          40           1               1          -itest.par
 da mo year  prcp  dur   tp     ip  tmax  tmin  rad  w-vl w-dir  tdew
             (mm)  (h)               (C)   (C) (l/d) (m/s)(Deg)   (C)
  1  1     1   0.0  0.00 0.00   0.00  -6.1 -12.6 114.  4.0  277. -11.7
  2  1     1   2.6  6.13 0.06   1.01  -4.5 -11.5 138.  2.8   93.  -8.1
";

#[test]
fn self_diff_is_identical() {
    let diff = diff_cli_text(BASE_CLI, BASE_CLI).expect("valid fixture");

    assert_eq!(diff, CliDiff::Identical { daily_records: 2 });
    assert!(diff.is_identical());
}

#[test]
fn perturbation_reports_first_divergent_day_and_field() {
    let changed = BASE_CLI.replace("6.13", "6.14");
    let diff = diff_cli_text(BASE_CLI, &changed).expect("valid fixture");

    match diff {
        CliDiff::Divergent(Divergence::Field {
            row_index,
            expected_date,
            actual_date,
            field,
            expected,
            actual,
            ..
        }) => {
            assert_eq!(row_index, 2);
            assert_eq!(expected_date.day, 2);
            assert_eq!(actual_date.day, 2);
            assert_eq!(field, CliField::DurationH);
            assert_eq!(expected, "6.13");
            assert_eq!(actual, "6.14");
        }
        other => panic!("unexpected diff result: {other:?}"),
    }
}

#[test]
fn missing_actual_row_is_localized() {
    let shortened = BASE_CLI
        .lines()
        .take(BASE_CLI.lines().count() - 1)
        .collect::<Vec<_>>()
        .join("\n");

    let diff = diff_cli_text(BASE_CLI, &shortened).expect("valid fixture");

    match diff {
        CliDiff::Divergent(Divergence::MissingActualRow {
            row_index,
            expected_date,
            ..
        }) => {
            assert_eq!(row_index, 2);
            assert_eq!(expected_date.day, 2);
        }
        other => panic!("unexpected diff result: {other:?}"),
    }
}

#[test]
fn malformed_daily_row_fails_closed() {
    let malformed = BASE_CLI.replace("  2  1     1   2.6", "  2  1     1");
    let error = diff_cli_text(BASE_CLI, &malformed).expect_err("malformed row must fail");

    assert!(matches!(
        error,
        CliDiffError::MalformedDailyRow {
            line_number: 9,
            field_count: 12,
            ..
        }
    ));
}

#[test]
fn invalid_daily_value_fails_closed() {
    let malformed = BASE_CLI.replace("138.", "bad");
    let error = diff_cli_text(BASE_CLI, &malformed).expect_err("bad value must fail");

    assert!(matches!(
        error,
        CliDiffError::InvalidNumericField {
            line_number: 9,
            field: CliField::SolarLangleyDay,
            ..
        }
    ));
}

#[test]
fn missing_header_and_empty_table_errors_are_reported() {
    let missing_header = diff_cli_text("5.32300\n", BASE_CLI).expect_err("header is required");
    assert_eq!(missing_header.to_string(), "missing `.cli` daily header");

    let empty_table = "\
5.32300
 da mo year  prcp  dur   tp     ip  tmax  tmin  rad  w-vl w-dir  tdew
             (mm)  (h)               (C)   (C) (l/d) (m/s)(Deg)   (C)
";
    let empty_error = diff_cli_text(BASE_CLI, empty_table).expect_err("rows are required");
    assert_eq!(
        empty_error.to_string(),
        "daily header found but no daily rows parsed"
    );
}

#[test]
fn missing_units_line_error_is_reported() {
    let missing_units = "\
5.32300
 da mo year  prcp  dur   tp     ip  tmax  tmin  rad  w-vl w-dir  tdew";

    let error = diff_cli_text(BASE_CLI, missing_units).expect_err("units line is required");

    assert_eq!(
        error.to_string(),
        "missing units line after daily header at line 2"
    );
}

#[test]
fn file_read_error_keeps_io_source() {
    let error = diff_cli_files("/definitely/not/a/cligen/file.cli", "/also/missing.cli")
        .expect_err("missing file must fail");

    assert!(error.source().is_some());
    assert!(error
        .to_string()
        .contains("/definitely/not/a/cligen/file.cli"));
}
