use std::path::{Path, PathBuf};
use std::process::Command;

use cligen::par::ParFile;
use cligen::station::{FixedMonthly5323, StationDocumentV1};
use serde_json::Value;

const FIXTURES: [&str; 4] = [
    "fixtures/new-meadows-id/id106388.par",
    "fixtures/mt-wilson-ca/ca046006.par",
    "fixtures/fish-springs-ut/ut422852.par",
    "fixtures/jeogla-au/ASN00057011.par",
];

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .unwrap()
}

fn converted_fixture(relative: &str) -> (Vec<u8>, FixedMonthly5323, StationDocumentV1) {
    let bytes = std::fs::read(repo_root().join(relative)).unwrap();
    let par = ParFile::parse(&bytes).unwrap();
    let model = par.fixed_monthly().clone();
    let document = StationDocumentV1::from_legacy_par(&par).unwrap();
    (bytes, model, document)
}

fn assert_f32(label: &str, actual: f32, expected: f32) {
    assert_eq!(
        actual.to_bits(),
        expected.to_bits(),
        "{label}: actual {actual:?}, expected {expected:?}"
    );
}

fn assert_f32_array<const N: usize>(label: &str, actual: &[f32; N], expected: &[f32; N]) {
    for index in 0..N {
        assert_f32(&format!("{label}[{index}]"), actual[index], expected[index]);
    }
}

fn assert_f32_2d<const N: usize, const M: usize>(
    label: &str,
    actual: &[[f32; M]; N],
    expected: &[[f32; M]; N],
) {
    for index in 0..N {
        assert_f32_array(
            &format!("{label}[{index}]"),
            &actual[index],
            &expected[index],
        );
    }
}

fn assert_f32_3d<const N: usize, const M: usize, const L: usize>(
    label: &str,
    actual: &[[[f32; L]; M]; N],
    expected: &[[[f32; L]; M]; N],
) {
    for index in 0..N {
        assert_f32_2d(
            &format!("{label}[{index}]"),
            &actual[index],
            &expected[index],
        );
    }
}

fn assert_model_bits(actual: &FixedMonthly5323, expected: &FixedMonthly5323) {
    assert_eq!(actual.stidd, expected.stidd, "stidd");
    assert_eq!(actual.nst, expected.nst, "nst");
    assert_eq!(actual.nstat, expected.nstat, "nstat");
    assert_eq!(actual.igcode, expected.igcode, "igcode");
    assert_f32("ylt", actual.ylt, expected.ylt);
    assert_f32("yll", actual.yll, expected.yll);
    assert_eq!(actual.years, expected.years, "years");
    assert_eq!(actual.itype, expected.itype, "itype");
    assert_eq!(actual.elev_ft, expected.elev_ft, "elev_ft");
    assert_f32("tp6", actual.tp6, expected.tp6);
    assert_f32_2d("rst", &actual.rst, &expected.rst);
    assert_f32_2d("prw", &actual.prw, &expected.prw);
    assert_f32_array("obmx", &actual.obmx, &expected.obmx);
    assert_f32_array("obmn", &actual.obmn, &expected.obmn);
    assert_f32_array("stdtx", &actual.stdtx, &expected.stdtx);
    assert_f32_array("stdtm", &actual.stdtm, &expected.stdtm);
    assert_f32_array("obsl", &actual.obsl, &expected.obsl);
    assert_f32_array("stdsl", &actual.stdsl, &expected.stdsl);
    assert_f32_array("wi_raw", &actual.wi_raw, &expected.wi_raw);
    assert_f32_array("rh", &actual.rh, &expected.rh);
    assert_f32_array("timpkd", &actual.timpkd, &expected.timpkd);
    assert_f32_3d("wvl", &actual.wvl, &expected.wvl);
    assert_f32_array("calm", &actual.calm, &expected.calm);
    assert_eq!(actual.site, expected.site, "site");
    assert_f32_array("wgt", &actual.wgt, &expected.wgt);
}

