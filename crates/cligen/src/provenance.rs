//! Deterministic generated-artifact provenance (SPEC-PROVENANCE revision 1).
//!
//! The DTOs in this module use declaration order as their canonical JSON
//! order. They contain no maps, clocks, environment values, or filesystem
//! resolution. Paths are retained exactly as lexical runspec values.

use std::error::Error;
use std::fmt;

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

/// The only provenance envelope revision accepted by this module.
pub const PROVENANCE_SCHEMA_VERSION: u32 = 1;
/// Source-authority identity independently pinned from the producer version.
pub const REFERENCE_TREE_SHA256: &str =
    "24966eaed920c2b9fd0b8a9ab1242b32053a730f0691a6a18dc4f44a3096bd5b";
/// Repository identity for the revision-1 producer.
pub const PRODUCER_REPOSITORY: &str = "https://github.com/rogerlew/cligen-rs";

/// One independently versioned schema identity.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SchemaIdentityV1 {
    pub id: String,
    pub version: String,
}

impl SchemaIdentityV1 {
    /// Legacy CLIGEN station parameter text.
    #[must_use]
    pub fn legacy_station() -> Self {
        Self::new("cligen_par", "5.32.3")
    }

    /// Modern fixed-monthly station JSON.
    #[must_use]
    pub fn modern_station() -> Self {
        Self::new("org.openwepp.cligen.station", "1")
    }

    /// Legacy observed `.prn` text.
    #[must_use]
    pub fn legacy_observed() -> Self {
        Self::new("cligen_prn", "5.32.3")
    }

    /// Frozen WEPP-compatible `.cli` text.
    #[must_use]
    pub fn cli_text() -> Self {
        Self::new("org.openwepp.cligen.cli.text", "1")
    }

    /// Parametric `.cli.parquet` output.
    #[must_use]
    pub fn cli_parquet() -> Self {
        Self::new("org.openwepp.cligen.cli.parquet", "1")
    }

    fn new(id: &str, version: &str) -> Self {
        Self {
            id: id.to_owned(),
            version: version.to_owned(),
        }
    }
}

/// Identity of the executable that produced an artifact.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ProducerV1 {
    pub name: String,
    pub version: String,
    pub repository: String,
    pub implementation_revision: Option<String>,
}

impl ProducerV1 {
    /// Construct the cligen-rs producer identity.
    ///
    /// The revision remains explicitly null unless a caller deliberately
    /// supplies one; this module does not inspect Git or the environment.
    #[must_use]
    pub fn cligen_rs(implementation_revision: Option<String>) -> Self {
        Self {
            name: "cligen-rs".to_owned(),
            version: env!("CARGO_PKG_VERSION").to_owned(),
            repository: PRODUCER_REPOSITORY.to_owned(),
            implementation_revision,
        }
    }
}

/// Artifact origin vocabulary for provenance revision 1.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ArtifactOriginV1 {
    #[serde(rename = "generated")]
    Generated,
}

/// Pinned source authority, distinct from the Rust producer.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SourceAuthorityV1 {
    pub cligen_version: String,
    pub reference_tree_sha256: String,
}

impl SourceAuthorityV1 {
    /// Construct the pinned CLIGEN 5.32.3 authority identity.
    #[must_use]
    pub fn cligen_5_32_3() -> Self {
        Self {
            cligen_version: crate::REFERENCE_VERSION.to_owned(),
            reference_tree_sha256: REFERENCE_TREE_SHA256.to_owned(),
        }
    }
}

/// Station-model identity, independent of station syntax.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum StationModelV1 {
    #[serde(rename = "fixed_monthly_5_32_3")]
    FixedMonthly5323,
}

/// Honest fit-state vocabulary for current station artifacts.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum FitStatusV1 {
    #[serde(rename = "unreported")]
    Unreported,
}

/// Explicit fit identity; revision 1 never invents a fitter or dataset.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct FitIdentityV1 {
    pub status: FitStatusV1,
    pub id: Option<String>,
}

/// Collection-level lineage cannot be inferred from a path-only runspec.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct StationCollectionIdentityV1 {
    pub status: FitStatusV1,
    pub name: Option<String>,
    pub version: Option<String>,
    pub archive_sha256: Option<String>,
}

impl StationCollectionIdentityV1 {
    #[must_use]
    pub fn unreported() -> Self {
        Self {
            status: FitStatusV1::Unreported,
            name: None,
            version: None,
            archive_sha256: None,
        }
    }
}

impl FitIdentityV1 {
    /// The only fit state supported by provenance revision 1.
    #[must_use]
    pub const fn unreported() -> Self {
        Self {
            status: FitStatusV1::Unreported,
            id: None,
        }
    }
}

/// Selected station input and syntax-independent model identity.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct StationProvenanceV1 {
    pub input_schema: SchemaIdentityV1,
    pub input_sha256: String,
    pub model: StationModelV1,
    pub parameter_set_sha256: String,
    pub fit: FitIdentityV1,
    pub collection: StationCollectionIdentityV1,
    pub legacy_source_sha256: String,
}

/// Stable generation-profile identifiers from the runspec surface.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum GenerationProfileV1 {
    #[serde(rename = "faithful_5_32_3")]
    Faithful5323,
    #[serde(rename = "fast_batch_v0")]
    FastBatchV0,
}

/// QC conditioning policy, absent when the selected profile has no knob.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum QcPolicyV1 {
    #[serde(rename = "faithful")]
    Faithful,
    #[serde(rename = "off")]
    Off,
}

