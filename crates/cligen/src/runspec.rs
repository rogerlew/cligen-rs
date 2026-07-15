//! The schema-versioned `inp.yaml` intake boundary from SPEC-RUNSPEC.
//!
//! This is interface code, not a ported Fortran unit. It resolves lexical
//! runspec paths at the `(document, base_dir)` boundary and passes complete,
//! already-open bytes to the faithful `RunInputs` seam.

use std::fmt;
use std::fs::{self, File, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};

use serde::Deserialize;
use unicode_casefold::UnicodeCaseFold as _;
use unicode_normalization::UnicodeNormalization as _;

use crate::modes::{
    run_to_cli_resolved, GeneratedRun, ResolvedRunInputs, RunError, RunTermination,
};
use crate::observed::{PrnError, PrnReader};
use crate::par::{ParError, ParFile};
use crate::parquet_output::{self, ParquetArtifactV1, ParquetOutputError};
use crate::profile::{GenerationProfile, QcFilter};
use crate::provenance::{
    ActualOutputV1, ArtifactIdentityV1, ArtifactProvenanceV1, CoverageV1, DateV1,
    EffectiveObservedV1, EffectiveOutputV1, EffectiveRunspecV1, EffectiveStationV1,
    EffectiveStormV1, FitIdentityV1, GenerationModeV1, GenerationProfileV1, GenerationProvenanceV1,
    InterpolationV1, ObservedInputV1, ProvenanceError, QcPolicyV1, RngSchemeV1, SchemaIdentityV1,
    StationCollectionIdentityV1, StationModelV1, StationProvenanceV1, StationSelectorV1,
};
use crate::quality::{self, QualityError};
use crate::station::{
    parameter_set_sha256, routed_parameter_set_sha256, A8cDailyPrecipitation, FixedMonthly5323,
    StationDocumentError, StationDocumentV1, StationDocumentV2, StationModelIdV2,
};
use crate::storm::SingleStormParams;
use crate::typed_output::{ClimateIdentityV1, ClimateRowV1, TypedOutputError};

/// The sole currently-supported runspec schema revision.
pub const RUNSPEC_VERSION: i64 = 1;

/// A deserialized SPEC-RUNSPEC revision 1 document.
#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RunspecDocument {
    #[serde(default, deserialize_with = "deserialize_present_value")]
    pub cligen_runspec: Option<i64>,
    #[serde(default, deserialize_with = "deserialize_present_value")]
    pub station: Option<StationSpec>,
    #[serde(default, deserialize_with = "deserialize_present_value")]
    pub mode: Option<RunMode>,
    #[serde(default, deserialize_with = "deserialize_present_value")]
    pub simulation: Option<SimulationSpec>,
    #[serde(default)]
    pub rng: RngSpec,
    #[serde(default)]
    pub generation_profile: GenerationProfile,
    /// SPEC-RUNSPEC rev 5 / SPEC-GENERATION-PROFILES: the QC
    /// conditioning policy. Rejected with `fast_batch_v0` (pre-knob).
    #[serde(default, deserialize_with = "deserialize_present_value")]
    pub qc_filter: Option<QcFilter>,
    #[serde(default, deserialize_with = "deserialize_present_value")]
    pub observed: Option<ObservedSpec>,
    #[serde(default, deserialize_with = "deserialize_present_value")]
    pub single_storm: Option<SingleStormSpec>,
    #[serde(default, deserialize_with = "deserialize_present_value")]
    pub design_storm: Option<DesignStormSpec>,
    #[serde(default, deserialize_with = "deserialize_present_value")]
    pub output: Option<OutputSpec>,
}

/// The single-station parameter-file selection.
#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct StationSpec {
    #[serde(default, deserialize_with = "deserialize_present_string")]
    pub par: Option<String>,
    #[serde(default, deserialize_with = "deserialize_present_string")]
    pub document: Option<String>,
}

fn deserialize_present_string<'de, D>(deserializer: D) -> Result<Option<String>, D::Error>
where
    D: serde::Deserializer<'de>,
{
    struct PresentStringVisitor;

    impl serde::de::Visitor<'_> for PresentStringVisitor {
        type Value = Option<String>;

        fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
            formatter.write_str("a non-null string path")
        }

        fn visit_str<E>(self, value: &str) -> Result<Self::Value, E>
        where
            E: serde::de::Error,
        {
            Ok(Some(value.to_owned()))
        }

        fn visit_string<E>(self, value: String) -> Result<Self::Value, E>
        where
            E: serde::de::Error,
        {
            Ok(Some(value))
        }
    }

    deserializer.deserialize_any(PresentStringVisitor)
}

fn deserialize_present_value<'de, D, T>(deserializer: D) -> Result<Option<T>, D::Error>
where
    D: serde::Deserializer<'de>,
    T: Deserialize<'de>,
{
    T::deserialize(deserializer).map(Some)
}

fn deserialize_present_bool<'de, D>(deserializer: D) -> Result<Option<bool>, D::Error>
where
    D: serde::Deserializer<'de>,
{
    struct PresentBoolVisitor;

    impl serde::de::Visitor<'_> for PresentBoolVisitor {
        type Value = Option<bool>;

        fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
            formatter.write_str("a non-null boolean")
        }

        fn visit_bool<E>(self, value: bool) -> Result<Self::Value, E>
        where
            E: serde::de::Error,
        {
            Ok(Some(value))
        }
    }

    deserializer.deserialize_any(PresentBoolVisitor)
}

/// Generation mode names from SPEC-RUNSPEC.
#[derive(Debug, Clone, Copy, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum RunMode {
    Continuous,
    Observed,
    SingleStorm,
    DesignStorm,
}

impl RunMode {
    fn iopt(self) -> i32 {
        match self {
            RunMode::Continuous => 5,
            RunMode::Observed => 6,
            RunMode::SingleStorm => 4,
            RunMode::DesignStorm => 7,
        }
    }

    fn legacy_flag(self) -> Option<i32> {
        match self {
            RunMode::Continuous => None,
            _ => Some(self.iopt()),
        }
    }
}

/// The optional continuous/observed simulation controls.
#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SimulationSpec {
    #[serde(default, deserialize_with = "deserialize_present_value")]
    pub begin_year: Option<i32>,
    #[serde(default, deserialize_with = "deserialize_present_value")]
    pub years: Option<i32>,
    #[serde(default)]
    pub interpolation: Interpolation,
}

/// Monthly parameter interpolation selection.
#[derive(Debug, Clone, Copy, Default, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum Interpolation {
    #[default]
    None,
    Linear,
    Fourier,
    MonthlyMeanPreserving,
}

impl Interpolation {
    fn source_value(self) -> i32 {
        match self {
            Interpolation::None => 0,
            Interpolation::Linear => 1,
            Interpolation::Fourier => 2,
            Interpolation::MonthlyMeanPreserving => 3,
        }
    }
}

/// Optional RNG burn count.
#[derive(Debug, Clone, Default, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RngSpec {
    #[serde(default, deserialize_with = "deserialize_present_value")]
    pub burn: Option<i64>,
}

/// Observed-series input selection.
#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ObservedSpec {
    #[serde(default, deserialize_with = "deserialize_present_string")]
    pub prn: Option<String>,
}

/// A source-calendar date used by a storm mode.
#[derive(Debug, Clone, Copy, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct StormDate {
    #[serde(default, deserialize_with = "deserialize_present_value")]
    pub month: Option<i32>,
    #[serde(default, deserialize_with = "deserialize_present_value")]
    pub day: Option<i32>,
    #[serde(default, deserialize_with = "deserialize_present_value")]
    pub year: Option<i32>,
}

/// The typed iopt-4 single-storm inputs.
#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SingleStormSpec {
    #[serde(default, deserialize_with = "deserialize_present_value")]
    pub date: Option<StormDate>,
    #[serde(default, deserialize_with = "deserialize_present_value")]
    pub amount_in: Option<f64>,
    #[serde(default, deserialize_with = "deserialize_present_value")]
    pub duration_h: Option<f64>,
    #[serde(default, deserialize_with = "deserialize_present_value")]
    pub time_to_peak_fraction: Option<f64>,
    #[serde(default, deserialize_with = "deserialize_present_value")]
    pub max_intensity_in_per_h: Option<f64>,
}

/// The typed iopt-7 design-storm inputs.
#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DesignStormSpec {
    #[serde(default, deserialize_with = "deserialize_present_value")]
    pub date: Option<StormDate>,
    #[serde(default, deserialize_with = "deserialize_present_value")]
    pub amount_in: Option<f64>,
}