fn valid_json_value() -> Value {
    let (_, _, document) = converted_fixture(FIXTURES[0]);
    serde_json::from_slice(&document.to_json_bytes().unwrap()).unwrap()
}

fn parse_value(value: &Value) -> Result<StationDocumentV1, String> {
    StationDocumentV1::parse_json(&serde_json::to_vec(value).unwrap())
        .map_err(|error| error.to_string())
}

fn assert_rejected(name: &str, value: &Value, expected_path: &str) {
    let error = parse_value(value).unwrap_err();
    assert!(
        error.contains(expected_path),
        "{name}: expected error path {expected_path:?}, got {error:?}"
    );
}

fn with_removed(mut value: Value, pointer: &str, key: &str) -> Value {
    value
        .pointer_mut(pointer)
        .unwrap()
        .as_object_mut()
        .unwrap()
        .remove(key);
    value
}

fn replace_location_latitude(bytes: &[u8], replacement: &str) -> Vec<u8> {
    let text = std::str::from_utf8(bytes).unwrap();
    let location = text.find("\"location\": {").unwrap();
    let relative = text[location..].find("\"latitude\": ").unwrap();
    let value_start = location + relative + "\"latitude\": ".len();
    let value_end = text[value_start..]
        .find([',', '\n'])
        .map(|offset| value_start + offset)
        .unwrap();
    let mut changed = String::with_capacity(text.len() + replacement.len());
    changed.push_str(&text[..value_start]);
    changed.push_str(replacement);
    changed.push_str(&text[value_end..]);
    changed.into_bytes()
}

#[test]
fn legacy_conversion_is_bitwise_lossless_and_json_is_deterministic() {
    for fixture in FIXTURES {
        let (source, expected, document) = converted_fixture(fixture);
        assert_eq!(
            document.lineage.source_sha256,
            cligen::quality::sha256_hex(&source),
            "{fixture}: lineage must hash the parsed ParFile's retained bytes"
        );
        let first = document.to_json_bytes().unwrap();
        let second = document.to_json_bytes().unwrap();
        assert_eq!(first, second, "{fixture}: repeated serialization");
        assert_eq!(first.last(), Some(&b'\n'), "{fixture}: trailing LF");

        let reparsed = StationDocumentV1::parse_json(&first).unwrap();
        assert_eq!(
            reparsed.to_json_bytes().unwrap(),
            first,
            "{fixture}: parse/serialize idempotence"
        );
        assert_model_bits(&reparsed.to_model().unwrap(), &expected);
    }
}

#[test]
fn negative_zero_survives_document_serialization_by_bits() {
    let (_, _, mut document) = converted_fixture(FIXTURES[0]);
    document.parameters.precipitation.mean_daily[0] = -0.0;
    let bytes = document.to_json_bytes().unwrap();
    assert!(
        std::str::from_utf8(&bytes).unwrap().contains("-0.0"),
        "the canonical JSON must declare the negative sign"
    );
    let model = StationDocumentV1::parse_json(&bytes)
        .unwrap()
        .to_model()
        .unwrap();
    assert_eq!(
        model.rst[0][0].to_bits(),
        (-0.0f32).to_bits(),
        "negative zero must not normalize to positive zero"
    );
}

