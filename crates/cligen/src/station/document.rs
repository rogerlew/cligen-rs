//! Strict JSON station document revision 1.
//!
//! Serialization is deterministic: declaration-ordered structs and fixed
//! arrays only, pretty JSON, and one trailing LF. The document stores `f32`
//! values directly; it never widens and narrows faithful model parameters.

use std::error::Error;
use std::fmt;

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use crate::par::ParFile;

use super::FixedMonthly5323;

/// The only station-file schema revision understood by this module.
pub const STATION_SCHEMA_VERSION: u32 = 1;
/// Version of the exact legacy `.par` to fixed-monthly adapter.
pub const ADAPTER_VERSION: u32 = 1;

/// Station-model identity, independent of the station-file schema.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum StationModelId {
    #[serde(rename = "fixed_monthly_5_32_3")]
    FixedMonthly5323,
}

/// Exact source format named by revision-1 lineage.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum LegacySourceFormat {
    #[serde(rename = "cligen_par_5_32_3")]
    CligenPar5323,
}

/// Exact conversion algorithm named by revision-1 lineage.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum AdapterId {
    #[serde(rename = "cligen_rs_legacy_par_to_fixed_monthly")]
    CligenRsLegacyParToFixedMonthly,
}

/// Closed unit vocabulary for revision 1.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Unit {
    DegreeNorth,
    DegreeEast,
    Foot,
    Inch,
    InchPerHour,
    DegreeFahrenheit,
    LangleyPerDay,
    MeterPerSecond,
    Year,
    Fraction,
    Percent,
    Dimensionless,
}

/// Explicit units of every numeric family in the fixed-monthly payload.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct StationUnits {
    pub latitude: Unit,
    pub longitude: Unit,
    pub elevation: Unit,
    pub record_length: Unit,
    pub precipitation_depth: Unit,
    pub precipitation_intensity: Unit,
    pub temperature: Unit,
    pub solar_radiation: Unit,
    pub wind_speed: Unit,
    pub probability: Unit,
    pub frequency: Unit,
    pub skew: Unit,
    pub interpolation_weight: Unit,
}

impl StationUnits {
    /// The sole valid unit assignment for `fixed_monthly_5_32_3`.
    #[must_use]
    pub const fn fixed_monthly_5_32_3() -> Self {
        Self {
            latitude: Unit::DegreeNorth,
            longitude: Unit::DegreeEast,
            elevation: Unit::Foot,
            record_length: Unit::Year,
            precipitation_depth: Unit::Inch,
            precipitation_intensity: Unit::InchPerHour,
            temperature: Unit::DegreeFahrenheit,
            solar_radiation: Unit::LangleyPerDay,
            wind_speed: Unit::MeterPerSecond,
            probability: Unit::Fraction,
            frequency: Unit::Percent,
            skew: Unit::Dimensionless,
            interpolation_weight: Unit::Dimensionless,
        }
    }
}

/// Deterministic legacy-source lineage carried by a converted document.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct StationLineage {
    pub source_format: LegacySourceFormat,
    pub source_sha256: String,
    pub adapter: AdapterId,
    pub adapter_version: u32,
}

/// Exact record-1 identity fields.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct IdentityParameters {
    /// Exact 41-byte source `A41`, including right padding.
    pub station_name_raw: String,
    pub state_code: i32,
    pub station_code: i32,
    pub wind_et_flag: i32,
}

/// Geographic and record-period fields.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct LocationParameters {
    pub latitude: f32,
    pub longitude: f32,
    pub record_years: i32,
    pub elevation: i32,
}

/// Station storm-shape fields.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct StormParameters {
    pub single_storm_type: i32,
    pub max_six_hour_precipitation: f32,
    pub time_to_peak_cdf: [f32; 12],
}

/// Monthly precipitation occurrence, amount, and intensity parameters.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PrecipitationParameters {
    pub mean_daily: [f32; 12],
    pub standard_deviation_daily: [f32; 12],
    pub skew: [f32; 12],
    pub probability_wet_given_wet: [f32; 12],
    pub probability_wet_given_dry: [f32; 12],
    /// Raw `.par` intensity, before `sta_parms` halves it to depth.
    pub max_half_hour_intensity: [f32; 12],
}

/// Monthly temperature and dew-point parameters.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct TemperatureParameters {
    pub maximum_mean: [f32; 12],
    pub minimum_mean: [f32; 12],
    pub maximum_standard_deviation: [f32; 12],
    pub minimum_standard_deviation: [f32; 12],
    pub dew_point_mean: [f32; 12],
}