/// Destination and output-surface controls.
#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct OutputSpec {
    #[serde(default, deserialize_with = "deserialize_present_string")]
    pub cli: Option<String>,
    /// Optional SPEC-CLI-PARQUET revision-1 companion. A1 retains the
    /// required legacy text destination during migration.
    #[serde(default, deserialize_with = "deserialize_present_string")]
    pub parquet: Option<String>,
    #[serde(default)]
    pub overwrite: bool,
    #[serde(default, deserialize_with = "deserialize_present_string")]
    pub command_echo: Option<String>,
    /// SPEC-RUNSPEC rev 4 / SPEC-QUALITY-REPORT: emit the
    /// `<output.cli>.quality.json` sidecar (default true).
    #[serde(default, deserialize_with = "deserialize_present_bool")]
    pub quality: Option<bool>,
}

/// A typed, field-addressable failure at the runspec boundary.
#[derive(Debug)]
pub enum RunspecError {
    Parse {
        field_path: String,
        message: String,
    },
    Validation {
        field_path: String,
        message: String,
    },
    Input {
        field_path: String,
        path: PathBuf,
        message: String,
    },
    Output {
        field_path: String,
        path: PathBuf,
        message: String,
    },
    OutputCollision {
        path: PathBuf,
    },
    Run(RunError),
    Provenance(ProvenanceError),
    TypedOutput(TypedOutputError),
    Parquet(ParquetOutputError),
    Quality(QualityError),
}

impl fmt::Display for RunspecError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            RunspecError::Parse {
                field_path,
                message,
            }
            | RunspecError::Validation {
                field_path,
                message,
            } => write!(f, "{field_path}: {message}"),
            RunspecError::Input {
                field_path,
                path,
                message,
            }
            | RunspecError::Output {
                field_path,
                path,
                message,
            } => write!(f, "{field_path} ({}) : {message}", path.display()),
            RunspecError::OutputCollision { path } => write!(
                f,
                "output.overwrite: refusing to replace existing output {}",
                path.display()
            ),
            RunspecError::Run(error) => write!(f, "generation: {error}"),
            RunspecError::Provenance(error) => write!(f, "provenance: {error}"),
            RunspecError::TypedOutput(error) => write!(f, "typed output: {error}"),
            RunspecError::Parquet(error) => write!(f, "output.parquet: {error}"),
            RunspecError::Quality(error) => write!(f, "output.quality: {error}"),
        }
    }
}

impl std::error::Error for RunspecError {}

/// The resolved document and its declared input bytes, ready for the
/// faithful orchestration seam.
#[derive(Debug)]
pub struct PreparedRun {
    pub output_path: PathBuf,
    /// Optional SPEC-CLI-PARQUET companion destination.
    pub parquet_path: Option<PathBuf>,
    pub overwrite: bool,
    pub iopt: i32,
    pub interpolation: i32,
    pub burn: u32,
    pub generation_profile: GenerationProfile,
    pub begin_year: Option<i32>,
    pub years: Option<i32>,
    pub command_echo: String,
    pub storm: Option<SingleStormParams>,
    /// Resolved `qc_filter` (default `Faithful`).
    pub qc_filter: QcFilter,
    /// SPEC-RUNSPEC rev 4 `output.quality` (default true).
    pub quality: bool,
    station: FixedMonthly5323,
    daily_precipitation: Option<A8cDailyPrecipitation>,
    station_provenance: StationProvenanceV1,
    effective_runspec: EffectiveRunspecV1,
    observed_input: Option<ObservedInputV1>,
    prn_bytes: Option<Vec<u8>>,
    resolved_output_path: PathBuf,
    resolved_parquet_path: Option<PathBuf>,
}

/// One generated revision-1 typed climate result from a single generator pass.
#[derive(Debug, Clone, PartialEq)]
pub struct GeneratedClimateV1 {
    pub legacy_cli: String,
    pub rows: Vec<ClimateRowV1>,
    /// Provenance for the frozen text artifact. Parquet emission reuses the
    /// run identity with its own independently versioned artifact descriptor.
    pub provenance: ArtifactProvenanceV1,
    pub process: crate::quality::report::ProcessMetrics,
}

impl PreparedRun {
    /// Generate the `.cli` text without touching the output path.
    pub fn generate(&self) -> Result<String, RunspecError> {
        Ok(self.generate_output()?.render_cli())
    }

    /// Generate the frozen text projection and public typed row stream in one
    /// pass without touching output paths.
    ///
    /// # Errors
    /// Returns generation, provenance, or typed-row validation failures.
    pub fn generate_climate_v1(&self) -> Result<GeneratedClimateV1, RunspecError> {
        let generated = self.generate_output()?;
        self.build_climate_v1(&generated)
    }

    fn generate_output(&self) -> Result<GeneratedRun, RunspecError> {
        self.validate_prepared_snapshot()?;
        run_to_cli_resolved(&ResolvedRunInputs {
            iopt: self.iopt,
            interp: self.interpolation,
            burn: self.burn,
            generation_profile: self.generation_profile,
            qc_filter: self.qc_filter,
            begin_year: self.begin_year,
            years: self.years,
            station: &self.station,
            daily_precipitation: self.daily_precipitation.as_ref(),
            prn_bytes: self.prn_bytes.as_deref(),
            storm: self.storm,
            version: 5.3230,
            command_echo: &self.command_echo,
        })
        .map_err(RunspecError::Run)
    }

    /// Generate one typed climate stream and publish the required `.cli`, its
    /// mandatory provenance companion, optional `.cli.parquet`, and enabled
    /// quality report. `output.overwrite` governs both declared climate
    /// destinations; derived companions are rewritten to match the text.
    pub fn generate_and_write(&self) -> Result<(), RunspecError> {
        self.validate_prepared_snapshot()?;
        let _lock = OutputLock::acquire(&self.output_path)?;
        self.preflight_outputs()?;
        let generated = self.generate_output()?;
        let provenance =
            self.artifact_provenance(&generated, self.text_artifact_identity(&generated))?;
        let legacy_cli = generated.render_cli();
        let mut output = self.open_output()?;
        output
            .write_all(legacy_cli.as_bytes())
            .map_err(|error| output_error(&self.output_path, error))?;
        self.write_provenance_sidecar(&provenance)?;
        if let Some(path) = &self.parquet_path {
            let rows = self.build_climate_rows_v1(&generated)?;
            self.write_parquet(path, &generated, &rows)?;
        }
        if self.quality {
            self.write_quality_sidecar(&legacy_cli, &provenance, &generated.process)?;
        }
        Ok(())
    }

    /// The sidecar destination: `<output.cli>.quality.json`.
    #[must_use]
    pub fn quality_sidecar_path(&self) -> PathBuf {
        let mut name = self.output_path.as_os_str().to_owned();
        name.push(".quality.json");
        PathBuf::from(name)
    }

    /// Mandatory text provenance destination: `<output.cli>.provenance.json`.
    #[must_use]
    pub fn provenance_sidecar_path(&self) -> PathBuf {
        let mut name = self.output_path.as_os_str().to_owned();
        name.push(".provenance.json");
        PathBuf::from(name)
    }

    /// Generate and return the full shared provenance block for the frozen
    /// text artifact. Actual coverage is generation-derived and therefore
    /// cannot be constructed truthfully from requested fields alone.
    ///
    /// # Errors
    /// Returns generation or provenance validation failures.
    pub fn quality_provenance(&self) -> Result<ArtifactProvenanceV1, RunspecError> {
        let generated = self.generate_output()?;
        self.artifact_provenance(&generated, self.text_artifact_identity(&generated))
    }

    /// Generate an in-memory quality report with provenance bound inside the
    /// trusted run orchestration path.
    ///
    /// # Errors
    /// Returns generation, provenance, intake, or report failures.
    pub fn generate_quality_report(&self) -> Result<quality::QualityReport, RunspecError> {
        let generated = self.generate_output()?;
        let provenance =
            self.artifact_provenance(&generated, self.text_artifact_identity(&generated))?;
        let legacy_cli = generated.render_cli();
        quality::compute_report_with_station(
            &legacy_cli,
            &self.station,
            &self.station_provenance.legacy_source_sha256,
            Some(self.quality_station_identity()),
            Some(provenance),
            Some(generated.process),
        )
        .map_err(RunspecError::Quality)
    }

    fn build_climate_v1(
        &self,
        generated: &GeneratedRun,
    ) -> Result<GeneratedClimateV1, RunspecError> {
        let provenance =
            self.artifact_provenance(generated, self.text_artifact_identity(generated))?;
        let rows = self.build_climate_rows_v1(generated)?;
        Ok(GeneratedClimateV1 {
            legacy_cli: generated.render_cli(),
            rows,
            provenance,
            process: generated.process.clone(),
        })
    }