#[test]
fn station_document_fails_closed_for_structural_and_contract_mutations() {
    let valid = valid_json_value();

    let mut unknown = valid.clone();
    unknown
        .as_object_mut()
        .unwrap()
        .insert("unexpected".to_owned(), Value::Bool(true));
    assert_rejected("unknown top-level field", &unknown, "unexpected");

    let missing_schema = with_removed(valid.clone(), "", "station_schema_version");
    assert_rejected(
        "missing schema version",
        &missing_schema,
        "station_schema_version",
    );
    let missing_model = with_removed(valid.clone(), "", "station_model");
    assert_rejected("missing model", &missing_model, "station_model");
    let missing_unit = with_removed(valid.clone(), "/units", "temperature");
    assert_rejected("missing unit", &missing_unit, "units");

    let mut schema = valid.clone();
    schema["station_schema_version"] = Value::from(2);
    assert_rejected("foreign schema", &schema, "station_schema_version");
    let mut model = valid.clone();
    model["station_model"] = Value::from("interannual_fourier_v1");
    assert_rejected("foreign model", &model, "station_model");
    let mut unit = valid.clone();
    unit["units"]["temperature"] = Value::from("degree_celsius");
    assert_rejected("foreign unit", &unit, "units.temperature");

    let mut annual = valid.clone();
    annual["parameters"].as_object_mut().unwrap().insert(
        "annual_variation".to_owned(),
        Value::Object(Default::default()),
    );
    assert_rejected("annual field", &annual, "annual_variation");

    let mut shape = valid.clone();
    shape["parameters"]["storm"]["time_to_peak_cdf"]
        .as_array_mut()
        .unwrap()
        .pop();
    assert_rejected(
        "wrong monthly shape",
        &shape,
        "parameters.storm.time_to_peak_cdf",
    );

    let mut short_name = valid.clone();
    short_name["parameters"]["identity"]["station_name_raw"] = Value::from("short");
    assert_rejected(
        "short station name",
        &short_name,
        "parameters.identity.station_name_raw",
    );
    let mut non_ascii_name = valid.clone();
    non_ascii_name["parameters"]["identity"]["station_name_raw"] =
        Value::from(format!("{}é", " ".repeat(40)));
    assert_rejected(
        "non-ASCII station name",
        &non_ascii_name,
        "parameters.identity.station_name_raw",
    );

    let mut storm_type = valid.clone();
    storm_type["parameters"]["storm"]["single_storm_type"] = Value::from(0);
    assert_rejected(
        "bad storm type",
        &storm_type,
        "parameters.storm.single_storm_type",
    );

    let mut sha = valid;
    sha["lineage"]["source_sha256"] = Value::from("A".repeat(64));
    assert_rejected("bad SHA", &sha, "lineage.source_sha256");

    let source = std::fs::read_to_string(repo_root().join(FIXTURES[0])).unwrap();
    let invalid_source = source.replace("TYPE= 3", "TYPE= 0");
    let parsed = ParFile::parse(invalid_source.as_bytes()).unwrap();
    let error = StationDocumentV1::from_legacy_par(&parsed)
        .unwrap_err()
        .to_string();
    assert!(
        error.contains("parameters.storm.single_storm_type"),
        "{error}"
    );
}

#[test]
fn station_document_rejects_duplicate_nonfinite_and_overflow_numbers() {
    let (_, _, document) = converted_fixture(FIXTURES[0]);
    let canonical = document.to_json_bytes().unwrap();
    let text = std::str::from_utf8(&canonical).unwrap();
    let version_line = "  \"station_schema_version\": 1,\n";
    let duplicate = text.replacen(version_line, &format!("{version_line}{version_line}"), 1);
    assert!(
        StationDocumentV1::parse_json(duplicate.as_bytes()).is_err(),
        "duplicate object keys must fail closed"
    );

    let nonfinite = replace_location_latitude(&canonical, "NaN");
    let error = StationDocumentV1::parse_json(&nonfinite)
        .unwrap_err()
        .to_string();
    assert!(error.contains("parameters.location.latitude"), "{error}");

    let overflow = replace_location_latitude(&canonical, "1e400");
    let error = StationDocumentV1::parse_json(&overflow)
        .unwrap_err()
        .to_string();
    assert!(error.contains("parameters.location.latitude"), "{error}");
}

