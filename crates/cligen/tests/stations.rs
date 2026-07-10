//! SPEC-STATION-DB acceptance gates: air-gap sync with hash
//! verification, fail-closed vectors (hash mismatch, traversal
//! archive), the pinned au nearest oracle, and the CLI-level
//! sync → nearest → validate → run flow.

use std::path::{Path, PathBuf};
use std::process::Command;

use cligen::quality::sha256_hex;
use cligen::stations::query::{nearest, NearestQuery};
use cligen::stations::sync::{sync_collection, SyncOutcome};
use cligen::stations::{Archive, Collection, Manifests, StationsError};

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .unwrap()
}

fn fixtures_dir() -> PathBuf {
    repo_root().join("crates/cligen/tests/fixtures/stations")
}

fn temp_dir(tag: &str) -> PathBuf {
    let dir = repo_root().join("target/stations-tests").join(tag);
    let _ = std::fs::remove_dir_all(&dir);
    std::fs::create_dir_all(&dir).unwrap();
    dir
}

fn au_collection() -> Collection {
    Manifests::embedded().get("au").unwrap().clone()
}

#[test]
fn air_gap_sync_verifies_publishes_and_skips_when_current() {
    let cache = temp_dir("air-gap-sync");
    let au = au_collection();
    let outcome = sync_collection(&au, &cache, Some(&fixtures_dir()), false).unwrap();
    assert_eq!(outcome, SyncOutcome::Synced);
    let payload = au.cache_dir(&cache);
    assert!(payload.join("au_stations.db").is_file());
    assert!(payload.join("997953_AU,Melbourne.par").is_file());
    // Second sync of the same (name, version): skipped, not re-fetched.
    let outcome = sync_collection(&au, &cache, Some(&fixtures_dir()), false).unwrap();
    assert_eq!(outcome, SyncOutcome::AlreadySynced);
}

#[test]
fn hash_mismatch_fails_closed_before_extraction() {
    let cache = temp_dir("hash-mismatch-cache");
    let tampered_source = temp_dir("hash-mismatch-src");
    let au = au_collection();
    let mut bytes = std::fs::read(fixtures_dir().join(au.archive_file_name())).unwrap();
    let last = bytes.len() - 1;
    bytes[last] ^= 0xff;
    std::fs::write(tampered_source.join(au.archive_file_name()), bytes).unwrap();

    let error = sync_collection(&au, &cache, Some(&tampered_source), false).unwrap_err();
    assert!(
        matches!(error, StationsError::HashMismatch { .. }),
        "{error}"
    );
    assert!(
        !au.cache_dir(&cache).exists(),
        "a failed sync must leave the cache untouched"
    );
}

#[test]
fn traversal_archive_fails_closed() {
    let cache = temp_dir("traversal-cache");
    let source = temp_dir("traversal-src");
    // A malicious payload whose entry path escapes the payload root.
    // `tar::Builder`'s convenience APIs refuse to WRITE `..` paths, so
    // forge the header name directly — the attack shape a hostile
    // archive would carry.
    let mut archive_bytes = Vec::new();
    {
        let gz = flate2::write::GzEncoder::new(&mut archive_bytes, flate2::Compression::default());
        let mut tar = tar::Builder::new(gz);
        let contents = b"evil";
        let mut header = tar::Header::new_gnu();
        let name = b"../evil.par";
        header.as_old_mut().name[..name.len()].copy_from_slice(name);
        header.set_size(contents.len() as u64);
        header.set_mode(0o644);
        header.set_entry_type(tar::EntryType::Regular);
        header.set_cksum();
        tar.append(&header, contents.as_slice()).unwrap();
        tar.into_inner().unwrap().finish().unwrap();
    }
    let evil = Collection {
        name: "evil-test".to_owned(),
        version: "0.0".to_owned(),
        description: "traversal vector".to_owned(),
        lineage: "test".to_owned(),
        catalog: "cat.db".to_owned(),
        catalog_rows: 0,
        archive: Archive {
            url: "https://invalid.invalid/evil.tar.gz".to_owned(),
            sha256: sha256_hex(&archive_bytes),
            bytes: archive_bytes.len() as u64,
        },
    };
    std::fs::write(source.join(evil.archive_file_name()), &archive_bytes).unwrap();

    let error = sync_collection(&evil, &cache, Some(&source), false).unwrap_err();
    assert!(
        matches!(error, StationsError::BadArchiveEntry { .. }),
        "{error}"
    );
    assert!(!evil.cache_dir(&cache).exists());
    assert!(
        !cache.join("evil.par").exists() && !repo_root().join("evil.par").exists(),
        "traversal payload must not land anywhere"
    );
}