/// Run mode identity.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum GenerationModeV1 {
    Continuous,
    Observed,
    SingleStorm,
    DesignStorm,
}

/// Monthly parameter interpolation identity.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum InterpolationV1 {
    None,
    Linear,
    Fourier,
    MonthlyMeanPreserving,
}

/// Source RNG scheme. Burn is intentionally not called a seed.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum RngSchemeV1 {
    #[serde(rename = "cligen_randn_5_32_3")]
    CligenRandn5323,
    #[serde(rename = "splitmix64_monthly_v0")]
    SplitMix64MonthlyV0,
}

/// Generation choices duplicated from the canonical effective runspec.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct GenerationProvenanceV1 {
    pub profile: GenerationProfileV1,
    pub qc_policy: Option<QcPolicyV1>,
    pub mode: GenerationModeV1,
    pub interpolation: InterpolationV1,
    pub rng_scheme: RngSchemeV1,
    pub burn_per_stream: u32,
}

/// Which station selector appeared in the runspec.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum StationSelectorV1 {
    #[serde(rename = "par")]
    LegacyPar,
    #[serde(rename = "document")]
    StationDocument,
}

/// Canonical station selection with its exact lexical path and input hash.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct EffectiveStationV1 {
    pub selector: StationSelectorV1,
    pub lexical_path: String,
    pub input_sha256: String,
}

/// Canonical observed selection with its exact lexical path and input hash.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct EffectiveObservedV1 {
    pub lexical_path: String,
    pub input_sha256: String,
}

/// One date supplied to or reported by a run.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DateV1 {
    pub year: i32,
    pub month: u8,
    pub day: u8,
}

/// Canonical resolved single/design-storm values.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct EffectiveStormV1 {
    pub date: DateV1,
    pub amount_in: f64,
    pub duration_h: Option<f64>,
    pub time_to_peak_fraction: Option<f64>,
    pub max_intensity_in_per_h: Option<f64>,
}

/// Canonical output selection and materialized defaults.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct EffectiveOutputV1 {
    pub cli_lexical_path: String,
    pub parquet_lexical_path: Option<String>,
    pub quality: bool,
    pub overwrite: bool,
    pub command_echo: String,
}

/// Fully materialized runspec content used as the stable run identity.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct EffectiveRunspecV1 {
    pub cligen_runspec: u32,
    pub station: EffectiveStationV1,
    pub mode: GenerationModeV1,
    pub begin_year: Option<i32>,
    pub years: Option<i32>,
    pub interpolation: InterpolationV1,
    pub burn: u32,
    pub generation_profile: GenerationProfileV1,
    pub qc_filter: Option<QcPolicyV1>,
    pub observed: Option<EffectiveObservedV1>,
    pub storm: Option<EffectiveStormV1>,
    pub output: EffectiveOutputV1,
}

impl EffectiveRunspecV1 {
    /// Compact canonical JSON whose SHA-256 is the stable run identifier.
    ///
    /// # Errors
    /// Returns the first field-addressed contract error or a serialization
    /// failure.
    pub fn to_compact_json_bytes(&self) -> Result<Vec<u8>, ProvenanceError> {
        self.validate()?;
        serialize_compact(self)
    }

    /// Validate and hash compact declaration-ordered JSON.
    ///
    /// # Errors
    /// Returns the first field-addressed contract error or a serialization
    /// failure.
    pub fn sha256(&self) -> Result<String, ProvenanceError> {
        let bytes = self.to_compact_json_bytes()?;
        Ok(sha256_hex(&bytes))
    }

    /// Validate all resolved values without changing lexical paths.
    ///
    /// # Errors
    /// Returns the first field-addressed contract error.
    pub fn validate(&self) -> Result<(), ProvenanceError> {
        validate_effective_runspec(self)
    }
}

/// Exact observed input identity, or null for a non-observed run.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ObservedInputV1 {
    pub schema: SchemaIdentityV1,
    pub input_sha256: String,
}

/// Why the emitted span ended.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum CoverageV1 {
    CompleteRun,
    ObservedSourceEnd,
    SingleEvent,
}

/// Actual emitted span, distinct from the requested span.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ActualOutputV1 {
    pub emitted_day_count: u64,
    pub first_date: Option<DateV1>,
    pub last_date: Option<DateV1>,
    pub coverage: CoverageV1,
}

/// Artifact media types for output schema revision 1.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum MediaTypeV1 {
    #[serde(rename = "text/plain; charset=utf-8")]
    CliText,
    #[serde(rename = "application/vnd.apache.parquet")]
    Parquet,
}

/// Calendar identity, explicit for continuous and storm outputs.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum CalendarV1 {
    ProlepticGregorian,
    SourceStormCalendar,
}

/// Precipitation representation supported by A1.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum PrecipitationRepresentationV1 {
    #[serde(rename = "parametric")]
    Parametric,
}

/// Numeric origin before text formatting or exact widening to f64.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum NumericOriginV1 {
    #[serde(rename = "cligen_f32_daily_row")]
    CligenF32DailyRow,
}

/// Output-artifact identity, independent of station and profile versions.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ArtifactIdentityV1 {
    pub output_schema: SchemaIdentityV1,
    pub media_type: MediaTypeV1,
    pub calendar: CalendarV1,
    pub precipitation_representation: PrecipitationRepresentationV1,
    pub numeric_origin: NumericOriginV1,
    /// Exact artifact bytes where an adjacent verifier can hash them. Parquet
    /// cannot self-embed its own digest and therefore carries null.
    pub content_sha256: Option<String>,
}

