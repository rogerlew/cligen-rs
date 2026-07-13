//! A1 package-level acceptance: real runspec output, faithful text parity,
//! exact typed/Parquet values, and independently versioned provenance.

use std::path::{Path, PathBuf};

use cligen::par::ParFile;
use cligen::parquet_output::read_cli_parquet_v1;
use cligen::provenance::{
    ArtifactProvenanceV1, CalendarV1, CoverageV1, MediaTypeV1, SchemaIdentityV1,
};
use cligen::runspec::RunspecDocument;
use cligen::station::StationDocumentV1;
use cligen::typed_output::ClimateRowV1;
use serde_yaml::{Mapping, Value};

const CLIMATE_GOLDENS: [&str; 10] = [
    "new-meadows-id-seed0",
    "new-meadows-id-seed17",
    "jeogla-au-seed0",
    "jeogla-au-seed17",
    "mt-wilson-ca-observed-seed0",
    "mt-wilson-ca-observed-seed17",
    "fish-springs-ut-observed-padded-seed0",
    "fish-springs-ut-observed-padded-seed17",
    "fish-springs-ut-observed-truncated-seed0",
    "fish-springs-ut-observed-truncated-seed17",
];

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .unwrap()
}

fn key(value: &str) -> Value {
    Value::String(value.to_owned())
}

fn mapping_mut<'a>(document: &'a mut Value, field: &str) -> &'a mut Mapping {
    document
        .as_mapping_mut()
        .unwrap()
        .get_mut(key(field))
        .unwrap()
        .as_mapping_mut()
        .unwrap()
}

fn sidecar(path: &Path, suffix: &str) -> PathBuf {
    let mut name = path.as_os_str().to_owned();
    name.push(suffix);
    PathBuf::from(name)
}

fn golden(case: &str) -> Vec<u8> {
    std::fs::read(
        repo_root()
            .join("docs/work-packages/20260709-golden-fixture-harness/artifacts/goldens")
            .join(format!("{case}.cli")),
    )
    .unwrap()
}

fn footer_value<'a>(footer: &'a [(String, Option<String>)], key: &str) -> Option<&'a str> {
    footer
        .iter()
        .find(|(candidate, _)| candidate == key)
        .and_then(|(_, value)| value.as_deref())
}

#[test]
fn all_climate_goldens_emit_conforming_parquet_and_text_provenance() {
    let root = repo_root();
    let work = root.join("target/a1-golden-output");
    std::fs::create_dir_all(&work).unwrap();

    for case in CLIMATE_GOLDENS {
        let original_path = root
            .join("crates/cligen/tests/fixtures/runspec")
            .join(case)
            .join("inp.yaml");
        let mut document: Value =
            serde_yaml::from_slice(&std::fs::read(&original_path).unwrap()).unwrap();
        let cli_path = work.join(format!("{case}.cli"));
        let parquet_path = work.join(format!("{case}.cli.parquet"));
        let output = mapping_mut(&mut document, "output");
        output.insert(key("cli"), Value::String(cli_path.display().to_string()));
        output.insert(
            key("parquet"),
            Value::String(parquet_path.display().to_string()),
        );
        output.insert(key("overwrite"), Value::Bool(true));

        let yaml = serde_yaml::to_string(&document).unwrap();
        let run = RunspecDocument::parse(&yaml)
            .unwrap()
            .resolve(original_path.parent().unwrap())
            .unwrap();
        let expected_typed = if matches!(
            case,
            "new-meadows-id-seed0" | "fish-springs-ut-observed-truncated-seed0"
        ) {
            Some(run.generate_climate_v1().unwrap().rows)
        } else {
            None
        };
        run.generate_and_write().unwrap();

        assert_eq!(std::fs::read(&cli_path).unwrap(), golden(case), "{case}");
        let text_provenance = ArtifactProvenanceV1::parse_json(
            &std::fs::read(sidecar(&cli_path, ".provenance.json")).unwrap(),
        )
        .unwrap();
        text_provenance
            .verify_cli_bytes(&std::fs::read(&cli_path).unwrap())
            .unwrap();
        assert_eq!(text_provenance.artifact.media_type, MediaTypeV1::CliText);
        assert_eq!(
            text_provenance.station.input_schema,
            SchemaIdentityV1::legacy_station()
        );

        let readback = read_cli_parquet_v1(&parquet_path).unwrap();
        if let Some(expected) = expected_typed {
            assert_eq!(readback.rows, expected, "{case}: exact typed readback");
        }
        let compact = footer_value(&readback.footer_metadata, "cligen.provenance").unwrap();
        let parquet_provenance = ArtifactProvenanceV1::parse_json(compact.as_bytes()).unwrap();
        assert_eq!(
            parquet_provenance.artifact.output_schema,
            SchemaIdentityV1::cli_parquet()
        );
        assert_eq!(
            parquet_provenance.effective_runspec_sha256,
            text_provenance.effective_runspec_sha256
        );
        assert_eq!(
            parquet_provenance.station.parameter_set_sha256,
            text_provenance.station.parameter_set_sha256
        );
        let expected_coverage = if case.contains("observed") {
            CoverageV1::ObservedSourceEnd
        } else {
            CoverageV1::CompleteRun
        };
        assert_eq!(parquet_provenance.actual.coverage, expected_coverage);
        assert_eq!(
            parquet_provenance.actual.emitted_day_count as usize,
            readback.rows.len()
        );
    }
}