/// Monthly solar-radiation parameters.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SolarRadiationParameters {
    pub mean_daily: [f32; 12],
    pub standard_deviation_daily: [f32; 12],
}

/// One direction's four monthly wind parameter families.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct WindDirectionParameters {
    pub frequency: [f32; 12],
    pub mean_speed: [f32; 12],
    pub standard_deviation_speed: [f32; 12],
    pub skew: [f32; 12],
}

/// One fixed-width wind-interpolation station and weight.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct WindInterpolationStation {
    /// Exact 19-byte source `A19`, including right padding.
    pub station_name_raw: String,
    pub weight: f32,
}

/// Monthly wind parameters. Direction array order is the source order
/// N, NNE, NE, ENE, E, ESE, SE, SSE, S, SSW, SW, WSW, W, WNW, NW, NNW.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct WindParameters {
    pub directions: [WindDirectionParameters; 16],
    pub calm_frequency: [f32; 12],
    pub interpolation_stations: [WindInterpolationStation; 3],
}

/// Revision-1 payload grouped by meaning rather than legacy record layout.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct StationParameters {
    pub identity: IdentityParameters,
    pub location: LocationParameters,
    pub storm: StormParameters,
    pub precipitation: PrecipitationParameters,
    pub temperature: TemperatureParameters,
    pub solar_radiation: SolarRadiationParameters,
    pub wind: WindParameters,
}

/// The revision-1 DTO for station model `fixed_monthly_5_32_3`.
///
/// It is an alias rather than the generator's model type: the explicit
/// conversions below are the compatibility boundary.
pub type FixedMonthly5323Document = StationParameters;

/// One strict modern station JSON document.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct StationDocumentV1 {
    pub station_schema_version: u32,
    pub station_model: StationModelId,
    pub units: StationUnits,
    pub lineage: StationLineage,
    pub parameters: StationParameters,
}

/// Typed modern-station parse, validation, or serialization failure.
#[derive(Debug)]
pub enum StationDocumentError {
    Parse {
        field_path: String,
        source: serde_json::Error,
    },
    Validation {
        field_path: String,
        message: String,
    },
    Serialize {
        source: serde_json::Error,
    },
}

impl fmt::Display for StationDocumentError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Parse { field_path, source } => {
                write!(f, "station document {field_path}: {source}")
            }
            Self::Validation {
                field_path,
                message,
            } => write!(f, "station document {field_path}: {message}"),
            Self::Serialize { source } => write!(f, "serialize station document: {source}"),
        }
    }
}

impl Error for StationDocumentError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            Self::Parse { source, .. } | Self::Serialize { source } => Some(source),
            Self::Validation { .. } => None,
        }
    }
}

impl StationDocumentV1 {
    /// Convert one self-consistent parsed legacy file and hash its exact
    /// retained `.par` bytes into deterministic lineage.
    ///
    /// # Errors
    /// Returns a field-addressed validation error for non-finite model values
    /// or malformed fixed-width source strings.
    pub fn from_legacy_par(par: &ParFile) -> Result<Self, StationDocumentError> {
        let legacy_par_bytes = par.to_bytes();
        let document = Self {
            station_schema_version: STATION_SCHEMA_VERSION,
            station_model: StationModelId::FixedMonthly5323,
            units: StationUnits::fixed_monthly_5_32_3(),
            lineage: StationLineage {
                source_format: LegacySourceFormat::CligenPar5323,
                source_sha256: sha256_hex(&legacy_par_bytes),
                adapter: AdapterId::CligenRsLegacyParToFixedMonthly,
                adapter_version: ADAPTER_VERSION,
            },
            parameters: StationParameters::from(par.fixed_monthly()),
        };
        document.validate()?;
        Ok(document)
    }

    /// Parse exactly one strict JSON document and validate its fixed model
    /// contract. Unknown fields and enum variants fail closed.
    ///
    /// # Errors
    /// Returns a field-addressed parse or validation error.
    pub fn parse_json(bytes: &[u8]) -> Result<Self, StationDocumentError> {
        let mut deserializer = serde_json::Deserializer::from_slice(bytes);
        let document: Self =
            serde_path_to_error::deserialize(&mut deserializer).map_err(|error| {
                StationDocumentError::Parse {
                    field_path: normalize_path(error.path().to_string()),
                    source: error.into_inner(),
                }
            })?;
        deserializer
            .end()
            .map_err(|source| StationDocumentError::Parse {
                field_path: "document".to_owned(),
                source,
            })?;
        document.validate()?;
        Ok(document)
    }