impl ArtifactIdentityV1 {
    /// Frozen WEPP-compatible text identity for a continuous/observed run.
    #[must_use]
    pub fn cli_text(content_sha256: String) -> Self {
        Self {
            output_schema: SchemaIdentityV1::cli_text(),
            media_type: MediaTypeV1::CliText,
            calendar: CalendarV1::ProlepticGregorian,
            precipitation_representation: PrecipitationRepresentationV1::Parametric,
            numeric_origin: NumericOriginV1::CligenF32DailyRow,
            content_sha256: Some(content_sha256),
        }
    }

    /// Frozen text identity for a deprecated single/design storm.
    #[must_use]
    pub fn storm_cli_text(content_sha256: String) -> Self {
        Self {
            calendar: CalendarV1::SourceStormCalendar,
            ..Self::cli_text(content_sha256)
        }
    }

    /// Parametric Parquet identity for a continuous/observed run.
    #[must_use]
    pub fn cli_parquet() -> Self {
        Self {
            output_schema: SchemaIdentityV1::cli_parquet(),
            media_type: MediaTypeV1::Parquet,
            calendar: CalendarV1::ProlepticGregorian,
            precipitation_representation: PrecipitationRepresentationV1::Parametric,
            numeric_origin: NumericOriginV1::CligenF32DailyRow,
            content_sha256: None,
        }
    }
}

/// Canonical provenance for one generated climate artifact.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ArtifactProvenanceV1 {
    pub provenance_schema_version: u32,
    pub producer: ProducerV1,
    pub origin: ArtifactOriginV1,
    pub source_authority: SourceAuthorityV1,
    pub station: StationProvenanceV1,
    pub generation: GenerationProvenanceV1,
    pub effective_runspec: EffectiveRunspecV1,
    pub effective_runspec_sha256: String,
    pub observed_input: Option<ObservedInputV1>,
    pub actual: ActualOutputV1,
    pub artifact: ArtifactIdentityV1,
}

impl ArtifactProvenanceV1 {
    /// Construct the revision-1 envelope and bind it to the canonical
    /// effective-runspec hash.
    ///
    /// # Errors
    /// Returns the first field-addressed contract error or a serialization
    /// failure while hashing the effective runspec.
    pub fn new(
        station: StationProvenanceV1,
        generation: GenerationProvenanceV1,
        effective_runspec: EffectiveRunspecV1,
        observed_input: Option<ObservedInputV1>,
        actual: ActualOutputV1,
        artifact: ArtifactIdentityV1,
    ) -> Result<Self, ProvenanceError> {
        let effective_runspec_sha256 = effective_runspec.sha256()?;
        let provenance = Self {
            provenance_schema_version: PROVENANCE_SCHEMA_VERSION,
            producer: ProducerV1::cligen_rs(None),
            origin: ArtifactOriginV1::Generated,
            source_authority: SourceAuthorityV1::cligen_5_32_3(),
            station,
            generation,
            effective_runspec,
            effective_runspec_sha256,
            observed_input,
            actual,
            artifact,
        };
        provenance.validate()?;
        Ok(provenance)
    }

    /// Parse one strict compact or pretty provenance JSON object.
    ///
    /// # Errors
    /// Returns a field-addressed parse or validation error. Trailing JSON
    /// values are rejected.
    pub fn parse_json(bytes: &[u8]) -> Result<Self, ProvenanceError> {
        let mut deserializer = serde_json::Deserializer::from_slice(bytes);
        let provenance: Self =
            serde_path_to_error::deserialize(&mut deserializer).map_err(|error| {
                ProvenanceError::Parse {
                    field_path: normalize_path(error.path().to_string()),
                    source: error.into_inner(),
                }
            })?;
        deserializer
            .end()
            .map_err(|source| ProvenanceError::Parse {
                field_path: "document".to_owned(),
                source,
            })?;
        provenance.validate()?;
        Ok(provenance)
    }

    /// Compact canonical JSON used in Parquet metadata.
    ///
    /// # Errors
    /// Validates before serialization and rejects stale or malformed hashes.
    pub fn to_compact_json_bytes(&self) -> Result<Vec<u8>, ProvenanceError> {
        self.validate()?;
        serialize_compact(self)
    }

    /// Pretty canonical JSON plus one LF used by text companions.
    ///
    /// # Errors
    /// Validates before serialization and rejects stale or malformed hashes.
    pub fn to_pretty_json_bytes(&self) -> Result<Vec<u8>, ProvenanceError> {
        self.validate()?;
        let mut bytes = serde_json::to_vec_pretty(self)
            .map_err(|source| ProvenanceError::Serialize { source })?;
        bytes.push(b'\n');
        Ok(bytes)
    }

    /// Validate identities, cross-field consistency, dates, and hashes.
    ///
    /// # Errors
    /// Returns the first field-addressed contract violation.
    pub fn validate(&self) -> Result<(), ProvenanceError> {
        validate_envelope(self)
    }

