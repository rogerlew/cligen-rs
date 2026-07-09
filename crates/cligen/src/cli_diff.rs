//! Field-wise differ for CLIGEN `.cli` fixture outputs.
//!
//! The differ is a harness tool specified by
//! `docs/specifications/SPEC-CLI-DIFF.md`. It validates the daily table
//! shape and reports the first divergent daily field.

use std::error::Error;
use std::fmt;
use std::fs;
use std::path::{Path, PathBuf};

const FIELD_COUNT: usize = 13;

/// One daily-table field in a `.cli` row.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
#[repr(usize)]
pub enum CliField {
    Day,
    Month,
    Year,
    PrecipMm,
    DurationH,
    TimeToPeak,
    PeakIntensity,
    TmaxC,
    TminC,
    SolarLangleyDay,
    WindVelocityMS,
    WindDirectionDeg,
    TdewC,
}

const FIELDS: [CliField; FIELD_COUNT] = [
    CliField::Day,
    CliField::Month,
    CliField::Year,
    CliField::PrecipMm,
    CliField::DurationH,
    CliField::TimeToPeak,
    CliField::PeakIntensity,
    CliField::TmaxC,
    CliField::TminC,
    CliField::SolarLangleyDay,
    CliField::WindVelocityMS,
    CliField::WindDirectionDeg,
    CliField::TdewC,
];

const FIELD_NAMES: [&str; FIELD_COUNT] = [
    "day",
    "month",
    "year",
    "precip_mm",
    "duration_h",
    "time_to_peak",
    "peak_intensity",
    "tmax_c",
    "tmin_c",
    "solar_langley_day",
    "wind_velocity_m_s",
    "wind_direction_deg",
    "tdew_c",
];

impl CliField {
    /// Stable field name used in differ reports.
    #[must_use]
    pub fn name(self) -> &'static str {
        FIELD_NAMES[self as usize]
    }
}

impl fmt::Display for CliField {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.name())
    }
}

/// Date key from a daily `.cli` row.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CliDate {
    pub day: i32,
    pub month: i32,
    pub year: i32,
}

impl fmt::Display for CliDate {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{:04}-{:02}-{:02}", self.year, self.month, self.day)
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
struct CliRecord {
    line_number: usize,
    date: CliDate,
    fields: [String; FIELD_COUNT],
}

#[derive(Clone, Debug, Eq, PartialEq)]
struct CliFile {
    records: Vec<CliRecord>,
}

/// Result of comparing two `.cli` files.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum CliDiff {
    Identical { daily_records: usize },
    Divergent(Divergence),
}

impl CliDiff {
    /// Returns true when no daily-field divergence was found.
    #[must_use]
    pub fn is_identical(&self) -> bool {
        matches!(self, Self::Identical { .. })
    }
}

/// First divergence found between two `.cli` daily tables.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum Divergence {
    Field {
        row_index: usize,
        expected_line: usize,
        actual_line: usize,
        expected_date: CliDate,
        actual_date: CliDate,
        field: CliField,
        expected: String,
        actual: String,
    },
    MissingActualRow {
        row_index: usize,
        expected_line: usize,
        expected_date: CliDate,
    },
    ExtraActualRow {
        row_index: usize,
        actual_line: usize,
        actual_date: CliDate,
    },
}

impl fmt::Display for Divergence {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Field {
                row_index,
                expected_line,
                actual_line,
                expected_date,
                actual_date,
                field,
                expected,
                actual,
            } => write!(
                f,
                "first divergence at row {row_index}: field {field}, expected {expected} \
                 on {expected_date} line {expected_line}, actual {actual} on {actual_date} \
                 line {actual_line}"
            ),
            Self::MissingActualRow {
                row_index,
                expected_line,
                expected_date,
            } => write!(
                f,
                "first divergence at row {row_index}: actual file is missing expected \
                 row for {expected_date} from line {expected_line}"
            ),
            Self::ExtraActualRow {
                row_index,
                actual_line,
                actual_date,
            } => write!(
                f,
                "first divergence at row {row_index}: actual file has extra row for \
                 {actual_date} on line {actual_line}"
            ),
        }
    }
}

