//! Station collections, local cache, and location query
//! (SPEC-STATION-DB).
//!
//! The crate ships hash-pinned collection **manifests**; the station
//! payloads (verbatim collection trees + their python-produced SQLite
//! catalogs) live outside the crate and are fetched into a local
//! cache only by the explicit `cligen stations sync` subcommand.
//! Simulation paths never touch the network. The catalog of record
//! is the shipped SQLite `stations` table — python produces it; this
//! crate only reads it.

pub mod query;
pub mod sync;

use std::error::Error;
use std::fmt;
use std::path::{Path, PathBuf};

use serde::Deserialize;

/// The embedded manifest document (SPEC-STATION-DB §Manifest).
pub const EMBEDDED_MANIFESTS: &str = include_str!("manifests.json");

/// The manifest schema revision this crate understands.
pub const MANIFEST_SCHEMA_VERSION: i64 = 1;

/// All collection manifests known to this build.
#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Manifests {
    pub schema_version: i64,
    pub collections: Vec<Collection>,
}

/// One hash-pinned collection contract.
#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Collection {
    /// Cache key and CLI selector (`[a-z0-9-]+`).
    pub name: String,
    /// Opaque payload version; (name, version) bytes are immutable.
    pub version: String,
    pub description: String,
    /// Provenance lineage (SPEC-STATION-DB §Provenance obligations).
    pub lineage: String,
    /// Payload-root-relative path of the python-produced SQLite catalog.
    pub catalog: String,
    /// Expected `stations` row count; cross-checked at sync.
    pub catalog_rows: u64,
    pub archive: Archive,
}

/// The payload archive identity: the sha256 is the trust anchor.
#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Archive {
    pub url: String,
    pub sha256: String,
    pub bytes: u64,
}

impl Manifests {
    /// The manifest set embedded in this build.
    ///
    /// # Panics
    ///
    /// Panics if the embedded document is invalid — a build defect,
    /// caught by the manifest unit test before any release.
    #[must_use]
    pub fn embedded() -> Self {
        Self::from_json(EMBEDDED_MANIFESTS).expect("embedded manifests must be valid")
    }

    /// Parse and validate a manifest document (fail closed).
    ///
    /// # Errors
    ///
    /// Rejects unknown fields, a foreign `schema_version`, malformed
    /// collection names, and non-64-hex hashes.
    pub fn from_json(text: &str) -> Result<Self, StationsError> {
        let manifests: Manifests =
            serde_json::from_str(text).map_err(|error| StationsError::Manifest {
                message: error.to_string(),
            })?;
        if manifests.schema_version != MANIFEST_SCHEMA_VERSION {
            return Err(StationsError::Manifest {
                message: format!(
                    "schema_version {} is not the supported {MANIFEST_SCHEMA_VERSION}",
                    manifests.schema_version
                ),
            });
        }
        for collection in &manifests.collections {
            collection.validate()?;
        }
        Ok(manifests)
    }

    /// Look up a collection by name.
    ///
    /// # Errors
    ///
    /// Unknown names are typed errors listing the known set.
    pub fn get(&self, name: &str) -> Result<&Collection, StationsError> {
        self.collections
            .iter()
            .find(|collection| collection.name == name)
            .ok_or_else(|| StationsError::UnknownCollection {
                name: name.to_owned(),
                known: self
                    .collections
                    .iter()
                    .map(|collection| collection.name.clone())
                    .collect(),
            })
    }
}