fn normalize_run_id(rows: &mut [ClimateRowV1], run_id: &str) {
    for row in rows {
        row.run_id = run_id.to_owned();
    }
}

#[test]
fn legacy_and_modern_station_inputs_share_values_but_not_input_identity() {
    let root = repo_root();
    let work = root.join("target/a1-station-axes");
    std::fs::create_dir_all(&work).unwrap();
    let par_path = root.join("fixtures/new-meadows-id/id106388.par");
    let par_bytes = std::fs::read(&par_path).unwrap();
    let par = ParFile::parse(&par_bytes).unwrap();
    let station_document = StationDocumentV1::from_legacy_par(&par).unwrap();
    let station_path = work.join("new-meadows.station.json");
    std::fs::write(&station_path, station_document.to_json_bytes().unwrap()).unwrap();

    let make = |selector: &str, station: &Path, stem: &str| {
        let cli = work.join(format!("{stem}.cli"));
        let parquet = work.join(format!("{stem}.cli.parquet"));
        format!(
            "cligen_runspec: 1\n\
             station: {{ {selector}: {} }}\n\
             mode: continuous\n\
             simulation: {{ begin_year: 1, years: 1 }}\n\
             output: {{ cli: {}, parquet: {}, overwrite: true, command_echo: \"-iid106388.par\" }}\n",
            station.display(),
            cli.display(),
            parquet.display(),
        )
    };
    let legacy = RunspecDocument::parse(&make("par", &par_path, "legacy"))
        .unwrap()
        .resolve(&root)
        .unwrap();
    let modern = RunspecDocument::parse(&make("document", &station_path, "modern"))
        .unwrap()
        .resolve(&root)
        .unwrap();
    let mut legacy_generated = legacy.generate_climate_v1().unwrap();
    let mut modern_generated = modern.generate_climate_v1().unwrap();

    assert_eq!(legacy_generated.legacy_cli, modern_generated.legacy_cli);
    assert_ne!(
        legacy_generated.provenance.station.input_schema,
        modern_generated.provenance.station.input_schema
    );
    assert_ne!(
        legacy_generated.provenance.station.input_sha256,
        modern_generated.provenance.station.input_sha256
    );
    assert_eq!(
        legacy_generated.provenance.station.model,
        modern_generated.provenance.station.model
    );
    assert_eq!(
        legacy_generated.provenance.station.parameter_set_sha256,
        modern_generated.provenance.station.parameter_set_sha256
    );
    let canonical_run_id = legacy_generated.provenance.effective_runspec_sha256.clone();
    normalize_run_id(&mut modern_generated.rows, &canonical_run_id);
    normalize_run_id(&mut legacy_generated.rows, &canonical_run_id);
    assert_eq!(legacy_generated.rows, modern_generated.rows);
}

