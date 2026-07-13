//! `.cli` daily-table intake for the quality instrument.
//!
//! Parses the WEPP-format daily table from `.cli` **text** — the
//! consumer surface SPEC-QUALITY-REPORT pins — into typed f64 rows.
//! This is a dedicated intake, not a reuse of [`crate::cli_diff`]:
//! the differ's contract is exact-token comparison (it retains field
//! lexemes), while this surface consumes parsed numeric values. Both
//! parsers assert the same 13-field daily-row shape from
//! SPEC-CLI-DIFF §Semantics; the adjudication is recorded in
//! `docs/work-packages/20260710-q1-quality-report/artifacts/estimator-adjudication.md`.

use std::error::Error;
use std::fmt;

/// One parsed daily `.cli` row (SPEC-CLI-DIFF field table, f64 view).
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct DailyValue {
    pub day: i32,
    pub month: i32,
    pub year: i32,
    pub precip_mm: f64,
    pub duration_h: f64,
    pub time_to_peak: f64,
    /// Printed `.cli ip`: peak/mean event-intensity ratio (`xmav`),
    /// dimensionless. Metrics v2 historically mislabeled this as an
    /// intensity; metrics v3 corrects the quality-only name.
    pub peak_intensity_ratio: f64,
    pub tmax_c: f64,
    pub tmin_c: f64,
    pub radiation_ly: f64,
    pub wind_speed_ms: f64,
    pub wind_direction_deg: f64,
    pub dewpoint_c: f64,
}

impl DailyValue {
    /// Wet-day predicate: positive printed precipitation.
    #[must_use]
    pub fn is_wet(&self) -> bool {
        self.precip_mm > 0.0
    }

    /// Observed-comparison wet-day predicate fixed by
    /// SPEC-OBSERVED-TARGET-CORPUS: daily precipitation at least 1 mm.
    #[must_use]
    pub fn is_r1mm(&self) -> bool {
        self.precip_mm >= 1.0
    }

    /// Arithmetic daily mean air temperature used only by the explicit
    /// winter climate proxy surface.
    #[must_use]
    pub fn mean_air_temperature_c(&self) -> f64 {
        (self.tmax_c + self.tmin_c) / 2.0
    }

    /// Chronological sort key.
    #[must_use]
    pub fn date_key(&self) -> (i32, i32, i32) {
        (self.year, self.month, self.day)
    }
}

/// The parsed daily table, rows in file order.
#[derive(Debug, Clone)]
pub struct CliTable {
    pub rows: Vec<DailyValue>,
}

/// Typed intake failure — fail closed, no inferred defaults.
#[derive(Debug)]
pub enum QualityIntakeError {
    /// No `da mo year` daily header line found.
    MissingDailyHeader,
    /// Header found but no units line follows.
    MissingUnitsLine { header_line: usize },
    /// Header and units found but zero daily rows parsed.
    NoDailyRecords,
    /// A non-empty daily row with a field count other than 13.
    MalformedDailyRow {
        line_number: usize,
        field_count: usize,
    },
    /// A field that does not parse as a finite number.
    InvalidNumericField {
        line_number: usize,
        field_index: usize,
        value: String,
    },
    /// Printed precipitation is finite but outside the physical input domain.
    NegativePrecipitation { line_number: usize, value: f64 },
    /// A date field outside its calendar domain.
    InvalidDate { line_number: usize },
    /// Row dates are not strictly increasing (the WEPP daily table is
    /// chronological; decade blocking depends on it).
    MisorderedRow { line_number: usize },
    /// A multi-row daily file contains a date that is invalid in the
    /// proleptic Gregorian calendar. The one-row storm exception retains
    /// the source storm calendar union documented by `max_source_day`.
    NonGregorianDailyDate { line_number: usize },
    /// Consecutive rows in a multi-row daily file are not adjacent calendar
    /// days. Metrics v3 refuses to bridge an unreported gap.
    DateGap {
        line_number: usize,
        expected: (i32, i32, i32),
        actual: (i32, i32, i32),
    },
}