impl Collection {
    fn validate(&self) -> Result<(), StationsError> {
        let name_ok = !self.name.is_empty()
            && self
                .name
                .bytes()
                .all(|byte| byte.is_ascii_lowercase() || byte.is_ascii_digit() || byte == b'-');
        if !name_ok {
            return Err(StationsError::Manifest {
                message: format!("collection name {:?} is not [a-z0-9-]+", self.name),
            });
        }
        let sha_ok = self.archive.sha256.len() == 64
            && self
                .archive
                .sha256
                .bytes()
                .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase());
        if !sha_ok {
            return Err(StationsError::Manifest {
                message: format!(
                    "{}: archive.sha256 must be 64 lowercase hex characters",
                    self.name
                ),
            });
        }
        // R1 finding 2: manifest paths feed `Path::join` — pin them
        // to safe shapes before any filesystem use.
        if !is_single_normal_component(&self.version) {
            return Err(StationsError::Manifest {
                message: format!(
                    "{}: version {:?} must be a single normal path component",
                    self.name, self.version
                ),
            });
        }
        if !is_safe_relative_path(&self.catalog) {
            return Err(StationsError::Manifest {
                message: format!(
                    "{}: catalog {:?} must be a safe payload-relative path",
                    self.name, self.catalog
                ),
            });
        }
        Ok(())
    }

    /// This collection's cache directory under `cache_root`.
    #[must_use]
    pub fn cache_dir(&self, cache_root: &Path) -> PathBuf {
        cache_root
            .join("stations")
            .join(&self.name)
            .join(&self.version)
    }

    /// Whether the collection is synced (cache entry published).
    #[must_use]
    pub fn is_synced(&self, cache_root: &Path) -> bool {
        self.cache_dir(cache_root).join(&self.catalog).is_file()
    }

    /// The archive file name used by the `--from` air-gap source.
    #[must_use]
    pub fn archive_file_name(&self) -> String {
        format!("{}-{}.tar.gz", self.name, self.version)
    }
}

/// Resolve the cache root (SPEC-STATION-DB §Cache):
/// `$CLIGEN_DATA_DIR`, else `$XDG_CACHE_HOME/cligen`, else
/// `$HOME/.cache/cligen` (`%USERPROFILE%` on Windows). A relative
/// environment value is absolutized against the working directory so
/// emitted station paths are always absolute (R1 finding 6).
///
/// # Errors
///
/// Fails closed when no environment root can be resolved.
pub fn cache_root_from_env() -> Result<PathBuf, StationsError> {
    let root = cache_root_from(|name| std::env::var_os(name))?;
    if root.is_absolute() {
        return Ok(root);
    }
    let cwd = std::env::current_dir().map_err(|source| StationsError::Io {
        context: "resolve working directory for a relative cache root".to_owned(),
        source,
    })?;
    Ok(cwd.join(root))
}

/// The cache-root resolution rule over an abstract variable lookup
/// (unit-testable without touching process environment).
fn cache_root_from(
    var: impl Fn(&str) -> Option<std::ffi::OsString>,
) -> Result<PathBuf, StationsError> {
    let present = |name: &str| var(name).filter(|value| !value.is_empty());
    if let Some(dir) = present("CLIGEN_DATA_DIR") {
        return Ok(PathBuf::from(dir));
    }
    if let Some(dir) = present("XDG_CACHE_HOME") {
        return Ok(PathBuf::from(dir).join("cligen"));
    }
    for home in ["HOME", "USERPROFILE"] {
        if let Some(dir) = present(home) {
            return Ok(PathBuf::from(dir).join(".cache").join("cligen"));
        }
    }
    Err(StationsError::CacheRoot)
}

/// Typed failure across the stations surface — fail closed everywhere.
#[derive(Debug)]
pub enum StationsError {
    Manifest {
        message: String,
    },
    UnknownCollection {
        name: String,
        known: Vec<String>,
    },
    CacheRoot,
    NotSynced {
        name: String,
    },
    Io {
        context: String,
        source: std::io::Error,
    },
    Http {
        url: String,
        message: String,
    },
    SizeMismatch {
        name: String,
        expected: u64,
        actual: u64,
    },
    HashMismatch {
        name: String,
        expected: String,
        actual: String,
    },
    BadArchiveEntry {
        name: String,
        entry: String,
        reason: &'static str,
    },
    Catalog {
        name: String,
        message: String,
    },
    UnresolvedCatalogRow {
        name: String,
        par: String,
    },
    Query {
        message: String,
    },
}

