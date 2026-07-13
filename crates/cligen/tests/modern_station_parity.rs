//! End-to-end parity of revision-1 station documents with legacy .par
//! intake across the complete committed golden matrix.

use std::path::{Path, PathBuf};
use std::process::Command;

use cligen::quality::QualityReport;
use serde_yaml::{Mapping, Value};

const GOLDENS: [&str; 12] = [
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
    "new-meadows-id-single-storm-seed0",
    "new-meadows-id-single-storm-seed17",
];

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .unwrap()
}

fn key(name: &str) -> Value {
    Value::String(name.to_owned())
}

fn field_mapping_mut<'a>(document: &'a mut Value, field: &str) -> &'a mut Mapping {
    document
        .as_mapping_mut()
        .unwrap()
        .get_mut(key(field))
        .unwrap()
        .as_mapping_mut()
        .unwrap()
}

fn string_field<'a>(document: &'a Value, section: &str, field: &str) -> &'a str {
    document
        .as_mapping()
        .unwrap()
        .get(key(section))
        .unwrap()
        .as_mapping()
        .unwrap()
        .get(key(field))
        .unwrap()
        .as_str()
        .unwrap()
}

fn set_string(mapping: &mut Mapping, field: &str, value: &Path) {
    mapping.insert(
        key(field),
        Value::String(value.to_str().unwrap().to_owned()),
    );
}

fn write_runspec(path: &Path, document: &Value) {
    std::fs::write(path, serde_yaml::to_string(document).unwrap()).unwrap();
}

fn assert_command_succeeds(binary: &str, args: &[&Path], context: &str) {
    let mut command = Command::new(binary);
    for argument in args {
        command.arg(argument);
    }
    let output = command.output().unwrap();
    assert!(
        output.status.success(),
        "{context}: {}",
        String::from_utf8_lossy(&output.stderr)
    );
}

fn convert_station(binary: &str, par: &Path, document: &Path, repeat: &Path, case: &str) {
    for destination in [document, repeat] {
        let output = Command::new(binary)
            .arg("stations")
            .arg("convert")
            .arg(par)
            .arg(destination)
            .output()
            .unwrap();
        assert!(
            output.status.success(),
            "{case}: station conversion failed: {}",
            String::from_utf8_lossy(&output.stderr)
        );
    }
    assert_eq!(
        std::fs::read(document).unwrap(),
        std::fs::read(repeat).unwrap(),
        "{case}: repeated conversion was not deterministic"
    );
}

fn validate_and_run(binary: &str, runspec: &Path, output: &Path, case: &str) {
    assert_command_succeeds(binary, &[Path::new("validate"), runspec], case);
    assert!(
        !output.exists(),
        "{case}: validation must not create the output"
    );
    assert_command_succeeds(binary, &[Path::new("run"), runspec], case);
}

fn quality_sidecar(cli: &Path) -> PathBuf {
    let mut path = cli.as_os_str().to_owned();
    path.push(".quality.json");
    PathBuf::from(path)
}

