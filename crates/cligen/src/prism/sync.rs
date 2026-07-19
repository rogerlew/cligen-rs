//! Explicit, hash-pinned acquisition of the PRISM runtime bundle.

use std::collections::BTreeSet;
use std::fs;
use std::io::Read;
use std::path::{Component, Path, PathBuf};

use serde::{Deserialize, Serialize};

use super::grid::{required_runtime_files, GridManifest};
use super::{io_error, sha256_file, Distribution, PrismError};

const SYNC_RECEIPT: &str = "SYNC-RECEIPT.json";

/// Result of an explicit runtime synchronization.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SyncOutcome {
    Synced,
    AlreadySynced,
}

#[derive(Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct SyncReceipt {
    schema_version: u32,
    bundle_id: String,
    bundle_version: String,
    runtime_archive_sha256: String,
    grid_manifest_sha256: String,
    source_manifest_sha256: String,
}

/// Acquire, verify, validate, and atomically publish the registered runtime.
///
/// `from` selects an air-gap directory containing the registered archive;
/// otherwise the embedded release URL is fetched. This is the only PRISM
/// operation permitted to touch the network.
pub fn sync(
    distribution: &Distribution,
    cache_root: &Path,
    from: Option<&Path>,
    force: bool,
) -> Result<SyncOutcome, PrismError> {
    if require_synced(distribution, cache_root).is_ok() && !force {
        return Ok(SyncOutcome::AlreadySynced);
    }
    let payload = load_payload(distribution, from)?;
    synchronize_payload(distribution, cache_root, &payload)
}

fn load_payload(distribution: &Distribution, from: Option<&Path>) -> Result<Vec<u8>, PrismError> {
    match from {
        Some(directory) => fs::read(directory.join(distribution.runtime_archive_name()))
            .map_err(|source| io_error("read PRISM air-gap archive", source)),
        None => fetch(distribution),
    }
}

fn synchronize_payload(
    distribution: &Distribution,
    cache_root: &Path,
    payload: &[u8],
) -> Result<SyncOutcome, PrismError> {
    verify_archive(distribution, payload)?;
    let (target, staging) = create_staging(distribution, cache_root)?;
    prepare_staging(distribution, payload, &staging)?;
    publish(&staging, &target)?;
    Ok(SyncOutcome::Synced)
}

fn create_staging(
    distribution: &Distribution,
    cache_root: &Path,
) -> Result<(PathBuf, PathBuf), PrismError> {
    let target = distribution.cache_dir(cache_root);
    let staging = target.with_extension(format!("tmp-{}", std::process::id()));
    if staging.exists() {
        fs::remove_dir_all(&staging).map_err(|source| io_error("clear PRISM staging", source))?;
    }
    Ok((target, staging))
}

fn prepare_staging(
    distribution: &Distribution,
    payload: &[u8],
    staging: &Path,
) -> Result<(), PrismError> {
    let prepared = extract(payload, staging)
        .and_then(|()| validate_extraction(distribution, staging))
        .and_then(|()| write_receipt(distribution, staging));
    if let Err(error) = prepared {
        let _ = fs::remove_dir_all(staging);
        return Err(error);
    }
    Ok(())
}

/// Require an exact published runtime without reading the large grid payload.
pub fn require_synced(
    distribution: &Distribution,
    cache_root: &Path,
) -> Result<PathBuf, PrismError> {
    let root = distribution.cache_dir(cache_root);
    let bytes =
        fs::read(root.join(SYNC_RECEIPT)).map_err(|_| PrismError::NotSynced(root.clone()))?;
    let receipt: SyncReceipt =
        serde_json::from_slice(&bytes).map_err(|_| PrismError::NotSynced(root.clone()))?;
    if !receipt_matches(&receipt, distribution) || !runtime_files_present(&root) {
        return Err(PrismError::NotSynced(root));
    }
    Ok(root)
}

