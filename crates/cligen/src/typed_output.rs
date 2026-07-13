//! Typed, pre-format climate rows for independently versioned outputs.
//!
//! This is an output-boundary projection of faithful [`crate::modes::DailyRow`]
//! values. It is not a generator implementation and never feeds widened values
//! back into CLIGEN.

use std::error::Error;
use std::fmt;

use crate::modes::DailyRow;

/// Stable repeated identities carried by every revision-1 typed row.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ClimateIdentityV1 {
    pub run_id: String,
    pub generation_profile: String,
    pub station_parameter_set_sha256: String,
}

impl ClimateIdentityV1 {
    /// Validate the revision-1 identity vocabulary.
    ///
    /// # Errors
    /// Returns [`TypedOutputError`] when either SHA-256 is malformed or the
    /// generation profile is not defined by revision 1.
    pub fn validate(&self) -> Result<(), TypedOutputError> {
        validate_sha256("run_id", &self.run_id)?;
        validate_sha256(
            "station_parameter_set_sha256",
            &self.station_parameter_set_sha256,
        )?;
        match self.generation_profile.as_str() {
            "faithful_5_32_3" | "fast_batch_v0" => Ok(()),
            value => Err(TypedOutputError::InvalidIdentity(format!(
                "unsupported generation_profile {value:?}"
            ))),
        }
    }
}

/// One non-null revision-1 parametric climate output row.
///
/// # Units
/// Units are encoded in field names where practical and are fully specified
/// by `SPEC-CLI-PARQUET`: precipitation in mm, duration in hours,
/// temperatures in degrees Celsius, radiation in langley/day, wind velocity
/// in m/s, and wind direction in degrees clockwise from north.
///
/// # Numerics
/// Faithful `f32` values widen exactly once to `f64` in
/// [`Self::try_from_daily`]. Every finite IEEE-754 binary32 value is exactly
/// representable as binary64, including the sign of zero.
#[derive(Debug, Clone, PartialEq)]
pub struct ClimateRowV1 {
    pub run_id: String,
    pub generation_profile: String,
    pub station_parameter_set_sha256: String,
    pub sim_day_index: i32,
    pub year: i32,
    pub month: i8,
    pub day_of_month: i8,
    pub precip_mm: f64,
    pub duration_h: f64,
    pub time_to_peak_fraction: f64,
    pub peak_intensity_ratio: f64,
    pub tmax_c: f64,
    pub tmin_c: f64,
    pub solar_langley_day: f64,
    pub wind_velocity_m_s: f64,
    pub wind_direction_deg: f64,
    pub tdew_c: f64,
}

impl ClimateRowV1 {
    /// Project one faithful pre-format daily row into output schema revision 1.
    ///
    /// # Numerics
    /// Each source value is converted directly with Rust's exact `f32` to
    /// `f64` widening conversion. No arithmetic or text formatting intervenes.
    ///
    /// # Errors
    /// Returns [`TypedOutputError`] for invalid identity values, indices,
    /// dates, or non-finite climate values.
    pub fn try_from_daily(
        identity: &ClimateIdentityV1,
        sim_day_index: i32,
        source: &DailyRow,
    ) -> Result<Self, TypedOutputError> {
        identity.validate()?;
        let month = i8::try_from(source.mo).map_err(|_| TypedOutputError::InvalidDate {
            year: source.iyear,
            month: source.mo,
            day: source.jd,
        })?;
        let day_of_month = i8::try_from(source.jd).map_err(|_| TypedOutputError::InvalidDate {
            year: source.iyear,
            month: source.mo,
            day: source.jd,
        })?;
        let row = Self {
            run_id: identity.run_id.clone(),
            generation_profile: identity.generation_profile.clone(),
            station_parameter_set_sha256: identity.station_parameter_set_sha256.clone(),
            sim_day_index,
            year: source.iyear,
            month,
            day_of_month,
            precip_mm: source.xr as f64,
            duration_h: source.dur as f64,
            time_to_peak_fraction: source.tpr as f64,
            peak_intensity_ratio: source.xmav as f64,
            tmax_c: source.tmxg as f64,
            tmin_c: source.tmng as f64,
            solar_langley_day: source.radg as f64,
            wind_velocity_m_s: source.wv as f64,
            wind_direction_deg: source.th as f64,
            tdew_c: source.tdp as f64,
        };
        row.validate()?;
        Ok(row)
    }

    /// Validate one row independently of a sequence.
    ///
    /// # Errors
    /// Returns [`TypedOutputError`] for malformed identity, index, date, or
    /// non-finite numeric values.
    pub fn validate(&self) -> Result<(), TypedOutputError> {
        ClimateIdentityV1 {
            run_id: self.run_id.clone(),
            generation_profile: self.generation_profile.clone(),
            station_parameter_set_sha256: self.station_parameter_set_sha256.clone(),
        }
        .validate()?;
        if self.sim_day_index < 1 {
            return Err(TypedOutputError::InvalidDayIndex(self.sim_day_index));
        }
        validate_date(self.year, self.month, self.day_of_month)?;
        for (name, value) in self.numeric_values() {
            if !value.is_finite() {
                return Err(TypedOutputError::NonFinite { name });
            }
            let narrowed = value as f32;
            if !narrowed.is_finite() || (narrowed as f64).to_bits() != value.to_bits() {
                return Err(TypedOutputError::NotExactF32 { name });
            }
        }
        Ok(())
    }