    /// Verify that adjacent text bytes are the artifact named by this
    /// provenance envelope.
    ///
    /// # Errors
    /// Rejects invalid/non-text provenance or a content-digest mismatch.
    pub fn verify_cli_bytes(&self, bytes: &[u8]) -> Result<(), ProvenanceError> {
        self.validate()?;
        if self.artifact.media_type != MediaTypeV1::CliText {
            return Err(invalid(
                "artifact.media_type",
                "CLI byte verification requires a text artifact",
            ));
        }
        let expected = self
            .artifact
            .content_sha256
            .as_deref()
            .ok_or_else(|| invalid("artifact.content_sha256", "is required"))?;
        require_hash_value("artifact.content_sha256", expected, &sha256_hex(bytes))
    }
}

/// Typed provenance parse, validation, or serialization failure.
#[derive(Debug)]
pub enum ProvenanceError {
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

impl fmt::Display for ProvenanceError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Parse { field_path, source } => {
                write!(f, "provenance {field_path}: {source}")
            }
            Self::Validation {
                field_path,
                message,
            } => write!(f, "provenance {field_path}: {message}"),
            Self::Serialize { source } => write!(f, "serialize provenance: {source}"),
        }
    }
}

impl Error for ProvenanceError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            Self::Parse { source, .. } | Self::Serialize { source } => Some(source),
            Self::Validation { .. } => None,
        }
    }
}

fn validate_envelope(value: &ArtifactProvenanceV1) -> Result<(), ProvenanceError> {
    validate_constants(value)?;
    validate_station(&value.station, &value.effective_runspec)?;
    validate_generation(&value.generation, &value.effective_runspec)?;
    value.effective_runspec.validate()?;
    validate_observed(value)?;
    validate_actual(&value.actual, &value.effective_runspec)?;
    validate_artifact(
        &value.artifact,
        value.generation.mode,
        &value.effective_runspec.output,
    )?;
    validate_hash("effective_runspec_sha256", &value.effective_runspec_sha256)?;
    let expected = value.effective_runspec.sha256()?;
    if value.effective_runspec_sha256 != expected {
        return Err(invalid(
            "effective_runspec_sha256",
            "does not match compact canonical effective_runspec JSON",
        ));
    }
    Ok(())
}

fn validate_constants(value: &ArtifactProvenanceV1) -> Result<(), ProvenanceError> {
    require_equal_u32(
        "provenance_schema_version",
        value.provenance_schema_version,
        PROVENANCE_SCHEMA_VERSION,
    )?;
    if value.producer.name != "cligen-rs" || value.producer.repository != PRODUCER_REPOSITORY {
        return Err(invalid(
            "producer",
            "must name the cligen-rs producer and repository",
        ));
    }
    if value.producer.version.is_empty() {
        return Err(invalid(
            "producer.version",
            "must be a non-empty package version",
        ));
    }
    if matches!(value.producer.implementation_revision.as_deref(), Some("")) {
        return Err(invalid(
            "producer.implementation_revision",
            "must be null or a non-empty deliberate build revision",
        ));
    }
    if value.source_authority.cligen_version != crate::REFERENCE_VERSION {
        return Err(invalid("source_authority.cligen_version", "must be 5.32.3"));
    }
    require_hash_value(
        "source_authority.reference_tree_sha256",
        &value.source_authority.reference_tree_sha256,
        REFERENCE_TREE_SHA256,
    )
}

fn validate_station(
    station: &StationProvenanceV1,
    runspec: &EffectiveRunspecV1,
) -> Result<(), ProvenanceError> {
    validate_station_schema(&station.input_schema, runspec.station.selector)?;
    validate_hash("station.input_sha256", &station.input_sha256)?;
    validate_hash(
        "station.parameter_set_sha256",
        &station.parameter_set_sha256,
    )?;
    validate_hash(
        "station.legacy_source_sha256",
        &station.legacy_source_sha256,
    )?;
    if station.fit != FitIdentityV1::unreported() {
        return Err(invalid(
            "station.fit",
            "revision 1 requires {status: unreported, id: null}",
        ));
    }
    if station.collection != StationCollectionIdentityV1::unreported() {
        return Err(invalid(
            "station.collection",
            "revision 1 path-only intake requires explicit unreported status",
        ));
    }
    if runspec.station.selector == StationSelectorV1::LegacyPar
        && station.legacy_source_sha256 != station.input_sha256
    {
        return Err(invalid(
            "station.legacy_source_sha256",
            "must equal input_sha256 for a selected legacy .par",
        ));
    }
    require_hash_value(
        "station.input_sha256",
        &station.input_sha256,
        &runspec.station.input_sha256,
    )
}

fn validate_station_schema(
    schema: &SchemaIdentityV1,
    selector: StationSelectorV1,
) -> Result<(), ProvenanceError> {
    let expected = match selector {
        StationSelectorV1::LegacyPar => SchemaIdentityV1::legacy_station(),
        StationSelectorV1::StationDocument => SchemaIdentityV1::modern_station(),
    };
    if schema != &expected {
        return Err(invalid(
            "station.input_schema",
            "does not match the effective station selector",
        ));
    }
    Ok(())
}

