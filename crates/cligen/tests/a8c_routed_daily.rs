//! Contract tests for the non-default A8c routed daily pilot.

use std::path::{Path, PathBuf};

use cligen::provenance::{
    FitStatusV1, GenerationProfileV1, RngSchemeV1, SchemaIdentityV1, StationModelV1,
};
use cligen::quality::QualityReport;
use cligen::runspec::RunspecDocument;
use cligen::station::{StationDocumentV2, A8A_ANALYSIS_SHA256, A8B_DECISION_SHA256};
use serde_json::Value;

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .unwrap()
}

fn station_path(station: &str) -> PathBuf {
    repo_root()
        .join("docs/work-packages/20260715-a8c-routed-daily-pilot/artifacts/stations")
        .join(format!("{station}.station.json"))
}

fn runspec(document: &Path, years: i32, burn: u32, profile: &str, qc: &str) -> String {
    format!(
        "cligen_runspec: 1\nstation:\n  document: {:?}\nmode: continuous\nsimulation:\n  begin_year: 1\n  years: {years}\n  interpolation: none\nrng:\n  burn: {burn}\ngeneration_profile: {profile}\nqc_filter: {qc}\noutput:\n  cli: target/a8c-routed-daily-test.cli\n  overwrite: true\n  quality: false\n",
        document.to_string_lossy()
    )
}

fn generated_rows(cli: &str) -> Vec<&str> {
    cli.lines()
        .filter(|line| {
            let fields: Vec<_> = line.split_whitespace().collect();
            fields.len() == 13
                && fields[0].parse::<u8>().is_ok()
                && fields[1].parse::<u8>().is_ok()
                && fields[2].parse::<i32>().is_ok()
        })
        .collect()
}

fn revision_one_copy(source: &Path, destination: &Path) {
    let mut value: Value = serde_json::from_slice(&std::fs::read(source).unwrap()).unwrap();
    value["station_schema_version"] = Value::from(1);
    value["station_model"] = Value::from("fixed_monthly_5_32_3");
    value.as_object_mut().unwrap().remove("daily_precipitation");
    std::fs::write(destination, serde_json::to_vec_pretty(&value).unwrap()).unwrap();
}

#[test]
fn routed_station_documents_are_deterministic_and_fail_closed() {
    for station in [
        "az026481", "ca040442", "az028820", "id101022", "la160549", "co050130",
    ] {
        let bytes = std::fs::read(station_path(station)).unwrap();
        let document = StationDocumentV2::parse_json(&bytes).unwrap();
        assert_eq!(document.to_json_bytes().unwrap(), bytes, "{station}");
    }

    let bytes = std::fs::read(station_path("az026481")).unwrap();
    let mut value: Value = serde_json::from_slice(&bytes).unwrap();
    value["daily_precipitation"]["route"] = Value::from("legacy_daily_fallback");
    let error = StationDocumentV2::parse_json(&serde_json::to_vec(&value).unwrap()).unwrap_err();
    assert!(error.to_string().contains("daily_precipitation.route"));

    let mut value: Value = serde_json::from_slice(&bytes).unwrap();
    value["daily_precipitation"]["source_analysis_sha256"] = Value::from(A8B_DECISION_SHA256);
    let error = StationDocumentV2::parse_json(&serde_json::to_vec(&value).unwrap()).unwrap_err();
    assert!(error
        .to_string()
        .contains("daily_precipitation.source_analysis_sha256"));
    assert_ne!(A8A_ANALYSIS_SHA256, A8B_DECISION_SHA256);
}

