use std::error::Error as _;
use std::path::{Path, PathBuf};

use cligen::par::ParFile;
use cligen::provenance::{
    sha256_hex, ActualOutputV1, ArtifactIdentityV1, ArtifactProvenanceV1, CoverageV1, DateV1,
    EffectiveObservedV1, EffectiveOutputV1, EffectiveRunspecV1, EffectiveStationV1,
    EffectiveStormV1, FitIdentityV1, GenerationModeV1, GenerationProfileV1, GenerationProvenanceV1,
    InterpolationV1, ObservedInputV1, ProvenanceError, QcPolicyV1, RngSchemeV1, SchemaIdentityV1,
    StationCollectionIdentityV1, StationModelV1, StationProvenanceV1, StationSelectorV1,
};
use cligen::station::{parameter_set_sha256, StationDocumentV1};
use serde_json::Value;

const HASH_A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const HASH_B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .unwrap()
}

fn continuous_runspec() -> EffectiveRunspecV1 {
    EffectiveRunspecV1 {
        cligen_runspec: 1,
        station: EffectiveStationV1 {
            selector: StationSelectorV1::LegacyPar,
            lexical_path: "stations/id106388.par".to_owned(),
            input_sha256: HASH_A.to_owned(),
        },
        mode: GenerationModeV1::Continuous,
        begin_year: Some(1),
        years: Some(31),
        interpolation: InterpolationV1::None,
        burn: 17,
        generation_profile: GenerationProfileV1::Faithful5323,
        qc_filter: Some(QcPolicyV1::Faithful),
        observed: None,
        storm: None,
        output: EffectiveOutputV1 {
            cli_lexical_path: "out/wepp.cli".to_owned(),
            parquet_lexical_path: Some("out/wepp.cli.parquet".to_owned()),
            quality: true,
            overwrite: false,
            command_echo: "-r17 -iid106388.par".to_owned(),
        },
    }
}

fn generation(runspec: &EffectiveRunspecV1) -> GenerationProvenanceV1 {
    GenerationProvenanceV1 {
        profile: runspec.generation_profile,
        qc_policy: runspec.qc_filter,
        mode: runspec.mode,
        interpolation: runspec.interpolation,
        rng_scheme: RngSchemeV1::CligenRandn5323,
        burn_per_stream: runspec.burn,
    }
}

fn storm_runspec() -> EffectiveRunspecV1 {
    let mut runspec = continuous_runspec();
    runspec.mode = GenerationModeV1::SingleStorm;
    runspec.begin_year = None;
    runspec.years = None;
    runspec.observed = None;
    runspec.storm = Some(EffectiveStormV1 {
        date: DateV1 {
            year: 100,
            month: 2,
            day: 29,
        },
        amount_in: 2.25,
        duration_h: Some(6.0),
        time_to_peak_fraction: Some(0.4_f32 as f64),
        max_intensity_in_per_h: Some(1.5),
    });
    runspec.output.cli_lexical_path = "out/storm.cli".to_owned();
    runspec.output.parquet_lexical_path = None;
    runspec.output.command_echo = "-r17 -iid106388.par -t4".to_owned();
    runspec
}

fn station(runspec: &EffectiveRunspecV1) -> StationProvenanceV1 {
    StationProvenanceV1 {
        input_schema: SchemaIdentityV1::legacy_station(),
        input_sha256: runspec.station.input_sha256.clone(),
        model: StationModelV1::FixedMonthly5323,
        parameter_set_sha256: HASH_B.to_owned(),
        fit: FitIdentityV1::unreported(),
        collection: StationCollectionIdentityV1::unreported(),
        legacy_source_sha256: runspec.station.input_sha256.clone(),
    }
}

fn continuous_provenance() -> ArtifactProvenanceV1 {
    let runspec = continuous_runspec();
    ArtifactProvenanceV1::new(
        station(&runspec),
        generation(&runspec),
        runspec,
        None,
        ActualOutputV1 {
            emitted_day_count: 11_322,
            first_date: Some(DateV1 {
                year: 1,
                month: 1,
                day: 1,
            }),
            last_date: Some(DateV1 {
                year: 31,
                month: 12,
                day: 31,
            }),
            coverage: CoverageV1::CompleteRun,
        },
        ArtifactIdentityV1::cli_text(HASH_A.to_owned()),
    )
    .unwrap()
}