fn validate_generation(
    generation: &GenerationProvenanceV1,
    runspec: &EffectiveRunspecV1,
) -> Result<(), ProvenanceError> {
    if generation.profile != runspec.generation_profile
        || generation.qc_policy != runspec.qc_filter
        || generation.mode != runspec.mode
        || generation.interpolation != runspec.interpolation
        || generation.burn_per_stream != runspec.burn
    {
        return Err(invalid(
            "generation",
            "must agree with the canonical effective runspec",
        ));
    }
    let expected_rng = match generation.profile {
        GenerationProfileV1::Faithful5323 => RngSchemeV1::CligenRandn5323,
        GenerationProfileV1::FastBatchV0 => RngSchemeV1::SplitMix64MonthlyV0,
    };
    if generation.rng_scheme != expected_rng {
        return Err(invalid(
            "generation.rng_scheme",
            "does not match the declared generation profile",
        ));
    }
    match generation.profile {
        GenerationProfileV1::Faithful5323 if generation.qc_policy.is_none() => Err(invalid(
            "generation.qc_policy",
            "faithful_5_32_3 requires an explicit policy",
        )),
        GenerationProfileV1::FastBatchV0 if generation.qc_policy.is_some() => Err(invalid(
            "generation.qc_policy",
            "fast_batch_v0 has no QC policy knob",
        )),
        _ => Ok(()),
    }
}

fn validate_effective_runspec(value: &EffectiveRunspecV1) -> Result<(), ProvenanceError> {
    require_equal_u32("effective_runspec.cligen_runspec", value.cligen_runspec, 1)?;
    validate_lexical_path(
        "effective_runspec.station.lexical_path",
        &value.station.lexical_path,
    )?;
    validate_hash(
        "effective_runspec.station.input_sha256",
        &value.station.input_sha256,
    )?;
    validate_output(&value.output)?;
    if value.burn > i32::MAX as u32 {
        return Err(invalid(
            "effective_runspec.burn",
            "must fit the faithful signed 32-bit header/control field",
        ));
    }
    validate_profile_qc(value.generation_profile, value.qc_filter)?;
    validate_mode_fields(value)
}

fn validate_output(value: &EffectiveOutputV1) -> Result<(), ProvenanceError> {
    validate_lexical_path(
        "effective_runspec.output.cli_lexical_path",
        &value.cli_lexical_path,
    )?;
    if let Some(path) = &value.parquet_lexical_path {
        validate_lexical_path("effective_runspec.output.parquet_lexical_path", path)?;
        if !path.ends_with(".cli.parquet") {
            return Err(invalid(
                "effective_runspec.output.parquet_lexical_path",
                "must end in .cli.parquet",
            ));
        }
        if path == &value.cli_lexical_path {
            return Err(invalid(
                "effective_runspec.output.parquet_lexical_path",
                "must differ from the text output path",
            ));
        }
    }
    if value
        .command_echo
        .chars()
        .any(|character| matches!(character, '\0' | '\r' | '\n'))
    {
        return Err(invalid(
            "effective_runspec.output.command_echo",
            "must not contain NUL or record terminators",
        ));
    }
    Ok(())
}

fn validate_profile_qc(
    profile: GenerationProfileV1,
    qc: Option<QcPolicyV1>,
) -> Result<(), ProvenanceError> {
    match (profile, qc) {
        (GenerationProfileV1::Faithful5323, None) => Err(invalid(
            "effective_runspec.qc_filter",
            "faithful_5_32_3 requires a materialized QC policy",
        )),
        (GenerationProfileV1::FastBatchV0, Some(_)) => Err(invalid(
            "effective_runspec.qc_filter",
            "fast_batch_v0 has no QC policy knob",
        )),
        _ => Ok(()),
    }
}

fn validate_mode_fields(value: &EffectiveRunspecV1) -> Result<(), ProvenanceError> {
    match value.mode {
        GenerationModeV1::Continuous => validate_continuous(value),
        GenerationModeV1::Observed => validate_observed_runspec(value),
        GenerationModeV1::SingleStorm => validate_storm_runspec(value, true),
        GenerationModeV1::DesignStorm => validate_storm_runspec(value, false),
    }
}

fn validate_continuous(value: &EffectiveRunspecV1) -> Result<(), ProvenanceError> {
    validate_positive_years(value)?;
    reject_some("effective_runspec.observed", &value.observed)?;
    reject_some("effective_runspec.storm", &value.storm)
}

fn validate_observed_runspec(value: &EffectiveRunspecV1) -> Result<(), ProvenanceError> {
    validate_positive_years(value)?;
    let observed = value
        .observed
        .as_ref()
        .ok_or_else(|| invalid("effective_runspec.observed", "is required in observed mode"))?;
    validate_lexical_path(
        "effective_runspec.observed.lexical_path",
        &observed.lexical_path,
    )?;
    validate_hash(
        "effective_runspec.observed.input_sha256",
        &observed.input_sha256,
    )?;
    reject_some("effective_runspec.storm", &value.storm)
}

fn validate_storm_runspec(value: &EffectiveRunspecV1, single: bool) -> Result<(), ProvenanceError> {
    if value.begin_year.is_some() || value.years.is_some() {
        return Err(invalid(
            "effective_runspec.begin_year",
            "simulation span must be null in storm mode",
        ));
    }
    if value.interpolation != InterpolationV1::None {
        return Err(invalid(
            "effective_runspec.interpolation",
            "must be none in storm mode",
        ));
    }
    if value.output.parquet_lexical_path.is_some() {
        return Err(invalid(
            "effective_runspec.output.parquet_lexical_path",
            "Parquet is not supported in storm mode",
        ));
    }
    reject_some("effective_runspec.observed", &value.observed)?;
    let storm = value
        .storm
        .as_ref()
        .ok_or_else(|| invalid("effective_runspec.storm", "is required in storm mode"))?;
    validate_storm(storm, single)
}

