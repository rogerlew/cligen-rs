//! SPEC-QUALITY-REPORT acceptance gates (Q1 Stage S):
//! post-hoc == run-emitted after nulling the run-only surfaces,
//! legacy-Fortran measurability, byte determinism, single-storm
//! group coverage, and the `output.quality` opt-out.

use std::path::{Path, PathBuf};
use std::process::Command;

use cligen::modes::{run_to_cli, RunInputs, RunOutput};
use cligen::profile::GenerationProfile;
use cligen::quality::{compute_report, QualityReport};
use cligen::runspec::load_runspec_file;
use serde_json::Value;

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .unwrap()
}

fn golden_text(case: &str) -> String {
    std::fs::read_to_string(
        repo_root()
            .join("docs/work-packages/20260709-golden-fixture-harness/artifacts/goldens")
            .join(format!("{case}.cli")),
    )
    .unwrap()
}

fn par_bytes(station: &str) -> Vec<u8> {
    std::fs::read(repo_root().join("fixtures").join(station)).unwrap()
}

const DAILY_HEADER: &str = " da mo year  prcp  dur   tp     ip  tmax  tmin  rad  w-vl w-dir  tdew\n             (mm)  (h)               (C)   (C) (l/d) (m/s)(Deg)   (C)\n";

fn synthetic_cli(rows: &str) -> String {
    format!("5.32300\nquality edge vector\n{DAILY_HEADER}{rows}")
}

fn daily_row(day: i32, month: i32, year: i32, precip: f64) -> String {
    format!(
        " {day:2} {month:2} {year:5} {precip:5.1}  1.00 0.50   2.00  10.0   1.0 200.  3.0  180.   0.0\n"
    )
}

fn new_meadows_run_output() -> RunOutput {
    let par = par_bytes("new-meadows-id/id106388.par");
    run_to_cli(&RunInputs {
        iopt: 5,
        interp: 0,
        burn: 0,
        generation_profile: GenerationProfile::Faithful5323,
        qc_filter: cligen::profile::QcFilter::Faithful,
        begin_year: Some(1),
        years: Some(31),
        par_bytes: &par,
        prn_bytes: None,
        storm: None,
        version: 5.3230,
        command_echo: "-iid106388.par",
    })
    .unwrap()
}

fn validate_schema(value: &Value, schema: &Value, root: &Value, path: &str) -> Result<(), String> {
    if let Some(reference) = schema.get("$ref").and_then(Value::as_str) {
        let target = reference
            .strip_prefix("#/$defs/")
            .and_then(|name| root["$defs"].get(name))
            .ok_or_else(|| format!("{path}: unresolved ref {reference}"))?;
        return validate_schema(value, target, root, path);
    }
    if let Some(alternatives) = schema.get("anyOf").and_then(Value::as_array) {
        if alternatives
            .iter()
            .any(|candidate| validate_schema(value, candidate, root, path).is_ok())
        {
            return Ok(());
        }
        return Err(format!("{path}: no anyOf branch matched {value}"));
    }
    if let Some(expected) = schema.get("const") {
        if value != expected {
            return Err(format!("{path}: expected const {expected}, found {value}"));
        }
    }
    if let Some(values) = schema.get("enum").and_then(Value::as_array) {
        if !values.contains(value) {
            return Err(format!("{path}: value {value} not in enum"));
        }
    }
    if let Some(types) = schema.get("type") {
        let matches = match types {
            Value::String(kind) => value_has_type(value, kind),
            Value::Array(kinds) => kinds
                .iter()
                .filter_map(Value::as_str)
                .any(|kind| value_has_type(value, kind)),
            _ => false,
        };
        if !matches {
            return Err(format!("{path}: {value} does not match type {types}"));
        }
    }
    if let Some(properties) = schema.get("properties").and_then(Value::as_object) {
        let object = value
            .as_object()
            .ok_or_else(|| format!("{path}: expected object"))?;
        if let Some(required) = schema.get("required").and_then(Value::as_array) {
            for key in required.iter().filter_map(Value::as_str) {
                if !object.contains_key(key) {
                    return Err(format!("{path}: missing required key {key}"));
                }
            }
        }
        if schema.get("additionalProperties") == Some(&Value::Bool(false)) {
            for key in object.keys() {
                if !properties.contains_key(key) {
                    return Err(format!("{path}: unexpected key {key}"));
                }
            }
        }
        for (key, child) in object {
            if let Some(child_schema) = properties.get(key) {
                validate_schema(child, child_schema, root, &format!("{path}.{key}"))?;
            }
        }
    }
    if let Some(items) = schema.get("items") {
        let array = value
            .as_array()
            .ok_or_else(|| format!("{path}: expected array"))?;
        let min = schema.get("minItems").and_then(Value::as_u64).unwrap_or(0) as usize;
        let max = schema
            .get("maxItems")
            .and_then(Value::as_u64)
            .unwrap_or(u64::MAX) as usize;
        if !(min..=max).contains(&array.len()) {
            return Err(format!(
                "{path}: array length {} outside {min}..={max}",
                array.len()
            ));
        }
        for (index, child) in array.iter().enumerate() {
            validate_schema(child, items, root, &format!("{path}[{index}]"))?;
        }
    }
    Ok(())
}