fn receipt_matches(receipt: &SyncReceipt, distribution: &Distribution) -> bool {
    receipt.schema_version == 1
        && receipt.bundle_id == distribution.bundle_id
        && receipt.bundle_version == distribution.version
        && receipt_hashes_match(receipt, distribution)
}

fn receipt_hashes_match(receipt: &SyncReceipt, distribution: &Distribution) -> bool {
    receipt.runtime_archive_sha256 == distribution.runtime_archive.sha256
        && receipt.grid_manifest_sha256 == distribution.grid_manifest_sha256
        && receipt.source_manifest_sha256 == distribution.source_manifest_sha256
}

fn runtime_files_present(root: &Path) -> bool {
    required_runtime_files()
        .iter()
        .all(|name| root.join(name).is_file())
}

fn fetch(distribution: &Distribution) -> Result<Vec<u8>, PrismError> {
    let agent = ureq::AgentBuilder::new()
        .redirects(0)
        .timeout(std::time::Duration::from_secs(600))
        .build();
    let token = std::env::var("CLIGEN_SYNC_TOKEN").ok();
    let mut url = distribution.runtime_archive.url.clone();
    let mut authorize = true;
    for _ in 0..=5 {
        match fetch_hop(
            &agent,
            &url,
            authorize.then_some(token.as_deref()).flatten(),
            distribution.runtime_archive.bytes,
        )? {
            FetchHop::Payload(payload) => return Ok(payload),
            FetchHop::Redirect(location) => {
                url = location;
                authorize = false;
            }
        }
    }
    Err(PrismError::Http {
        url,
        message: "more than 5 redirects".to_owned(),
    })
}

enum FetchHop {
    Payload(Vec<u8>),
    Redirect(String),
}

fn fetch_hop(
    agent: &ureq::Agent,
    url: &str,
    token: Option<&str>,
    expected_bytes: u64,
) -> Result<FetchHop, PrismError> {
    let mut request = agent
        .get(url)
        .set("Accept", "application/octet-stream")
        .set("User-Agent", "cligen-rs prism sync");
    if let Some(value) = token {
        request = request.set("Authorization", &format!("Bearer {value}"));
    }
    let response = request.call().map_err(|error| PrismError::Http {
        url: url.to_owned(),
        message: error.to_string(),
    })?;
    if (301..=308).contains(&response.status()) {
        let location = response
            .header("Location")
            .ok_or_else(|| PrismError::Http {
                url: url.to_owned(),
                message: "redirect without Location".to_owned(),
            })?;
        return Ok(FetchHop::Redirect(location.to_owned()));
    }
    read_response(response, expected_bytes).map(FetchHop::Payload)
}

fn read_response(response: ureq::Response, expected_bytes: u64) -> Result<Vec<u8>, PrismError> {
    let mut payload = Vec::with_capacity(expected_bytes as usize);
    response
        .into_reader()
        .take(expected_bytes + 1)
        .read_to_end(&mut payload)
        .map_err(|source| io_error("read PRISM response", source))?;
    Ok(payload)
}

fn verify_archive(distribution: &Distribution, payload: &[u8]) -> Result<(), PrismError> {
    if payload.len() as u64 != distribution.runtime_archive.bytes {
        return Err(PrismError::SizeMismatch {
            expected: distribution.runtime_archive.bytes,
            actual: payload.len() as u64,
        });
    }
    let actual = crate::quality::sha256_hex(payload);
    if actual != distribution.runtime_archive.sha256 {
        return Err(PrismError::HashMismatch {
            label: "runtime archive".to_owned(),
            expected: distribution.runtime_archive.sha256.clone(),
            actual,
        });
    }
    Ok(())
}