impl fmt::Display for StationsError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            StationsError::Manifest { message } => write!(f, "manifest: {message}"),
            StationsError::UnknownCollection { name, known } => write!(
                f,
                "unknown collection {name:?}; known: {}",
                known.join(", ")
            ),
            StationsError::CacheRoot => f.write_str(
                "cannot resolve a cache root: set CLIGEN_DATA_DIR (or XDG_CACHE_HOME/HOME)",
            ),
            StationsError::NotSynced { name } => write!(
                f,
                "collection {name} is not synced; run `cligen stations sync {name}`"
            ),
            StationsError::Io { context, source } => write!(f, "{context}: {source}"),
            StationsError::Http { url, message } => write!(f, "fetch {url}: {message}"),
            StationsError::SizeMismatch {
                name,
                expected,
                actual,
            } => write!(
                f,
                "{name}: payload is {actual} bytes, manifest pins {expected}"
            ),
            StationsError::HashMismatch {
                name,
                expected,
                actual,
            } => write!(
                f,
                "{name}: payload sha256 {actual} does not match the manifest pin {expected}; \
                 nothing was extracted"
            ),
            StationsError::BadArchiveEntry {
                name,
                entry,
                reason,
            } => write!(f, "{name}: archive entry {entry:?} rejected: {reason}"),
            StationsError::Catalog { name, message } => {
                write!(f, "{name}: catalog: {message}")
            }
            StationsError::UnresolvedCatalogRow { name, par } => write!(
                f,
                "{name}: catalog row {par:?} does not resolve to a payload file"
            ),
            StationsError::Query { message } => write!(f, "query: {message}"),
        }
    }
}

impl Error for StationsError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            StationsError::Io { source, .. } => Some(source),
            _ => None,
        }
    }
}

/// Resolve a catalog `par` value to a payload-relative path by the
/// pinned probe order (SPEC-STATION-DB §Catalog-to-file resolution).
///
/// The catalog stores **bare file names** (SPEC-STATION-DB §Payload
/// format); anything else — separators, `..`, absolute paths — is
/// hostile or corrupt catalog data and never reaches `Path::join`
/// (R1 finding 2).
#[must_use]
pub fn resolve_par(payload_dir: &Path, par: &str) -> Option<PathBuf> {
    if !is_single_normal_component(par) {
        return None;
    }
    const PROBE_ORDER: [&str; 6] = [
        "",
        "all_years",
        "additional",
        "30-year",
        "20-year",
        "10-year",
    ];
    for prefix in PROBE_ORDER {
        let candidate = if prefix.is_empty() {
            payload_dir.join(par)
        } else {
            payload_dir.join(prefix).join(par)
        };
        if candidate.is_file() {
            return Some(candidate);
        }
    }
    None
}

/// Exactly one `Component::Normal` — a bare file or directory name.
fn is_single_normal_component(value: &str) -> bool {
    let mut components = Path::new(value).components();
    matches!(
        (components.next(), components.next()),
        (Some(std::path::Component::Normal(_)), None)
    )
}