/// Errors raised while parsing or reading `.cli` files.
#[derive(Debug)]
pub enum CliDiffError {
    Io {
        path: PathBuf,
        source: std::io::Error,
    },
    MissingDailyHeader,
    MissingUnitsLine {
        header_line: usize,
    },
    NoDailyRecords,
    MalformedDailyRow {
        line_number: usize,
        field_count: usize,
        line: String,
    },
    InvalidNumericField {
        line_number: usize,
        field: CliField,
        value: String,
    },
}

impl fmt::Display for CliDiffError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Io { path, source } => write!(f, "{}: {source}", path.display()),
            Self::MissingDailyHeader => f.write_str("missing `.cli` daily header"),
            Self::MissingUnitsLine { header_line } => {
                write!(
                    f,
                    "missing units line after daily header at line {header_line}"
                )
            }
            Self::NoDailyRecords => f.write_str("daily header found but no daily rows parsed"),
            Self::MalformedDailyRow {
                line_number,
                field_count,
                line,
            } => write!(
                f,
                "malformed daily row at line {line_number}: expected {FIELD_COUNT} fields, \
                 found {field_count}: {line}"
            ),
            Self::InvalidNumericField {
                line_number,
                field,
                value,
            } => write!(
                f,
                "invalid numeric field at line {line_number}, field {field}: {value}"
            ),
        }
    }
}

impl Error for CliDiffError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            Self::Io { source, .. } => Some(source),
            Self::MissingDailyHeader
            | Self::MissingUnitsLine { .. }
            | Self::NoDailyRecords
            | Self::MalformedDailyRow { .. }
            | Self::InvalidNumericField { .. } => None,
        }
    }
}

/// Compare two `.cli` files read from disk.
///
/// # Errors
///
/// Returns an error if either file cannot be read or either `.cli` daily
/// table is malformed.
pub fn diff_cli_files(
    expected_path: impl AsRef<Path>,
    actual_path: impl AsRef<Path>,
) -> Result<CliDiff, CliDiffError> {
    let expected_path = expected_path.as_ref();
    let actual_path = actual_path.as_ref();
    let expected = read_cli_file(expected_path)?;
    let actual = read_cli_file(actual_path)?;
    diff_cli_text(&expected, &actual)
}

/// Compare two `.cli` texts.
///
/// # Errors
///
/// Returns an error if either `.cli` daily table is malformed.
pub fn diff_cli_text(expected: &str, actual: &str) -> Result<CliDiff, CliDiffError> {
    let expected = parse_cli(expected)?;
    let actual = parse_cli(actual)?;
    Ok(compare_cli(&expected, &actual))
}

fn read_cli_file(path: &Path) -> Result<String, CliDiffError> {
    fs::read_to_string(path).map_err(|source| CliDiffError::Io {
        path: path.to_path_buf(),
        source,
    })
}

fn parse_cli(text: &str) -> Result<CliFile, CliDiffError> {
    let lines: Vec<&str> = text.lines().collect();
    let data_start = find_data_start(&lines)?;
    let mut records = Vec::new();

    for (line_index, line) in lines.iter().enumerate().skip(data_start) {
        if line.trim().is_empty() {
            continue;
        }
        records.push(parse_record(line_index + 1, line)?);
    }

    if records.is_empty() {
        return Err(CliDiffError::NoDailyRecords);
    }

    Ok(CliFile { records })
}

fn find_data_start(lines: &[&str]) -> Result<usize, CliDiffError> {
    for (line_index, line) in lines.iter().enumerate() {
        if is_daily_header(line) {
            if line_index + 1 >= lines.len() {
                return Err(CliDiffError::MissingUnitsLine {
                    header_line: line_index + 1,
                });
            }
            return Ok(line_index + 2);
        }
    }
    Err(CliDiffError::MissingDailyHeader)
}

