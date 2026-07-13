//! Non-default A4a evidence gate over the five hash-pinned Q2 catalogs.
//! No network access: the caller supplies an already-synced CLIGEN_DATA_DIR.

use std::path::{Path, PathBuf};

use cligen::par::{ParError, ParFile};
use cligen::station::{FixedMonthly5323, StationDocumentV1};
use cligen::stations::{resolve_par, Manifests};
use sha2::{Digest, Sha256};

#[derive(Debug, Default)]
struct CollectionResult {
    rows: u64,
    converted: u64,
    inherited_invalid: u64,
    negative_zero_fields: u64,
}

#[test]
#[ignore = "requires all five hash-pinned Q2 collections under CLIGEN_DATA_DIR"]
fn all_q2_catalog_stations_convert_bit_identically() {
    let configured_root = std::env::var_os("CLIGEN_DATA_DIR")
        .map(PathBuf::from)
        .expect("set CLIGEN_DATA_DIR to an already-synced Q2 cache; this gate never syncs");
    let cache_root = configured_root
        .canonicalize()
        .expect("CLIGEN_DATA_DIR must name an existing synced Q2 cache");
    let manifests = Manifests::embedded();
    let mut aggregate = Sha256::new();
    let mut total = CollectionResult::default();

    for collection in &manifests.collections {
        let payload = collection.cache_dir(&cache_root);
        assert!(
            collection.is_synced(&cache_root),
            "{} is not synced",
            collection.name
        );
        let result = scan_collection(
            &payload,
            &collection.catalog,
            &collection.name,
            &mut aggregate,
        );
        assert_eq!(
            result.rows, collection.catalog_rows,
            "{} catalog rows",
            collection.name
        );
        let expected_invalid = u64::from(collection.name == "ghcn-intl") * 42;
        assert_eq!(
            result.inherited_invalid, expected_invalid,
            "{} inherited malformed rows",
            collection.name
        );
        assert_eq!(
            result.converted + result.inherited_invalid,
            result.rows,
            "{} accounted rows",
            collection.name
        );
        println!(
            "A4A_SCAN collection={} rows={} converted={} inherited_invalid={} negative_zero_fields={}",
            collection.name,
            result.rows,
            result.converted,
            result.inherited_invalid,
            result.negative_zero_fields
        );
        total.rows += result.rows;
        total.converted += result.converted;
        total.inherited_invalid += result.inherited_invalid;
        total.negative_zero_fields += result.negative_zero_fields;
    }

    assert_eq!(total.rows, 18_119);
    assert_eq!(total.converted, 18_077);
    assert_eq!(total.inherited_invalid, 42);
    assert_eq!(total.negative_zero_fields, 120);
    println!(
        "A4A_SCAN total_rows={} converted={} inherited_invalid={} negative_zero_fields={} aggregate_sha256={:x}",
        total.rows,
        total.converted,
        total.inherited_invalid,
        total.negative_zero_fields,
        aggregate.finalize()
    );
}

fn scan_collection(
    payload: &Path,
    catalog_name: &str,
    collection_name: &str,
    aggregate: &mut Sha256,
) -> CollectionResult {
    let catalog = rusqlite::Connection::open(payload.join(catalog_name)).unwrap();
    let mut query = catalog
        .prepare("SELECT par FROM stations ORDER BY par COLLATE BINARY")
        .unwrap();
    let rows = query.query_map([], |row| row.get::<_, String>(0)).unwrap();
    let mut result = CollectionResult::default();
    for row in rows {
        let par_id = row.unwrap();
        result.rows += 1;
        let path = resolve_par(payload, &par_id)
            .unwrap_or_else(|| panic!("{collection_name}/{par_id}: unresolved catalog row"));
        let bytes = std::fs::read(&path).unwrap();
        let par = match ParFile::parse(&bytes) {
            Ok(par) => par,
            Err(error) if inherited_long_name_failure(collection_name, &error) => {
                result.inherited_invalid += 1;
                continue;
            }
            Err(error) => panic!("{collection_name}/{par_id}: unexpected legacy failure: {error}"),
        };
        let document = StationDocumentV1::from_legacy_par(&par)
            .unwrap_or_else(|error| panic!("{collection_name}/{par_id}: convert: {error}"));
        let json = document.to_json_bytes().unwrap();
        let reparsed = StationDocumentV1::parse_json(&json)
            .unwrap_or_else(|error| panic!("{collection_name}/{par_id}: reparse: {error}"));
        assert_eq!(
            reparsed.to_json_bytes().unwrap(),
            json,
            "{collection_name}/{par_id}: deterministic bytes"
        );
        let modern = reparsed.into_model().unwrap();
        let (legacy_digest, negative_zeros) = model_digest(par.fixed_monthly());
        let (modern_digest, modern_negative_zeros) = model_digest(&modern);
        assert_eq!(
            legacy_digest, modern_digest,
            "{collection_name}/{par_id}: model bits"
        );
        assert_eq!(
            negative_zeros, modern_negative_zeros,
            "{collection_name}/{par_id}: negative zero count"
        );
        aggregate.update(collection_name.as_bytes());
        aggregate.update([0]);
        aggregate.update(par_id.as_bytes());
        aggregate.update([0]);
        aggregate.update(&json);
        result.converted += 1;
        result.negative_zero_fields += negative_zeros;
    }
    result
}

fn inherited_long_name_failure(collection: &str, error: &ParError) -> bool {
    collection == "ghcn-intl"
        && matches!(
            error,
            ParError::Field {
                record: 1,
                cols: (42, 43),
                ..
            }
        )
}

fn model_digest(model: &FixedMonthly5323) -> ([u8; 32], u64) {
    let mut hash = Sha256::new();
    let mut negative_zeros = 0;
    hash.update(model.stidd.as_bytes());
    for value in [
        model.nst,
        model.nstat,
        model.igcode,
        model.years,
        model.itype,
        model.elev_ft,
    ] {
        hash.update(value.to_le_bytes());
    }
    add_f32(&mut hash, model.ylt, &mut negative_zeros);
    add_f32(&mut hash, model.yll, &mut negative_zeros);
    add_f32(&mut hash, model.tp6, &mut negative_zeros);
    for month in 0..12 {
        for value in model.rst[month] {
            add_f32(&mut hash, value, &mut negative_zeros);
        }
        for value in model.prw[month] {
            add_f32(&mut hash, value, &mut negative_zeros);
        }
        for values in [
            &model.obmx,
            &model.obmn,
            &model.stdtx,
            &model.stdtm,
            &model.obsl,
            &model.stdsl,
            &model.wi_raw,
            &model.rh,
            &model.timpkd,
            &model.calm,
        ] {
            add_f32(&mut hash, values[month], &mut negative_zeros);
        }
    }
    for direction in &model.wvl {
        for parameter in direction {
            for value in parameter {
                add_f32(&mut hash, *value, &mut negative_zeros);
            }
        }
    }
    for index in 0..3 {
        hash.update(model.site[index].as_bytes());
        add_f32(&mut hash, model.wgt[index], &mut negative_zeros);
    }
    (hash.finalize().into(), negative_zeros)
}

fn add_f32(hash: &mut Sha256, value: f32, negative_zeros: &mut u64) {
    let bits = value.to_bits();
    if bits == (-0.0f32).to_bits() {
        *negative_zeros += 1;
    }
    hash.update(bits.to_le_bytes());
}
