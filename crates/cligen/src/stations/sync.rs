//! `cligen stations sync` — the only network-touching operation in
//! the tool (SPEC-STATION-DB §Network posture).
//!
//! Fetch (or read from the `--from` air-gap directory), verify the
//! manifest SHA-256 **before extraction**, extract with traversal
//! guards into a temporary sibling, cross-check the python-produced
//! catalog (row count + per-row file resolution), then atomically
//! publish the cache entry.

use std::fs;
use std::io::Read;
use std::path::{Component, Path, PathBuf};

use crate::quality::sha256_hex;
use crate::stations::{resolve_par, Collection, StationsError};

/// Environment variable holding the optional bearer token for
/// private payload hosting. Never logged, never cached.
pub const SYNC_TOKEN_ENV: &str = "CLIGEN_SYNC_TOKEN";

/// Outcome of one collection sync.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SyncOutcome {
    /// Fetched, verified, extracted, validated, published.
    Synced,
    /// Cache entry for (name, version) already present; not re-fetched.
    AlreadySynced,
}

/// Sync one collection into `cache_root`.
///
/// `from`: air-gap source directory holding
/// `<name>-<version>.tar.gz`; `None` fetches `archive.url`.
///
/// # Errors
///
/// Fails closed on fetch errors, size or SHA-256 mismatch (before any
/// extraction), unsafe archive entries, catalog mismatches, and
/// unresolvable catalog rows. A failed sync leaves the cache
/// untouched.
pub fn sync_collection(
    collection: &Collection,
    cache_root: &Path,
    from: Option<&Path>,
    force: bool,
) -> Result<SyncOutcome, StationsError> {
    let target = collection.cache_dir(cache_root);
    if collection.is_synced(cache_root) && !force {
        return Ok(SyncOutcome::AlreadySynced);
    }

    let payload = match from {
        Some(dir) => read_local_archive(collection, dir)?,
        None => fetch_archive(collection)?,
    };
    verify_payload(collection, &payload)?;

    let staging = target.with_extension(format!("tmp-{}", std::process::id()));
    if staging.exists() {
        fs::remove_dir_all(&staging).map_err(|source| io_error("clear staging dir", source))?;
    }
    let extraction = extract_archive(collection, &payload, &staging)
        .and_then(|()| validate_catalog(collection, &staging));
    if let Err(error) = extraction {
        let _ = fs::remove_dir_all(&staging);
        return Err(error);
    }
    publish_staging(&staging, &target)?;
    Ok(SyncOutcome::Synced)
}

/// Failure-safe publication (R1 finding 1): an existing entry is
/// retired aside, the staging renamed in, and the retired copy
/// removed only after success — a rename failure restores the prior
/// entry and cleans staging, so the cache never loses a valid entry.
fn publish_staging(staging: &Path, target: &Path) -> Result<(), StationsError> {
    if let Some(parent) = target.parent() {
        fs::create_dir_all(parent).map_err(|source| io_error("create cache parents", source))?;
    }
    let retired = target.with_extension(format!("old-{}", std::process::id()));
    let had_previous = target.exists();
    if had_previous {
        if retired.exists() {
            fs::remove_dir_all(&retired)
                .map_err(|source| io_error("clear retired cache entry", source))?;
        }
        fs::rename(target, &retired)
            .map_err(|source| io_error("retire superseded cache entry", source))?;
    }
    if let Err(source) = fs::rename(staging, target) {
        if had_previous {
            let _ = fs::rename(&retired, target);
        }
        let _ = fs::remove_dir_all(staging);
        return Err(io_error("publish cache entry", source));
    }
    if had_previous {
        fs::remove_dir_all(&retired)
            .map_err(|source| io_error("remove retired cache entry", source))?;
    }
    Ok(())
}

fn io_error(context: &str, source: std::io::Error) -> StationsError {
    StationsError::Io {
        context: context.to_owned(),
        source,
    }
}

fn read_local_archive(collection: &Collection, dir: &Path) -> Result<Vec<u8>, StationsError> {
    let path = dir.join(collection.archive_file_name());
    fs::read(&path).map_err(|source| io_error(&format!("read {}", path.display()), source))
}

/// Fetch the manifest URL. Redirects are followed manually (≤ 5 hops)
/// and the Authorization header is **never** forwarded across a
/// redirect — GitHub's asset endpoint 302s to pre-signed storage that
/// rejects a second credential.
fn fetch_archive(collection: &Collection) -> Result<Vec<u8>, StationsError> {
    let agent = ureq::AgentBuilder::new()
        .redirects(0)
        .timeout(std::time::Duration::from_secs(600))
        .build();
    let token = std::env::var(SYNC_TOKEN_ENV).ok();
    let mut url = collection.archive.url.clone();
    let mut authorize = true;
    for _hop in 0..=5 {
        let mut request = agent
            .get(&url)
            .set("Accept", "application/octet-stream")
            .set("User-Agent", "cligen-rs stations sync");
        if authorize {
            if let Some(token) = &token {
                request = request.set("Authorization", &format!("Bearer {token}"));
            }
        }
        let response = match request.call() {
            Ok(response) => response,
            Err(ureq::Error::Status(status, response)) => {
                return Err(StationsError::Http {
                    url,
                    message: format!("HTTP {status} {}", response.status_text()),
                });
            }
            Err(error) => {
                return Err(StationsError::Http {
                    url,
                    message: error.to_string(),
                });
            }
        };
        if (301..=308).contains(&response.status()) {
            let location = response
                .header("Location")
                .ok_or_else(|| StationsError::Http {
                    url: url.clone(),
                    message: "redirect without Location".to_owned(),
                })?;
            url = location.to_owned();
            authorize = false;
            continue;
        }
        let mut payload = Vec::with_capacity(collection.archive.bytes as usize);
        response
            .into_reader()
            .take(collection.archive.bytes + 1)
            .read_to_end(&mut payload)
            .map_err(|source| io_error("read payload body", source))?;
        return Ok(payload);
    }
    Err(StationsError::Http {
        url,
        message: "more than 5 redirects".to_owned(),
    })
}