fn value_has_type(value: &Value, kind: &str) -> bool {
    match kind {
        "null" => value.is_null(),
        "boolean" => value.is_boolean(),
        "integer" => value.as_i64().is_some() || value.as_u64().is_some(),
        "number" => value.is_number(),
        "string" => value.is_string(),
        "array" => value.is_array(),
        "object" => value.is_object(),
        _ => false,
    }
}

/// (golden case, station .par) spanning continuous, observed
/// (sentinel-padded and hard-EOF truncated), and single-storm modes.
const MODE_SPAN: [(&str, &str); 5] = [
    ("new-meadows-id-seed0", "new-meadows-id/id106388.par"),
    ("jeogla-au-seed17", "jeogla-au/ASN00057011.par"),
    ("mt-wilson-ca-observed-seed0", "mt-wilson-ca/ca046006.par"),
    (
        "fish-springs-ut-observed-truncated-seed17",
        "fish-springs-ut/ut422852.par",
    ),
    (
        "new-meadows-id-single-storm-seed0",
        "new-meadows-id/id106388.par",
    ),
];

#[test]
fn post_hoc_equals_run_emitted_after_nulling_run_only_surfaces() {
    let root = repo_root();
    for (case, station) in MODE_SPAN {
        let runspec = root
            .join("crates/cligen/tests/fixtures/runspec")
            .join(case)
            .join("inp.yaml");
        let run = load_runspec_file(&runspec).unwrap();
        let cli_text = run.generate().unwrap();
        assert_eq!(cli_text, golden_text(case), "{case}: parity precondition");
        let par = par_bytes(station);

        let mut run_emitted =
            compute_report(&cli_text, &par, Some(run.quality_provenance()), None).unwrap();
        assert!(
            run_emitted.identity.provenance.is_some(),
            "{case}: run-emitted provenance"
        );
        run_emitted.null_run_only_surfaces();

        let post_hoc = compute_report(&cli_text, &par, None, None).unwrap();
        assert_eq!(
            run_emitted.to_json_bytes().unwrap(),
            post_hoc.to_json_bytes().unwrap(),
            "{case}: byte equality after nulling group P, identity.provenance, \
             and par_convergence.observed_passthrough"
        );
    }
}

#[test]
fn observed_mode_sets_observed_passthrough() {
    let root = repo_root();
    let runspec =
        root.join("crates/cligen/tests/fixtures/runspec/mt-wilson-ca-observed-seed0/inp.yaml");
    let run = load_runspec_file(&runspec).unwrap();
    let report = compute_report(
        &golden_text("mt-wilson-ca-observed-seed0"),
        &par_bytes("mt-wilson-ca/ca046006.par"),
        Some(run.quality_provenance()),
        None,
    )
    .unwrap();
    let group_a = report.par_convergence.unwrap();
    assert_eq!(group_a.observed_passthrough, Some(true));
    let provenance = report.identity.provenance.unwrap();
    assert_eq!(provenance.mode, "observed");
    assert_eq!(provenance.interpolation, "fourier");
}

#[test]
fn single_storm_reports_carry_tails_and_identity_only() {
    let report = compute_report(
        &golden_text("new-meadows-id-single-storm-seed0"),
        &par_bytes("new-meadows-id/id106388.par"),
        None,
        None,
    )
    .unwrap();
    assert_eq!(report.identity.content.days, 1);
    assert_eq!(report.identity.content.years, 1);
    assert_eq!(report.identity.content.span, [12, 12]);
    assert!(report.par_convergence.is_none());
    assert!(report.interannual.is_none());
    assert!(report.covariation.is_none());
    assert!(report.process.is_none());
    assert_eq!(report.tails.per_year.len(), 1);
    assert_eq!(report.tails.top_events.len(), 1);
    let event = &report.tails.top_events[0];
    assert_eq!((event.year, event.month, event.day), (12, 6, 15));
}

