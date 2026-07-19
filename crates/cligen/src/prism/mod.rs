//! Cargo-distributed stochastic PRISM preprocessing and orchestration.
//!
//! The crate embeds only the immutable distribution contract. Large Norm91m
//! payload bytes are acquired by explicit [`sync::sync`] and all query/run
//! paths are local-only (SPEC-A10-STOCHASTIC-PRISM-COMPARATOR).

pub mod grid;
pub mod localize;
pub mod run;
pub mod sync;

use std::fmt;
use std::fs::File;
use std::io::Read;
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

/// Embedded runtime/source distribution identity.
pub const EMBEDDED_DISTRIBUTION: &str = include_str!("distribution.json");

/// Public preprocessing identity carried in every receipt.
pub const PROFILE_ID: &str = "stochastic_prism_localized_par_v1";

/// PRISM distribution manifest schema understood by this build.
pub const DISTRIBUTION_SCHEMA_VERSION: u32 = 1;

/// One external payload identity.
#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ArchiveIdentity {
    pub url: String,
    pub file_name: String,
    pub bytes: u64,
    pub sha256: String,
}

/// Strict distribution identity embedded in the crate.
#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Distribution {
    pub schema_version: u32,
    pub bundle_id: String,
    pub version: String,
    pub description: String,
    pub attribution: String,
    pub grid_manifest_sha256: String,
    pub source_manifest_sha256: String,
    pub build_receipt_sha256: String,
    pub attribution_sha256: String,
    pub runtime_archive: ArchiveIdentity,
    pub source_archive: ArchiveIdentity,
}

impl Distribution {
    /// Parse and validate a strict distribution document.
    ///
    /// # Errors
    /// Rejects unknown fields, foreign versions, unsafe file names, and
    /// malformed content identities.
    pub fn from_json(text: &str) -> Result<Self, PrismError> {
        let value: Self =
            serde_json::from_str(text).map_err(|error| PrismError::Manifest(error.to_string()))?;
        value.validate()?;
        Ok(value)
    }

    /// Return the manifest embedded in this crate.
    ///
    /// # Panics
    /// Panics only for a build-time-invalid embedded document, which is gated
    /// by tests.
    #[must_use]
    pub fn embedded() -> Self {
        Self::from_json(EMBEDDED_DISTRIBUTION).expect("embedded PRISM distribution must be valid")
    }

    fn validate(&self) -> Result<(), PrismError> {
        if self.schema_version != DISTRIBUTION_SCHEMA_VERSION {
            return Err(PrismError::Manifest(format!(
                "schema_version {} is not supported",
                self.schema_version
            )));
        }
        if self.bundle_id != "prism_norm91m_9120_4km_m4_m5_v1" || self.version != "2026.07" {
            return Err(PrismError::Manifest(
                "bundle_id/version does not identify revision 1".to_owned(),
            ));
        }
        for (label, hash) in [
            ("grid_manifest_sha256", self.grid_manifest_sha256.as_str()),
            (
                "source_manifest_sha256",
                self.source_manifest_sha256.as_str(),
            ),
            ("build_receipt_sha256", self.build_receipt_sha256.as_str()),
            ("attribution_sha256", self.attribution_sha256.as_str()),
            (
                "runtime_archive.sha256",
                self.runtime_archive.sha256.as_str(),
            ),
            ("source_archive.sha256", self.source_archive.sha256.as_str()),
        ] {
            validate_sha256(label, hash)?;
        }
        validate_archive(
            "runtime_archive",
            &self.runtime_archive,
            "prism-normals-runtime-2026.07.tar.gz",
        )?;
        validate_archive(
            "source_archive",
            &self.source_archive,
            "prism-normals-source-2026.07.tar.gz",
        )?;
        if self.attribution.trim().is_empty() {
            return Err(PrismError::Manifest("attribution is empty".to_owned()));
        }
        Ok(())
    }

    /// Published cache directory for this exact bundle identity.
    #[must_use]
    pub fn cache_dir(&self, cache_root: &Path) -> PathBuf {
        cache_root
            .join("prism")
            .join(&self.bundle_id)
            .join(&self.version)
    }

    /// Air-gap archive name.
    #[must_use]
    pub fn runtime_archive_name(&self) -> &str {
        &self.runtime_archive.file_name
    }
}

