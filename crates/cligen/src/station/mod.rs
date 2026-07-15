//! Versioned modern station documents and their model-independent intake
//! boundary.
//!
//! The station-file schema and the station model are separate compatibility
//! axes. [`StationDocumentV1`] is a JSON transport; [`FixedMonthly5323`] is
//! the faithful typed station state consumed by the generator. Neither type
//! selects a generation profile or an output schema.

mod document;
mod document_v2;
mod model;

pub use document::{
    parameter_set_sha256, AdapterId, FixedMonthly5323Document, IdentityParameters,
    LegacySourceFormat, LocationParameters, PrecipitationParameters, SolarRadiationParameters,
    StationDocumentError, StationDocumentV1, StationLineage, StationModelId, StationParameters,
    StationUnits, StormParameters, TemperatureParameters, Unit, WindDirectionParameters,
    WindInterpolationStation, WindParameters, ADAPTER_VERSION, STATION_SCHEMA_VERSION,
};
pub use document_v2::{
    routed_parameter_set_sha256, A8cDailyPrecipitation, A8cMonthCoefficients,
    A8cSeasonCoefficients, DailyPrecipitationRoute, StationDocumentV2, StationModelIdV2,
    A8A_ANALYSIS_SHA256, A8A_FIT_ID, A8B_DECISION_SHA256, A8B_FIT_ID, STATION_SCHEMA_VERSION_V2,
};
pub use model::FixedMonthly5323;