#[test]
fn catalog_row_count_mismatch_fails_closed() {
    let cache = temp_dir("rowcount-cache");
    let mut au = au_collection();
    au.catalog_rows = 8; // real payload has 7
    let error = sync_collection(&au, &cache, Some(&fixtures_dir()), false).unwrap_err();
    assert!(matches!(error, StationsError::Catalog { .. }), "{error}");
    assert!(!au.cache_dir(&cache).exists());
}

/// Pinned from an independent Python implementation (sqlite3 +
/// haversine, R = 6371.0088) over `au_stations.db` (2026.07.1,
/// east-positive longitudes), query point (-37.5, 145.5).
const AU_ORACLE: [(&str, f64); 7] = [
    ("997955_AU,KilmoreEast.par", 53.432104),
    ("997953_AU,Melbourne.par", 58.720220),
    ("997958_AU,BunyipFireArea.par", 69.221317),
    ("997957_AU,Cranbourne.par", 70.774816),
    ("997956_AU,DelburnFireArea.par", 112.332286),
    ("997954_AU,Morwell.par", 114.067777),
    ("997959_AU,Beechworth.par", 165.386830),
];

#[test]
fn nearest_matches_pinned_au_oracle() {
    let cache = temp_dir("oracle-cache");
    let manifests = Manifests::embedded();
    let au = manifests.get("au").unwrap();
    sync_collection(au, &cache, Some(&fixtures_dir()), false).unwrap();

    let rows = nearest(
        &manifests,
        &cache,
        &NearestQuery {
            latitude: -37.5,
            longitude: 145.5,
            count: 7,
            collection: Some("au".to_owned()),
            min_years: None,
        },
    )
    .unwrap();
    assert_eq!(rows.len(), 7);
    for (row, (id, distance)) in rows.iter().zip(AU_ORACLE) {
        assert_eq!(row.id, id);
        assert!(
            (row.distance_km - distance).abs() < 1e-4,
            "{id}: {} vs oracle {distance}",
            row.distance_km
        );
        assert!(row.path.is_file(), "{id}: emitted path must exist");
    }
    // count truncation and the years filter surface.
    let top2 = nearest(
        &manifests,
        &cache,
        &NearestQuery {
            latitude: -37.5,
            longitude: 145.5,
            count: 2,
            collection: Some("au".to_owned()),
            min_years: Some(100.0),
        },
    )
    .unwrap();
    assert_eq!(top2.len(), 2);
    assert!(top2.iter().all(|row| row.years >= 100.0));
}

#[test]
fn nearest_requires_a_synced_collection_and_valid_point() {
    let cache = temp_dir("unsynced-cache");
    let manifests = Manifests::embedded();
    let query = NearestQuery {
        latitude: -37.5,
        longitude: 145.5,
        count: 5,
        collection: Some("au".to_owned()),
        min_years: None,
    };
    assert!(matches!(
        nearest(&manifests, &cache, &query),
        Err(StationsError::NotSynced { .. })
    ));
    let bad_point = NearestQuery {
        latitude: 91.0,
        ..query
    };
    assert!(matches!(
        nearest(&manifests, &cache, &bad_point),
        Err(StationsError::Query { .. })
    ));
}

