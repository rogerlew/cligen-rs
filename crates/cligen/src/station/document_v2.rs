//! Strict JSON station document revision 2 for the A8c routed pilot.
//!
//! This extension transport reuses revision 1's exact fixed-monthly payload
//! and adds an explicit daily-precipitation route. It does not change the
//! faithful typed station state or infer a route from climate parameters.

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use super::{
    FixedMonthly5323, StationDocumentError, StationDocumentV1, StationLineage, StationModelId,
    StationParameters, StationUnits, STATION_SCHEMA_VERSION,
};

/// Station-document revision used by the A8c pilot.
pub const STATION_SCHEMA_VERSION_V2: u32 = 2;
/// Exact A8a analysis supplying eligible-route coefficients.
pub const A8A_ANALYSIS_SHA256: &str =
    "78b9b9bb5cd5172459bfb27ba13f7b20ca2cec5af19cab9547c425c7a6e6e89b";
/// Exact A8b decision certifying the legacy-only fallback.
pub const A8B_DECISION_SHA256: &str =
    "b227951faa72287afd859fb9872eb75aa559714ab6b5efd2303560b73e5a1efb";
/// Eligible daily-fit identity.
pub const A8A_FIT_ID: &str = "a8a_o2_logqspline_gaussian_copula_v1";
/// Explicit fallback identity.
pub const A8B_FIT_ID: &str = "legacy_daily_only_v1";

/// Station-model identity, independent of the station-file revision.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum StationModelIdV2 {
    #[serde(rename = "fixed_monthly_5_32_3")]
    FixedMonthly5323,
    #[serde(rename = "a8c_integrated_daily_v1")]
    A8cIntegratedDailyV1,
}

/// Explicit runtime route; no runtime descriptor may replace it.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum DailyPrecipitationRoute {
    #[serde(rename = "integrated_daily")]
    IntegratedDaily,
    #[serde(rename = "legacy_daily_fallback")]
    LegacyDailyFallback,
}

/// One season's wet-amount shape and within-spell dependence.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct A8cSeasonCoefficients {
    pub season: String,
    pub log_quantile_knots_mm: [f64; 11],
    pub gaussian_copula_rho: f64,
}

/// One month's four-state occurrence kernel and amount reallocation.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct A8cMonthCoefficients {
    pub month: u8,
    pub occurrence_probabilities: [f64; 4],
    pub amount_dispersion: f64,
    pub legacy_amount_dispersion: f64,
}

/// Route and coefficient block added by station-document revision 2.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct A8cDailyPrecipitation {
    pub route: DailyPrecipitationRoute,
    pub fit_id: String,
    pub source_analysis_sha256: String,
    pub seasons: Vec<A8cSeasonCoefficients>,
    pub months: Vec<A8cMonthCoefficients>,
}

/// Strict station-document revision 2.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct StationDocumentV2 {
    pub station_schema_version: u32,
    pub station_model: StationModelIdV2,
    pub units: StationUnits,
    pub lineage: StationLineage,
    pub parameters: StationParameters,
    pub daily_precipitation: A8cDailyPrecipitation,
}

impl StationDocumentV2 {
    /// Parse exactly one strict revision-2 JSON document.
    ///
    /// # Errors
    /// Returns a field-addressed parse or validation failure.
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
    /// Validates before serialization.
    pub fn to_json_bytes(&self) -> Result<Vec<u8>, StationDocumentError> {
        self.validate()?;
        let mut bytes = serde_json::to_vec_pretty(self)
            .map_err(|source| StationDocumentError::Serialize { source })?;
        bytes.push(b'\n');
        Ok(bytes)
    }

    /// Validate the revision-1 base and the complete routed extension.
    ///
    /// # Errors
    /// Returns the first field-addressed contract violation.
    pub fn validate(&self) -> Result<(), StationDocumentError> {
        if self.station_schema_version != STATION_SCHEMA_VERSION_V2 {
            return invalid(
                "station_schema_version",
                format!("must equal {STATION_SCHEMA_VERSION_V2}"),
            );
        }
        validate_base(self)?;
        validate_route(self)
    }

    /// Copy the unchanged fixed-monthly base into generator state.
    ///
    /// # Errors
    /// Validates the entire document before exposing its base model.
    pub fn to_base_model(&self) -> Result<FixedMonthly5323, StationDocumentError> {
        self.validate()?;
        Ok(FixedMonthly5323::from(&self.parameters))
    }
}

/// Hash the complete routed parameter payload without changing revision-1
/// parameter hashes.
///
/// # Errors
/// Returns validation or deterministic JSON serialization failures.
pub fn routed_parameter_set_sha256(
    document: &StationDocumentV2,
) -> Result<String, StationDocumentError> {
    #[derive(Serialize)]
    struct RoutedParameters<'a> {
        base: &'a StationParameters,
        daily_precipitation: &'a A8cDailyPrecipitation,
    }

    document.validate()?;
    let bytes = serde_json::to_vec(&RoutedParameters {
        base: &document.parameters,
        daily_precipitation: &document.daily_precipitation,
    })
    .map_err(|source| StationDocumentError::Serialize { source })?;
    Ok(sha256_hex(&bytes))
}