    /// Emit deterministic pretty JSON with one trailing LF.
    ///
    /// # Errors
    /// Validates before serialization and surfaces the JSON serializer error.
    pub fn to_json_bytes(&self) -> Result<Vec<u8>, StationDocumentError> {
        self.validate()?;
        let mut bytes = serde_json::to_vec_pretty(self)
            .map_err(|source| StationDocumentError::Serialize { source })?;
        bytes.push(b'\n');
        Ok(bytes)
    }

    /// Validate the schema/model/unit/lineage envelope and all model values.
    ///
    /// # Errors
    /// Returns the first field-addressed contract violation.
    pub fn validate(&self) -> Result<(), StationDocumentError> {
        validate_envelope(self)?;
        validate_parameters(&self.parameters)
    }

    /// Copy the document payload into the serialization-independent model.
    ///
    /// # Errors
    /// Validates the complete document before exposing generator state.
    pub fn to_model(&self) -> Result<FixedMonthly5323, StationDocumentError> {
        self.validate()?;
        Ok(FixedMonthly5323::from(&self.parameters))
    }

    /// Consume the document and return serialization-independent model state.
    ///
    /// # Errors
    /// Validates the complete document before exposing generator state.
    pub fn into_model(self) -> Result<FixedMonthly5323, StationDocumentError> {
        self.validate()?;
        Ok(FixedMonthly5323::from(self.parameters))
    }
}

/// Hash the canonical model parameters independently of their input syntax.
///
/// Legacy `.par` bytes and a modern station document that represent the same
/// `fixed_monthly_5_32_3` state produce the same digest. The hashed payload is
/// the declaration-ordered compact JSON form of [`StationParameters`]; it
/// excludes input bytes, schema identity, units, and conversion lineage.
///
/// # Errors
/// Returns a field-addressed validation error for invalid model state, or a
/// serialization error if the canonical JSON payload cannot be emitted.
pub fn parameter_set_sha256(model: &FixedMonthly5323) -> Result<String, StationDocumentError> {
    let parameters = StationParameters::from(model);
    validate_parameters(&parameters)?;
    let bytes = serde_json::to_vec(&parameters)
        .map_err(|source| StationDocumentError::Serialize { source })?;
    Ok(sha256_hex(&bytes))
}

impl From<&FixedMonthly5323> for StationParameters {
    fn from(model: &FixedMonthly5323) -> Self {
        let precipitation = PrecipitationParameters {
            mean_daily: std::array::from_fn(|month| model.rst[month][0]),
            standard_deviation_daily: std::array::from_fn(|month| model.rst[month][1]),
            skew: std::array::from_fn(|month| model.rst[month][2]),
            probability_wet_given_wet: std::array::from_fn(|month| model.prw[month][0]),
            probability_wet_given_dry: std::array::from_fn(|month| model.prw[month][1]),
            max_half_hour_intensity: model.wi_raw,
        };
        let wind = WindParameters {
            directions: std::array::from_fn(|direction| WindDirectionParameters {
                frequency: model.wvl[direction][0],
                mean_speed: model.wvl[direction][1],
                standard_deviation_speed: model.wvl[direction][2],
                skew: model.wvl[direction][3],
            }),
            calm_frequency: model.calm,
            interpolation_stations: std::array::from_fn(|index| WindInterpolationStation {
                station_name_raw: model.site[index].clone(),
                weight: model.wgt[index],
            }),
        };
        Self {
            identity: IdentityParameters {
                station_name_raw: model.stidd.clone(),
                state_code: model.nst,
                station_code: model.nstat,
                wind_et_flag: model.igcode,
            },
            location: LocationParameters {
                latitude: model.ylt,
                longitude: model.yll,
                record_years: model.years,
                elevation: model.elev_ft,
            },
            storm: StormParameters {
                single_storm_type: model.itype,
                max_six_hour_precipitation: model.tp6,
                time_to_peak_cdf: model.timpkd,
            },
            precipitation,
            temperature: TemperatureParameters {
                maximum_mean: model.obmx,
                minimum_mean: model.obmn,
                maximum_standard_deviation: model.stdtx,
                minimum_standard_deviation: model.stdtm,
                dew_point_mean: model.rh,
            },
            solar_radiation: SolarRadiationParameters {
                mean_daily: model.obsl,
                standard_deviation_daily: model.stdsl,
            },
            wind,
        }
    }
}