/// Minimal one-shot HTTP responder on a loopback listener; returns
/// the received request head.
fn respond_once(
    listener: &std::net::TcpListener,
    status_line: &str,
    headers: &str,
    body: &[u8],
) -> String {
    use std::io::{Read as _, Write as _};
    let (mut stream, _) = listener.accept().unwrap();
    let mut request = Vec::new();
    let mut byte = [0u8; 1];
    while !request.ends_with(b"\r\n\r\n") {
        stream.read_exact(&mut byte).unwrap();
        request.push(byte[0]);
    }
    write!(
        stream,
        "{status_line}\r\n{headers}Content-Length: {}\r\nConnection: close\r\n\r\n",
        body.len()
    )
    .unwrap();
    stream.write_all(body).unwrap();
    String::from_utf8_lossy(&request).into_owned()
}

#[test]
fn network_sync_follows_redirects_without_forwarding_auth() {
    let listener = std::net::TcpListener::bind("127.0.0.1:0").unwrap();
    let port = listener.local_addr().unwrap().port();
    let archive = std::fs::read(fixtures_dir().join(au_collection().archive_file_name())).unwrap();

    let server = std::thread::spawn(move || {
        let first = respond_once(
            &listener,
            "HTTP/1.1 302 Found",
            &format!("Location: http://127.0.0.1:{port}/real\r\n"),
            b"",
        );
        let second = respond_once(&listener, "HTTP/1.1 200 OK", "", &archive);
        (first, second)
    });

    let mut au = au_collection();
    au.name = "au-net".to_owned(); // distinct cache key for this vector
    au.archive.url = format!("http://127.0.0.1:{port}/asset");
    let cache = temp_dir("net-sync-cache");
    // R1 finding 5: the vector must carry a real token so the
    // no-forwarding assertion cannot pass vacuously. No other
    // in-process test reads this variable; the CLI tests run in
    // subprocesses with their own environments.
    std::env::set_var("CLIGEN_SYNC_TOKEN", "test-token-q2");
    let outcome = sync_collection(&au, &cache, None, false);
    std::env::remove_var("CLIGEN_SYNC_TOKEN");
    assert_eq!(outcome.unwrap(), SyncOutcome::Synced);
    assert!(au.cache_dir(&cache).join("au_stations.db").is_file());

    let (first, second) = server.join().unwrap();
    assert!(
        first.contains("Accept: application/octet-stream"),
        "{first}"
    );
    assert!(
        first.contains("Authorization: Bearer test-token-q2"),
        "the origin request must carry the token: {first}"
    );
    // The redirect hop must never carry credentials (pre-signed
    // storage rejects a second Authorization).
    assert!(!second.contains("Authorization"), "{second}");
}

#[test]
fn forced_resync_with_bad_payload_preserves_the_existing_entry() {
    // R1 finding 1 regression: a failed --force re-sync must leave
    // the previously published entry intact and usable.
    let cache = temp_dir("force-preserve-cache");
    let tampered_source = temp_dir("force-preserve-src");
    let au = au_collection();
    sync_collection(&au, &cache, Some(&fixtures_dir()), false).unwrap();

    let mut bytes = std::fs::read(fixtures_dir().join(au.archive_file_name())).unwrap();
    let last = bytes.len() - 1;
    bytes[last] ^= 0xff;
    std::fs::write(tampered_source.join(au.archive_file_name()), bytes).unwrap();
    let error = sync_collection(&au, &cache, Some(&tampered_source), true).unwrap_err();
    assert!(matches!(error, StationsError::HashMismatch { .. }));
    assert!(
        au.cache_dir(&cache).join("au_stations.db").is_file(),
        "the valid entry must survive a failed forced re-sync"
    );

    // And a successful --force re-publishes cleanly (no leftover
    // staging or retired directories).
    let outcome = sync_collection(&au, &cache, Some(&fixtures_dir()), true).unwrap();
    assert_eq!(outcome, SyncOutcome::Synced);
    let versions_dir = au.cache_dir(&cache);
    let parent = versions_dir.parent().unwrap();
    let leftovers: Vec<String> = std::fs::read_dir(parent)
        .unwrap()
        .map(|entry| entry.unwrap().file_name().to_string_lossy().into_owned())
        .filter(|name| name != &au.version)
        .collect();
    assert!(
        leftovers.is_empty(),
        "leftover cache entries: {leftovers:?}"
    );
}

