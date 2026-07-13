//! The ADR-0002 quality-report instrument (SPEC-QUALITY-REPORT).
//!
//! Observation-only interface code: computes the versioned metric
//! vector from the **text** `.cli` surface plus the parsed `.par` —
//! never from in-process f32 state — so the same code path measures
//! cligen-rs output and legacy-Fortran `.cli` byte streams. Zero
//! interaction with RNG state, generation order, or output
//! formatting; the `.cli` byte stream is untouched.
//!
//! Group P is accumulated through the run-scoped, observation-only
//! [`process::ProcessCounters`] seam and remains `null` post hoc.

pub mod estimators;
pub mod groups;
pub mod intake;
pub mod process;
pub mod report;
pub mod targets;

use std::error::Error;
use std::fmt;
use std::fmt::Write as _;

use sha2::{Digest, Sha256};

use crate::par::{ParError, ParFile};
use crate::provenance::{
    ArtifactProvenanceV1, DateV1, GenerationModeV1, MediaTypeV1, ProvenanceError,
};
use crate::station::{parameter_set_sha256, FixedMonthly5323, StationDocumentError};
use intake::QualityIntakeError;
use report::{
    Identity, IdentityContent, ProcessMetrics, METRICS_VERSION, QUALITY_REPORT_SCHEMA_VERSION,
};

pub use report::QualityReport;
/// Migration alias for the shared SPEC-PROVENANCE object.
pub type Provenance = ArtifactProvenanceV1;

/// Typed failure computing a quality report.
#[derive(Debug)]
pub enum QualityError {
    /// The `.cli` daily table failed the fail-closed intake.
    Cli(QualityIntakeError),
    /// The `.par` bytes failed the SPEC-PAR typed parse.
    Par(ParError),
    /// The station model could not produce its canonical content identity.
    Station(StationDocumentError),
    /// Supplied shared provenance was invalid or did not match report inputs.
    Provenance(ProvenanceError),
    /// Public post-hoc computation cannot attest run-only provenance/process.
    RunOnlyInputs,
    /// Report serialization failed (unreachable for reports built by
    /// this module; surfaced rather than swallowed).
    Serialize(serde_json::Error),
}

impl fmt::Display for QualityError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            QualityError::Cli(error) => write!(f, ".cli intake: {error}"),
            QualityError::Par(error) => write!(f, ".par intake: {error}"),
            QualityError::Station(error) => write!(f, "station identity: {error}"),
            QualityError::Provenance(error) => write!(f, "report provenance: {error}"),
            QualityError::RunOnlyInputs => {
                f.write_str("run-only provenance/process metrics require trusted run orchestration")
            }
            QualityError::Serialize(error) => write!(f, "report serialization: {error}"),
        }
    }
}

impl Error for QualityError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            QualityError::Cli(error) => Some(error),
            QualityError::Par(error) => Some(error),
            QualityError::Station(error) => Some(error),
            QualityError::Provenance(error) => Some(error),
            QualityError::Serialize(error) => Some(error),
            QualityError::RunOnlyInputs => None,
        }
    }
}

/// Compute a quality report from `.cli` text and `.par` bytes.
///
/// This public surface is post-hoc: `provenance` and `process` must both be
/// `None`, producing `identity.provenance: null`, `process: null`, and
/// `par_convergence.observed_passthrough: null`. Trusted run orchestration uses
/// the crate-private station-state seam so callers cannot attest invented
/// run-only data.
///
/// A single-event file (exactly one daily row — the storm modes)
/// carries group D plus identity only: one day supports no
/// distributional metric.
///
/// # Errors
///
/// Fails closed on a malformed `.cli` daily table or `.par` file, or supplied
/// run-only inputs.
pub fn compute_report(
    cli_text: &str,
    par_bytes: &[u8],
    provenance: Option<Provenance>,
    process: Option<ProcessMetrics>,
) -> Result<QualityReport, QualityError> {
    if provenance.is_some() || process.is_some() {
        return Err(QualityError::RunOnlyInputs);
    }
    let par = ParFile::parse(par_bytes).map_err(QualityError::Par)?;
    compute_report_with_station(
        cli_text,
        par.fixed_monthly(),
        &sha256_hex(par_bytes),
        provenance,
        process,
    )
}