impl From<&StationParameters> for FixedMonthly5323 {
    fn from(parameters: &StationParameters) -> Self {
        let rst = std::array::from_fn(|month| {
            [
                parameters.precipitation.mean_daily[month],
                parameters.precipitation.standard_deviation_daily[month],
                parameters.precipitation.skew[month],
            ]
        });
        let prw = std::array::from_fn(|month| {
            [
                parameters.precipitation.probability_wet_given_wet[month],
                parameters.precipitation.probability_wet_given_dry[month],
            ]
        });
        let wvl = std::array::from_fn(|direction| {
            let values = &parameters.wind.directions[direction];
            [
                values.frequency,
                values.mean_speed,
                values.standard_deviation_speed,
                values.skew,
            ]
        });
        Self {
            stidd: parameters.identity.station_name_raw.clone(),
            nst: parameters.identity.state_code,
            nstat: parameters.identity.station_code,
            igcode: parameters.identity.wind_et_flag,
            ylt: parameters.location.latitude,
            yll: parameters.location.longitude,
            years: parameters.location.record_years,
            itype: parameters.storm.single_storm_type,
            elev_ft: parameters.location.elevation,
            tp6: parameters.storm.max_six_hour_precipitation,
            rst,
            prw,
            obmx: parameters.temperature.maximum_mean,
            obmn: parameters.temperature.minimum_mean,
            stdtx: parameters.temperature.maximum_standard_deviation,
            stdtm: parameters.temperature.minimum_standard_deviation,
            obsl: parameters.solar_radiation.mean_daily,
            stdsl: parameters.solar_radiation.standard_deviation_daily,
            wi_raw: parameters.precipitation.max_half_hour_intensity,
            rh: parameters.temperature.dew_point_mean,
            timpkd: parameters.storm.time_to_peak_cdf,
            wvl,
            calm: parameters.wind.calm_frequency,
            site: std::array::from_fn(|index| {
                parameters.wind.interpolation_stations[index]
                    .station_name_raw
                    .clone()
            }),
            wgt: std::array::from_fn(|index| parameters.wind.interpolation_stations[index].weight),
        }
    }
}

impl From<StationParameters> for FixedMonthly5323 {
    fn from(parameters: StationParameters) -> Self {
        Self::from(&parameters)
    }
}

fn validate_envelope(document: &StationDocumentV1) -> Result<(), StationDocumentError> {
    if document.station_schema_version != STATION_SCHEMA_VERSION {
        return invalid(
            "station_schema_version",
            format!("must equal {STATION_SCHEMA_VERSION}"),
        );
    }
    if document.station_model != StationModelId::FixedMonthly5323 {
        return invalid("station_model", "unsupported station model");
    }
    if document.units != StationUnits::fixed_monthly_5_32_3() {
        return invalid("units", "unit assignments must match fixed_monthly_5_32_3");
    }
    validate_lineage(&document.lineage)
}

fn validate_lineage(lineage: &StationLineage) -> Result<(), StationDocumentError> {
    if lineage.source_format != LegacySourceFormat::CligenPar5323 {
        return invalid("lineage.source_format", "unsupported source format");
    }
    if !is_lower_hex_sha256(&lineage.source_sha256) {
        return invalid(
            "lineage.source_sha256",
            "must be exactly 64 lowercase hexadecimal characters",
        );
    }
    if lineage.adapter != AdapterId::CligenRsLegacyParToFixedMonthly {
        return invalid("lineage.adapter", "unsupported adapter");
    }
    if lineage.adapter_version != ADAPTER_VERSION {
        return invalid(
            "lineage.adapter_version",
            format!("must equal {ADAPTER_VERSION}"),
        );
    }
    Ok(())
}

fn validate_parameters(parameters: &StationParameters) -> Result<(), StationDocumentError> {
    validate_fixed_ascii(
        "parameters.identity.station_name_raw",
        &parameters.identity.station_name_raw,
        41,
    )?;
    validate_location(&parameters.location)?;
    validate_storm(&parameters.storm)?;
    validate_precipitation(&parameters.precipitation)?;
    validate_temperature(&parameters.temperature)?;
    validate_solar(&parameters.solar_radiation)?;
    validate_wind(&parameters.wind)
}

fn validate_location(location: &LocationParameters) -> Result<(), StationDocumentError> {
    validate_finite("parameters.location.latitude", &[location.latitude])?;
    validate_finite("parameters.location.longitude", &[location.longitude])
}

fn validate_storm(storm: &StormParameters) -> Result<(), StationDocumentError> {
    if !(1..=4).contains(&storm.single_storm_type) {
        return invalid(
            "parameters.storm.single_storm_type",
            "must be an integer in 1..=4",
        );
    }
    validate_finite(
        "parameters.storm.max_six_hour_precipitation",
        &[storm.max_six_hour_precipitation],
    )?;
    validate_finite("parameters.storm.time_to_peak_cdf", &storm.time_to_peak_cdf)
}

