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

use crate::modes::{run_to_cli_resolved, ResolvedRunInputs, RunError, RunOutput};
use crate::observed::{PrnError, PrnReader};
use crate::par::{ParError, ParFile};
use crate::profile::{GenerationProfile, QcFilter};
use crate::quality::{self, Provenance, QualityError};
use crate::station::{FixedMonthly5323, StationDocumentError, StationDocumentV1};
use crate::storm::SingleStormParams;

/// The sole currently-supported runspec schema revision.
pub const RUNSPEC_VERSION: i64 = 1;

/// A deserialized SPEC-RUNSPEC revision 1 document.
#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RunspecDocument {
    #[serde(default)]
    pub cligen_runspec: Option<i64>,
    #[serde(default)]
    pub station: Option<StationSpec>,
    #[serde(default)]
    pub mode: Option<RunMode>,
    #[serde(default)]
    pub simulation: Option<SimulationSpec>,
    #[serde(default)]
    pub rng: RngSpec,
    #[serde(default)]
    pub generation_profile: GenerationProfile,
    /// SPEC-RUNSPEC rev 5 / SPEC-GENERATION-PROFILES: the QC
    /// conditioning policy. Rejected with `fast_batch_v0` (pre-knob).
    #[serde(default)]
    pub qc_filter: Option<QcFilter>,
    #[serde(default)]
    pub observed: Option<ObservedSpec>,
    #[serde(default)]
    pub single_storm: Option<SingleStormSpec>,
    #[serde(default)]
    pub design_storm: Option<DesignStormSpec>,
    #[serde(default)]
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
    #[serde(default)]
    pub begin_year: Option<i32>,
    #[serde(default)]
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
    #[serde(default)]
    pub burn: Option<i64>,
}

/// Observed-series input selection.
#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ObservedSpec {
    #[serde(default)]
    pub prn: Option<String>,
}

/// A source-calendar date used by a storm mode.
#[derive(Debug, Clone, Copy, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct StormDate {
    #[serde(default)]
    pub month: Option<i32>,
    #[serde(default)]
    pub day: Option<i32>,
    #[serde(default)]
    pub year: Option<i32>,
}

/// The typed iopt-4 single-storm inputs.
#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SingleStormSpec {
    #[serde(default)]
    pub date: Option<StormDate>,
    #[serde(default)]
    pub amount_in: Option<f64>,
    #[serde(default)]
    pub duration_h: Option<f64>,
    #[serde(default)]
    pub time_to_peak_fraction: Option<f64>,
    #[serde(default)]
    pub max_intensity_in_per_h: Option<f64>,
}

/// The typed iopt-7 design-storm inputs.
#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DesignStormSpec {
    #[serde(default)]
    pub date: Option<StormDate>,
    #[serde(default)]
    pub amount_in: Option<f64>,
}

/// Destination and output-surface controls.
#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct OutputSpec {
    #[serde(default)]
    pub cli: Option<String>,
    #[serde(default)]
    pub overwrite: bool,
    #[serde(default)]
    pub command_echo: Option<String>,
    /// SPEC-RUNSPEC rev 4 / SPEC-QUALITY-REPORT: emit the
    /// `<output.cli>.quality.json` sidecar (default true).
    #[serde(default)]
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
    legacy_par_sha256: String,
    prn_bytes: Option<Vec<u8>>,
}

impl PreparedRun {
    /// Generate the `.cli` text without touching the output path.
    pub fn generate(&self) -> Result<String, RunspecError> {
        Ok(self.generate_output()?.cli)
    }

    fn generate_output(&self) -> Result<RunOutput, RunspecError> {
        run_to_cli_resolved(&ResolvedRunInputs {
            iopt: self.iopt,
            interp: self.interpolation,
            burn: self.burn,
            generation_profile: self.generation_profile,
            qc_filter: self.qc_filter,
            begin_year: self.begin_year,
            years: self.years,
            station: &self.station,
            prn_bytes: self.prn_bytes.as_deref(),
            storm: self.storm,
            version: 5.3230,
            command_echo: &self.command_echo,
        })
        .map_err(RunspecError::Run)
    }