#[test]
fn parquet_collision_preflight_does_not_publish_the_text_artifact() {
    let root = repo_root();
    let work = root.join("target/a1-collision-preflight");
    std::fs::create_dir_all(&work).unwrap();
    let cli = work.join("blocked.cli");
    let parquet = work.join("blocked.cli.parquet");
    let _ = std::fs::remove_file(&cli);
    let _ = std::fs::remove_file(sidecar(&cli, ".provenance.json"));
    std::fs::write(&parquet, b"existing").unwrap();
    let yaml = format!(
        "cligen_runspec: 1\n\
         station: {{ par: {} }}\n\
         mode: continuous\n\
         simulation: {{ begin_year: 1, years: 1 }}\n\
         output: {{ cli: {}, parquet: {} }}\n",
        root.join("fixtures/new-meadows-id/id106388.par").display(),
        cli.display(),
        parquet.display(),
    );
    let run = RunspecDocument::parse(&yaml)
        .unwrap()
        .resolve(&root)
        .unwrap();
    let error = run.generate_and_write().unwrap_err();
    assert!(error.to_string().contains("blocked.cli.parquet"));
    assert!(!cli.exists());
    assert!(!sidecar(&cli, ".provenance.json").exists());
    assert_eq!(std::fs::read(&parquet).unwrap(), b"existing");
}

#[test]
fn source_calendar_storm_text_does_not_pass_through_gregorian_typed_rows() {
    let root = repo_root();
    let work = root.join("target/a1-source-calendar-storm");
    std::fs::create_dir_all(&work).unwrap();
    let cli = work.join("storm.cli");
    let yaml = format!(
        "cligen_runspec: 1\n\
         station: {{ par: {} }}\n\
         mode: single_storm\n\
         rng: {{ burn: 0 }}\n\
         single_storm: {{ date: {{ month: 2, day: 29, year: 100 }}, amount_in: 2.25, duration_h: 6.0, time_to_peak_fraction: 0.4, max_intensity_in_per_h: 1.5 }}\n\
         output: {{ cli: {}, overwrite: true, quality: false }}\n",
        root.join("fixtures/new-meadows-id/id106388.par").display(),
        cli.display(),
    );
    let run = RunspecDocument::parse(&yaml)
        .unwrap()
        .resolve(&root)
        .unwrap();
    let expected = run.generate().unwrap();
    let typed_error = run.generate_climate_v1().unwrap_err();
    assert!(typed_error.to_string().contains("continuous and observed"));

    run.generate_and_write().unwrap();
    assert_eq!(std::fs::read_to_string(&cli).unwrap(), expected);
    let provenance = ArtifactProvenanceV1::parse_json(
        &std::fs::read(sidecar(&cli, ".provenance.json")).unwrap(),
    )
    .unwrap();
    assert_eq!(provenance.actual.coverage, CoverageV1::SingleEvent);
    assert_eq!(
        provenance.artifact.calendar,
        CalendarV1::SourceStormCalendar
    );
}

#[test]
fn suffix_only_parquet_basename_is_a_valid_declared_destination() {
    let root = repo_root();
    let work = root.join("target/a1-suffix-only-parquet");
    std::fs::create_dir_all(&work).unwrap();
    let cli = work.join("weather.cli");
    let parquet = work.join(".cli.parquet");
    let yaml = format!(
        "cligen_runspec: 1\n\
         station: {{ par: {} }}\n\
         mode: continuous\n\
         simulation: {{ begin_year: 1, years: 1 }}\n\
         output: {{ cli: {}, parquet: {}, overwrite: true, quality: false }}\n",
        root.join("fixtures/new-meadows-id/id106388.par").display(),
        cli.display(),
        parquet.display(),
    );
    let run = RunspecDocument::parse(&yaml)
        .unwrap()
        .resolve(&root)
        .unwrap();
    run.generate_and_write().unwrap();
    assert_eq!(read_cli_parquet_v1(&parquet).unwrap().rows.len(), 365);
}