/// Compute a report against syntax-independent fixed-monthly station state.
///
/// A1 identifies syntax-independent model parameters in `identity.content`;
/// run-only SPEC-PROVENANCE separately retains the selected station syntax
/// and exact input bytes.
pub(crate) fn compute_report_with_station(
    cli_text: &str,
    station: &FixedMonthly5323,
    station_source_sha256: &str,
    provenance: Option<Provenance>,
    process: Option<ProcessMetrics>,
) -> Result<QualityReport, QualityError> {
    let table = intake::parse_cli_table(cli_text).map_err(QualityError::Cli)?;
    let rows = &table.rows;
    let parameter_set_sha256 = parameter_set_sha256(station).map_err(QualityError::Station)?;
    let cli_sha256 = sha256_hex(cli_text.as_bytes());
    if let Some(value) = &provenance {
        validate_report_provenance(
            value,
            &parameter_set_sha256,
            station_source_sha256,
            &cli_sha256,
            rows,
        )?;
    }

    let content = IdentityContent {
        tool: format!("cligen-rs {}", env!("CARGO_PKG_VERSION")),
        station_model: "fixed_monthly_5_32_3".to_owned(),
        station_parameter_set_sha256: parameter_set_sha256,
        station_source_sha256: station_source_sha256.to_owned(),
        cli_sha256,
        days: rows.len() as u64,
        years: groups::distinct_years(rows),
        span: [rows[0].year, rows[rows.len() - 1].year],
    };
    let observed_passthrough = provenance
        .as_ref()
        .map(|provenance| provenance.generation.mode == GenerationModeV1::Observed);

    let single_event = rows.len() == 1;
    let (par_convergence, interannual, covariation) = if single_event {
        (None, None, None)
    } else {
        let decades = groups::decade_slices(rows);
        let targets = targets::ParTargets::from_station(station);
        (
            Some(groups::par_convergence(
                rows,
                &decades,
                &targets,
                observed_passthrough,
            )),
            Some(groups::interannual(rows, &decades)),
            Some(groups::covariation(rows, &decades)),
        )
    };

    Ok(QualityReport {
        quality_report_schema_version: QUALITY_REPORT_SCHEMA_VERSION,
        metrics_version: METRICS_VERSION,
        identity: Identity {
            content,
            provenance,
        },
        par_convergence,
        interannual,
        covariation,
        tails: groups::tails(rows),
        process,
    })
}

fn validate_report_provenance(
    provenance: &ArtifactProvenanceV1,
    parameter_set_sha256: &str,
    station_source_sha256: &str,
    cli_sha256: &str,
    rows: &[intake::DailyValue],
) -> Result<(), QualityError> {
    provenance.validate().map_err(QualityError::Provenance)?;
    let first = rows.first().expect("quality intake rejects empty tables");
    let last = rows.last().expect("quality intake rejects empty tables");
    let actual_first = DateV1 {
        year: first.year,
        month: first.month as u8,
        day: first.day as u8,
    };
    let actual_last = DateV1 {
        year: last.year,
        month: last.month as u8,
        day: last.day as u8,
    };
    let matches = provenance.artifact.media_type == MediaTypeV1::CliText
        && provenance.artifact.content_sha256.as_deref() == Some(cli_sha256)
        && provenance.station.parameter_set_sha256 == parameter_set_sha256
        && provenance.station.legacy_source_sha256 == station_source_sha256
        && provenance.actual.emitted_day_count == rows.len() as u64
        && provenance.actual.first_date == Some(actual_first)
        && provenance.actual.last_date == Some(actual_last);
    if !matches {
        return Err(QualityError::Provenance(ProvenanceError::Validation {
            field_path: "identity.provenance".to_owned(),
            message: "does not match the measured text/station inputs".to_owned(),
        }));
    }
    Ok(())
}

/// Lowercase-hex SHA-256 of a byte stream.
#[must_use]
pub fn sha256_hex(bytes: &[u8]) -> String {
    let digest = Sha256::digest(bytes);
    let mut hex = String::with_capacity(64);
    for byte in digest {
        write!(hex, "{byte:02x}").expect("writing to a String cannot fail");
    }
    hex
}