    fn build_climate_rows_v1(
        &self,
        generated: &GeneratedRun,
    ) -> Result<Vec<ClimateRowV1>, RunspecError> {
        if matches!(self.iopt, 4 | 7) {
            return Err(invalid(
                "typed_output",
                "ClimateRowV1 is supported only for continuous and observed modes",
            ));
        }
        let identity = ClimateIdentityV1 {
            run_id: self
                .effective_runspec
                .sha256()
                .map_err(RunspecError::Provenance)?,
            generation_profile: self.generation_profile.id().to_owned(),
            station_parameter_set_sha256: self.station_provenance.parameter_set_sha256.clone(),
        };
        let mut rows = Vec::with_capacity(generated.rows.len());
        for (offset, source) in generated.rows.iter().enumerate() {
            let sim_day_index = i32::try_from(offset + 1).map_err(|_| {
                invalid(
                    "typed_output.sim_day_index",
                    "generated row count exceeds i32",
                )
            })?;
            rows.push(
                ClimateRowV1::try_from_daily(&identity, sim_day_index, source)
                    .map_err(RunspecError::TypedOutput)?,
            );
        }
        Ok(rows)
    }

    fn artifact_provenance(
        &self,
        generated: &GeneratedRun,
        artifact: ArtifactIdentityV1,
    ) -> Result<ArtifactProvenanceV1, RunspecError> {
        ArtifactProvenanceV1::new(
            self.station_provenance.clone(),
            GenerationProvenanceV1 {
                profile: self.effective_runspec.generation_profile,
                qc_policy: self.effective_runspec.qc_filter,
                mode: self.effective_runspec.mode,
                interpolation: self.effective_runspec.interpolation,
                rng_scheme: provenance_rng(self.generation_profile),
                burn_per_stream: self.effective_runspec.burn,
            },
            self.effective_runspec.clone(),
            self.observed_input.clone(),
            self.actual_output(generated),
            artifact,
        )
        .map_err(RunspecError::Provenance)
    }

    fn actual_output(&self, generated: &GeneratedRun) -> ActualOutputV1 {
        let date = |row: &crate::modes::DailyRow| DateV1 {
            year: row.iyear,
            // Generated rows are source-calendar validated before emission.
            month: row.mo as u8,
            day: row.jd as u8,
        };
        let requested_last = self
            .begin_year
            .zip(self.years)
            .and_then(|(begin, years)| begin.checked_add(years - 1))
            .map(|year| DateV1 {
                year,
                month: 12,
                day: 31,
            });
        let actual_last = generated.rows.last().map(date);
        let coverage = match self.iopt {
            4 | 7 => CoverageV1::SingleEvent,
            6 if generated.termination == RunTermination::EarlyStop
                && actual_last != requested_last =>
            {
                CoverageV1::ObservedSourceEnd
            }
            _ => CoverageV1::CompleteRun,
        };
        ActualOutputV1 {
            emitted_day_count: generated.rows.len() as u64,
            first_date: generated.rows.first().map(date),
            last_date: actual_last,
            coverage,
        }
    }

    fn text_artifact_identity(&self, generated: &GeneratedRun) -> ArtifactIdentityV1 {
        let content_sha256 = quality::sha256_hex(generated.render_cli().as_bytes());
        match self.iopt {
            4 | 7 => ArtifactIdentityV1::storm_cli_text(content_sha256),
            _ => ArtifactIdentityV1::cli_text(content_sha256),
        }
    }

    fn preflight_outputs(&self) -> Result<(), RunspecError> {
        self.validate_prepared_snapshot()?;
        self.validate_distinct_destinations()?;
        if self.overwrite {
            return Ok(());
        }
        for (field_path, path) in std::iter::once(("output.cli", &self.output_path)).chain(
            self.parquet_path
                .as_ref()
                .map(|path| ("output.parquet", path)),
        ) {
            if path.try_exists().map_err(|error| RunspecError::Output {
                field_path: field_path.to_owned(),
                path: path.clone(),
                message: error.to_string(),
            })? {
                return Err(RunspecError::OutputCollision { path: path.clone() });
            }
        }
        Ok(())
    }

    fn validate_prepared_snapshot(&self) -> Result<(), RunspecError> {
        self.validate_output_snapshot()?;
        let mode = runtime_mode(self.effective_runspec.mode);
        ensure_snapshot(
            self.iopt == mode.iopt(),
            "prepared_run.iopt",
            "generation mode changed after runspec resolution",
        )?;
        ensure_snapshot(
            self.interpolation == runtime_interpolation(self.effective_runspec.interpolation),
            "prepared_run.interpolation",
            "interpolation changed after runspec resolution",
        )?;
        ensure_snapshot(
            self.burn == self.effective_runspec.burn,
            "prepared_run.burn",
            "burn changed after runspec resolution",
        )?;
        ensure_snapshot(
            provenance_profile(self.generation_profile)
                == self.effective_runspec.generation_profile
                && provenance_qc(self.generation_profile, self.qc_filter)
                    == self.effective_runspec.qc_filter,
            "prepared_run.generation_profile",
            "generation profile or QC policy changed after runspec resolution",
        )?;
        ensure_snapshot(
            self.begin_year == self.effective_runspec.begin_year
                && self.years == self.effective_runspec.years,
            "prepared_run.simulation",
            "simulation span changed after runspec resolution",
        )?;
        ensure_snapshot(
            provenance_storm(mode, self.storm) == self.effective_runspec.storm,
            "prepared_run.storm",
            "storm inputs changed after runspec resolution",
        )
    }

    fn validate_output_snapshot(&self) -> Result<(), RunspecError> {
        ensure_snapshot(
            self.output_path == self.resolved_output_path
                && self.parquet_path == self.resolved_parquet_path,
            "prepared_run.output",
            "resolved output destinations changed after runspec resolution",
        )?;
        ensure_snapshot(
            self.overwrite == self.effective_runspec.output.overwrite
                && self.quality == self.effective_runspec.output.quality
                && self.command_echo == self.effective_runspec.output.command_echo,
            "prepared_run.output",
            "output controls changed after runspec resolution",
        )
    }

    fn validate_distinct_destinations(&self) -> Result<(), RunspecError> {
        let provenance = self.provenance_sidecar_path();
        let provenance_staging = companion_staging_path(&provenance)?;
        let mut final_paths = vec![
            ("output.cli", self.output_path.clone()),
            ("output.provenance", provenance),
        ];
        let mut paths = vec![
            final_paths[0].clone(),
            final_paths[1].clone(),
            ("output.provenance.staging", provenance_staging.clone()),
        ];
        paths.push((
            "output.lock",
            output_lock_path(&destination_identity(&self.output_path)?)?,
        ));
        let mut reserved_staging = vec![provenance_staging];
        if self.quality {
            let quality = self.quality_sidecar_path();
            let quality_staging = companion_staging_path(&quality)?;
            final_paths.push(("output.quality", quality.clone()));
            paths.push(("output.quality", quality));
            paths.push(("output.quality.staging", quality_staging.clone()));
            reserved_staging.push(quality_staging);
        }
        if let Some(parquet) = &self.parquet_path {
            let staging = parquet_output::staging_path(parquet).map_err(RunspecError::Parquet)?;
            final_paths.push(("output.parquet", parquet.clone()));
            paths.push(("output.parquet", parquet.clone()));
            paths.push(("output.parquet.staging", staging.clone()));
            reserved_staging.push(staging);
        }
        for (field, path) in final_paths {
            reject_directory_destination(field, &path)?;
        }
        validate_unique_destinations(&paths)?;
        for path in reserved_staging {
            reject_existing_staging(&path)?;
        }
        Ok(())
    }

    fn write_provenance_sidecar(
        &self,
        provenance: &ArtifactProvenanceV1,
    ) -> Result<(), RunspecError> {
        let bytes = provenance
            .to_pretty_json_bytes()
            .map_err(RunspecError::Provenance)?;
        let path = self.provenance_sidecar_path();
        write_atomic_companion(&path, &bytes, "output.provenance")
    }

    fn write_parquet(
        &self,
        path: &Path,
        generated: &GeneratedRun,
        rows: &[ClimateRowV1],
    ) -> Result<(), RunspecError> {
        let provenance = self.artifact_provenance(generated, ArtifactIdentityV1::cli_parquet())?;
        parquet_output::write_cli_parquet_v1(
            path,
            ParquetArtifactV1 {
                provenance: &provenance,
            },
            rows,
            self.overwrite,
        )
        .map_err(RunspecError::Parquet)
    }

