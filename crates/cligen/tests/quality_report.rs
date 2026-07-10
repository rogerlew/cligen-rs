//! SPEC-QUALITY-REPORT acceptance gates (Q1 Stage S):
//! post-hoc == run-emitted after nulling the run-only surfaces,
//! legacy-Fortran measurability, byte determinism, single-storm
//! group coverage, and the `output.quality` opt-out.

use std::path::{Path, PathBuf};
use std::process::Command;

use cligen::quality::{compute_report, QualityReport};
use cligen::runspec::load_runspec_file;

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
            compute_report(&cli_text, &par, Some(run.quality_provenance())).unwrap();
        assert!(
            run_emitted.identity.provenance.is_some(),
            "{case}: run-emitted provenance"
        );
        run_emitted.null_run_only_surfaces();

        let post_hoc = compute_report(&cli_text, &par, None).unwrap();
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
        let report = compute_report(&cli_text, &par_bytes(par), None).unwrap();
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
    let first = compute_report(&cli_text, &par, None).unwrap();
    let second = compute_report(&cli_text, &par, None).unwrap();
    assert_eq!(first, second);
    assert_eq!(
        first.to_json_bytes().unwrap(),
        second.to_json_bytes().unwrap()
    );
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