    fn numeric_values(&self) -> [(&'static str, f64); 10] {
        [
            ("precip_mm", self.precip_mm),
            ("duration_h", self.duration_h),
            ("time_to_peak_fraction", self.time_to_peak_fraction),
            ("peak_intensity_ratio", self.peak_intensity_ratio),
            ("tmax_c", self.tmax_c),
            ("tmin_c", self.tmin_c),
            ("solar_langley_day", self.solar_langley_day),
            ("wind_velocity_m_s", self.wind_velocity_m_s),
            ("wind_direction_deg", self.wind_direction_deg),
            ("tdew_c", self.tdew_c),
        ]
    }
}

/// Validate a complete revision-1 row sequence and its repeated identities.
///
/// Dates and simulation indices must both be contiguous from one. Revision 1
/// represents a complete generated or observed-source-prefix daily stream;
/// filtered streams require a future schema revision.
///
/// # Errors
/// Returns [`TypedOutputError`] for an empty stream or the first row that
/// violates the identity, index, numeric, date, or ordering contract.
pub fn validate_climate_rows_v1(
    rows: &[ClimateRowV1],
    identity: &ClimateIdentityV1,
) -> Result<(), TypedOutputError> {
    identity.validate()?;
    if rows.is_empty() {
        return Err(TypedOutputError::EmptyRows);
    }
    let mut previous = None;
    for (offset, row) in rows.iter().enumerate() {
        row.validate()?;
        let expected_index = i32::try_from(offset + 1)
            .map_err(|_| TypedOutputError::InvalidDayIndex(row.sim_day_index))?;
        if row.sim_day_index != expected_index {
            return Err(TypedOutputError::NonContiguousIndex {
                expected: expected_index,
                actual: row.sim_day_index,
            });
        }
        if row.run_id != identity.run_id
            || row.generation_profile != identity.generation_profile
            || row.station_parameter_set_sha256 != identity.station_parameter_set_sha256
        {
            return Err(TypedOutputError::IdentityMismatch(row.sim_day_index));
        }
        let date = (row.year, row.month, row.day_of_month);
        if previous.is_some_and(|prior| next_date(prior) != Some(date)) {
            return Err(TypedOutputError::NonContiguousDate(row.sim_day_index));
        }
        previous = Some(date);
    }
    Ok(())
}

/// Revision-1 typed output validation failure.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TypedOutputError {
    EmptyRows,
    InvalidIdentity(String),
    InvalidDayIndex(i32),
    NonContiguousIndex { expected: i32, actual: i32 },
    IdentityMismatch(i32),
    InvalidDate { year: i32, month: i32, day: i32 },
    NonContiguousDate(i32),
    NonFinite { name: &'static str },
    NotExactF32 { name: &'static str },
}

impl fmt::Display for TypedOutputError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::EmptyRows => write!(f, "typed climate row stream is empty"),
            Self::InvalidIdentity(message) => write!(f, "invalid typed-row identity: {message}"),
            Self::InvalidDayIndex(index) => write!(f, "invalid simulation day index {index}"),
            Self::NonContiguousIndex { expected, actual } => write!(
                f,
                "non-contiguous simulation day index: expected {expected}, got {actual}"
            ),
            Self::IdentityMismatch(index) => {
                write!(f, "typed-row identity mismatch at simulation day {index}")
            }
            Self::InvalidDate { year, month, day } => {
                write!(f, "invalid proleptic Gregorian date {year}-{month}-{day}")
            }
            Self::NonContiguousDate(index) => {
                write!(f, "non-contiguous date at simulation day {index}")
            }
            Self::NonFinite { name } => write!(f, "non-finite typed-row field {name}"),
            Self::NotExactF32 { name } => {
                write!(f, "typed-row field {name} is not an exact f32 widening")
            }
        }
    }
}

impl Error for TypedOutputError {}

fn validate_sha256(name: &str, value: &str) -> Result<(), TypedOutputError> {
    if value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        Ok(())
    } else {
        Err(TypedOutputError::InvalidIdentity(format!(
            "{name} must be 64 lowercase hexadecimal characters"
        )))
    }
}

fn validate_date(year: i32, month: i8, day: i8) -> Result<(), TypedOutputError> {
    let month_i32 = i32::from(month);
    let day_i32 = i32::from(day);
    if !(1..=99_999).contains(&year) || !(1..=12).contains(&month_i32) {
        return Err(TypedOutputError::InvalidDate {
            year,
            month: month_i32,
            day: day_i32,
        });
    }
    let mut days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    if year % 400 == 0 || (year % 4 == 0 && year % 100 != 0) {
        days[1] = 29;
    }
    if day_i32 < 1 || day_i32 > days[(month - 1) as usize] {
        return Err(TypedOutputError::InvalidDate {
            year,
            month: month_i32,
            day: day_i32,
        });
    }
    Ok(())
}

fn next_date((year, month, day): (i32, i8, i8)) -> Option<(i32, i8, i8)> {
    let mut days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    if year % 400 == 0 || (year % 4 == 0 && year % 100 != 0) {
        days[1] = 29;
    }
    if i32::from(day) < days[(month - 1) as usize] {
        Some((year, month, day + 1))
    } else if month < 12 {
        Some((year, month + 1, 1))
    } else {
        year.checked_add(1).map(|next_year| (next_year, 1, 1))
    }
}