fn is_daily_header(line: &str) -> bool {
    let mut fields = line.split_whitespace();
    matches!(
        (fields.next(), fields.next(), fields.next()),
        (Some("da"), Some("mo"), Some("year"))
    )
}

fn parse_record(line_number: usize, line: &str) -> Result<CliRecord, CliDiffError> {
    let tokens: Vec<String> = line.split_whitespace().map(str::to_owned).collect();
    let field_count = tokens.len();
    let fields: [String; FIELD_COUNT] = match tokens.try_into() {
        Ok(fields) => fields,
        Err(tokens) => {
            return Err(CliDiffError::MalformedDailyRow {
                line_number,
                field_count: tokens.len(),
                line: line.to_owned(),
            });
        }
    };

    validate_numeric_fields(line_number, &fields)?;
    let date = CliDate {
        day: parse_i32(line_number, CliField::Day, &fields[0])?,
        month: parse_i32(line_number, CliField::Month, &fields[1])?,
        year: parse_i32(line_number, CliField::Year, &fields[2])?,
    };

    debug_assert_eq!(field_count, FIELD_COUNT);
    Ok(CliRecord {
        line_number,
        date,
        fields,
    })
}

fn validate_numeric_fields(
    line_number: usize,
    fields: &[String; FIELD_COUNT],
) -> Result<(), CliDiffError> {
    for (index, value) in fields.iter().enumerate() {
        let field = FIELDS[index];
        if index < 3 {
            parse_i32(line_number, field, value)?;
        } else {
            parse_f64(line_number, field, value)?;
        }
    }
    Ok(())
}

fn parse_i32(line_number: usize, field: CliField, value: &str) -> Result<i32, CliDiffError> {
    value
        .parse::<i32>()
        .map_err(|_| invalid_numeric_field(line_number, field, value))
}

fn parse_f64(line_number: usize, field: CliField, value: &str) -> Result<f64, CliDiffError> {
    value
        .parse::<f64>()
        .map_err(|_| invalid_numeric_field(line_number, field, value))
}

fn invalid_numeric_field(line_number: usize, field: CliField, value: &str) -> CliDiffError {
    CliDiffError::InvalidNumericField {
        line_number,
        field,
        value: value.to_owned(),
    }
}

fn compare_cli(expected: &CliFile, actual: &CliFile) -> CliDiff {
    let shared_len = expected.records.len().min(actual.records.len());

    for row_index in 0..shared_len {
        let expected_record = &expected.records[row_index];
        let actual_record = &actual.records[row_index];
        if let Some(divergence) = compare_record(row_index + 1, expected_record, actual_record) {
            return CliDiff::Divergent(divergence);
        }
    }

    compare_lengths(expected, actual, shared_len)
}

fn compare_record(
    row_index: usize,
    expected: &CliRecord,
    actual: &CliRecord,
) -> Option<Divergence> {
    for (field_index, field) in FIELDS.iter().copied().enumerate() {
        let expected_value = &expected.fields[field_index];
        let actual_value = &actual.fields[field_index];
        if expected_value != actual_value {
            return Some(Divergence::Field {
                row_index,
                expected_line: expected.line_number,
                actual_line: actual.line_number,
                expected_date: expected.date.clone(),
                actual_date: actual.date.clone(),
                field,
                expected: expected_value.clone(),
                actual: actual_value.clone(),
            });
        }
    }
    None
}

fn compare_lengths(expected: &CliFile, actual: &CliFile, shared_len: usize) -> CliDiff {
    if let Some(record) = expected.records.get(shared_len) {
        CliDiff::Divergent(Divergence::MissingActualRow {
            row_index: shared_len + 1,
            expected_line: record.line_number,
            expected_date: record.date.clone(),
        })
    } else if let Some(record) = actual.records.get(shared_len) {
        CliDiff::Divergent(Divergence::ExtraActualRow {
            row_index: shared_len + 1,
            actual_line: record.line_number,
            actual_date: record.date.clone(),
        })
    } else {
        CliDiff::Identical {
            daily_records: expected.records.len(),
        }
    }
}