fn extract(payload: &[u8], staging: &Path) -> Result<(), PrismError> {
    fs::create_dir_all(staging).map_err(|source| io_error("create PRISM staging", source))?;
    let allowed: BTreeSet<&str> = required_runtime_files().into_iter().collect();
    let mut seen = BTreeSet::new();
    let mut archive = tar::Archive::new(flate2::read::GzDecoder::new(payload));
    for entry in archive
        .entries()
        .map_err(|source| io_error("open PRISM archive", source))?
    {
        let entry = entry.map_err(|source| io_error("read PRISM archive", source))?;
        extract_entry(entry, staging, &allowed, &mut seen)?;
    }
    if seen != allowed.into_iter().map(str::to_owned).collect() {
        return Err(PrismError::InvalidGrid(
            "runtime archive member set is incomplete".to_owned(),
        ));
    }
    Ok(())
}

fn extract_entry<R: Read>(
    mut entry: tar::Entry<'_, R>,
    staging: &Path,
    allowed: &BTreeSet<&str>,
    seen: &mut BTreeSet<String>,
) -> Result<(), PrismError> {
    let raw = entry
        .path()
        .map_err(|source| io_error("decode PRISM member", source))?
        .into_owned();
    let name = safe_member(&raw)?;
    require_allowed_member(&entry, allowed, seen, &raw, &name)?;
    let destination = super::grid::required_path(staging, &name)?;
    let mut output = fs::File::create(&destination)
        .map_err(|source| io_error("create PRISM runtime member", source))?;
    std::io::copy(&mut entry, &mut output)
        .map_err(|source| io_error("write PRISM runtime member", source))?;
    Ok(())
}

fn require_allowed_member<R: Read>(
    entry: &tar::Entry<'_, R>,
    allowed: &BTreeSet<&str>,
    seen: &mut BTreeSet<String>,
    raw: &Path,
    name: &str,
) -> Result<(), PrismError> {
    if !entry.header().entry_type().is_file() || !allowed.contains(name) {
        return Err(PrismError::InvalidGrid(format!(
            "unexpected runtime archive member {}",
            raw.display()
        )));
    }
    if !seen.insert(name.to_owned()) {
        return Err(PrismError::InvalidGrid(format!(
            "duplicate runtime member {name}"
        )));
    }
    Ok(())
}

fn safe_member(path: &Path) -> Result<String, PrismError> {
    let mut name = None;
    for component in path.components() {
        match component {
            Component::CurDir => {}
            Component::Normal(value) if name.is_none() => name = value.to_str().map(str::to_owned),
            _ => {
                return Err(PrismError::InvalidGrid(format!(
                    "unsafe runtime archive member {}",
                    path.display()
                )))
            }
        }
    }
    name.ok_or_else(|| PrismError::InvalidGrid("empty runtime archive member".to_owned()))
}

fn validate_extraction(distribution: &Distribution, root: &Path) -> Result<(), PrismError> {
    let manifest = GridManifest::load(root, distribution)?;
    manifest.verify_files(root)?;
    for (name, expected) in [
        ("source-manifest.json", &distribution.source_manifest_sha256),
        ("BUILD-RECEIPT.json", &distribution.build_receipt_sha256),
        ("ATTRIBUTION.md", &distribution.attribution_sha256),
    ] {
        verify_auxiliary(root, name, expected)?;
    }
    Ok(())
}

fn verify_auxiliary(root: &Path, name: &str, expected: &str) -> Result<(), PrismError> {
    let actual = sha256_file(&root.join(name))?;
    if actual == expected {
        Ok(())
    } else {
        Err(PrismError::HashMismatch {
            label: name.to_owned(),
            expected: expected.to_owned(),
            actual,
        })
    }
}

fn write_receipt(distribution: &Distribution, root: &Path) -> Result<(), PrismError> {
    let receipt = SyncReceipt {
        schema_version: 1,
        bundle_id: distribution.bundle_id.clone(),
        bundle_version: distribution.version.clone(),
        runtime_archive_sha256: distribution.runtime_archive.sha256.clone(),
        grid_manifest_sha256: distribution.grid_manifest_sha256.clone(),
        source_manifest_sha256: distribution.source_manifest_sha256.clone(),
    };
    let mut bytes = serde_json::to_vec_pretty(&receipt)
        .map_err(|error| PrismError::Manifest(error.to_string()))?;
    bytes.push(b'\n');
    fs::write(root.join(SYNC_RECEIPT), bytes)
        .map_err(|source| io_error("write PRISM sync receipt", source))
}

