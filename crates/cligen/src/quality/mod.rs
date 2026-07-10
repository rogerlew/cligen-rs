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
use intake::QualityIntakeError;
use report::{Identity, IdentityContent, ProcessMetrics, METRICS_VERSION};

pub use report::{Provenance, QualityReport};

/// Typed failure computing a quality report.
#[derive(Debug)]
pub enum QualityError {
    /// The `.cli` daily table failed the fail-closed intake.
    Cli(QualityIntakeError),
    /// The `.par` bytes failed the SPEC-PAR typed parse.
    Par(ParError),
    /// Report serialization failed (unreachable for reports built by
    /// this module; surfaced rather than swallowed).
    Serialize(serde_json::Error),
}

impl fmt::Display for QualityError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            QualityError::Cli(error) => write!(f, ".cli intake: {error}"),
            QualityError::Par(error) => write!(f, ".par intake: {error}"),
            QualityError::Serialize(error) => write!(f, "report serialization: {error}"),
        }
    }
}

impl Error for QualityError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            QualityError::Cli(error) => Some(error),
            QualityError::Par(error) => Some(error),
            QualityError::Serialize(error) => Some(error),
        }
    }
}

/// Compute a quality report from `.cli` text and `.par` bytes.
///
/// `provenance` is `Some` only on the run-emitted path; `cligen
/// quality` passes `None` and the report carries
/// `identity.provenance: null`, `process: null`, and
/// `par_convergence.observed_passthrough: null`.
///
/// A single-event file (exactly one daily row — the storm modes)
/// carries group D plus identity only: one day supports no
/// distributional metric.
///
/// # Errors
///
/// Fails closed on a malformed `.cli` daily table or `.par` file.
pub fn compute_report(
    cli_text: &str,
    par_bytes: &[u8],
    provenance: Option<Provenance>,
    process: Option<ProcessMetrics>,
) -> Result<QualityReport, QualityError> {
    let par = ParFile::parse(par_bytes).map_err(QualityError::Par)?;
    let table = intake::parse_cli_table(cli_text).map_err(QualityError::Cli)?;
    let rows = &table.rows;

    let content = IdentityContent {
        tool: format!("cligen-rs {}", env!("CARGO_PKG_VERSION")),
        par_sha256: sha256_hex(par_bytes),
        cli_sha256: sha256_hex(cli_text.as_bytes()),
        days: rows.len() as u64,
        years: groups::distinct_years(rows),
        span: [rows[0].year, rows[rows.len() - 1].year],
    };
    let observed_passthrough = provenance
        .as_ref()
        .map(|provenance| provenance.mode == "observed");

    let single_event = rows.len() == 1;
    let (par_convergence, interannual, covariation) = if single_event {
        (None, None, None)
    } else {
        let decades = groups::decade_slices(rows);
        let targets = targets::ParTargets::from_par(&par);
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