    /// Generate the `.cli` text and apply `output.overwrite` without
    /// prompts. When `output.quality` is enabled (the default) the
    /// `<output.cli>.quality.json` sidecar is computed from the
    /// already-produced `.cli` text + fixed-monthly station state and always
    /// rewritten — `output.overwrite` governs the `.cli` only
    /// (SPEC-QUALITY-REPORT §Emission). The `.cli` byte stream is
    /// untouched by the sidecar path.
    pub fn generate_and_write(&self) -> Result<(), RunspecError> {
        let generated = self.generate_output()?;
        let mut output = self.open_output()?;
        output
            .write_all(generated.cli.as_bytes())
            .map_err(|error| output_error(&self.output_path, error))?;
        if self.quality {
            self.write_quality_sidecar(&generated)?;
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

    /// The run-emitted `identity.provenance` block: the resolved
    /// runspec surface (SPEC-QUALITY-REPORT §Emission). `qc_filter`
    /// is `"faithful"` on the faithful backend (the only conditioning
    /// behavior implemented; the knob itself is Q3) and `null` for
    /// the pre-knob `fast_batch_v0`.
    #[must_use]
    pub fn quality_provenance(&self) -> Provenance {
        Provenance {
            generation_profile: match self.generation_profile {
                GenerationProfile::Faithful5323 => "faithful_5_32_3".to_owned(),
                GenerationProfile::FastBatchV0 => "fast_batch_v0".to_owned(),
            },
            qc_filter: match self.generation_profile {
                GenerationProfile::Faithful5323 => {
                    Some(self.qc_filter.provenance_name().to_owned())
                }
                GenerationProfile::FastBatchV0 => None,
            },
            mode: match self.iopt {
                4 => "single_storm",
                6 => "observed",
                7 => "design_storm",
                _ => "continuous",
            }
            .to_owned(),
            burn: self.burn,
            begin_year: self.begin_year,
            years: self.years,
            interpolation: match self.interpolation {
                1 => "linear",
                2 => "fourier",
                3 => "monthly_mean_preserving",
                _ => "none",
            }
            .to_owned(),
        }
    }

    fn write_quality_sidecar(&self, generated: &RunOutput) -> Result<(), RunspecError> {
        let report = quality::compute_report_with_station(
            &generated.cli,
            &self.station,
            &self.legacy_par_sha256,
            Some(self.quality_provenance()),
            Some(generated.process.clone()),
        )
        .map_err(RunspecError::Quality)?;
        let bytes = report
            .to_json_bytes()
            .map_err(|error| RunspecError::Quality(QualityError::Serialize(error)))?;
        let path = self.quality_sidecar_path();
        fs::write(&path, bytes).map_err(|error| RunspecError::Output {
            field_path: "output.quality".to_owned(),
            path,
            message: error.to_string(),
        })
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
    legacy_par_sha256: String,
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
        let station = read_station(base_dir, station_selection)?;
        let prn = self.read_observed_input(base_dir, mode)?;
        let fields = self.resolve_mode_fields(mode, prn.as_ref().map(|value| value.1))?;
        let burn = self.burn_value()?;
        let command_echo = output.command_echo.clone().unwrap_or_else(|| {
            self.canonical_echo(
                mode,
                station_selection,
                prn.as_ref().map(|value| value.0.as_str()),
                output_lexical,
                fields.interpolation,
                burn,
            )
        });
        let generation_profile = self.generation_profile;
        let qc_filter = self.qc_filter.unwrap_or_default();
        Ok(PreparedRun {
            output_path: resolve_path(base_dir, output_lexical),
            overwrite: output.overwrite,
            iopt: fields.iopt,
            interpolation: fields.interpolation,
            burn,
            generation_profile,
            begin_year: fields.begin_year,
            years: fields.years,
            command_echo: qc_filter.command_echo(generation_profile.command_echo(command_echo)),
            storm: fields.storm,
            qc_filter,
            quality: output.quality.unwrap_or(true),
            station: station.model,
            legacy_par_sha256: station.legacy_par_sha256,
            prn_bytes: prn.map(|value| value.2),
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
        required_text(self.output_ref()?.cli.as_deref(), "output.cli")?;
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
        positive_required(simulation.begin_year, "simulation.begin_year")?;
        positive_required(simulation.years, "simulation.years")?;
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
        )
    }

    fn read_observed_input(
        &self,
        base_dir: &Path,
        mode: RunMode,
    ) -> Result<Option<(String, i32, Vec<u8>)>, RunspecError> {
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
        Ok(Some((lexical, initial_year, bytes)))
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
        u32::try_from(burn).map_err(|_| invalid("rng.burn", "must fit in u32"))
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

fn required_i32(value: Option<i32>, path: &str) -> Result<i32, RunspecError> {
    value.ok_or_else(|| missing(path))
}

fn required_text<'a>(value: Option<&'a str>, path: &str) -> Result<&'a str, RunspecError> {
    let value = value.ok_or_else(|| missing(path))?;
    if value.is_empty() {
        return Err(invalid(path, "must be a non-empty path"));
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
    let par = ParFile::parse(&bytes).map_err(|error| par_error(path, error))?;
    let document = StationDocumentV1::from_legacy_par(&par)
        .map_err(|error| station_document_error("station.par", path, error))?;
    Ok(ResolvedStation {
        model: par.into_fixed_monthly(),
        legacy_par_sha256: document.lineage.source_sha256,
    })
}

fn read_station_document(path: &Path) -> Result<ResolvedStation, RunspecError> {
    let bytes = fs::read(path).map_err(|error| input_error("station.document", path, error))?;
    let document = StationDocumentV1::parse_json(&bytes)
        .map_err(|error| station_document_error("station.document", path, error))?;
    let legacy_par_sha256 = document.lineage.source_sha256.clone();
    let model = document
        .into_model()
        .map_err(|error| station_document_error("station.document", path, error))?;
    Ok(ResolvedStation {
        model,
        legacy_par_sha256,
    })
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