fn validate_archive(
    label: &str,
    archive: &ArchiveIdentity,
    expected: &str,
) -> Result<(), PrismError> {
    if archive.file_name != expected || archive.bytes == 0 || archive.url.trim().is_empty() {
        return Err(PrismError::Manifest(format!(
            "{label} has an invalid file name, size, or URL"
        )));
    }
    if Path::new(&archive.file_name)
        .file_name()
        .and_then(|name| name.to_str())
        != Some(archive.file_name.as_str())
    {
        return Err(PrismError::Manifest(format!(
            "{label}.file_name is not one safe component"
        )));
    }
    Ok(())
}

pub(crate) fn validate_sha256(label: &str, value: &str) -> Result<(), PrismError> {
    let valid = value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase());
    if valid {
        Ok(())
    } else {
        Err(PrismError::Manifest(format!(
            "{label} must be 64 lowercase hexadecimal characters"
        )))
    }
}

/// Typed PRISM surface failure.
#[derive(Debug)]
pub enum PrismError {
    Manifest(String),
    NotSynced(PathBuf),
    InvalidCoordinate(String),
    InvalidRequest(String),
    InvalidGrid(String),
    InvalidStation(String),
    Render(String),
    Output(String),
    Http {
        url: String,
        message: String,
    },
    SizeMismatch {
        expected: u64,
        actual: u64,
    },
    HashMismatch {
        label: String,
        expected: String,
        actual: String,
    },
    Io {
        context: String,
        source: std::io::Error,
    },
}

impl fmt::Display for PrismError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Manifest(message) => write!(formatter, "PRISM manifest: {message}"),
            Self::NotSynced(path) => write!(
                formatter,
                "PRISM runtime data are not synced at {}; run `cligen prism sync`",
                path.display()
            ),
            Self::InvalidCoordinate(message) => write!(formatter, "PRISM coordinate: {message}"),
            Self::InvalidRequest(message) => write!(formatter, "PRISM request: {message}"),
            Self::InvalidGrid(message) => write!(formatter, "PRISM grid: {message}"),
            Self::InvalidStation(message) => write!(formatter, "PRISM station: {message}"),
            Self::Render(message) => write!(formatter, "PRISM .par rendering: {message}"),
            Self::Output(message) => write!(formatter, "PRISM output: {message}"),
            Self::Http { url, message } => write!(formatter, "PRISM fetch {url}: {message}"),
            Self::SizeMismatch { expected, actual } => write!(
                formatter,
                "PRISM runtime archive size mismatch: expected {expected}, got {actual}"
            ),
            Self::HashMismatch {
                label,
                expected,
                actual,
            } => write!(
                formatter,
                "PRISM {label} SHA-256 mismatch: expected {expected}, got {actual}"
            ),
            Self::Io { context, source } => write!(formatter, "PRISM {context}: {source}"),
        }
    }
}

impl std::error::Error for PrismError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            Self::Io { source, .. } => Some(source),
            _ => None,
        }
    }
}

pub(crate) fn io_error(context: impl Into<String>, source: std::io::Error) -> PrismError {
    PrismError::Io {
        context: context.into(),
        source,
    }
}

pub(crate) fn sha256_file(path: &Path) -> Result<String, PrismError> {
    let mut input = File::open(path)
        .map_err(|source| io_error(format!("open {} for hashing", path.display()), source))?;
    let mut digest = Sha256::new();
    let mut buffer = [0_u8; 1024 * 1024];
    loop {
        let count = input
            .read(&mut buffer)
            .map_err(|source| io_error(format!("hash {}", path.display()), source))?;
        if count == 0 {
            break;
        }
        digest.update(&buffer[..count]);
    }
    Ok(format!("{:x}", digest.finalize()))
}

#[cfg(test)]
mod tests {
    use std::io;
    use std::path::PathBuf;

    use super::PrismError;

    #[test]
    fn every_error_variant_renders() {
        let errors = [
            PrismError::Manifest("m".to_owned()),
            PrismError::NotSynced(PathBuf::from("cache")),
            PrismError::InvalidCoordinate("c".to_owned()),
            PrismError::InvalidRequest("r".to_owned()),
            PrismError::InvalidGrid("g".to_owned()),
            PrismError::InvalidStation("s".to_owned()),
            PrismError::Render("x".to_owned()),
            PrismError::Output("o".to_owned()),
            PrismError::Http {
                url: "u".to_owned(),
                message: "h".to_owned(),
            },
            PrismError::SizeMismatch {
                expected: 1,
                actual: 2,
            },
            PrismError::HashMismatch {
                label: "l".to_owned(),
                expected: "e".to_owned(),
                actual: "a".to_owned(),
            },
            PrismError::Io {
                context: "i".to_owned(),
                source: io::Error::other("source"),
            },
        ];
        for error in errors {
            assert!(error.to_string().starts_with("PRISM"));
        }
    }
}