fn validate_storm(value: &EffectiveStormV1, single: bool) -> Result<(), ProvenanceError> {
    validate_source_storm_date("effective_runspec.storm.date", value.date)?;
    validate_positive_f64("effective_runspec.storm.amount_in", value.amount_in)?;
    if single {
        let duration = require_some("effective_runspec.storm.duration_h", value.duration_h)?;
        validate_positive_f64("effective_runspec.storm.duration_h", duration)?;
        let peak = require_some(
            "effective_runspec.storm.time_to_peak_fraction",
            value.time_to_peak_fraction,
        )?;
        let peak_f32 = peak as f32;
        if !(peak.is_finite()
            && peak_f32.is_finite()
            && (peak_f32 as f64).to_bits() == peak.to_bits()
            && 0.0 < peak
            && peak <= 1.0)
        {
            return Err(invalid(
                "effective_runspec.storm.time_to_peak_fraction",
                "must be an exact finite f32 widening in (0, 1]",
            ));
        }
        let intensity = require_some(
            "effective_runspec.storm.max_intensity_in_per_h",
            value.max_intensity_in_per_h,
        )?;
        validate_positive_f64("effective_runspec.storm.max_intensity_in_per_h", intensity)?;
    } else if value.duration_h.is_some()
        || value.time_to_peak_fraction.is_some()
        || value.max_intensity_in_per_h.is_some()
    {
        return Err(invalid(
            "effective_runspec.storm",
            "design storm permits only date and amount_in",
        ));
    }
    Ok(())
}

fn validate_positive_years(value: &EffectiveRunspecV1) -> Result<(), ProvenanceError> {
    if value.begin_year.is_none_or(|year| year < 1) {
        return Err(invalid(
            "effective_runspec.begin_year",
            "must be a resolved integer greater than or equal to 1",
        ));
    }
    if value.years.is_none_or(|years| years < 1) {
        return Err(invalid(
            "effective_runspec.years",
            "must be a resolved integer greater than or equal to 1",
        ));
    }
    let span_invalid = match requested_span(value) {
        Ok((_, last)) => last.year > 99_999,
        Err(_) => true,
    };
    if span_invalid {
        return Err(invalid(
            "effective_runspec.years",
            "requested final year must fit the legacy positive i5 output field",
        ));
    }
    Ok(())
}

fn validate_observed(value: &ArtifactProvenanceV1) -> Result<(), ProvenanceError> {
    match (
        value.generation.mode,
        &value.observed_input,
        &value.effective_runspec.observed,
    ) {
        (GenerationModeV1::Observed, Some(input), Some(effective)) => {
            if input.schema != SchemaIdentityV1::legacy_observed() {
                return Err(invalid(
                    "observed_input.schema",
                    "revision 1 supports cligen_prn/5.32.3 only",
                ));
            }
            validate_hash("observed_input.input_sha256", &input.input_sha256)?;
            require_hash_value(
                "observed_input.input_sha256",
                &input.input_sha256,
                &effective.input_sha256,
            )
        }
        (GenerationModeV1::Observed, _, _) => {
            Err(invalid("observed_input", "is required in observed mode"))
        }
        (_, None, None) => Ok(()),
        _ => Err(invalid(
            "observed_input",
            "must be null outside observed mode",
        )),
    }
}

fn validate_actual(
    value: &ActualOutputV1,
    runspec: &EffectiveRunspecV1,
) -> Result<(), ProvenanceError> {
    let span = match (value.emitted_day_count, value.first_date, value.last_date) {
        (0, None, None) => None,
        (0, _, _) => {
            return Err(invalid(
                "actual",
                "zero emitted days require null first_date and last_date",
            ));
        }
        (_, Some(first), Some(last)) => {
            validate_actual_date("actual.first_date", first, runspec.mode)?;
            validate_actual_date("actual.last_date", last, runspec.mode)?;
            if first > last {
                return Err(invalid("actual.last_date", "must not precede first_date"));
            }
            Some((first, last))
        }
        _ => {
            return Err(invalid(
                "actual",
                "nonzero emitted days require both first_date and last_date",
            ));
        }
    };
    validate_coverage_kind(value.coverage, runspec.mode)?;
    validate_actual_count(value.emitted_day_count, span, runspec.mode)?;
    validate_coverage_span(value, span, runspec)
}

fn validate_coverage_kind(
    coverage: CoverageV1,
    mode: GenerationModeV1,
) -> Result<(), ProvenanceError> {
    let coverage_ok = match mode {
        GenerationModeV1::Continuous => coverage == CoverageV1::CompleteRun,
        GenerationModeV1::Observed => matches!(
            coverage,
            CoverageV1::CompleteRun | CoverageV1::ObservedSourceEnd
        ),
        GenerationModeV1::SingleStorm | GenerationModeV1::DesignStorm => {
            coverage == CoverageV1::SingleEvent
        }
    };
    if !coverage_ok {
        return Err(invalid(
            "actual.coverage",
            "does not match the generation mode",
        ));
    }
    Ok(())
}