#[test]
fn canonical_json_and_effective_hash_are_deterministic() {
    let provenance = continuous_provenance();
    let expected_runspec_json = concat!(
        "{\"cligen_runspec\":1,\"station\":{\"selector\":\"par\",",
        "\"lexical_path\":\"stations/id106388.par\",\"input_sha256\":\"",
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "\"},\"mode\":\"continuous\",\"begin_year\":1,\"years\":31,",
        "\"interpolation\":\"none\",\"burn\":17,\"generation_profile\":",
        "\"faithful_5_32_3\",\"qc_filter\":\"faithful\",\"observed\":null,",
        "\"storm\":null,\"output\":{\"cli_lexical_path\":\"out/wepp.cli\",",
        "\"parquet_lexical_path\":\"out/wepp.cli.parquet\",\"quality\":true,",
        "\"overwrite\":false,\"command_echo\":\"-r17 -iid106388.par\"}}"
    );
    assert_eq!(
        provenance
            .effective_runspec
            .to_compact_json_bytes()
            .unwrap(),
        expected_runspec_json.as_bytes()
    );
    assert_eq!(
        provenance.effective_runspec_sha256,
        "ac52388ac573d6eaf625d1fe1edd8ea0a3e31ac86ac331bc23abf4b3f86490dc"
    );
    let compact = provenance.to_compact_json_bytes().unwrap();
    assert_eq!(compact, provenance.to_compact_json_bytes().unwrap());
    assert_eq!(
        provenance.effective_runspec_sha256,
        provenance.effective_runspec.sha256().unwrap()
    );

    let text = std::str::from_utf8(&compact).unwrap();
    assert!(text.starts_with("{\"provenance_schema_version\":1,\"producer\":"));
    assert!(text.contains("\"fit\":{\"status\":\"unreported\",\"id\":null}"));
    assert!(!text.contains("timestamp"));
    assert!(!text.contains("resolved_path"));
    assert!(!text.ends_with('\n'));

    let pretty = provenance.to_pretty_json_bytes().unwrap();
    assert!(pretty.ends_with(b"\n"));
    assert!(!pretty[..pretty.len() - 1].ends_with(b"\n"));
    assert_eq!(
        ArtifactProvenanceV1::parse_json(&compact).unwrap(),
        provenance
    );
    assert_eq!(
        ArtifactProvenanceV1::parse_json(&pretty).unwrap(),
        provenance
    );
}

#[test]
fn canonical_storm_vector_pins_exact_f32_number_spelling() {
    let runspec = storm_runspec();
    let expected = concat!(
        "{\"cligen_runspec\":1,\"station\":{\"selector\":\"par\",",
        "\"lexical_path\":\"stations/id106388.par\",\"input_sha256\":\"",
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "\"},\"mode\":\"single_storm\",\"begin_year\":null,\"years\":null,",
        "\"interpolation\":\"none\",\"burn\":17,\"generation_profile\":",
        "\"faithful_5_32_3\",\"qc_filter\":\"faithful\",\"observed\":null,",
        "\"storm\":{\"date\":{\"year\":100,\"month\":2,\"day\":29},",
        "\"amount_in\":2.25,\"duration_h\":6.0,\"time_to_peak_fraction\":",
        "0.4000000059604645,\"max_intensity_in_per_h\":1.5},\"output\":{",
        "\"cli_lexical_path\":\"out/storm.cli\",\"parquet_lexical_path\":null,",
        "\"quality\":true,\"overwrite\":false,\"command_echo\":",
        "\"-r17 -iid106388.par -t4\"}}"
    );
    assert_eq!(
        runspec.to_compact_json_bytes().unwrap(),
        expected.as_bytes()
    );
    assert_eq!(
        runspec.sha256().unwrap(),
        "bf9aac32f1bba2b0452b26329bb62e87b1b53035600632a2083791e1f652cf54"
    );

    let mut exponent = runspec;
    exponent.storm.as_mut().unwrap().amount_in = 1.0e-7_f32 as f64;
    exponent.output.command_echo = "tab\tquote\"backslash\\".to_owned();
    let json = String::from_utf8(exponent.to_compact_json_bytes().unwrap()).unwrap();
    assert!(json.contains("\"amount_in\":1.0000000116860974e-7"));
    assert!(json.contains("\"command_echo\":\"tab\\tquote\\\"backslash\\\\\""));
}