#[test]
fn legacy_fortran_production_cli_measures_cleanly() {
    // The vendored stochastic production wepp.cli files are RAW
    // legacy-Fortran output (fixture-manifest.md §Cross-reference
    // interpretation) — the legacy-measurability exemplars.
    for (station, par, daily_records) in [
        ("new-meadows-id", "new-meadows-id/id106388.par", 11322u64),
        ("jeogla-au", "jeogla-au/ASN00057011.par", 15340u64),
    ] {
        let cli_text =
            std::fs::read_to_string(repo_root().join("fixtures").join(station).join("wepp.cli"))
                .unwrap();
        let report = compute_report(&cli_text, &par_bytes(par), None, None).unwrap();
        assert_eq!(report.identity.content.days, daily_records, "{station}");
        assert!(report.identity.provenance.is_none());
        assert!(report.par_convergence.is_some(), "{station}");
        assert!(report.interannual.is_some(), "{station}");
        assert!(report.covariation.is_some(), "{station}");
        assert!(report.process.is_none());
        // Well-formed end-to-end: serializes and round-trips.
        let bytes = report.to_json_bytes().unwrap();
        let round_trip: QualityReport = serde_json::from_slice(&bytes).unwrap();
        assert_eq!(round_trip, report, "{station}");
    }
}

#[test]
fn report_computation_and_serialization_are_deterministic() {
    let cli_text = golden_text("new-meadows-id-seed0");
    let par = par_bytes("new-meadows-id/id106388.par");
    let first = compute_report(&cli_text, &par, None, None).unwrap();
    let second = compute_report(&cli_text, &par, None, None).unwrap();
    assert_eq!(first, second);
    assert_eq!(
        first.to_json_bytes().unwrap(),
        second.to_json_bytes().unwrap()
    );
}

#[test]
fn malformed_and_zero_row_tables_fail_closed_at_report_boundary() {
    let par = par_bytes("new-meadows-id/id106388.par");
    let first = daily_row(1, 1, 1, 1.0);
    let cases = [
        (
            synthetic_cli(&(first.clone() + "  2  1  1  0.0  0.0\n")),
            "expected 13 fields, found 5",
        ),
        (
            synthetic_cli(
                &(first.clone() + "  2  1  1  nope  1.00 0.50 2.00 10.0 1.0 200. 3.0 180. 0.0\n"),
            ),
            "invalid numeric field",
        ),
        (
            synthetic_cli(&(first.clone() + &daily_row(1, 1, 1, 2.0))),
            "is not after the preceding row",
        ),
        (synthetic_cli(""), "no daily rows parsed"),
    ];
    for (cli, expected) in cases {
        let error = compute_report(&cli, &par, None, None).unwrap_err();
        assert!(
            error.to_string().contains(expected),
            "{error} vs {expected}"
        );
    }
}

#[test]
fn skew_null_and_partial_decades_land_in_the_pinned_cells() {
    let par = par_bytes("new-meadows-id/id106388.par");
    let two_wet_days = synthetic_cli(&(daily_row(1, 1, 1, 1.0) + &daily_row(2, 1, 1, 2.0)));
    let report = compute_report(&two_wet_days, &par, None, None).unwrap();
    let january = &report
        .par_convergence
        .as_ref()
        .unwrap()
        .precip_wet_skew
        .months
        .jan;
    assert_eq!(january.n, 2);
    assert_eq!(january.generated, None);
    assert_eq!(january.abs_err, None);
    assert_eq!(january.rel_err, None);

    let rows = (1..=12)
        .map(|year| daily_row(1, 1, year, year as f64))
        .collect::<String>();
    let report = compute_report(&synthetic_cli(&rows), &par, None, None).unwrap();
    let group_a = report.par_convergence.as_ref().unwrap();
    let group_b = report.interannual.as_ref().unwrap();
    let group_c = report.covariation.as_ref().unwrap();
    assert_eq!(
        group_a
            .precip_wet_mean_mm
            .by_decade
            .iter()
            .map(|block| block.n_years)
            .collect::<Vec<_>>(),
        vec![10, 2]
    );
    assert_eq!(
        group_b
            .by_decade
            .iter()
            .map(|block| block.n_years)
            .collect::<Vec<_>>(),
        vec![10, 2]
    );
    assert_eq!(
        group_c
            .by_decade
            .iter()
            .map(|block| block.n_years)
            .collect::<Vec<_>>(),
        vec![10, 2]
    );
}