/// Size and SHA-256 verification — before anything is extracted.
fn verify_payload(collection: &Collection, payload: &[u8]) -> Result<(), StationsError> {
    if payload.len() as u64 != collection.archive.bytes {
        return Err(StationsError::SizeMismatch {
            name: collection.name.clone(),
            expected: collection.archive.bytes,
            actual: payload.len() as u64,
        });
    }
    let actual = sha256_hex(payload);
    if actual != collection.archive.sha256 {
        return Err(StationsError::HashMismatch {
            name: collection.name.clone(),
            expected: collection.archive.sha256.clone(),
            actual,
        });
    }
    Ok(())
}

/// Extract with traversal guards: regular files and directories only,
/// strictly relative paths, no `..`, no symlinks or hard links.
fn extract_archive(
    collection: &Collection,
    payload: &[u8],
    staging: &Path,
) -> Result<(), StationsError> {
    fs::create_dir_all(staging).map_err(|source| io_error("create staging dir", source))?;
    let mut archive = tar::Archive::new(flate2::read::GzDecoder::new(payload));
    let entries = archive
        .entries()
        .map_err(|source| io_error("open archive", source))?;
    for entry in entries {
        let mut entry = entry.map_err(|source| io_error("read archive entry", source))?;
        let raw_path = entry
            .path()
            .map_err(|source| io_error("decode entry path", source))?
            .into_owned();
        let relative = safe_relative_path(collection, &raw_path)?;
        let kind = entry.header().entry_type();
        match kind {
            tar::EntryType::Directory => {
                fs::create_dir_all(staging.join(&relative))
                    .map_err(|source| io_error("create payload dir", source))?;
            }
            tar::EntryType::Regular => {
                let destination = staging.join(&relative);
                if let Some(parent) = destination.parent() {
                    fs::create_dir_all(parent)
                        .map_err(|source| io_error("create payload parents", source))?;
                }
                let mut file = fs::File::create(&destination)
                    .map_err(|source| io_error("create payload file", source))?;
                std::io::copy(&mut entry, &mut file)
                    .map_err(|source| io_error("write payload file", source))?;
            }
            _ => {
                return Err(StationsError::BadArchiveEntry {
                    name: collection.name.clone(),
                    entry: raw_path.display().to_string(),
                    reason: "only regular files and directories are allowed",
                });
            }
        }
    }
    Ok(())
}

/// Reject absolute paths, `..`, and other non-normal components; a
/// leading `./` (deterministic-tar shape) is accepted and stripped.
fn safe_relative_path(collection: &Collection, raw: &Path) -> Result<PathBuf, StationsError> {
    let mut relative = PathBuf::new();
    for component in raw.components() {
        match component {
            Component::Normal(part) => relative.push(part),
            Component::CurDir => {}
            Component::ParentDir | Component::RootDir | Component::Prefix(_) => {
                return Err(StationsError::BadArchiveEntry {
                    name: collection.name.clone(),
                    entry: raw.display().to_string(),
                    reason: "path escapes the payload root",
                });
            }
        }
    }
    Ok(relative)
}

/// Cross-check the shipped catalog: row count matches the manifest
/// pin and every catalog row resolves to a payload file.
fn validate_catalog(collection: &Collection, staging: &Path) -> Result<(), StationsError> {
    let catalog_path = staging.join(&collection.catalog);
    let connection = rusqlite::Connection::open_with_flags(
        &catalog_path,
        rusqlite::OpenFlags::SQLITE_OPEN_READ_ONLY,
    )
    .map_err(|error| catalog_error(collection, error))?;
    let rows: u64 = connection
        .query_row("SELECT count(*) FROM stations", [], |row| row.get(0))
        .map_err(|error| catalog_error(collection, error))?;
    if rows != collection.catalog_rows {
        return Err(StationsError::Catalog {
            name: collection.name.clone(),
            message: format!(
                "stations table has {rows} rows, manifest pins {}",
                collection.catalog_rows
            ),
        });
    }
    let mut statement = connection
        .prepare("SELECT par FROM stations")
        .map_err(|error| catalog_error(collection, error))?;
    let pars = statement
        .query_map([], |row| row.get::<_, String>(0))
        .map_err(|error| catalog_error(collection, error))?;
    for par in pars {
        let par = par.map_err(|error| catalog_error(collection, error))?;
        if resolve_par(staging, &par).is_none() {
            return Err(StationsError::UnresolvedCatalogRow {
                name: collection.name.clone(),
                par,
            });
        }
    }
    Ok(())
}

fn catalog_error(collection: &Collection, error: rusqlite::Error) -> StationsError {
    StationsError::Catalog {
        name: collection.name.clone(),
        message: error.to_string(),
    }
}