#[test]
fn published_schema_pins_the_provenance_envelope() {
    let schema: Value = serde_json::from_str(include_str!(
        "../../../docs/specifications/provenance-v1.schema.json"
    ))
    .unwrap();
    assert_eq!(
        schema["properties"]["provenance_schema_version"]["const"],
        1
    );
    assert_eq!(
        schema["properties"]["source_authority"]["$ref"],
        "#/$defs/source_authority"
    );
    let value = serde_json::to_value(continuous_provenance()).unwrap();
    for required in schema["required"].as_array().unwrap() {
        assert!(value.get(required.as_str().unwrap()).is_some());
    }
}

#[test]
fn parameter_set_hash_is_syntax_independent_and_signed_zero_sensitive() {
    let bytes = std::fs::read(repo_root().join("fixtures/new-meadows-id/id106388.par")).unwrap();
    let par = ParFile::parse(&bytes).unwrap();
    let legacy_hash = parameter_set_sha256(par.fixed_monthly()).unwrap();
    assert_eq!(
        legacy_hash,
        "45962c35d173a2c8c1622599146d18a0b55ff2195d58ffc60ae4fad9d1b32e61"
    );
    let document = StationDocumentV1::from_legacy_par(&par).unwrap();
    let document_bytes = document.to_json_bytes().unwrap();
    assert_ne!(sha256_hex(&bytes), sha256_hex(&document_bytes));
    assert_eq!(document.lineage.source_sha256, sha256_hex(&bytes));
    let modern = document.to_model().unwrap();
    assert_eq!(parameter_set_sha256(&modern).unwrap(), legacy_hash);

    let mut signed_zero = modern.clone();
    signed_zero.ylt = -0.0;
    let negative = parameter_set_sha256(&signed_zero).unwrap();
    signed_zero.ylt = 0.0;
    assert_ne!(parameter_set_sha256(&signed_zero).unwrap(), negative);
}

#[test]
fn observed_identity_and_source_end_are_explicit() {
    let mut runspec = continuous_runspec();
    runspec.mode = GenerationModeV1::Observed;
    runspec.begin_year = Some(1990);
    runspec.interpolation = InterpolationV1::Fourier;
    runspec.observed = Some(EffectiveObservedV1 {
        lexical_path: "inputs/ws.prn".to_owned(),
        input_sha256: HASH_B.to_owned(),
    });
    let provenance = ArtifactProvenanceV1::new(
        station(&runspec),
        generation(&runspec),
        runspec,
        Some(ObservedInputV1 {
            schema: SchemaIdentityV1::legacy_observed(),
            input_sha256: HASH_B.to_owned(),
        }),
        ActualOutputV1 {
            emitted_day_count: 2,
            first_date: Some(DateV1 {
                year: 1990,
                month: 1,
                day: 1,
            }),
            last_date: Some(DateV1 {
                year: 1990,
                month: 1,
                day: 2,
            }),
            coverage: CoverageV1::ObservedSourceEnd,
        },
        ArtifactIdentityV1::cli_parquet(),
    )
    .unwrap();
    let json = String::from_utf8(provenance.to_compact_json_bytes().unwrap()).unwrap();
    assert!(json.contains("\"coverage\":\"observed_source_end\""));
    assert!(json.contains("\"input_sha256\":\"bbbbbbbb"));
}

#[test]
fn source_storm_calendar_and_gregorian_calendar_remain_independent() {
    let mut runspec = continuous_runspec();
    runspec.mode = GenerationModeV1::SingleStorm;
    runspec.begin_year = None;
    runspec.years = None;
    runspec.output.parquet_lexical_path = None;
    runspec.storm = Some(EffectiveStormV1 {
        date: DateV1 {
            year: 100,
            month: 2,
            day: 29,
        },
        amount_in: 2.25,
        duration_h: Some(6.0),
        time_to_peak_fraction: Some(0.4_f32 as f64),
        max_intensity_in_per_h: Some(1.5),
    });
    let storm = ArtifactProvenanceV1::new(
        station(&runspec),
        generation(&runspec),
        runspec,
        None,
        ActualOutputV1 {
            emitted_day_count: 1,
            first_date: Some(DateV1 {
                year: 100,
                month: 2,
                day: 29,
            }),
            last_date: Some(DateV1 {
                year: 100,
                month: 2,
                day: 29,
            }),
            coverage: CoverageV1::SingleEvent,
        },
        ArtifactIdentityV1::storm_cli_text(HASH_A.to_owned()),
    )
    .unwrap();
    storm.validate().unwrap();

    let mut non_f32_storm = storm.clone();
    non_f32_storm
        .effective_runspec
        .storm
        .as_mut()
        .unwrap()
        .amount_in = std::f64::consts::PI;
    assert_error_path(
        non_f32_storm.validate().unwrap_err(),
        "effective_runspec.storm.amount_in",
    );

    let mut continuous = continuous_provenance();
    continuous.actual.first_date = Some(DateV1 {
        year: 100,
        month: 2,
        day: 29,
    });
    assert!(continuous.validate().is_err());
}