impl fmt::Display for QualityIntakeError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::MissingDailyHeader => f.write_str("missing `.cli` daily header"),
            Self::MissingUnitsLine { header_line } => write!(
                f,
                "missing units line after daily header at line {header_line}"
            ),
            Self::NoDailyRecords => f.write_str("daily header found but no daily rows parsed"),
            Self::MalformedDailyRow {
                line_number,
                field_count,
            } => write!(
                f,
                "malformed daily row at line {line_number}: expected 13 fields, found {field_count}"
            ),
            Self::InvalidNumericField {
                line_number,
                field_index,
                value,
            } => write!(
                f,
                "invalid numeric field at line {line_number}, field {field_index}: {value:?}"
            ),
            Self::NegativePrecipitation { line_number, value } => write!(
                f,
                "negative precipitation at line {line_number}: {value} mm"
            ),
            Self::InvalidDate { line_number } => {
                write!(f, "invalid calendar date at line {line_number}")
            }
            Self::MisorderedRow { line_number } => write!(
                f,
                "daily row at line {line_number} is not after the preceding row"
            ),
            Self::NonGregorianDailyDate { line_number } => write!(
                f,
                "daily row at line {line_number} is not a Gregorian calendar date"
            ),
            Self::DateGap {
                line_number,
                expected,
                actual,
            } => write!(
                f,
                "daily row at line {line_number} is not the next calendar day: expected \
                 {:04}-{:02}-{:02}, found {:04}-{:02}-{:02}",
                expected.0, expected.1, expected.2, actual.0, actual.1, actual.2
            ),
        }
    }
}

impl Error for QualityIntakeError {}

/// Parse the daily table from `.cli` text.
///
/// # Errors
///
/// Fails closed on a missing daily header or units line, zero rows,
/// wrong field counts, non-finite numeric fields, negative precipitation,
/// invalid dates, and non-chronological rows.
pub fn parse_cli_table(text: &str) -> Result<CliTable, QualityIntakeError> {
    let lines: Vec<&str> = text.lines().collect();
    let data_start = find_data_start(&lines)?;
    let mut rows = Vec::new();
    let mut row_lines = Vec::new();
    for (line_index, line) in lines.iter().enumerate().skip(data_start) {
        if line.trim().is_empty() {
            continue;
        }
        let row = parse_row(line_index + 1, line)?;
        if let Some(previous) = rows.last() {
            let prev: &DailyValue = previous;
            if row.date_key() <= prev.date_key() {
                return Err(QualityIntakeError::MisorderedRow {
                    line_number: line_index + 1,
                });
            }
        }
        rows.push(row);
        row_lines.push(line_index + 1);
    }
    if rows.is_empty() {
        return Err(QualityIntakeError::NoDailyRecords);
    }
    validate_daily_calendar(&rows, &row_lines)?;
    Ok(CliTable { rows })
}

fn find_data_start(lines: &[&str]) -> Result<usize, QualityIntakeError> {
    for (line_index, line) in lines.iter().enumerate() {
        let mut fields = line.split_whitespace();
        if matches!(
            (fields.next(), fields.next(), fields.next()),
            (Some("da"), Some("mo"), Some("year"))
        ) {
            if line_index + 1 >= lines.len() {
                return Err(QualityIntakeError::MissingUnitsLine {
                    header_line: line_index + 1,
                });
            }
            return Ok(line_index + 2);
        }
    }
    Err(QualityIntakeError::MissingDailyHeader)
}