fn validate_actual_count(
    count: u64,
    span: Option<(DateV1, DateV1)>,
    mode: GenerationModeV1,
) -> Result<(), ProvenanceError> {
    let expected = match (span, mode) {
        (None, _) => 0,
        (Some((first, last)), GenerationModeV1::Continuous | GenerationModeV1::Observed) => {
            let days = gregorian_ordinal(last) - gregorian_ordinal(first) + 1;
            u64::try_from(days).map_err(|_| {
                invalid(
                    "actual.emitted_day_count",
                    "date span cannot be represented as a day count",
                )
            })?
        }
        (Some((first, last)), GenerationModeV1::SingleStorm | GenerationModeV1::DesignStorm) => {
            if first != last {
                return Err(invalid(
                    "actual.last_date",
                    "single-event first_date and last_date must match",
                ));
            }
            1
        }
    };
    if count != expected {
        return Err(invalid(
            "actual.emitted_day_count",
            "does not equal the inclusive emitted date span",
        ));
    }
    Ok(())
}

fn validate_coverage_span(
    value: &ActualOutputV1,
    span: Option<(DateV1, DateV1)>,
    runspec: &EffectiveRunspecV1,
) -> Result<(), ProvenanceError> {
    match value.coverage {
        CoverageV1::CompleteRun => {
            let requested = requested_span(runspec)?;
            if span != Some(requested) {
                return Err(invalid(
                    "actual",
                    "complete_run must equal the requested first and last dates",
                ));
            }
        }
        CoverageV1::ObservedSourceEnd => {
            let (requested_first, requested_last) = requested_span(runspec)?;
            let Some((first, last)) = span else {
                return Err(invalid(
                    "actual",
                    "observed_source_end requires a non-empty emitted span",
                ));
            };
            if first != requested_first || last >= requested_last {
                return Err(invalid(
                    "actual",
                    "observed_source_end must be a strict prefix of the requested span",
                ));
            }
        }
        CoverageV1::SingleEvent => {
            if span.is_none() || value.emitted_day_count != 1 {
                return Err(invalid(
                    "actual",
                    "single_event must contain exactly one emitted source-calendar date",
                ));
            }
        }
    }
    Ok(())
}

fn requested_span(value: &EffectiveRunspecV1) -> Result<(DateV1, DateV1), ProvenanceError> {
    let begin = value
        .begin_year
        .ok_or_else(|| invalid("effective_runspec.begin_year", "is required"))?;
    let years = value
        .years
        .ok_or_else(|| invalid("effective_runspec.years", "is required"))?;
    let last_year = begin
        .checked_add(years - 1)
        .ok_or_else(|| invalid("effective_runspec.years", "requested final year overflows"))?;
    Ok((
        DateV1 {
            year: begin,
            month: 1,
            day: 1,
        },
        DateV1 {
            year: last_year,
            month: 12,
            day: 31,
        },
    ))
}