fn publish(staging: &Path, target: &Path) -> Result<(), PrismError> {
    if let Some(parent) = target.parent() {
        fs::create_dir_all(parent)
            .map_err(|source| io_error("create PRISM cache parents", source))?;
    }
    let retired = target.with_extension(format!("old-{}", std::process::id()));
    let prior = target.exists();
    retire_prior(target, &retired, prior)?;
    if let Err(source) = fs::rename(staging, target) {
        if prior {
            let _ = fs::rename(&retired, target);
        }
        return Err(io_error("publish PRISM cache", source));
    }
    if prior {
        fs::remove_dir_all(retired)
            .map_err(|source| io_error("remove retired PRISM cache", source))?;
    }
    Ok(())
}

fn retire_prior(target: &Path, retired: &Path, prior: bool) -> Result<(), PrismError> {
    if !prior {
        return Ok(());
    }
    if retired.exists() {
        fs::remove_dir_all(retired)
            .map_err(|source| io_error("clear retired PRISM cache", source))?;
    }
    fs::rename(target, retired).map_err(|source| io_error("retire PRISM cache", source))
}

#[cfg(test)]
mod tests {
    use std::fs;
    use std::io::Write;
    use std::path::{Path, PathBuf};

    use flate2::write::GzEncoder;
    use flate2::Compression;

    use super::{extract, publish, require_synced, safe_member, write_receipt};
    use crate::prism::grid::required_runtime_files;
    use crate::prism::{Distribution, PrismError};

    fn temporary(label: &str) -> PathBuf {
        std::env::temp_dir().join(format!(
            "cligen-prism-{label}-{}-{:?}",
            std::process::id(),
            std::thread::current().id()
        ))
    }

    fn runtime_archive() -> Vec<u8> {
        let compressed = GzEncoder::new(Vec::new(), Compression::default());
        let mut archive = tar::Builder::new(compressed);
        for name in required_runtime_files() {
            let bytes = name.as_bytes();
            let mut header = tar::Header::new_gnu();
            header.set_size(bytes.len() as u64);
            header.set_mode(0o644);
            header.set_cksum();
            archive.append_data(&mut header, name, bytes).unwrap();
        }
        archive.into_inner().unwrap().finish().unwrap()
    }

    #[test]
    fn extraction_allow_list_and_atomic_publication_are_enforced() {
        let root = temporary("extract");
        let staging = root.join("staging");
        let target = root.join("published");
        extract(&runtime_archive(), &staging).unwrap();
        for name in required_runtime_files() {
            assert!(staging.join(name).is_file());
        }
        publish(&staging, &target).unwrap();
        assert!(target.is_dir());

        let replacement = root.join("replacement");
        fs::create_dir(&replacement).unwrap();
        fs::File::create(replacement.join("new"))
            .unwrap()
            .write_all(b"new")
            .unwrap();
        publish(&replacement, &target).unwrap();
        assert!(target.join("new").is_file());
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn sync_receipt_is_strict_and_members_are_single_components() {
        let root = temporary("receipt");
        let distribution = Distribution::embedded();
        let cache = distribution.cache_dir(&root);
        fs::create_dir_all(&cache).unwrap();
        for name in required_runtime_files() {
            fs::write(cache.join(name), []).unwrap();
        }
        write_receipt(&distribution, &cache).unwrap();
        assert_eq!(require_synced(&distribution, &root).unwrap(), cache);
        fs::remove_file(cache.join("normals.f32le")).unwrap();
        assert!(matches!(
            require_synced(&distribution, &root),
            Err(PrismError::NotSynced(_))
        ));
        assert_eq!(
            safe_member(Path::new("./grid-manifest.json")).unwrap(),
            "grid-manifest.json"
        );
        assert!(safe_member(Path::new("../escape")).is_err());
        fs::remove_dir_all(root).unwrap();
    }
}