fn parse_row(line_number: usize, line: &str) -> Result<DailyValue, QualityIntakeError> {
    let tokens: Vec<&str> = line.split_whitespace().collect();
    if tokens.len() != 13 {
        return Err(QualityIntakeError::MalformedDailyRow {
            line_number,
            field_count: tokens.len(),
        });
    }
    let int = |index: usize| parse_i32(line_number, index, tokens[index]);
    let num = |index: usize| parse_finite_f64(line_number, index, tokens[index]);
    let row = DailyValue {
        day: int(0)?,
        month: int(1)?,
        year: int(2)?,
        precip_mm: num(3)?,
        duration_h: num(4)?,
        time_to_peak: num(5)?,
        peak_intensity_ratio: num(6)?,
        tmax_c: num(7)?,
        tmin_c: num(8)?,
        radiation_ly: num(9)?,
        wind_speed_ms: num(10)?,
        wind_direction_deg: num(11)?,
        dewpoint_c: num(12)?,
    };
    if !(1..=12).contains(&row.month)
        || row.day < 1
        || row.day > max_source_day(row.month, row.year)
    {
        return Err(QualityIntakeError::InvalidDate { line_number });
    }
    if row.precip_mm < 0.0 {
        return Err(QualityIntakeError::NegativePrecipitation {
            line_number,
            value: row.precip_mm,
        });
    }
    Ok(row)
}

fn validate_daily_calendar(
    rows: &[DailyValue],
    line_numbers: &[usize],
) -> Result<(), QualityIntakeError> {
    if rows.len() <= 1 {
        return Ok(());
    }
    for (index, row) in rows.iter().enumerate() {
        if row.day > max_gregorian_day(row.month, row.year) {
            return Err(QualityIntakeError::NonGregorianDailyDate {
                line_number: line_numbers[index],
            });
        }
        if index == 0 {
            continue;
        }
        let expected = next_gregorian_date(&rows[index - 1]).ok_or(
            QualityIntakeError::NonGregorianDailyDate {
                line_number: line_numbers[index - 1],
            },
        )?;
        let actual = (row.year, row.month, row.day);
        if actual != expected {
            return Err(QualityIntakeError::DateGap {
                line_number: line_numbers[index],
                expected,
                actual,
            });
        }
    }
    Ok(())
}

fn next_gregorian_date(row: &DailyValue) -> Option<(i32, i32, i32)> {
    if row.day < max_gregorian_day(row.month, row.year) {
        return Some((row.year, row.month, row.day + 1));
    }
    if row.month < 12 {
        return Some((row.year, row.month + 1, 1));
    }
    Some((row.year.checked_add(1)?, 1, 1))
}

/// Maximum valid day for a printed `.cli` month/year (C-R1-001).
///
/// A post-hoc surface cannot know the run mode, and the source has two
/// leap calendars over the printed year: the daily-mode Gregorian test
/// (`wxr_gen:3766-3770`) and the storm-mode `nt` test
/// (`wxr_gen:3758-3763`, leap exactly on century years). Their union —
/// the set of years for which some source mode emits February 29 — is
/// exactly `year % 4 == 0`: Gregorian contributes div-4-non-century
/// and div-400 years, the storm rule contributes every century year
/// (all divisible by 4). February 29 is therefore accepted iff the
/// printed year is divisible by 4; impossible days are rejected in
/// every month.
fn max_source_day(month: i32, year: i32) -> i32 {
    match month {
        2 => 28 + i32::from(year % 4 == 0),
        4 | 6 | 9 | 11 => 30,
        _ => 31,
    }
}

/// Gregorian month length used by multi-row daily quality intake and
/// complete-period aggregation.
#[must_use]
pub(crate) fn max_gregorian_day(month: i32, year: i32) -> i32 {
    match month {
        2 => {
            let leap = year % 4 == 0 && (year % 100 != 0 || year % 400 == 0);
            28 + i32::from(leap)
        }
        4 | 6 | 9 | 11 => 30,
        _ => 31,
    }
}

fn parse_i32(
    line_number: usize,
    field_index: usize,
    value: &str,
) -> Result<i32, QualityIntakeError> {
    value
        .parse::<i32>()
        .map_err(|_| QualityIntakeError::InvalidNumericField {
            line_number,
            field_index,
            value: value.to_owned(),
        })
}

fn parse_finite_f64(
    line_number: usize,
    field_index: usize,
    value: &str,
) -> Result<f64, QualityIntakeError> {
    let parsed = value
        .parse::<f64>()
        .map_err(|_| QualityIntakeError::InvalidNumericField {
            line_number,
            field_index,
            value: value.to_owned(),
        })?;
    if !parsed.is_finite() {
        return Err(QualityIntakeError::InvalidNumericField {
            line_number,
            field_index,
            value: value.to_owned(),
        });
    }
    Ok(parsed)
}