fn gregorian_ordinal(value: DateV1) -> i64 {
    let completed_years = i64::from(value.year - 1);
    let mut ordinal =
        365 * completed_years + completed_years / 4 - completed_years / 100 + completed_years / 400;
    let month_lengths = [31_i64, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    ordinal += month_lengths[..usize::from(value.month - 1)]
        .iter()
        .sum::<i64>();
    if value.month > 2 && is_leap_year(value.year) {
        ordinal += 1;
    }
    ordinal + i64::from(value.day)
}

fn validate_artifact(
    value: &ArtifactIdentityV1,
    mode: GenerationModeV1,
    output: &EffectiveOutputV1,
) -> Result<(), ProvenanceError> {
    validate_artifact_schema(value)?;
    validate_artifact_digest(value)?;
    validate_artifact_mode(value, mode)?;
    validate_artifact_output_selection(value, output)?;
    validate_artifact_calendar(value, mode)
}

fn validate_artifact_schema(value: &ArtifactIdentityV1) -> Result<(), ProvenanceError> {
    let expected_schema = match value.media_type {
        MediaTypeV1::CliText => SchemaIdentityV1::cli_text(),
        MediaTypeV1::Parquet => SchemaIdentityV1::cli_parquet(),
    };
    if value.output_schema != expected_schema {
        return Err(invalid(
            "artifact.output_schema",
            "does not match artifact media_type",
        ));
    }
    Ok(())
}

fn validate_artifact_digest(value: &ArtifactIdentityV1) -> Result<(), ProvenanceError> {
    match (value.media_type, &value.content_sha256) {
        (MediaTypeV1::CliText, Some(hash)) => validate_hash("artifact.content_sha256", hash)?,
        (MediaTypeV1::CliText, None) => {
            return Err(invalid(
                "artifact.content_sha256",
                "text artifacts require an exact content digest",
            ));
        }
        (MediaTypeV1::Parquet, None) => {}
        (MediaTypeV1::Parquet, Some(_)) => {
            return Err(invalid(
                "artifact.content_sha256",
                "self-embedded Parquet provenance must use null",
            ));
        }
    }
    Ok(())
}

fn validate_artifact_mode(
    value: &ArtifactIdentityV1,
    mode: GenerationModeV1,
) -> Result<(), ProvenanceError> {
    let is_storm = matches!(
        mode,
        GenerationModeV1::SingleStorm | GenerationModeV1::DesignStorm
    );
    if is_storm && value.media_type == MediaTypeV1::Parquet {
        return Err(invalid(
            "artifact.media_type",
            "Parquet is not supported in storm mode",
        ));
    }
    Ok(())
}

fn validate_artifact_output_selection(
    value: &ArtifactIdentityV1,
    output: &EffectiveOutputV1,
) -> Result<(), ProvenanceError> {
    if value.media_type == MediaTypeV1::Parquet && output.parquet_lexical_path.is_none() {
        return Err(invalid(
            "artifact.media_type",
            "Parquet artifact requires an effective Parquet output selection",
        ));
    }
    Ok(())
}

fn validate_artifact_calendar(
    value: &ArtifactIdentityV1,
    mode: GenerationModeV1,
) -> Result<(), ProvenanceError> {
    let is_storm = matches!(
        mode,
        GenerationModeV1::SingleStorm | GenerationModeV1::DesignStorm
    );
    let expected_calendar = if is_storm {
        CalendarV1::SourceStormCalendar
    } else {
        CalendarV1::ProlepticGregorian
    };
    if value.calendar != expected_calendar {
        return Err(invalid(
            "artifact.calendar",
            "does not match the generation mode",
        ));
    }
    Ok(())
}

fn validate_date(path: &str, value: DateV1) -> Result<(), ProvenanceError> {
    if !(1..=99_999).contains(&value.year) || !(1..=12).contains(&value.month) {
        return Err(invalid(path, "must be a valid proleptic Gregorian date"));
    }
    let max_day = days_in_month(value.year, value.month);
    if value.day == 0 || value.day > max_day {
        return Err(invalid(path, "must be a valid proleptic Gregorian date"));
    }
    Ok(())
}

fn validate_source_storm_date(path: &str, value: DateV1) -> Result<(), ProvenanceError> {
    if !(-9_999..=99_999).contains(&value.year) || !(1..=12).contains(&value.month) {
        return Err(invalid(path, "must be a valid source-storm-calendar date"));
    }
    let max_day = source_storm_days_in_month(value.year, value.month);
    if value.day == 0 || value.day > max_day {
        return Err(invalid(path, "must be a valid source-storm-calendar date"));
    }
    Ok(())
}

fn validate_actual_date(
    path: &str,
    value: DateV1,
    mode: GenerationModeV1,
) -> Result<(), ProvenanceError> {
    match mode {
        GenerationModeV1::SingleStorm | GenerationModeV1::DesignStorm => {
            validate_source_storm_date(path, value)
        }
        GenerationModeV1::Continuous | GenerationModeV1::Observed => validate_date(path, value),
    }
}

fn days_in_month(year: i32, month: u8) -> u8 {
    match month {
        2 if is_leap_year(year) => 29,
        2 => 28,
        4 | 6 | 9 | 11 => 30,
        _ => 31,
    }
}

fn source_storm_days_in_month(year: i32, month: u8) -> u8 {
    match month {
        2 if source_storm_leap_year(year) => 29,
        2 => 28,
        4 | 6 | 9 | 11 => 30,
        _ => 31,
    }
}

fn is_leap_year(year: i32) -> bool {
    year % 400 == 0 || (year % 4 == 0 && year % 100 != 0)
}

fn source_storm_leap_year(year: i32) -> bool {
    year - year / 400 * 400 == 0 || (year - year / 4 * 4 == 0 && year - year / 100 * 100 == 0)
}

fn validate_positive_f64(path: &str, value: f64) -> Result<(), ProvenanceError> {
    let narrowed = value as f32;
    if !(value.is_finite()
        && narrowed.is_finite()
        && (narrowed as f64).to_bits() == value.to_bits()
        && value > 0.0)
    {
        return Err(invalid(
            path,
            "must be an exact finite f32 widening greater than 0",
        ));
    }
    Ok(())
}

fn validate_lexical_path(path: &str, value: &str) -> Result<(), ProvenanceError> {
    if value.is_empty()
        || value
            .chars()
            .any(|character| matches!(character, '\0' | '\r' | '\n'))
    {
        return Err(invalid(
            path,
            "must be a non-empty lexical path without NUL or record terminators",
        ));
    }
    Ok(())
}

fn validate_hash(path: &str, value: &str) -> Result<(), ProvenanceError> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(invalid(path, "must be 64 lowercase hexadecimal characters"));
    }
    Ok(())
}

fn require_hash_value(path: &str, value: &str, expected: &str) -> Result<(), ProvenanceError> {
    validate_hash(path, value)?;
    if value != expected {
        return Err(invalid(
            path,
            "does not match the required content identity",
        ));
    }
    Ok(())
}

fn require_equal_u32(path: &str, value: u32, expected: u32) -> Result<(), ProvenanceError> {
    if value != expected {
        return Err(invalid(path, &format!("must be {expected}")));
    }
    Ok(())
}

fn require_some<T: Copy>(path: &str, value: Option<T>) -> Result<T, ProvenanceError> {
    value.ok_or_else(|| invalid(path, "is required"))
}

fn reject_some<T>(path: &str, value: &Option<T>) -> Result<(), ProvenanceError> {
    if value.is_some() {
        return Err(invalid(path, "must be null for this mode"));
    }
    Ok(())
}

fn serialize_compact<T: Serialize>(value: &T) -> Result<Vec<u8>, ProvenanceError> {
    serde_json::to_vec(value).map_err(|source| ProvenanceError::Serialize { source })
}

/// Return the lowercase SHA-256 content identity of exact input bytes.
#[must_use]
pub fn sha256_hex(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

fn normalize_path(path: String) -> String {
    if path.is_empty() || path == "." {
        "document".to_owned()
    } else {
        path
    }
}

fn invalid(path: &str, message: &str) -> ProvenanceError {
    ProvenanceError::Validation {
        field_path: path.to_owned(),
        message: message.to_owned(),
    }
}
