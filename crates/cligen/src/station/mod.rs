//! Versioned modern station documents and their model-independent intake
//! boundary.
//!
//! The station-file schema and the station model are separate compatibility
//! axes. [`StationDocumentV1`] is a JSON transport; [`FixedMonthly5323`] is
//! the faithful typed station state consumed by the generator. Neither type
//! selects a generation profile or an output schema.

mod document;
mod model;

pub use document::{
    AdapterId, FixedMonthly5323Document, IdentityParameters, LegacySourceFormat,
    LocationParameters, PrecipitationParameters, SolarRadiationParameters, StationDocumentError,
    StationDocumentV1, StationLineage, StationModelId, StationParameters, StationUnits,
    StormParameters, TemperatureParameters, Unit, WindDirectionParameters,
    WindInterpolationStation, WindParameters, ADAPTER_VERSION, STATION_SCHEMA_VERSION,
};
pub use model::FixedMonthly5323;