fn validate_base(document: &StationDocumentV2) -> Result<(), StationDocumentError> {
    StationDocumentV1 {
        station_schema_version: STATION_SCHEMA_VERSION,
        station_model: StationModelId::FixedMonthly5323,
        units: document.units.clone(),
        lineage: document.lineage.clone(),
        parameters: document.parameters.clone(),
    }
    .validate()
}

fn validate_route(document: &StationDocumentV2) -> Result<(), StationDocumentError> {
    match (document.station_model, document.daily_precipitation.route) {
        (StationModelIdV2::A8cIntegratedDailyV1, DailyPrecipitationRoute::IntegratedDaily) => {
            validate_integrated(&document.daily_precipitation)
        }
        (StationModelIdV2::FixedMonthly5323, DailyPrecipitationRoute::LegacyDailyFallback) => {
            validate_fallback(&document.daily_precipitation)
        }
        _ => invalid("daily_precipitation.route", "must agree with station_model"),
    }
}

fn validate_integrated(value: &A8cDailyPrecipitation) -> Result<(), StationDocumentError> {
    require_identity(value, A8A_FIT_ID, A8A_ANALYSIS_SHA256)?;
    if value.seasons.len() != 4 {
        return invalid("daily_precipitation.seasons", "must contain four seasons");
    }
    if value.months.len() != 12 {
        return invalid("daily_precipitation.months", "must contain twelve months");
    }
    for (index, season) in value.seasons.iter().enumerate() {
        validate_season(index, season)?;
    }
    for (index, month) in value.months.iter().enumerate() {
        validate_month(index, month)?;
    }
    Ok(())
}

fn validate_fallback(value: &A8cDailyPrecipitation) -> Result<(), StationDocumentError> {
    require_identity(value, A8B_FIT_ID, A8B_DECISION_SHA256)?;
    if !value.seasons.is_empty() || !value.months.is_empty() {
        return invalid(
            "daily_precipitation",
            "legacy fallback must not carry integrated coefficients",
        );
    }
    Ok(())
}

fn require_identity(
    value: &A8cDailyPrecipitation,
    fit_id: &str,
    source_sha256: &str,
) -> Result<(), StationDocumentError> {
    if value.fit_id != fit_id {
        return invalid("daily_precipitation.fit_id", format!("must equal {fit_id}"));
    }
    if value.source_analysis_sha256 != source_sha256 {
        return invalid(
            "daily_precipitation.source_analysis_sha256",
            "does not match the frozen parent artifact",
        );
    }
    Ok(())
}

fn validate_season(
    index: usize,
    value: &A8cSeasonCoefficients,
) -> Result<(), StationDocumentError> {
    const ORDER: [&str; 4] = ["DJF", "MAM", "JJA", "SON"];
    let base = format!("daily_precipitation.seasons[{index}]");
    if value.season != ORDER[index] {
        return invalid(
            format!("{base}.season"),
            "must follow DJF,MAM,JJA,SON order",
        );
    }
    if !value.gaussian_copula_rho.is_finite()
        || !(-0.95..=0.95).contains(&value.gaussian_copula_rho)
    {
        return invalid(
            format!("{base}.gaussian_copula_rho"),
            "must be finite and in [-0.95,0.95]",
        );
    }
    let mut previous = 0.0;
    for (knot, amount) in value.log_quantile_knots_mm.iter().enumerate() {
        if !amount.is_finite() || *amount <= 0.0 || (knot > 0 && *amount < previous) {
            return invalid(
                format!("{base}.log_quantile_knots_mm[{knot}]"),
                "must be finite, positive, and nondecreasing",
            );
        }
        previous = *amount;
    }
    Ok(())
}

fn validate_month(index: usize, value: &A8cMonthCoefficients) -> Result<(), StationDocumentError> {
    let base = format!("daily_precipitation.months[{index}]");
    if value.month as usize != index + 1 {
        return invalid(format!("{base}.month"), "must be 1..12 in order");
    }
    if value
        .occurrence_probabilities
        .iter()
        .any(|probability| !probability.is_finite() || !(0.0..1.0).contains(probability))
    {
        return invalid(
            format!("{base}.occurrence_probabilities"),
            "must be finite and strictly inside (0,1)",
        );
    }
    if !value.amount_dispersion.is_finite()
        || !value.legacy_amount_dispersion.is_finite()
        || value.amount_dispersion <= 0.0
        || value.legacy_amount_dispersion <= 0.0
        || value.amount_dispersion > value.legacy_amount_dispersion
    {
        return invalid(
            format!("{base}.amount_dispersion"),
            "must be positive and no greater than legacy_amount_dispersion",
        );
    }
    Ok(())
}

fn normalize_path(path: String) -> String {
    if path.is_empty() || path == "." {
        "document".to_owned()
    } else {
        path
    }
}

fn invalid<T>(
    field_path: impl Into<String>,
    message: impl Into<String>,
) -> Result<T, StationDocumentError> {
    Err(StationDocumentError::Validation {
        field_path: field_path.into(),
        message: message.into(),
    })
}

fn sha256_hex(bytes: &[u8]) -> String {
    let digest = Sha256::digest(bytes);
    format!("{digest:x}")
}