#[test]
fn truncated_observed_tail_exposes_partial_year_day_count() {
    let report = compute_report(
        &golden_text("fish-springs-ut-observed-truncated-seed17"),
        &par_bytes("fish-springs-ut/ut422852.par"),
        None,
        None,
    )
    .unwrap();
    let trailing = report.tails.per_year.last().unwrap();
    assert_eq!((trailing.year, trailing.n_days), (2026, 188));
}

#[test]
fn published_schema_structurally_validates_post_hoc_and_run_reports() {
    let root = repo_root();
    let schema: Value = serde_json::from_slice(
        &std::fs::read(root.join("docs/specifications/quality-report.schema.json")).unwrap(),
    )
    .unwrap();
    let post_hoc = compute_report(
        &golden_text("new-meadows-id-single-storm-seed0"),
        &par_bytes("new-meadows-id/id106388.par"),
        None,
        None,
    )
    .unwrap();
    validate_schema(
        &serde_json::to_value(post_hoc).unwrap(),
        &schema,
        &schema,
        "$",
    )
    .unwrap();

    let generated = new_meadows_run_output();
    let provenance = load_runspec_file(
        &root.join("crates/cligen/tests/fixtures/runspec/new-meadows-id-seed0/inp.yaml"),
    )
    .unwrap()
    .quality_provenance();
    let run_report = serde_json::to_value(
        compute_report(
            &generated.cli,
            &par_bytes("new-meadows-id/id106388.par"),
            Some(provenance),
            Some(generated.process),
        )
        .unwrap(),
    )
    .unwrap();
    validate_schema(&run_report, &schema, &schema, "$run").unwrap();
}

fn write_optout_runspec(dir: &Path, quality_line: &str, output_name: &str) -> PathBuf {
    let root = repo_root();
    let document = format!(
        "cligen_runspec: 1\n\
         station:\n  par: {par}\n\
         mode: continuous\n\
         simulation:\n  begin_year: 1\n  years: 2\n\
         output:\n  cli: {cli}\n  overwrite: true\n{quality_line}",
        par = root.join("fixtures/new-meadows-id/id106388.par").display(),
        cli = dir.join(output_name).display(),
    );
    let path = dir.join(format!("{output_name}.inp.yaml"));
    std::fs::write(&path, document).unwrap();
    path
}

#[test]
fn cligen_run_emits_sidecar_by_default_and_output_quality_false_opts_out() {
    let binary = env!("CARGO_BIN_EXE_cligen");
    let dir = repo_root().join("target/quality-optout");
    std::fs::create_dir_all(&dir).unwrap();

    let default_spec = write_optout_runspec(&dir, "", "default.cli");
    let status = Command::new(binary)
        .args(["run", default_spec.to_str().unwrap()])
        .status()
        .unwrap();
    assert!(status.success());
    assert!(dir.join("default.cli").exists());
    assert!(
        dir.join("default.cli.quality.json").exists(),
        "sidecar emitted by default"
    );
    let report: QualityReport =
        serde_json::from_slice(&std::fs::read(dir.join("default.cli.quality.json")).unwrap())
            .unwrap();
    assert_eq!(
        report.process.unwrap().qc_filter.as_deref(),
        Some("faithful")
    );

    let optout_spec = write_optout_runspec(&dir, "  quality: false\n", "optout.cli");
    let _ = std::fs::remove_file(dir.join("optout.cli.quality.json"));
    let status = Command::new(binary)
        .args(["run", optout_spec.to_str().unwrap()])
        .status()
        .unwrap();
    assert!(status.success());
    assert!(dir.join("optout.cli").exists());
    assert!(
        !dir.join("optout.cli.quality.json").exists(),
        "output.quality: false suppresses the sidecar"
    );
}

#[test]
fn repeated_runs_emit_byte_identical_sidecars() {
    let binary = env!("CARGO_BIN_EXE_cligen");
    let dir = repo_root().join("target/quality-determinism");
    std::fs::create_dir_all(&dir).unwrap();
    let spec = write_optout_runspec(&dir, "", "repeat.cli");
    let sidecar = dir.join("repeat.cli.quality.json");
    let mut renderings = Vec::new();
    for _ in 0..2 {
        let status = Command::new(binary)
            .args(["run", spec.to_str().unwrap()])
            .status()
            .unwrap();
        assert!(status.success());
        renderings.push(std::fs::read(&sidecar).unwrap());
    }
    assert_eq!(renderings[0], renderings[1]);
}