    fn write_quality_sidecar(
        &self,
        legacy_cli: &str,
        provenance: &ArtifactProvenanceV1,
        process: &crate::quality::report::ProcessMetrics,
    ) -> Result<(), RunspecError> {
        let report = quality::compute_report_with_station(
            legacy_cli,
            &self.station,
            &self.station_provenance.legacy_source_sha256,
            Some(self.quality_station_identity()),
            Some(provenance.clone()),
            Some(process.clone()),
        )
        .map_err(RunspecError::Quality)?;
        let bytes = report.to_json_bytes().map_err(RunspecError::Quality)?;
        let path = self.quality_sidecar_path();
        write_atomic_companion(&path, &bytes, "output.quality")
    }

    fn quality_station_identity(&self) -> (&'static str, &str) {
        let model = match self.station_provenance.model {
            StationModelV1::FixedMonthly5323 => "fixed_monthly_5_32_3",
            StationModelV1::A8cIntegratedDailyV1 => "a8c_integrated_daily_v1",
        };
        (model, &self.station_provenance.parameter_set_sha256)
    }

    fn open_output(&self) -> Result<File, RunspecError> {
        if self.overwrite {
            File::create(&self.output_path).map_err(|error| output_error(&self.output_path, error))
        } else {
            OpenOptions::new()
                .write(true)
                .create_new(true)
                .open(&self.output_path)
                .map_err(|error| {
                    if error.kind() == std::io::ErrorKind::AlreadyExists {
                        RunspecError::OutputCollision {
                            path: self.output_path.clone(),
                        }
                    } else {
                        output_error(&self.output_path, error)
                    }
                })
        }
    }
}

#[derive(Debug, Clone, Copy)]
struct ModeFields {
    iopt: i32,
    interpolation: i32,
    begin_year: Option<i32>,
    years: Option<i32>,
    storm: Option<SingleStormParams>,
}

fn provenance_mode(mode: RunMode) -> GenerationModeV1 {
    match mode {
        RunMode::Continuous => GenerationModeV1::Continuous,
        RunMode::Observed => GenerationModeV1::Observed,
        RunMode::SingleStorm => GenerationModeV1::SingleStorm,
        RunMode::DesignStorm => GenerationModeV1::DesignStorm,
    }
}

fn runtime_mode(mode: GenerationModeV1) -> RunMode {
    match mode {
        GenerationModeV1::Continuous => RunMode::Continuous,
        GenerationModeV1::Observed => RunMode::Observed,
        GenerationModeV1::SingleStorm => RunMode::SingleStorm,
        GenerationModeV1::DesignStorm => RunMode::DesignStorm,
    }
}

fn runtime_interpolation(interpolation: InterpolationV1) -> i32 {
    match interpolation {
        InterpolationV1::None => 0,
        InterpolationV1::Linear => 1,
        InterpolationV1::Fourier => 2,
        InterpolationV1::MonthlyMeanPreserving => 3,
    }
}

fn ensure_snapshot(condition: bool, field_path: &str, message: &str) -> Result<(), RunspecError> {
    if condition {
        Ok(())
    } else {
        Err(invalid(field_path, message))
    }
}

fn provenance_profile(profile: GenerationProfile) -> GenerationProfileV1 {
    match profile {
        GenerationProfile::Faithful5323 => GenerationProfileV1::Faithful5323,
        GenerationProfile::FastBatchV0 => GenerationProfileV1::FastBatchV0,
        GenerationProfile::A8cRoutedDailyV1 => GenerationProfileV1::A8cRoutedDailyV1,
    }
}

fn provenance_rng(profile: GenerationProfile) -> RngSchemeV1 {
    match profile {
        GenerationProfile::Faithful5323 => RngSchemeV1::CligenRandn5323,
        GenerationProfile::FastBatchV0 => RngSchemeV1::SplitMix64MonthlyV0,
        GenerationProfile::A8cRoutedDailyV1 => RngSchemeV1::CligenRandn5323PlusSplitMix64DailyV1,
    }
}

fn provenance_qc(profile: GenerationProfile, qc: QcFilter) -> Option<QcPolicyV1> {
    match profile {
        GenerationProfile::FastBatchV0 => None,
        GenerationProfile::Faithful5323 | GenerationProfile::A8cRoutedDailyV1 => Some(match qc {
            QcFilter::Faithful => QcPolicyV1::Faithful,
            QcFilter::Off => QcPolicyV1::Off,
        }),
    }
}

fn validate_profile_station(
    profile: GenerationProfile,
    qc: QcFilter,
    mode: RunMode,
    interpolation: i32,
    station: &ResolvedStation,
) -> Result<(), RunspecError> {
    match profile {
        GenerationProfile::A8cRoutedDailyV1 => {
            if station.daily_precipitation.is_none() {
                return Err(invalid(
                    "station.document",
                    "a8c_routed_daily_v1 requires a revision-2 routed station document",
                ));
            }
            if qc != QcFilter::Faithful {
                return Err(invalid(
                    "qc_filter",
                    "a8c_routed_daily_v1 requires faithful",
                ));
            }
            if mode != RunMode::Continuous {
                return Err(invalid(
                    "mode",
                    "a8c_routed_daily_v1 supports continuous mode only",
                ));
            }
            if interpolation != 0 {
                return Err(invalid(
                    "simulation.interpolation",
                    "a8c_routed_daily_v1 requires none",
                ));
            }
            Ok(())
        }
        GenerationProfile::Faithful5323 | GenerationProfile::FastBatchV0 => {
            if station.daily_precipitation.is_some() {
                Err(invalid(
                    "station.document",
                    "revision-2 routed documents require generation_profile a8c_routed_daily_v1",
                ))
            } else {
                Ok(())
            }
        }
    }
}

fn provenance_interpolation(interpolation: i32) -> InterpolationV1 {
    match interpolation {
        1 => InterpolationV1::Linear,
        2 => InterpolationV1::Fourier,
        3 => InterpolationV1::MonthlyMeanPreserving,
        _ => InterpolationV1::None,
    }
}

