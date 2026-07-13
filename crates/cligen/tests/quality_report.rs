//! SPEC-QUALITY-REPORT acceptance gates (Q1 Stage S):
//! post-hoc == run-emitted after nulling the run-only surfaces,
//! legacy-Fortran measurability, byte determinism, single-storm
//! group coverage, and the `output.quality` opt-out.

use std::error::Error as _;
use std::path::{Path, PathBuf};
use std::process::Command;

use cligen::modes::{run_to_cli, RunInputs, RunOutput};
use cligen::profile::GenerationProfile;
use cligen::quality::{compute_report, QualityError, QualityReport};
use cligen::runspec::load_runspec_file;
use cligen::station::StationDocumentError;
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
    new_meadows_run_output_for_years(31)
}

fn new_meadows_run_output_for_years(years: i32) -> RunOutput {
    let par = par_bytes("new-meadows-id/id106388.par");
    run_to_cli(&RunInputs {
        iopt: 5,
        interp: 0,
        burn: 0,
        generation_profile: GenerationProfile::Faithful5323,
        qc_filter: cligen::profile::QcFilter::Faithful,
        begin_year: Some(1),
        years: Some(years),
        par_bytes: &par,
        prn_bytes: None,
        storm: None,
        version: 5.3230,
        command_echo: "-iid106388.par",
    })
    .unwrap()
}

#[test]
fn quality_error_variants_retain_typed_sources() {
    let par = par_bytes("new-meadows-id/id106388.par");
    let cli = compute_report("not a .cli", &par, None, None).unwrap_err();
    assert!(matches!(cli, QualityError::Cli(_)));
    assert!(cli.source().is_some());

    let par_error = compute_report("not a .cli", b"not a .par", None, None).unwrap_err();
    assert!(matches!(par_error, QualityError::Par(_)));
    assert!(par_error.source().is_some());

    let station = QualityError::Station(StationDocumentError::Validation {
        field_path: "parameters".to_owned(),
        message: "non-finite value".to_owned(),
    });
    assert!(station.source().is_some());

    let source = serde_json::from_str::<Value>("{").unwrap_err();
    let serialize = QualityError::Serialize(source);
    assert!(serialize.source().is_some());

    let run_only = QualityError::RunOnlyInputs;
    assert!(run_only.source().is_none());
}

#[test]
fn run_only_quality_inputs_and_mutated_nested_provenance_fail_closed() {
    let root = repo_root();
    let run = load_runspec_file(
        &root.join("crates/cligen/tests/fixtures/runspec/new-meadows-id-seed0/inp.yaml"),
    )
    .unwrap();
    let provenance = run.quality_provenance().unwrap();
    let error = compute_report(
        &golden_text("new-meadows-id-seed0"),
        &par_bytes("new-meadows-id/id106388.par"),
        Some(provenance),
        None,
    )
    .unwrap_err();
    assert!(matches!(error, QualityError::RunOnlyInputs));

    let mut report = run.generate_quality_report().unwrap();
    report
        .identity
        .provenance
        .as_mut()
        .unwrap()
        .effective_runspec
        .output
        .command_echo = "mutated".to_owned();
    assert!(matches!(
        report.to_json_bytes(),
        Err(QualityError::Provenance(_))
    ));
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

        let mut run_emitted = run.generate_quality_report().unwrap();
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
    let report = run.generate_quality_report().unwrap();
    let group_a = report.par_convergence.unwrap();
    assert_eq!(group_a.observed_passthrough, Some(true));
    let provenance = report.identity.provenance.unwrap();
    assert_eq!(
        provenance.generation.mode,
        cligen::provenance::GenerationModeV1::Observed
    );
    assert_eq!(
        provenance.generation.interpolation,
        cligen::provenance::InterpolationV1::Fourier
    );
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

    // Metrics v3 requires every multirow stream to be contiguous, so use a
    // real 12-year daily run rather than the old one-row-per-year shortcut.
    let generated = new_meadows_run_output_for_years(12);
    let report = compute_report(&generated.cli, &par, None, None).unwrap();
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
fn published_combination_schema_and_public_parser_validate_both_report_kinds() {
    let root = repo_root();
    let public_quality =
        std::fs::read(root.join("docs/specifications/quality-report-s2-m3.schema.json")).unwrap();
    let runtime_quality =
        std::fs::read(root.join("crates/cligen/schemas/quality-report-s2-m3.schema.json")).unwrap();
    assert_eq!(
        runtime_quality, public_quality,
        "runtime quality schema drift"
    );
    let public_provenance =
        std::fs::read(root.join("docs/specifications/provenance-v1.schema.json")).unwrap();
    let runtime_provenance =
        std::fs::read(root.join("crates/cligen/schemas/provenance-v1.schema.json")).unwrap();
    assert_eq!(
        runtime_provenance, public_provenance,
        "runtime provenance schema drift"
    );
    let schema: Value = serde_json::from_slice(&public_quality).unwrap();
    assert_eq!(
        schema["properties"]["quality_report_schema_version"]["const"],
        2
    );
    assert_eq!(schema["properties"]["metrics_version"]["const"], 3);
    let post_hoc = compute_report(
        &golden_text("new-meadows-id-single-storm-seed0"),
        &par_bytes("new-meadows-id/id106388.par"),
        None,
        None,
    )
    .unwrap();
    assert_eq!(post_hoc.quality_report_schema_version, 2);
    assert_eq!(post_hoc.metrics_version, 3);
    let post_hoc_bytes = post_hoc.to_json_bytes().unwrap();
    assert_eq!(
        QualityReport::parse_json(&post_hoc_bytes).unwrap(),
        post_hoc
    );

    let run = load_runspec_file(
        &root.join("crates/cligen/tests/fixtures/runspec/new-meadows-id-seed0/inp.yaml"),
    )
    .unwrap();
    let run_report = run.generate_quality_report().unwrap();
    let run_bytes = run_report.to_json_bytes().unwrap();
    assert_eq!(QualityReport::parse_json(&run_bytes).unwrap(), run_report);
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
    assert!(dir.join("default.cli.provenance.json").exists());
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
    let provenance = cligen::provenance::ArtifactProvenanceV1::parse_json(
        &std::fs::read(dir.join("optout.cli.provenance.json")).unwrap(),
    )
    .unwrap();
    assert_eq!(
        provenance.artifact.output_schema,
        cligen::provenance::SchemaIdentityV1::cli_text()
    );
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