#[test]
fn faithful_run_emits_ordered_process_metrics_without_missing_draw_sites() {
    let generated = new_meadows_run_output();
    assert_eq!(generated.cli, golden_text("new-meadows-id-seed0"));
    let process = generated.process;
    assert_eq!(process.qc_filter.as_deref(), Some("faithful"));
    assert_eq!(
        process
            .retries
            .iter()
            .map(|entry| entry.parameter)
            .collect::<Vec<_>>(),
        (1..=9).collect::<Vec<_>>()
    );
    assert_eq!(process.acceptance_statistics.len(), 3_348);
    assert_eq!(
        process
            .cap_give_ups
            .iter()
            .map(|event| (event.parameter, event.month, event.year))
            .collect::<Vec<_>>(),
        vec![
            (9, 6, 17),
            (9, 6, 18),
            (9, 7, 23),
            (5, 9, 25),
            (5, 9, 26),
            (9, 9, 26),
            (5, 9, 27),
        ]
    );
    assert_eq!(process.v7_recovery_count, 0);
    assert_eq!(process.tdew_rangecheck_count, 7);
    assert_eq!(
        process.randn_draws,
        [12_970, 17_739, 17_602, 17_489, 124_405, 11_779, 50_101, 12_432, 17_507, 263_759,]
    );
    assert!(
        process
            .retries
            .iter()
            .flat_map(|entry| {
                serde_json::to_value(&entry.rejected_attempts)
                    .unwrap()
                    .as_object()
                    .unwrap()
                    .values()
                    .map(serde_json::Value::as_u64)
                    .collect::<Vec<_>>()
            })
            .flatten()
            .sum::<u64>()
            > 0
    );
}

#[test]
fn fast_batch_process_carries_null_qc_filter_and_no_faithful_verdicts() {
    let binary = env!("CARGO_BIN_EXE_cligen");
    let root = repo_root();
    let dir = root.join("target/quality-fast-process");
    std::fs::create_dir_all(&dir).unwrap();
    let document = format!(
        "cligen_runspec: 1\n\
         generation_profile: fast_batch_v0\n\
         station:\n  par: {}\n\
         mode: continuous\n\
         simulation:\n  begin_year: 1\n  years: 2\n\
         output:\n  cli: {}\n  overwrite: true\n",
        root.join("fixtures/new-meadows-id/id106388.par").display(),
        dir.join("fast.cli").display(),
    );
    let spec = dir.join("fast.inp.yaml");
    std::fs::write(&spec, document).unwrap();
    let status = Command::new(binary)
        .args(["run", spec.to_str().unwrap()])
        .status()
        .unwrap();
    assert!(status.success());
    let report: QualityReport =
        serde_json::from_slice(&std::fs::read(dir.join("fast.cli.quality.json")).unwrap()).unwrap();
    let process = report.process.unwrap();
    assert_eq!(process.qc_filter, None);
    assert!(process.acceptance_statistics.is_empty());
    assert!(process.cap_give_ups.is_empty());
    assert!(process.randn_draws.iter().any(|draws| *draws > 0));
}

#[test]
fn cligen_quality_stdout_matches_run_emitted_sidecar_after_nulling() {
    let binary = env!("CARGO_BIN_EXE_cligen");
    let root = repo_root();
    let dir = root.join("target/quality-posthoc");
    std::fs::create_dir_all(&dir).unwrap();
    let spec = write_optout_runspec(&dir, "", "posthoc.cli");
    let status = Command::new(binary)
        .args(["run", spec.to_str().unwrap()])
        .status()
        .unwrap();
    assert!(status.success());

    let sidecar_bytes = std::fs::read(dir.join("posthoc.cli.quality.json")).unwrap();
    let mut run_emitted: QualityReport = serde_json::from_slice(&sidecar_bytes).unwrap();
    run_emitted.null_run_only_surfaces();

    let output = Command::new(binary)
        .args([
            "quality",
            dir.join("posthoc.cli").to_str().unwrap(),
            "--par",
            root.join("fixtures/new-meadows-id/id106388.par")
                .to_str()
                .unwrap(),
        ])
        .output()
        .unwrap();
    assert!(output.status.success());
    assert_eq!(run_emitted.to_json_bytes().unwrap(), output.stdout);
}