fn provenance_storm(mode: RunMode, storm: Option<SingleStormParams>) -> Option<EffectiveStormV1> {
    let storm = storm?;
    let date = DateV1 {
        year: storm.ibyear,
        // SPEC-RUNSPEC validation has already established these ranges.
        month: storm.mo as u8,
        day: storm.jd as u8,
    };
    match mode {
        RunMode::SingleStorm => Some(EffectiveStormV1 {
            date,
            amount_in: storm.damt as f64,
            duration_h: Some(storm.usdur as f64),
            time_to_peak_fraction: Some(storm.ustpr as f64),
            max_intensity_in_per_h: Some(storm.uxmav as f64),
        }),
        RunMode::DesignStorm => Some(EffectiveStormV1 {
            date,
            amount_in: storm.damt as f64,
            duration_h: None,
            time_to_peak_fraction: None,
            max_intensity_in_per_h: None,
        }),
        RunMode::Continuous | RunMode::Observed => None,
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum StationSyntax {
    LegacyPar,
    Document,
}

#[derive(Debug, Clone, Copy)]
struct StationSelection<'a> {
    lexical: &'a str,
    syntax: StationSyntax,
}

#[derive(Debug)]
struct ResolvedStation {
    model: FixedMonthly5323,
    daily_precipitation: Option<A8cDailyPrecipitation>,
    legacy_par_sha256: String,
    input_schema: SchemaIdentityV1,
    input_sha256: String,
    parameter_set_sha256: String,
    model_id: StationModelV1,
    fit: FitIdentityV1,
}

#[derive(Debug)]
struct ResolvedObserved {
    lexical: String,
    initial_year: i32,
    bytes: Vec<u8>,
    input_sha256: String,
}

impl RunspecDocument {
    /// Parse exactly one YAML runspec document with field-path parse errors.
    pub fn parse(document: &str) -> Result<Self, RunspecError> {
        let mut documents = serde_yaml::Deserializer::from_str(document);
        let deserializer = documents.next().ok_or_else(|| RunspecError::Parse {
            field_path: "document".to_owned(),
            message: "expected one YAML document".to_owned(),
        })?;
        let runspec = serde_path_to_error::deserialize(deserializer).map_err(|error| {
            let field_path = normalized_parse_path(error.path().to_string());
            RunspecError::Parse {
                field_path,
                message: error.into_inner().to_string(),
            }
        })?;
        if documents.next().is_some() {
            return Err(RunspecError::Parse {
                field_path: "document".to_owned(),
                message: "expected exactly one YAML document".to_owned(),
            });
        }
        Ok(runspec)
    }

    /// Check every SPEC-RUNSPEC field and mode-conditional invariant.
    pub fn validate(&self) -> Result<(), RunspecError> {
        self.validate_required_fields()?;
        self.validate_scalar_domains()?;
        self.validate_mode_blocks()
    }

    /// Resolve lexical paths against `base_dir`, open and parse declared
    /// inputs, then materialize defaults for the faithful run seam.
    pub fn resolve(&self, base_dir: &Path) -> Result<PreparedRun, RunspecError> {
        self.validate()?;
        let station_selection = self.station_selection()?;
        let output = self.output_ref()?;
        let mode = self.mode_value()?;
        let output_lexical = required_text(output.cli.as_deref(), "output.cli")?;
        let output_path = resolve_path(base_dir, output_lexical);
        let parquet_lexical = output.parquet.clone();
        let parquet_path = parquet_lexical
            .as_deref()
            .map(|path| resolve_path(base_dir, path));
        if parquet_path.as_ref() == Some(&output_path) {
            return Err(invalid(
                "output.parquet",
                "must resolve to a path distinct from output.cli",
            ));
        }
        let station = read_station(base_dir, station_selection)?;
        let prn = self.read_observed_input(base_dir, mode)?;
        let fields =
            self.resolve_mode_fields(mode, prn.as_ref().map(|value| value.initial_year))?;
        let burn = self.burn_value()?;
        let command_echo = output.command_echo.clone().unwrap_or_else(|| {
            self.canonical_echo(
                mode,
                station_selection,
                prn.as_ref().map(|value| value.lexical.as_str()),
                output_lexical,
                fields.interpolation,
                burn,
            )
        });
        let generation_profile = self.generation_profile;
        let qc_filter = self.qc_filter.unwrap_or_default();
        validate_profile_station(
            generation_profile,
            qc_filter,
            mode,
            fields.interpolation,
            &station,
        )?;
        let command_echo = qc_filter.command_echo(generation_profile.command_echo(command_echo));
        let provenance_mode = provenance_mode(mode);
        let provenance_profile = provenance_profile(generation_profile);
        let provenance_qc = provenance_qc(generation_profile, qc_filter);
        let provenance_interpolation = provenance_interpolation(fields.interpolation);
        let station_selector = match station_selection.syntax {
            StationSyntax::LegacyPar => StationSelectorV1::LegacyPar,
            StationSyntax::Document => StationSelectorV1::StationDocument,
        };
        let station_provenance = StationProvenanceV1 {
            input_schema: station.input_schema.clone(),
            input_sha256: station.input_sha256.clone(),
            model: station.model_id,
            parameter_set_sha256: station.parameter_set_sha256.clone(),
            fit: station.fit.clone(),
            collection: StationCollectionIdentityV1::unreported(),
            legacy_source_sha256: station.legacy_par_sha256.clone(),
        };
        let effective_observed = prn.as_ref().map(|value| EffectiveObservedV1 {
            lexical_path: value.lexical.clone(),
            input_sha256: value.input_sha256.clone(),
        });
        let observed_input = prn.as_ref().map(|value| ObservedInputV1 {
            schema: SchemaIdentityV1::legacy_observed(),
            input_sha256: value.input_sha256.clone(),
        });
        let effective_runspec = EffectiveRunspecV1 {
            cligen_runspec: RUNSPEC_VERSION as u32,
            station: EffectiveStationV1 {
                selector: station_selector,
                lexical_path: station_selection.lexical.to_owned(),
                input_sha256: station.input_sha256,
            },
            mode: provenance_mode,
            begin_year: fields.begin_year,
            years: fields.years,
            interpolation: provenance_interpolation,
            burn,
            generation_profile: provenance_profile,
            qc_filter: provenance_qc,
            observed: effective_observed,
            storm: provenance_storm(mode, fields.storm),
            output: EffectiveOutputV1 {
                cli_lexical_path: output_lexical.to_owned(),
                parquet_lexical_path: parquet_lexical.clone(),
                quality: output.quality.unwrap_or(true),
                overwrite: output.overwrite,
                command_echo: command_echo.clone(),
            },
        };
        effective_runspec
            .validate()
            .map_err(RunspecError::Provenance)?;
        Ok(PreparedRun {
            output_path: output_path.clone(),
            parquet_path: parquet_path.clone(),
            overwrite: output.overwrite,
            iopt: fields.iopt,
            interpolation: fields.interpolation,
            burn,
            generation_profile,
            begin_year: fields.begin_year,
            years: fields.years,
            command_echo,
            storm: fields.storm,
            qc_filter,
            quality: output.quality.unwrap_or(true),
            station: station.model,
            daily_precipitation: station.daily_precipitation,
            station_provenance,
            effective_runspec,
            observed_input,
            prn_bytes: prn.map(|value| value.bytes),
            resolved_output_path: output_path,
            resolved_parquet_path: parquet_path,
        })
    }

    fn validate_required_fields(&self) -> Result<(), RunspecError> {
        let version = self
            .cligen_runspec
            .ok_or_else(|| missing("cligen_runspec"))?;
        if version != RUNSPEC_VERSION {
            return Err(invalid("cligen_runspec", "must equal 1"));
        }
        self.station_selection()?;
        self.mode_value()?;
        let output = self.output_ref()?;
        let cli = required_text(output.cli.as_deref(), "output.cli")?;
        if let Some(parquet) = output.parquet.as_deref() {
            let parquet = required_text(Some(parquet), "output.parquet")?;
            if !parquet.ends_with(".cli.parquet") {
                return Err(invalid("output.parquet", "must end with .cli.parquet"));
            }
            if parquet == cli {
                return Err(invalid(
                    "output.parquet",
                    "must be distinct from output.cli",
                ));
            }
        }
        if output.command_echo.as_ref().is_some_and(|echo| {
            echo.chars()
                .any(|character| matches!(character, '\0' | '\r' | '\n'))
        }) {
            return Err(invalid(
                "output.command_echo",
                "must not contain NUL or record terminators",
            ));
        }
        Ok(())
    }

    fn validate_scalar_domains(&self) -> Result<(), RunspecError> {
        if let Some(simulation) = &self.simulation {
            positive_year(simulation.begin_year, "simulation.begin_year")?;
            positive_year(simulation.years, "simulation.years")?;
        }
        if self.qc_filter.is_some() && self.generation_profile == GenerationProfile::FastBatchV0 {
            return Err(invalid(
                "qc_filter",
                "is not accepted with generation_profile fast_batch_v0 (pre-knob profile, always unconditioned)",
            ));
        }
        self.burn_value()?;
        if let Some(storm) = &self.single_storm {
            validate_single_storm(storm)?;
        }
        if let Some(storm) = &self.design_storm {
            validate_design_storm(storm)?;
        }
        Ok(())
    }

    fn validate_mode_blocks(&self) -> Result<(), RunspecError> {
        match self.mode_value()? {
            RunMode::Continuous => self.validate_continuous_blocks(),
            RunMode::Observed => self.validate_observed_blocks(),
            RunMode::SingleStorm => self.validate_single_storm_blocks(),
            RunMode::DesignStorm => self.validate_design_storm_blocks(),
        }
    }

    fn validate_continuous_blocks(&self) -> Result<(), RunspecError> {
        let simulation = self
            .simulation
            .as_ref()
            .ok_or_else(|| missing("simulation"))?;
        let begin = positive_required(simulation.begin_year, "simulation.begin_year")?;
        let years = positive_required(simulation.years, "simulation.years")?;
        validate_loop_span(begin, years)?;
        reject_present(self.observed.is_some(), "observed", "continuous mode")?;
        reject_present(
            self.single_storm.is_some(),
            "single_storm",
            "continuous mode",
        )?;
        reject_present(
            self.design_storm.is_some(),
            "design_storm",
            "continuous mode",
        )
    }

    fn validate_observed_blocks(&self) -> Result<(), RunspecError> {
        let observed = self.observed.as_ref().ok_or_else(|| missing("observed"))?;
        required_text(observed.prn.as_deref(), "observed.prn")?;
        reject_present(self.single_storm.is_some(), "single_storm", "observed mode")?;
        reject_present(self.design_storm.is_some(), "design_storm", "observed mode")
    }

    fn validate_single_storm_blocks(&self) -> Result<(), RunspecError> {
        reject_present(self.simulation.is_some(), "simulation", "single_storm mode")?;
        self.single_storm
            .as_ref()
            .ok_or_else(|| missing("single_storm"))?;
        reject_present(self.observed.is_some(), "observed", "single_storm mode")?;
        reject_present(
            self.design_storm.is_some(),
            "design_storm",
            "single_storm mode",
        )?;
        reject_present(
            self.output_ref()?.parquet.is_some(),
            "output.parquet",
            "single_storm mode",
        )
    }

    fn validate_design_storm_blocks(&self) -> Result<(), RunspecError> {
        reject_present(self.simulation.is_some(), "simulation", "design_storm mode")?;
        self.design_storm
            .as_ref()
            .ok_or_else(|| missing("design_storm"))?;
        reject_present(self.observed.is_some(), "observed", "design_storm mode")?;
        reject_present(
            self.single_storm.is_some(),
            "single_storm",
            "design_storm mode",
        )?;
        reject_present(
            self.output_ref()?.parquet.is_some(),
            "output.parquet",
            "design_storm mode",
        )
    }

    fn read_observed_input(
        &self,
        base_dir: &Path,
        mode: RunMode,
    ) -> Result<Option<ResolvedObserved>, RunspecError> {
        if mode != RunMode::Observed {
            return Ok(None);
        }
        let observed = self.observed.as_ref().ok_or_else(|| missing("observed"))?;
        let lexical = required_text(observed.prn.as_deref(), "observed.prn")?.to_owned();
        let path = resolve_path(base_dir, &lexical);
        let bytes = fs::read(&path).map_err(|error| input_error("observed.prn", &path, error))?;
        let reader =
            PrnReader::new(&bytes).map_err(|error| prn_error("observed.prn", &path, error))?;
        let initial_year = reader
            .initial_year()
            .map_err(|error| prn_error("observed.prn.initial_year", &path, error))?;
        if initial_year < 1 {
            return Err(invalid(
                "observed.prn.initial_year",
                "must resolve to an integer greater than or equal to 1",
            ));
        }
        let input_sha256 = quality::sha256_hex(&bytes);
        Ok(Some(ResolvedObserved {
            lexical,
            initial_year,
            bytes,
            input_sha256,
        }))
    }

    fn resolve_mode_fields(
        &self,
        mode: RunMode,
        observed_initial_year: Option<i32>,
    ) -> Result<ModeFields, RunspecError> {
        let interpolation = self
            .simulation
            .as_ref()
            .map_or(Interpolation::None, |simulation| simulation.interpolation)
            .source_value();
        match mode {
            RunMode::Continuous => self.resolve_continuous(interpolation),
            RunMode::Observed => self.resolve_observed(interpolation, observed_initial_year),
            RunMode::SingleStorm => self.resolve_single_storm(),
            RunMode::DesignStorm => self.resolve_design_storm(),
        }
    }

    fn resolve_continuous(&self, interpolation: i32) -> Result<ModeFields, RunspecError> {
        let simulation = self
            .simulation
            .as_ref()
            .ok_or_else(|| missing("simulation"))?;
        Ok(ModeFields {
            iopt: RunMode::Continuous.iopt(),
            interpolation,
            begin_year: Some(positive_required(
                simulation.begin_year,
                "simulation.begin_year",
            )?),
            years: Some(positive_required(simulation.years, "simulation.years")?),
            storm: None,
        })
    }

    fn resolve_observed(
        &self,
        interpolation: i32,
        observed_initial_year: Option<i32>,
    ) -> Result<ModeFields, RunspecError> {
        let simulation = self.simulation.as_ref();
        let initial_year =
            observed_initial_year.ok_or_else(|| missing("observed.prn.initial_year"))?;
        Ok(ModeFields {
            iopt: RunMode::Observed.iopt(),
            interpolation,
            begin_year: Some(
                simulation
                    .and_then(|value| value.begin_year)
                    .unwrap_or(initial_year),
            ),
            years: Some(simulation.and_then(|value| value.years).unwrap_or(100)),
            storm: None,
        })
    }

    fn resolve_single_storm(&self) -> Result<ModeFields, RunspecError> {
        let storm = self
            .single_storm
            .as_ref()
            .ok_or_else(|| missing("single_storm"))?;
        Ok(ModeFields {
            iopt: RunMode::SingleStorm.iopt(),
            interpolation: 0,
            begin_year: None,
            years: None,
            storm: Some(single_storm_params(storm)?),
        })
    }

    fn resolve_design_storm(&self) -> Result<ModeFields, RunspecError> {
        let storm = self
            .design_storm
            .as_ref()
            .ok_or_else(|| missing("design_storm"))?;
        Ok(ModeFields {
            iopt: RunMode::DesignStorm.iopt(),
            interpolation: 0,
            begin_year: None,
            years: None,
            storm: Some(design_storm_params(storm)?),
        })
    }

    fn canonical_echo(
        &self,
        mode: RunMode,
        station: StationSelection<'_>,
        prn: Option<&str>,
        output: &str,
        interpolation: i32,
        burn: u32,
    ) -> String {
        let mut fields = Vec::new();
        if burn != 0 {
            fields.push(format!("-r{burn}"));
        }
        fields.push(match station.syntax {
            StationSyntax::LegacyPar => format!("-i{}", station.lexical),
            StationSyntax::Document => {
                format!("--station-document={}", station.lexical)
            }
        });
        if let Some(prn) = prn {
            fields.push(format!("-O{prn}"));
        }
        if output != "wepp.cli" {
            fields.push(format!("-o{output}"));
        }
        if let Some(flag) = mode.legacy_flag() {
            fields.push(format!("-t{flag}"));
        }
        if interpolation != 0 {
            fields.push(format!("-I{interpolation}"));
        }
        fields.join(" ")
    }

    fn station_ref(&self) -> Result<&StationSpec, RunspecError> {
        self.station.as_ref().ok_or_else(|| missing("station"))
    }

    fn station_selection(&self) -> Result<StationSelection<'_>, RunspecError> {
        let station = self.station_ref()?;
        match (station.par.as_deref(), station.document.as_deref()) {
            (Some(par), None) => Ok(StationSelection {
                lexical: required_text(Some(par), "station.par")?,
                syntax: StationSyntax::LegacyPar,
            }),
            (None, Some(document)) => Ok(StationSelection {
                lexical: required_text(Some(document), "station.document")?,
                syntax: StationSyntax::Document,
            }),
            (None, None) => Err(invalid(
                "station",
                "exactly one of station.par or station.document is required",
            )),
            (Some(_), Some(_)) => Err(invalid(
                "station",
                "station.par and station.document are mutually exclusive",
            )),
        }
    }

    fn output_ref(&self) -> Result<&OutputSpec, RunspecError> {
        self.output.as_ref().ok_or_else(|| missing("output"))
    }

    fn mode_value(&self) -> Result<RunMode, RunspecError> {
        self.mode.ok_or_else(|| missing("mode"))
    }

    fn burn_value(&self) -> Result<u32, RunspecError> {
        let burn = self.rng.burn.unwrap_or(0);
        if burn < 0 {
            return Err(invalid(
                "rng.burn",
                "must be an integer greater than or equal to 0",
            ));
        }
        if burn > i64::from(i32::MAX) {
            return Err(invalid(
                "rng.burn",
                "must fit the faithful signed 32-bit header/control field",
            ));
        }
        Ok(burn as u32)
    }
}