/// A non-empty relative path made only of `Component::Normal` parts.
fn is_safe_relative_path(value: &str) -> bool {
    let mut any = false;
    for component in Path::new(value).components() {
        match component {
            std::path::Component::Normal(_) => any = true,
            std::path::Component::CurDir => {}
            _ => return false,
        }
    }
    any
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn embedded_manifests_are_valid_and_cover_the_five_collections() {
        let manifests = Manifests::embedded();
        let names: Vec<&str> = manifests
            .collections
            .iter()
            .map(|collection| collection.name.as_str())
            .collect();
        assert_eq!(
            names,
            ["us-legacy", "us-2015", "ghcn-intl", "au", "chile"],
            "manifest set is the five production collections"
        );
    }

    #[test]
    fn manifest_validation_fails_closed() {
        let bad_version =
            EMBEDDED_MANIFESTS.replace("\"schema_version\": 1", "\"schema_version\": 2");
        assert!(Manifests::from_json(&bad_version).is_err());
        let unknown_field =
            EMBEDDED_MANIFESTS.replace("\"schema_version\": 1", "\"schema_version\": 1, \"x\": 1");
        assert!(Manifests::from_json(&unknown_field).is_err());
        let bad_hash = EMBEDDED_MANIFESTS.replacen("6c84662d", "ZZ84662d", 1);
        assert!(Manifests::from_json(&bad_hash).is_err());
    }

    #[test]
    fn unknown_collection_is_a_typed_error() {
        let manifests = Manifests::embedded();
        assert!(matches!(
            manifests.get("nope"),
            Err(StationsError::UnknownCollection { .. })
        ));
        assert!(manifests.get("au").is_ok());
    }

    #[test]
    fn cache_root_resolution_order_is_pinned() {
        let with = |pairs: &'static [(&'static str, &'static str)]| {
            move |name: &str| {
                pairs
                    .iter()
                    .find(|(key, _)| *key == name)
                    .map(|(_, value)| std::ffi::OsString::from(value))
            }
        };
        assert_eq!(
            cache_root_from(with(&[("CLIGEN_DATA_DIR", "/data"), ("HOME", "/h")])).unwrap(),
            PathBuf::from("/data")
        );
        assert_eq!(
            cache_root_from(with(&[("XDG_CACHE_HOME", "/xdg"), ("HOME", "/h")])).unwrap(),
            PathBuf::from("/xdg/cligen")
        );
        assert_eq!(
            cache_root_from(with(&[("HOME", "/h")])).unwrap(),
            PathBuf::from("/h/.cache/cligen")
        );
        assert_eq!(
            cache_root_from(with(&[("USERPROFILE", "/u")])).unwrap(),
            PathBuf::from("/u/.cache/cligen")
        );
        // Empty values are absent; nothing set fails closed.
        assert!(matches!(
            cache_root_from(with(&[("CLIGEN_DATA_DIR", "")])),
            Err(StationsError::CacheRoot)
        ));
    }

    #[test]
    fn every_error_variant_renders_its_diagnostic() {
        let io = |kind: std::io::ErrorKind| std::io::Error::new(kind, "boom");
        let cases: Vec<(StationsError, &str)> = vec![
            (
                StationsError::Manifest {
                    message: "bad".into(),
                },
                "manifest: bad",
            ),
            (
                StationsError::UnknownCollection {
                    name: "x".into(),
                    known: vec!["au".into(), "chile".into()],
                },
                "known: au, chile",
            ),
            (StationsError::CacheRoot, "CLIGEN_DATA_DIR"),
            (
                StationsError::NotSynced { name: "au".into() },
                "stations sync au",
            ),
            (
                StationsError::Io {
                    context: "read x".into(),
                    source: io(std::io::ErrorKind::NotFound),
                },
                "read x",
            ),
            (
                StationsError::Http {
                    url: "https://x".into(),
                    message: "HTTP 404".into(),
                },
                "fetch https://x",
            ),
            (
                StationsError::SizeMismatch {
                    name: "au".into(),
                    expected: 2,
                    actual: 1,
                },
                "manifest pins 2",
            ),
            (
                StationsError::HashMismatch {
                    name: "au".into(),
                    expected: "aa".into(),
                    actual: "bb".into(),
                },
                "nothing was extracted",
            ),
            (
                StationsError::BadArchiveEntry {
                    name: "au".into(),
                    entry: "../x".into(),
                    reason: "path escapes the payload root",
                },
                "escapes the payload root",
            ),
            (
                StationsError::Catalog {
                    name: "au".into(),
                    message: "no table".into(),
                },
                "au: catalog: no table",
            ),
            (
                StationsError::UnresolvedCatalogRow {
                    name: "au".into(),
                    par: "x.par".into(),
                },
                "does not resolve",
            ),
            (
                StationsError::Query {
                    message: "no synced collections".into(),
                },
                "query: no synced",
            ),
        ];
        for (error, expected) in cases {
            let rendered = error.to_string();
            assert!(rendered.contains(expected), "{rendered:?} vs {expected:?}");
        }
    }
}