#[test]
fn aliased_and_reserved_destinations_fail_before_text_publication() {
    let root = repo_root();
    let work = root.join("target/a1-output-aliases");
    let nested = work.join("nested");
    std::fs::create_dir_all(&nested).unwrap();
    let cases = [
        (
            work.join("shared.cli.parquet"),
            nested.join("../shared.cli.parquet"),
        ),
        (
            work.join(".weather.cli.parquet.cligen-stage"),
            work.join("weather.cli.parquet"),
        ),
        (
            work.join("Weather.CLI.PARQUET"),
            work.join("weather.cli.parquet"),
        ),
        (
            work.join("é.cli.parquet"),
            work.join("e\u{301}.cli.parquet"),
        ),
        (work.join("ß.cli.parquet"), work.join("ss.cli.parquet")),
        (work.join("Σ.cli.parquet"), work.join("ς.cli.parquet")),
        (work.join("ﬀ.cli.parquet"), work.join("ff.cli.parquet")),
    ];
    for (cli, parquet) in cases {
        let _ = std::fs::remove_file(&cli);
        let _ = std::fs::remove_file(&parquet);
        let yaml = format!(
            "cligen_runspec: 1\n\
             station: {{ par: {} }}\n\
             mode: continuous\n\
             simulation: {{ begin_year: 1, years: 1 }}\n\
             output: {{ cli: {}, parquet: {}, overwrite: true, quality: false }}\n",
            root.join("fixtures/new-meadows-id/id106388.par").display(),
            cli.display(),
            parquet.display(),
        );
        let run = RunspecDocument::parse(&yaml)
            .unwrap()
            .resolve(&root)
            .unwrap();
        let error = run.generate_and_write().unwrap_err();
        assert!(error.to_string().contains("must not alias"));
        assert!(!cli.exists());
        assert!(!parquet.exists());
    }
}

#[cfg(unix)]
#[test]
fn companion_aliases_fail_closed_and_hardlinks_are_safely_replaced() {
    use std::os::unix::fs::{symlink, MetadataExt as _};

    let root = repo_root();
    let work = root.join("target/a1-companion-aliases");
    std::fs::create_dir_all(&work).unwrap();
    let cli = work.join("weather.cli");
    let provenance = sidecar(&cli, ".provenance.json");
    let lock = work.join(".weather.cli.cligen-lock");
    let yaml = format!(
        "cligen_runspec: 1\n\
         station: {{ par: {} }}\n\
         mode: continuous\n\
         simulation: {{ begin_year: 1, years: 1 }}\n\
         output: {{ cli: {}, overwrite: true, quality: false }}\n",
        root.join("fixtures/new-meadows-id/id106388.par").display(),
        cli.display(),
    );

    let _ = std::fs::remove_file(&cli);
    let _ = std::fs::remove_file(&provenance);
    symlink(&cli, &provenance).unwrap();
    let run = RunspecDocument::parse(&yaml)
        .unwrap()
        .resolve(&root)
        .unwrap();
    let error = run.generate_and_write().unwrap_err();
    assert!(error.to_string().contains("must not alias"));
    assert!(!cli.exists());

    std::fs::remove_file(&provenance).unwrap();
    std::fs::write(&lock, b"other writer").unwrap();
    let run = RunspecDocument::parse(&yaml)
        .unwrap()
        .resolve(&root)
        .unwrap();
    assert!(run
        .generate_and_write()
        .unwrap_err()
        .to_string()
        .contains("cligen-lock"));
    assert_eq!(std::fs::read(&lock).unwrap(), b"other writer");
    std::fs::remove_file(&lock).unwrap();

    std::fs::write(&cli, b"old climate").unwrap();
    std::fs::hard_link(&cli, &provenance).unwrap();
    let run = RunspecDocument::parse(&yaml)
        .unwrap()
        .resolve(&root)
        .unwrap();
    run.generate_and_write().unwrap();
    ArtifactProvenanceV1::parse_json(&std::fs::read(&provenance).unwrap()).unwrap();
    assert!(std::fs::read_to_string(&cli)
        .unwrap()
        .starts_with("5.32300\n"));
    assert_ne!(
        std::fs::metadata(&cli).unwrap().ino(),
        std::fs::metadata(&provenance).unwrap().ino()
    );
}