/// Load a runspec file, establishing its containing directory as the path
/// resolution base. Validation never opens or stats the output destination.
pub fn load_runspec_file(path: &Path) -> Result<PreparedRun, RunspecError> {
    let document =
        fs::read_to_string(path).map_err(|error| input_error("document", path, error))?;
    let document_path = if path.is_absolute() {
        path.to_owned()
    } else {
        std::env::current_dir()
            .map_err(|error| input_error("document", path, error))?
            .join(path)
    };
    let base_dir = document_path
        .parent()
        .ok_or_else(|| invalid("document", "has no parent directory"))?;
    RunspecDocument::parse(&document)?.resolve(base_dir)
}

fn validate_single_storm(storm: &SingleStormSpec) -> Result<(), RunspecError> {
    let date = storm.date.ok_or_else(|| missing("single_storm.date"))?;
    validate_storm_date(date, "single_storm.date")?;
    finite_positive(storm.amount_in, "single_storm.amount_in")?;
    finite_positive(storm.duration_h, "single_storm.duration_h")?;
    finite_fraction(
        storm.time_to_peak_fraction,
        "single_storm.time_to_peak_fraction",
    )?;
    finite_positive(
        storm.max_intensity_in_per_h,
        "single_storm.max_intensity_in_per_h",
    )?;
    Ok(())
}

fn validate_design_storm(storm: &DesignStormSpec) -> Result<(), RunspecError> {
    let date = storm.date.ok_or_else(|| missing("design_storm.date"))?;
    validate_storm_date(date, "design_storm.date")?;
    finite_positive(storm.amount_in, "design_storm.amount_in")?;
    Ok(())
}