#[test]
fn modern_station_documents_preserve_all_golden_outputs_and_sidecars() {
    let root = repo_root();
    let binary = env!("CARGO_BIN_EXE_cligen");
    let work = root.join("target/modern-station-parity");
    let _ = std::fs::remove_dir_all(&work);
    std::fs::create_dir_all(&work).unwrap();

    for case in GOLDENS {
        let original_path = root
            .join("crates/cligen/tests/fixtures/runspec")
            .join(case)
            .join("inp.yaml");
        let original_dir = original_path.parent().unwrap();
        let original: Value =
            serde_yaml::from_slice(&std::fs::read(&original_path).unwrap()).unwrap();
        let historical_echo = string_field(&original, "output", "command_echo").to_owned();
        let par = original_dir
            .join(string_field(&original, "station", "par"))
            .canonicalize()
            .unwrap();

        let case_dir = work.join(case);
        std::fs::create_dir_all(&case_dir).unwrap();
        let station_document = case_dir.join(format!("{case}.station.json"));
        let repeat_document = case_dir.join(format!("{case}.repeat.station.json"));
        convert_station(binary, &par, &station_document, &repeat_document, case);
        let station_document = station_document.canonicalize().unwrap();

        let mut resolved = original.clone();
        set_string(field_mapping_mut(&mut resolved, "station"), "par", &par);
        if original.as_mapping().unwrap().contains_key(key("observed")) {
            let prn = original_dir
                .join(string_field(&original, "observed", "prn"))
                .canonicalize()
                .unwrap();
            set_string(field_mapping_mut(&mut resolved, "observed"), "prn", &prn);
        }

        let legacy_output = case_dir.join("legacy.cli");
        let modern_output = case_dir.join("modern.cli");
        let mut legacy = resolved.clone();
        set_string(
            field_mapping_mut(&mut legacy, "output"),
            "cli",
            &legacy_output,
        );
        let mut modern = resolved;
        let modern_station = field_mapping_mut(&mut modern, "station");
        modern_station.remove(key("par"));
        set_string(modern_station, "document", &station_document);
        set_string(
            field_mapping_mut(&mut modern, "output"),
            "cli",
            &modern_output,
        );

        assert_eq!(
            string_field(&legacy, "output", "command_echo"),
            historical_echo,
            "{case}: legacy runspec changed the historical command echo"
        );
        assert_eq!(
            string_field(&modern, "output", "command_echo"),
            historical_echo,
            "{case}: modern runspec changed the historical command echo"
        );

        let legacy_runspec = case_dir.join("legacy.yaml");
        let modern_runspec = case_dir.join("modern.yaml");
        write_runspec(&legacy_runspec, &legacy);
        write_runspec(&modern_runspec, &modern);
        validate_and_run(binary, &legacy_runspec, &legacy_output, case);
        validate_and_run(binary, &modern_runspec, &modern_output, case);

        let legacy_cli = std::fs::read(&legacy_output).unwrap();
        let modern_cli = std::fs::read(&modern_output).unwrap();
        let golden = std::fs::read(
            root.join("docs/work-packages/20260709-golden-fixture-harness/artifacts/goldens")
                .join(format!("{case}.cli")),
        )
        .unwrap();
        assert_eq!(modern_cli, legacy_cli, "{case}: modern vs legacy CLI");
        assert_eq!(modern_cli, golden, "{case}: modern vs committed golden");
        let mut modern_quality: QualityReport =
            serde_json::from_slice(&std::fs::read(quality_sidecar(&modern_output)).unwrap())
                .unwrap();
        let mut legacy_quality: QualityReport =
            serde_json::from_slice(&std::fs::read(quality_sidecar(&legacy_output)).unwrap())
                .unwrap();
        assert_eq!(
            modern_quality.identity.content.station_parameter_set_sha256,
            legacy_quality.identity.content.station_parameter_set_sha256,
            "{case}: station parameter-set identity"
        );
        assert_ne!(
            modern_quality
                .identity
                .provenance
                .as_ref()
                .unwrap()
                .station
                .input_schema,
            legacy_quality
                .identity
                .provenance
                .as_ref()
                .unwrap()
                .station
                .input_schema,
            "{case}: selected input syntax remains truthful"
        );
        modern_quality.identity.provenance = None;
        legacy_quality.identity.provenance = None;
        assert_eq!(
            modern_quality, legacy_quality,
            "{case}: modern vs legacy quality metrics"
        );
    }

    let case = GOLDENS[0];
    let case_dir = work.join(case);
    let station_lexical = format!("./{case}.station.json");
    let original_path = root
        .join("crates/cligen/tests/fixtures/runspec")
        .join(case)
        .join("inp.yaml");
    let original: Value = serde_yaml::from_slice(&std::fs::read(&original_path).unwrap()).unwrap();
    let mut no_echo = original;
    let station = field_mapping_mut(&mut no_echo, "station");
    station.remove(key("par"));
    station.insert(key("document"), Value::String(station_lexical.clone()));
    let no_echo_output = case_dir.join("canonical-echo.cli");
    let output = field_mapping_mut(&mut no_echo, "output");
    output.remove(key("command_echo"));
    set_string(output, "cli", &no_echo_output);
    let no_echo_runspec = case_dir.join("canonical-echo.yaml");
    write_runspec(&no_echo_runspec, &no_echo);
    validate_and_run(binary, &no_echo_runspec, &no_echo_output, "canonical echo");
    let cli = std::fs::read_to_string(no_echo_output).unwrap();
    assert!(
        cli.lines()
            .take(5)
            .any(|line| line.contains(&format!("--station-document={station_lexical}"))),
        "canonical header did not retain the lexical station-document path"
    );
}