#[test]
fn hostile_catalog_par_values_never_reach_the_filesystem() {
    // R1 finding 2 regression: a catalog row naming an absolute or
    // traversing path must not resolve (and must fail the sync).
    use cligen::stations::resolve_par;
    let payload = temp_dir("hostile-par-payload");
    std::fs::write(payload.join("ok.par"), b"x").unwrap();
    assert!(resolve_par(&payload, "ok.par").is_some());
    for hostile in ["/etc/hostname", "../ok.par", "sub/../ok.par", "a/b.par", ""] {
        assert!(
            resolve_par(&payload, hostile).is_none(),
            "{hostile:?} must not resolve"
        );
    }
}

#[test]
fn network_error_status_fails_closed() {
    let listener = std::net::TcpListener::bind("127.0.0.1:0").unwrap();
    let port = listener.local_addr().unwrap().port();
    let server = std::thread::spawn(move || {
        respond_once(&listener, "HTTP/1.1 404 Not Found", "", b"nope");
    });
    let mut au = au_collection();
    au.name = "au-404".to_owned();
    au.archive.url = format!("http://127.0.0.1:{port}/missing");
    let cache = temp_dir("net-404-cache");
    let error = sync_collection(&au, &cache, None, false).unwrap_err();
    assert!(matches!(error, StationsError::Http { .. }), "{error}");
    assert!(!au.cache_dir(&cache).exists());
    server.join().unwrap();
}

#[test]
fn cli_sync_nearest_validate_run_round_trip() {
    let binary = env!("CARGO_BIN_EXE_cligen");
    let work = temp_dir("cli-round-trip");
    let cache = work.join("cache");

    let sync = Command::new(binary)
        .env("CLIGEN_DATA_DIR", &cache)
        .args([
            "stations",
            "sync",
            "au",
            "--from",
            fixtures_dir().to_str().unwrap(),
        ])
        .output()
        .unwrap();
    assert!(
        sync.status.success(),
        "sync: {}",
        String::from_utf8_lossy(&sync.stderr)
    );

    // `list` shows sync state for all collections and for one by name.
    for args in [vec!["stations", "list"], vec!["stations", "list", "au"]] {
        let listing = Command::new(binary)
            .env("CLIGEN_DATA_DIR", &cache)
            .args(&args)
            .output()
            .unwrap();
        assert!(listing.status.success());
        let text = String::from_utf8_lossy(&listing.stdout);
        assert!(text.contains("synced (7 stations)"), "{text}");
        if args.len() == 3 {
            assert!(!text.contains("us-legacy"), "{text}");
        }
    }

    let nearest = Command::new(binary)
        .env("CLIGEN_DATA_DIR", &cache)
        .args([
            "stations", "nearest", "--lat", "-37.5", "--lon", "145.5", "-n", "1", "--json",
        ])
        .output()
        .unwrap();
    assert!(
        nearest.status.success(),
        "nearest: {}",
        String::from_utf8_lossy(&nearest.stderr)
    );
    let rows: serde_json::Value = serde_json::from_slice(&nearest.stdout).unwrap();
    assert_eq!(rows[0]["id"], "997955_AU,KilmoreEast.par");
    let par_path = rows[0]["path"].as_str().unwrap().to_owned();
    assert!(Path::new(&par_path).is_file());

    // The emitted path is an ordinary station.par: validate + run.
    let output_cli = work.join("au-roundtrip.cli");
    let runspec = work.join("inp.yaml");
    std::fs::write(
        &runspec,
        format!(
            "cligen_runspec: 1\nstation:\n  par: {par}\nmode: continuous\n\
             simulation:\n  begin_year: 1\n  years: 1\noutput:\n  cli: {cli}\n",
            par = par_path,
            cli = output_cli.display(),
        ),
    )
    .unwrap();
    for action in ["validate", "run"] {
        let output = Command::new(binary)
            .args([action, runspec.to_str().unwrap()])
            .output()
            .unwrap();
        assert!(
            output.status.success(),
            "{action}: {}",
            String::from_utf8_lossy(&output.stderr)
        );
    }
    assert!(output_cli.is_file());
    assert!(work.join("au-roundtrip.cli.quality.json").is_file());
}