#[test]
fn validation_rejects_stale_uppercase_and_cross_axis_hashes() {
    let mut stale = continuous_provenance();
    stale.effective_runspec.output.command_echo = "changed".to_owned();
    assert_error_path(stale.validate().unwrap_err(), "effective_runspec_sha256");

    let mut uppercase = continuous_provenance();
    uppercase.station.parameter_set_sha256 = "A".repeat(64);
    assert_error_path(
        uppercase.validate().unwrap_err(),
        "station.parameter_set_sha256",
    );

    let mut cross_axis = continuous_provenance();
    cross_axis.station.input_schema = SchemaIdentityV1::modern_station();
    assert_error_path(cross_axis.validate().unwrap_err(), "station.input_schema");

    let mut false_lineage = continuous_provenance();
    false_lineage.station.legacy_source_sha256 = HASH_B.to_owned();
    assert_error_path(
        false_lineage.validate().unwrap_err(),
        "station.legacy_source_sha256",
    );

    let mut wrong_rng = continuous_provenance();
    wrong_rng.generation.rng_scheme = RngSchemeV1::SplitMix64MonthlyV0;
    assert_error_path(wrong_rng.validate().unwrap_err(), "generation.rng_scheme");

    let mut oversized_burn = continuous_provenance();
    oversized_burn.effective_runspec.burn = i32::MAX as u32 + 1;
    oversized_burn.generation.burn_per_stream = i32::MAX as u32 + 1;
    assert_error_path(
        oversized_burn.validate().unwrap_err(),
        "effective_runspec.burn",
    );
}

#[test]
fn actual_output_validation_rejects_inconsistent_spans_and_coverage() {
    let mut zero_with_dates = continuous_provenance();
    zero_with_dates.actual.emitted_day_count = 0;
    assert_error_path(zero_with_dates.validate().unwrap_err(), "actual");

    let mut nonzero_without_first = continuous_provenance();
    nonzero_without_first.actual.first_date = None;
    assert_error_path(nonzero_without_first.validate().unwrap_err(), "actual");

    let mut reversed = continuous_provenance();
    reversed.actual.last_date = Some(DateV1 {
        year: 1,
        month: 1,
        day: 1,
    });
    reversed.actual.first_date = Some(DateV1 {
        year: 2,
        month: 1,
        day: 1,
    });
    assert_error_path(reversed.validate().unwrap_err(), "actual.last_date");

    let mut wrong_coverage = continuous_provenance();
    wrong_coverage.actual.coverage = CoverageV1::ObservedSourceEnd;
    assert_error_path(wrong_coverage.validate().unwrap_err(), "actual.coverage");
}

#[test]
fn malformed_json_and_error_sources_are_reported() {
    let mut json: Value =
        serde_json::from_slice(&continuous_provenance().to_compact_json_bytes().unwrap()).unwrap();
    json.as_object_mut()
        .unwrap()
        .insert("unexpected".to_owned(), Value::Bool(true));
    let error = ArtifactProvenanceV1::parse_json(&serde_json::to_vec(&json).unwrap()).unwrap_err();
    assert!(error.to_string().contains("unexpected"));
    assert!(error.source().is_some());

    let trailing = ArtifactProvenanceV1::parse_json(b"{} {}").unwrap_err();
    assert!(trailing.source().is_some());

    let source = serde_json::from_str::<Value>("{").unwrap_err();
    let serialize = ProvenanceError::Serialize { source };
    assert!(serialize.to_string().starts_with("serialize provenance:"));
    assert!(serialize.source().is_some());

    let validation = ProvenanceError::Validation {
        field_path: "field".to_owned(),
        message: "bad".to_owned(),
    };
    assert_eq!(validation.to_string(), "provenance field: bad");
    assert!(validation.source().is_none());
}

#[test]
fn exact_input_sha_helper_is_lowercase_and_byte_sensitive() {
    assert_eq!(
        sha256_hex(b"abc"),
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    );
    assert_ne!(sha256_hex(b"abc"), sha256_hex(b"abc\n"));
}

fn assert_error_path(error: ProvenanceError, expected: &str) {
    match error {
        ProvenanceError::Validation { field_path, .. } => assert_eq!(field_path, expected),
        other => panic!("expected validation error, got {other}"),
    }
}