#[test]
fn published_station_schema_pins_the_envelope_and_array_shapes() {
    let schema: Value = serde_json::from_str(include_str!(
        "../../../docs/specifications/station-document.schema.json"
    ))
    .unwrap();
    assert_eq!(schema["properties"]["station_schema_version"]["const"], 1);
    assert_eq!(
        schema["properties"]["station_model"]["const"],
        "fixed_monthly_5_32_3"
    );
    assert_eq!(schema["additionalProperties"], false);
    assert_eq!(schema["$defs"]["monthValues"]["minItems"], 12);
    assert_eq!(schema["$defs"]["monthValues"]["maxItems"], 12);
    assert_eq!(
        schema["$defs"]["wind"]["properties"]["directions"]["minItems"],
        16
    );
    assert_eq!(
        schema["$defs"]["wind"]["properties"]["directions"]["maxItems"],
        16
    );
    assert_eq!(
        schema["$defs"]["wind"]["properties"]["interpolation_stations"]["minItems"],
        3
    );
    assert_eq!(
        schema["$defs"]["wind"]["properties"]["interpolation_stations"]["maxItems"],
        3
    );
}

#[test]
fn stations_convert_is_deterministic_and_enforces_collision_policy() {
    let root = repo_root();
    let binary = env!("CARGO_BIN_EXE_cligen");
    let directory = root.join(format!(
        "target/station-document-cli-{}",
        std::process::id()
    ));
    let _ = std::fs::remove_dir_all(&directory);
    std::fs::create_dir_all(&directory).unwrap();
    let par = root.join(FIXTURES[0]);
    let first = directory.join("first.station.json");
    let second = directory.join("second.station.json");

    let run_convert = |destination: &Path, overwrite: bool| {
        let mut command = Command::new(binary);
        command
            .env_remove("CLIGEN_DATA_DIR")
            .env_remove("XDG_CACHE_HOME")
            .env_remove("HOME")
            .env_remove("USERPROFILE");
        command.args([
            "stations",
            "convert",
            par.to_str().unwrap(),
            destination.to_str().unwrap(),
        ]);
        if overwrite {
            command.arg("--overwrite");
        }
        command.output().unwrap()
    };

    let initial = run_convert(&first, false);
    assert!(
        initial.status.success(),
        "initial conversion failed: {}",
        String::from_utf8_lossy(&initial.stderr)
    );
    let other = run_convert(&second, false);
    assert!(
        other.status.success(),
        "second conversion failed: {}",
        String::from_utf8_lossy(&other.stderr)
    );
    assert_eq!(
        std::fs::read(&first).unwrap(),
        std::fs::read(&second).unwrap()
    );

    std::fs::write(&first, b"preserve on collision").unwrap();
    let collision = run_convert(&first, false);
    assert!(
        !collision.status.success(),
        "existing output must fail closed"
    );
    assert_eq!(std::fs::read(&first).unwrap(), b"preserve on collision");

    let overwrite = run_convert(&first, true);
    assert!(
        overwrite.status.success(),
        "overwrite failed: {}",
        String::from_utf8_lossy(&overwrite.stderr)
    );
    assert_eq!(
        std::fs::read(&first).unwrap(),
        std::fs::read(&second).unwrap()
    );
    StationDocumentV1::parse_json(&std::fs::read(&first).unwrap()).unwrap();

    std::fs::remove_dir_all(directory).unwrap();
}

#[test]
fn run_error_renders_every_validated_input_boundary() {
    let par = cligen::par::ParFile::parse(b"short\n").unwrap_err();
    let station = StationDocumentV1::parse_json(b"{}").unwrap_err();
    let errors = [
        cligen::modes::RunError::Par(par),
        cligen::modes::RunError::Station(station),
        cligen::modes::RunError::Prn(cligen::observed::PrnError::NotText),
        cligen::modes::RunError::Storm(cligen::storm::StormError::Unsupported { surface: "test" }),
    ];
    for error in errors {
        assert!(!error.to_string().is_empty());
    }
}