fn validate_storm_date(date: StormDate, prefix: &str) -> Result<(), RunspecError> {
    let month = date
        .month
        .ok_or_else(|| missing(&format!("{prefix}.month")))?;
    let day = date.day.ok_or_else(|| missing(&format!("{prefix}.day")))?;
    let year = date
        .year
        .ok_or_else(|| missing(&format!("{prefix}.year")))?;
    if !(-9_999..=99_999).contains(&year) {
        return Err(invalid(
            &format!("{prefix}.year"),
            "must fit the legacy i5 output field (-9999..=99999)",
        ));
    }
    if !(1..=12).contains(&month) {
        return Err(invalid(&format!("{prefix}.month"), "must be in 1..=12"));
    }
    let max_day = days_in_storm_month(month, year);
    if !(1..=max_day).contains(&day) {
        return Err(invalid(
            &format!("{prefix}.day"),
            "is not valid for this month under the source storm calendar",
        ));
    }
    Ok(())
}

fn days_in_storm_month(month: i32, year: i32) -> i32 {
    match month {
        2 => 28 + i32::from(source_storm_leap_year(year)),
        4 | 6 | 9 | 11 => 30,
        _ => 31,
    }
}

fn source_storm_leap_year(year: i32) -> bool {
    year - year / 400 * 400 == 0 || (year - year / 4 * 4 == 0 && year - year / 100 * 100 == 0)
}

fn single_storm_params(storm: &SingleStormSpec) -> Result<SingleStormParams, RunspecError> {
    let date = storm.date.ok_or_else(|| missing("single_storm.date"))?;
    Ok(SingleStormParams {
        mo: required_i32(date.month, "single_storm.date.month")?,
        jd: required_i32(date.day, "single_storm.date.day")?,
        ibyear: required_i32(date.year, "single_storm.date.year")?,
        damt: finite_positive(storm.amount_in, "single_storm.amount_in")?,
        usdur: finite_positive(storm.duration_h, "single_storm.duration_h")?,
        ustpr: finite_fraction(
            storm.time_to_peak_fraction,
            "single_storm.time_to_peak_fraction",
        )?,
        uxmav: finite_positive(
            storm.max_intensity_in_per_h,
            "single_storm.max_intensity_in_per_h",
        )?,
    })
}

fn design_storm_params(storm: &DesignStormSpec) -> Result<SingleStormParams, RunspecError> {
    let date = storm.date.ok_or_else(|| missing("design_storm.date"))?;
    Ok(SingleStormParams {
        mo: required_i32(date.month, "design_storm.date.month")?,
        jd: required_i32(date.day, "design_storm.date.day")?,
        ibyear: required_i32(date.year, "design_storm.date.year")?,
        damt: finite_positive(storm.amount_in, "design_storm.amount_in")?,
        ..SingleStormParams::default()
    })
}

fn finite_positive(value: Option<f64>, path: &str) -> Result<f32, RunspecError> {
    let value = value.ok_or_else(|| missing(path))?;
    let narrowed = value as f32;
    if !value.is_finite() || !narrowed.is_finite() || value <= 0.0 {
        return Err(invalid(
            path,
            "must be finite, f32-convertible, and greater than 0",
        ));
    }
    Ok(narrowed)
}

fn finite_fraction(value: Option<f64>, path: &str) -> Result<f32, RunspecError> {
    let value = value.ok_or_else(|| missing(path))?;
    let narrowed = value as f32;
    if !(value.is_finite() && narrowed.is_finite() && 0.0 < value && value <= 1.0) {
        return Err(invalid(
            path,
            "must be finite, f32-convertible, and in (0, 1]",
        ));
    }
    Ok(narrowed)
}

fn positive_year(value: Option<i32>, path: &str) -> Result<(), RunspecError> {
    if let Some(value) = value {
        if value < 1 {
            return Err(invalid(
                path,
                "must be an integer greater than or equal to 1",
            ));
        }
    }
    Ok(())
}

fn positive_required(value: Option<i32>, path: &str) -> Result<i32, RunspecError> {
    let value = required_i32(value, path)?;
    if value < 1 {
        return Err(invalid(
            path,
            "must be an integer greater than or equal to 1",
        ));
    }
    Ok(value)
}

fn validate_loop_span(begin_year: i32, years: i32) -> Result<(), RunspecError> {
    if begin_year > 99_999 {
        return Err(invalid(
            "simulation.begin_year",
            "must fit the legacy positive i5 output field (<= 99999)",
        ));
    }
    if begin_year
        .checked_add(years - 1)
        .is_none_or(|year| year > 99_999)
    {
        return Err(invalid(
            "simulation.years",
            "final year must fit the legacy positive i5 output field (<= 99999)",
        ));
    }
    Ok(())
}

fn required_i32(value: Option<i32>, path: &str) -> Result<i32, RunspecError> {
    value.ok_or_else(|| missing(path))
}

fn required_text<'a>(value: Option<&'a str>, path: &str) -> Result<&'a str, RunspecError> {
    let value = value.ok_or_else(|| missing(path))?;
    if value.is_empty() {
        return Err(invalid(path, "must be a non-empty path"));
    }
    if value
        .chars()
        .any(|character| matches!(character, '\0' | '\r' | '\n'))
    {
        return Err(invalid(path, "must not contain NUL or record terminators"));
    }
    Ok(value)
}

fn reject_present(present: bool, path: &str, mode: &str) -> Result<(), RunspecError> {
    if present {
        Err(invalid(path, &format!("is not accepted in {mode}")))
    } else {
        Ok(())
    }
}

fn resolve_path(base_dir: &Path, lexical: &str) -> PathBuf {
    let path = Path::new(lexical);
    if path.is_absolute() {
        path.to_owned()
    } else {
        base_dir.join(path)
    }
}

fn destination_identity(path: &Path) -> Result<PathBuf, RunspecError> {
    destination_identity_inner(path, 0)
        .map(fold_destination_file_name)
        .map_err(|error| RunspecError::Output {
            field_path: "output".to_owned(),
            path: path.to_owned(),
            message: format!("cannot resolve destination identity: {error}"),
        })
}

fn fold_destination_file_name(path: PathBuf) -> PathBuf {
    let Some(name) = path.file_name().and_then(|name| name.to_str()) else {
        return path;
    };
    let folded = name.nfd().case_fold().collect::<String>();
    path.with_file_name(folded)
}

fn destination_identity_inner(path: &Path, depth: u8) -> Result<PathBuf, std::io::Error> {
    if depth >= 32 {
        return Err(std::io::Error::other(
            "too many symbolic links while resolving output destination",
        ));
    }
    match fs::symlink_metadata(path) {
        Ok(metadata) if metadata.file_type().is_symlink() => {
            let target = fs::read_link(path)?;
            let resolved = if target.is_absolute() {
                target
            } else {
                path.parent().unwrap_or_else(|| Path::new(".")).join(target)
            };
            destination_identity_inner(&resolved, depth + 1)
        }
        Ok(_) => fs::canonicalize(path),
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
            let file_name = path.file_name().ok_or_else(|| {
                std::io::Error::new(
                    std::io::ErrorKind::InvalidInput,
                    "output destination has no file name",
                )
            })?;
            let parent = path.parent().unwrap_or_else(|| Path::new("."));
            Ok(fs::canonicalize(parent)?.join(file_name))
        }
        Err(error) => Err(error),
    }
}

fn companion_staging_path(path: &Path) -> Result<PathBuf, RunspecError> {
    let file_name = path
        .file_name()
        .ok_or_else(|| invalid("output", "companion destination has no file name"))?;
    let mut staging_name = std::ffi::OsString::from(".");
    staging_name.push(file_name);
    staging_name.push(".cligen-stage");
    Ok(path.with_file_name(staging_name))
}

fn output_lock_path(path: &Path) -> Result<PathBuf, RunspecError> {
    let file_name = path
        .file_name()
        .ok_or_else(|| invalid("output.cli", "destination has no file name"))?;
    let mut lock_name = std::ffi::OsString::from(".");
    lock_name.push(file_name);
    lock_name.push(".cligen-lock");
    Ok(path.with_file_name(lock_name))
}

struct OutputLock {
    path: PathBuf,
    _file: File,
}

impl OutputLock {
    fn acquire(cli_path: &Path) -> Result<Self, RunspecError> {
        let path = output_lock_path(&destination_identity(cli_path)?)?;
        let file = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&path)
            .map_err(|error| {
                if error.kind() == std::io::ErrorKind::AlreadyExists {
                    RunspecError::OutputCollision { path: path.clone() }
                } else {
                    RunspecError::Output {
                        field_path: "output.lock".to_owned(),
                        path: path.clone(),
                        message: error.to_string(),
                    }
                }
            })?;
        Ok(Self { path, _file: file })
    }
}

impl Drop for OutputLock {
    fn drop(&mut self) {
        let _ = fs::remove_file(&self.path);
    }
}