#[cfg(test)]
mod tests {
    use super::*;

    const HEADER: &str = " da mo year  prcp  dur   tp     ip  tmax  tmin  rad  w-vl w-dir  tdew\n             (mm)  (h)               (C)   (C) (l/d) (m/s)(Deg)   (C)\n";

    fn table(rows: &str) -> String {
        format!("5.32300\nheader filler\n{HEADER}{rows}")
    }

    #[test]
    fn fail_closed_errors_render_their_diagnostics() {
        let cases: [(String, &str); 7] = [
            (
                "no daily header at all\n".to_owned(),
                "missing `.cli` daily header",
            ),
            (
                " da mo year  prcp\n".to_owned(),
                "missing units line after daily header at line 1",
            ),
            (table(""), "no daily rows parsed"),
            (
                table("  1  1     1   0.0  0.00\n"),
                "expected 13 fields, found 5",
            ),
            (
                table("  1  1     1   inf  0.00 0.00   0.00  -6.1 -12.6 114.  4.0  277. -11.7\n"),
                "invalid numeric field at line 5, field 3",
            ),
            (
                table("  1  1     1  -0.1  0.00 0.00   0.00  -6.1 -12.6 114.  4.0  277. -11.7\n"),
                "negative precipitation at line 5: -0.1 mm",
            ),
            (
                table("  1 13     1   0.0  0.00 0.00   0.00  -6.1 -12.6 114.  4.0  277. -11.7\n"),
                "invalid calendar date at line 5",
            ),
        ];
        for (text, expected) in cases {
            let error = parse_cli_table(&text).unwrap_err();
            let rendered = error.to_string();
            assert!(rendered.contains(expected), "{rendered:?} vs {expected:?}");
        }
    }

    // C-R1-001: month-specific day bounds with the union-of-source
    // leap calendars rule (`max_day` doc) — February 29 iff the
    // printed year is divisible by 4.
    #[test]
    fn impossible_calendar_dates_fail_closed() {
        let row = |day: i32, month: i32, year: i32| {
            table(&format!(
                "{day:>3}{month:>3} {year:>5}   0.0  0.00 0.00   0.00  -6.1 -12.6 114.  4.0  277. -11.7\n"
            ))
        };
        for (day, month, year) in [(31, 2, 1), (30, 2, 4), (29, 2, 3), (31, 4, 1), (0, 1, 1)] {
            let error = parse_cli_table(&row(day, month, year)).unwrap_err();
            assert!(
                error.to_string().contains("invalid calendar date"),
                "{day}-{month}-{year}: {error}"
            );
        }
        // Accepted: February 29 in div-4 years — the Gregorian daily
        // surface (year 4) and the storm-calendar century surface
        // (year 100, leap only under the storm nt test).
        for year in [4, 100, 1900, 2000] {
            let parsed = parse_cli_table(&row(29, 2, year)).unwrap();
            assert_eq!(parsed.rows[0].date_key(), (year, 2, 29));
        }
    }

    #[test]
    fn misordered_rows_fail_closed() {
        let text = table(
            "  2  1     1   0.0  0.00 0.00   0.00  -6.1 -12.6 114.  4.0  277. -11.7\n  1  1     1   0.0  0.00 0.00   0.00  -6.1 -12.6 114.  4.0  277. -11.7\n",
        );
        let error = parse_cli_table(&text).unwrap_err();
        assert!(
            error.to_string().contains("is not after the preceding row"),
            "{error}"
        );
    }

    #[test]
    fn run_end_blank_line_is_skipped() {
        let text =
            table(" 15  6    12  57.1  6.00 0.40   4.00  14.6   1.0 619.  5.7  305.   2.7\n  \n");
        let parsed = parse_cli_table(&text).unwrap();
        assert_eq!(parsed.rows.len(), 1);
        assert!(parsed.rows[0].is_wet());
        assert_eq!(parsed.rows[0].date_key(), (12, 6, 15));
    }
}