#[test]
fn runspec_pairings_reject_implicit_or_inconsistent_routes() {
    let root = repo_root();
    let integrated = station_path("az026481");
    let faithful =
        RunspecDocument::parse(&runspec(&integrated, 1, 0, "faithful_5_32_3", "faithful"))
            .unwrap()
            .resolve(&root)
            .unwrap_err();
    assert!(faithful.to_string().contains("station.document"));

    let work = root.join("target/a8c-routed-daily-pairing");
    std::fs::create_dir_all(&work).unwrap();
    let revision_one = work.join("station-v1.json");
    revision_one_copy(&integrated, &revision_one);
    let missing_route = RunspecDocument::parse(&runspec(
        &revision_one,
        1,
        0,
        "a8c_routed_daily_v1",
        "faithful",
    ))
    .unwrap()
    .resolve(&root)
    .unwrap_err();
    assert!(missing_route.to_string().contains("revision-2 routed"));

    let wrong_qc =
        RunspecDocument::parse(&runspec(&integrated, 1, 0, "a8c_routed_daily_v1", "off"))
            .unwrap()
            .resolve(&root)
            .unwrap_err();
    assert!(wrong_qc.to_string().contains("requires faithful"));
}

#[test]
fn fallback_rows_are_exactly_legacy_and_provenance_declares_the_route() {
    let root = repo_root();
    let work = root.join("target/a8c-routed-daily-fallback");
    std::fs::create_dir_all(&work).unwrap();
    let routed_station = station_path("ca040442");
    let revision_one = work.join("ca040442-v1.station.json");
    revision_one_copy(&routed_station, &revision_one);

    let routed = RunspecDocument::parse(&runspec(
        &routed_station,
        3,
        101,
        "a8c_routed_daily_v1",
        "faithful",
    ))
    .unwrap()
    .resolve(&root)
    .unwrap()
    .generate_climate_v1()
    .unwrap();
    let faithful = RunspecDocument::parse(&runspec(
        &revision_one,
        3,
        101,
        "faithful_5_32_3",
        "faithful",
    ))
    .unwrap()
    .resolve(&root)
    .unwrap()
    .generate_climate_v1()
    .unwrap();

    assert_eq!(
        generated_rows(&routed.legacy_cli),
        generated_rows(&faithful.legacy_cli)
    );
    assert_eq!(
        routed.provenance.station.model,
        StationModelV1::FixedMonthly5323
    );
    assert_eq!(routed.provenance.station.fit.status, FitStatusV1::Reported);
    assert_eq!(
        routed.provenance.station.fit.id.as_deref(),
        Some("legacy_daily_only_v1")
    );
    assert_eq!(
        routed.provenance.station.input_schema,
        SchemaIdentityV1::modern_station_v2()
    );
}

#[test]
fn integrated_stream_replays_and_nests_with_explicit_provenance() {
    let root = repo_root();
    let station = station_path("az026481");
    let generate = |years| {
        RunspecDocument::parse(&runspec(
            &station,
            years,
            1009,
            "a8c_routed_daily_v1",
            "faithful",
        ))
        .unwrap()
        .resolve(&root)
        .unwrap()
        .generate_climate_v1()
        .unwrap()
    };
    let short = generate(3);
    let long = generate(5);
    let replay = generate(5);
    let short_rows = generated_rows(&short.legacy_cli);
    let long_rows = generated_rows(&long.legacy_cli);

    assert_eq!(long.legacy_cli, replay.legacy_cli);
    assert_eq!(short_rows, long_rows[..short_rows.len()]);
    assert_eq!(
        long.provenance.generation.profile,
        GenerationProfileV1::A8cRoutedDailyV1
    );
    assert_eq!(
        long.provenance.generation.rng_scheme,
        RngSchemeV1::CligenRandn5323PlusSplitMix64DailyV1
    );
    assert_eq!(
        long.provenance.station.model,
        StationModelV1::A8cIntegratedDailyV1
    );
    assert_eq!(long.provenance.station.fit.status, FitStatusV1::Reported);
    let mut wrong_fit = long.provenance.clone();
    wrong_fit.station.fit.id = Some("legacy_daily_only_v1".to_owned());
    let error = wrong_fit.validate().unwrap_err();
    assert!(error.to_string().contains("station.fit"));

    let quality = RunspecDocument::parse(&runspec(
        &station,
        1,
        1009,
        "a8c_routed_daily_v1",
        "faithful",
    ))
    .unwrap()
    .resolve(&root)
    .unwrap()
    .generate_quality_report()
    .unwrap();
    let quality_bytes = quality.to_json_bytes().unwrap();
    assert_eq!(QualityReport::parse_json(&quality_bytes).unwrap(), quality);
}