fn validate_unique_destinations(paths: &[(&str, PathBuf)]) -> Result<(), RunspecError> {
    let mut identities = Vec::with_capacity(paths.len());
    for (field, path) in paths {
        let identity = destination_identity(path)?;
        if let Some((prior, _)) = identities
            .iter()
            .find(|(_, prior_identity)| prior_identity == &identity)
        {
            return Err(invalid(
                field,
                &format!("must not alias {prior} or a reserved staging path"),
            ));
        }
        identities.push((*field, identity));
    }
    Ok(())
}

fn reject_existing_staging(path: &Path) -> Result<(), RunspecError> {
    match fs::symlink_metadata(path) {
        Ok(_) => Err(RunspecError::OutputCollision {
            path: path.to_owned(),
        }),
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(()),
        Err(error) => Err(RunspecError::Output {
            field_path: "output.staging".to_owned(),
            path: path.to_owned(),
            message: error.to_string(),
        }),
    }
}

fn reject_directory_destination(field_path: &str, path: &Path) -> Result<(), RunspecError> {
    match fs::metadata(path) {
        Ok(metadata) if metadata.is_dir() => Err(RunspecError::Output {
            field_path: field_path.to_owned(),
            path: path.to_owned(),
            message: "destination is a directory".to_owned(),
        }),
        Ok(_) => Ok(()),
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(()),
        Err(error) => Err(RunspecError::Output {
            field_path: field_path.to_owned(),
            path: path.to_owned(),
            message: error.to_string(),
        }),
    }
}

fn write_atomic_companion(path: &Path, bytes: &[u8], field_path: &str) -> Result<(), RunspecError> {
    let staging = companion_staging_path(path)?;
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&staging)
        .map_err(|error| RunspecError::Output {
            field_path: field_path.to_owned(),
            path: path.to_owned(),
            message: error.to_string(),
        })?;
    let write_result = file.write_all(bytes).and_then(|()| file.flush());
    drop(file);
    if let Err(error) = write_result {
        let _ = fs::remove_file(&staging);
        return Err(RunspecError::Output {
            field_path: field_path.to_owned(),
            path: path.to_owned(),
            message: error.to_string(),
        });
    }
    if let Err(error) = fs::rename(&staging, path) {
        let _ = fs::remove_file(&staging);
        return Err(RunspecError::Output {
            field_path: field_path.to_owned(),
            path: path.to_owned(),
            message: error.to_string(),
        });
    }
    Ok(())
}

fn read_station(
    base_dir: &Path,
    selection: StationSelection<'_>,
) -> Result<ResolvedStation, RunspecError> {
    let path = resolve_path(base_dir, selection.lexical);
    match selection.syntax {
        StationSyntax::LegacyPar => read_legacy_station(&path),
        StationSyntax::Document => read_station_document(&path),
    }
}

fn read_legacy_station(path: &Path) -> Result<ResolvedStation, RunspecError> {
    let bytes = fs::read(path).map_err(|error| input_error("station.par", path, error))?;
    let input_sha256 = quality::sha256_hex(&bytes);
    let par = ParFile::parse(&bytes).map_err(|error| par_error(path, error))?;
    let document = StationDocumentV1::from_legacy_par(&par)
        .map_err(|error| station_document_error("station.par", path, error))?;
    let parameter_set_sha256 = parameter_set_sha256(par.fixed_monthly())
        .map_err(|error| station_document_error("station.par", path, error))?;
    Ok(ResolvedStation {
        model: par.into_fixed_monthly(),
        daily_precipitation: None,
        legacy_par_sha256: document.lineage.source_sha256,
        input_schema: SchemaIdentityV1::legacy_station(),
        input_sha256,
        parameter_set_sha256,
        model_id: StationModelV1::FixedMonthly5323,
        fit: FitIdentityV1::unreported(),
    })
}

fn read_station_document(path: &Path) -> Result<ResolvedStation, RunspecError> {
    let bytes = fs::read(path).map_err(|error| input_error("station.document", path, error))?;
    let input_sha256 = quality::sha256_hex(&bytes);
    let version = station_document_version(&bytes)
        .map_err(|error| station_document_error("station.document", path, error))?;
    match version {
        1 => read_station_document_v1(path, &bytes, input_sha256),
        2 => read_station_document_v2(path, &bytes, input_sha256),
        _ => Err(station_document_error(
            "station.document",
            path,
            StationDocumentError::Validation {
                field_path: "station_schema_version".to_owned(),
                message: "must equal 1 or 2".to_owned(),
            },
        )),
    }
}

fn read_station_document_v1(
    path: &Path,
    bytes: &[u8],
    input_sha256: String,
) -> Result<ResolvedStation, RunspecError> {
    let document = StationDocumentV1::parse_json(bytes)
        .map_err(|error| station_document_error("station.document", path, error))?;
    let legacy_par_sha256 = document.lineage.source_sha256.clone();
    let model = document
        .into_model()
        .map_err(|error| station_document_error("station.document", path, error))?;
    let parameter_set_sha256 = parameter_set_sha256(&model)
        .map_err(|error| station_document_error("station.document", path, error))?;
    Ok(ResolvedStation {
        model,
        daily_precipitation: None,
        legacy_par_sha256,
        input_schema: SchemaIdentityV1::modern_station(),
        input_sha256,
        parameter_set_sha256,
        model_id: StationModelV1::FixedMonthly5323,
        fit: FitIdentityV1::unreported(),
    })
}

fn read_station_document_v2(
    path: &Path,
    bytes: &[u8],
    input_sha256: String,
) -> Result<ResolvedStation, RunspecError> {
    let document = StationDocumentV2::parse_json(bytes)
        .map_err(|error| station_document_error("station.document", path, error))?;
    let legacy_par_sha256 = document.lineage.source_sha256.clone();
    let parameter_set_sha256 = routed_parameter_set_sha256(&document)
        .map_err(|error| station_document_error("station.document", path, error))?;
    let model = document
        .to_base_model()
        .map_err(|error| station_document_error("station.document", path, error))?;
    let model_id = match document.station_model {
        StationModelIdV2::FixedMonthly5323 => StationModelV1::FixedMonthly5323,
        StationModelIdV2::A8cIntegratedDailyV1 => StationModelV1::A8cIntegratedDailyV1,
    };
    let fit = FitIdentityV1::reported(document.daily_precipitation.fit_id.clone());
    Ok(ResolvedStation {
        model,
        daily_precipitation: Some(document.daily_precipitation),
        legacy_par_sha256,
        input_schema: SchemaIdentityV1::modern_station_v2(),
        input_sha256,
        parameter_set_sha256,
        model_id,
        fit,
    })
}

fn station_document_version(bytes: &[u8]) -> Result<u32, StationDocumentError> {
    #[derive(Deserialize)]
    struct VersionProbe {
        station_schema_version: u32,
    }

    let mut deserializer = serde_json::Deserializer::from_slice(bytes);
    let probe: VersionProbe =
        serde_path_to_error::deserialize(&mut deserializer).map_err(|error| {
            StationDocumentError::Parse {
                field_path: normalized_parse_path(error.path().to_string()),
                source: error.into_inner(),
            }
        })?;
    deserializer
        .end()
        .map_err(|source| StationDocumentError::Parse {
            field_path: "document".to_owned(),
            source,
        })?;
    Ok(probe.station_schema_version)
}

fn normalized_parse_path(path: String) -> String {
    if path.is_empty() || path == "." {
        "document".to_owned()
    } else {
        path
    }
}

fn missing(path: &str) -> RunspecError {
    invalid(path, "is required")
}

fn invalid(path: &str, message: &str) -> RunspecError {
    RunspecError::Validation {
        field_path: path.to_owned(),
        message: message.to_owned(),
    }
}

fn input_error(path: &str, input: &Path, error: std::io::Error) -> RunspecError {
    RunspecError::Input {
        field_path: path.to_owned(),
        path: input.to_owned(),
        message: error.to_string(),
    }
}

fn output_error(path: &Path, error: std::io::Error) -> RunspecError {
    RunspecError::Output {
        field_path: "output.cli".to_owned(),
        path: path.to_owned(),
        message: error.to_string(),
    }
}

fn par_error(path: &Path, error: ParError) -> RunspecError {
    RunspecError::Input {
        field_path: "station.par".to_owned(),
        path: path.to_owned(),
        message: error.to_string(),
    }
}

fn station_document_error(
    field_path: &str,
    path: &Path,
    error: StationDocumentError,
) -> RunspecError {
    RunspecError::Input {
        field_path: field_path.to_owned(),
        path: path.to_owned(),
        message: error.to_string(),
    }
}

fn prn_error(path_name: &str, path: &Path, error: PrnError) -> RunspecError {
    RunspecError::Input {
        field_path: path_name.to_owned(),
        path: path.to_owned(),
        message: error.to_string(),
    }
}