fn validate_precipitation(
    precipitation: &PrecipitationParameters,
) -> Result<(), StationDocumentError> {
    let fields = [
        ("mean_daily", &precipitation.mean_daily),
        (
            "standard_deviation_daily",
            &precipitation.standard_deviation_daily,
        ),
        ("skew", &precipitation.skew),
        (
            "probability_wet_given_wet",
            &precipitation.probability_wet_given_wet,
        ),
        (
            "probability_wet_given_dry",
            &precipitation.probability_wet_given_dry,
        ),
        (
            "max_half_hour_intensity",
            &precipitation.max_half_hour_intensity,
        ),
    ];
    for (name, values) in fields {
        validate_finite(&format!("parameters.precipitation.{name}"), values)?;
    }
    Ok(())
}

fn validate_temperature(temperature: &TemperatureParameters) -> Result<(), StationDocumentError> {
    let fields = [
        ("maximum_mean", &temperature.maximum_mean),
        ("minimum_mean", &temperature.minimum_mean),
        (
            "maximum_standard_deviation",
            &temperature.maximum_standard_deviation,
        ),
        (
            "minimum_standard_deviation",
            &temperature.minimum_standard_deviation,
        ),
        ("dew_point_mean", &temperature.dew_point_mean),
    ];
    for (name, values) in fields {
        validate_finite(&format!("parameters.temperature.{name}"), values)?;
    }
    Ok(())
}

fn validate_solar(solar: &SolarRadiationParameters) -> Result<(), StationDocumentError> {
    validate_finite("parameters.solar_radiation.mean_daily", &solar.mean_daily)?;
    validate_finite(
        "parameters.solar_radiation.standard_deviation_daily",
        &solar.standard_deviation_daily,
    )
}

fn validate_wind(wind: &WindParameters) -> Result<(), StationDocumentError> {
    for (index, direction) in wind.directions.iter().enumerate() {
        validate_wind_direction(direction, index)?;
    }
    validate_finite("parameters.wind.calm_frequency", &wind.calm_frequency)?;
    for (index, station) in wind.interpolation_stations.iter().enumerate() {
        validate_fixed_ascii(
            &format!("parameters.wind.interpolation_stations[{index}].station_name_raw"),
            &station.station_name_raw,
            19,
        )?;
        validate_finite(
            &format!("parameters.wind.interpolation_stations[{index}].weight"),
            &[station.weight],
        )?;
    }
    Ok(())
}

fn validate_wind_direction(
    direction: &WindDirectionParameters,
    index: usize,
) -> Result<(), StationDocumentError> {
    let fields = [
        ("frequency", &direction.frequency),
        ("mean_speed", &direction.mean_speed),
        (
            "standard_deviation_speed",
            &direction.standard_deviation_speed,
        ),
        ("skew", &direction.skew),
    ];
    for (name, values) in fields {
        validate_finite(
            &format!("parameters.wind.directions[{index}].{name}"),
            values,
        )?;
    }
    Ok(())
}

fn validate_finite(path: &str, values: &[f32]) -> Result<(), StationDocumentError> {
    for (index, value) in values.iter().enumerate() {
        if !value.is_finite() {
            return invalid(format!("{path}[{index}]"), "must be finite");
        }
    }
    Ok(())
}

fn validate_fixed_ascii(path: &str, value: &str, width: usize) -> Result<(), StationDocumentError> {
    if !value.is_ascii() {
        return invalid(path, "must contain only ASCII bytes");
    }
    if value.len() != width {
        return invalid(path, format!("must be exactly {width} bytes"));
    }
    Ok(())
}

fn is_lower_hex_sha256(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase())
}

fn sha256_hex(bytes: &[u8]) -> String {
    let digest = Sha256::digest(bytes);
    let mut output = String::with_capacity(64);
    for byte in digest {
        use std::fmt::Write as _;
        write!(output, "{byte:02x}").expect("writing to String cannot fail");
    }
    output
}

fn normalize_path(path: String) -> String {
    if path.is_empty() || path == "." {
        "document".to_owned()
    } else {
        path
    }
}

fn invalid(
    field_path: impl Into<String>,
    message: impl Into<String>,
) -> Result<(), StationDocumentError> {
    Err(StationDocumentError::Validation {
        field_path: field_path.into(),
        message: message.into(),
    })
}
