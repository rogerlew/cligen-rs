//! `qc_filter` acceptance (Q3, SPEC-GENERATION-PROFILES §qc_filter /
//! SPEC-RUNSPEC rev 5): the faithful default is byte-identical to the
//! pre-knob surface, `off` diverges exactly where conditioning acted,
//! declares itself in the header and provenance, and prices itself in
//! `process.counterfactual`.

use std::path::{Path, PathBuf};

use cligen::modes::{run_to_cli, RunInputs};
use cligen::profile::{GenerationProfile, QcFilter};
use cligen::runspec::RunspecDocument;

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .unwrap()
}

fn new_meadows_inputs<'a>(par: &'a [u8], echo: &'a str, qc: QcFilter) -> RunInputs<'a> {
    RunInputs {
        iopt: 5,
        interp: 0,
        burn: 0,
        generation_profile: GenerationProfile::Faithful5323,
        qc_filter: qc,
        begin_year: Some(1),
        years: Some(31),
        par_bytes: par,
        prn_bytes: None,
        storm: None,
        version: 5.3230,
        command_echo: echo,
    }
}

fn new_meadows_par() -> Vec<u8> {
    std::fs::read(repo_root().join("fixtures/new-meadows-id/id106388.par")).unwrap()
}

#[test]
fn explicit_faithful_qc_is_byte_identical_to_the_golden() {
    let par = new_meadows_par();
    let echo = QcFilter::Faithful.command_echo("-iid106388.par".to_owned());
    let output = run_to_cli(&new_meadows_inputs(&par, &echo, QcFilter::Faithful)).unwrap();
    let golden = std::fs::read_to_string(repo_root().join(
        "docs/work-packages/20260709-golden-fixture-harness/artifacts/goldens/new-meadows-id-seed0.cli",
    ))
    .unwrap();
    assert_eq!(output.cli, golden);
    assert!(output.process.counterfactual.is_none());
    assert!(!output.process.acceptance_statistics.is_empty());
}

#[test]
fn qc_off_diverges_declares_itself_and_prices_the_removed_conditioning() {
    let par = new_meadows_par();
    let faithful_echo = "-iid106388.par".to_owned();
    let off_echo = "-iid106388.par".to_owned();
    let faithful = run_to_cli(&new_meadows_inputs(
        &par,
        &faithful_echo,
        QcFilter::Faithful,
    ))
    .unwrap();
    let off_a = run_to_cli(&new_meadows_inputs(&par, &off_echo, QcFilter::Off)).unwrap();
    let off_b = run_to_cli(&new_meadows_inputs(&par, &off_echo, QcFilter::Off)).unwrap();

    // Deterministic, and divergent from faithful exactly because this
    // station's faithful run rejected batches (retries + cap hits).
    assert_eq!(off_a.cli, off_b.cli);
    assert_ne!(off_a.cli, faithful.cli);
    // The mandatory non-faithful header marker.
    assert!(off_a.cli.contains("-iid106388.par --qc-filter off"));
    assert!(!faithful.cli.contains("--qc-filter"));

    // Counterfactual pricing: 31 years × 12 refills × 9 parameters.
    let counterfactual = off_a.process.counterfactual.as_ref().unwrap();
    assert_eq!(counterfactual.batches, 31 * 12 * 9);
    assert!(
        counterfactual.would_reject > 0,
        "faithful rejected batches on this station; the counterfactual must see some"
    );
    assert!(counterfactual.would_reject < counterfactual.batches);
    // Under off there are no retries and no cap give-ups.
    assert!(off_a.process.cap_give_ups.is_empty());
    assert!(off_a
        .process
        .retries
        .iter()
        .all(|parameter| (0..12).all(|month| {
            let months = &parameter.rejected_attempts;
            [
                months.jan, months.feb, months.mar, months.apr, months.may, months.jun, months.jul,
                months.aug, months.sep, months.oct, months.nov, months.dec,
            ][month]
                == 0
        })));

    // Report provenance carries the knob; the sidecar surface accepts
    // the process block.
    let provenance_document = String::from(
        "cligen_runspec: 1\n\
         station: { par: fixtures/new-meadows-id/id106388.par }\n\
         mode: continuous\n\
         simulation: { begin_year: 1, years: 31 }\n\
         qc_filter: off\n\
         output: { cli: wepp.cli }\n",
    );
    let prepared = RunspecDocument::parse(&provenance_document)
        .unwrap()
        .resolve(&repo_root())
        .unwrap();
    let report = prepared.generate_quality_report().unwrap();
    assert_eq!(report.metrics_version, 3);
    let process = report.process.unwrap();
    assert_eq!(process.qc_filter.as_deref(), Some("off"));
    assert!(process.counterfactual.is_some());
}

#[test]
fn direct_run_api_marks_profiles_and_rejects_oversized_burns() {
    let par = new_meadows_par();
    let mut fast = new_meadows_inputs(&par, "-iid106388.par", QcFilter::Faithful);
    fast.generation_profile = GenerationProfile::FastBatchV0;
    fast.years = Some(1);
    let output = run_to_cli(&fast).unwrap();
    assert!(output
        .cli
        .contains("-iid106388.par --generation-profile fast-batch-v0"));

    let mut invalid_fast = new_meadows_inputs(&par, "-iid106388.par", QcFilter::Off);
    invalid_fast.generation_profile = GenerationProfile::FastBatchV0;
    assert!(run_to_cli(&invalid_fast)
        .unwrap_err()
        .to_string()
        .contains("qc_filter"));

    let mut oversized = new_meadows_inputs(&par, "-iid106388.par", QcFilter::Faithful);
    oversized.burn = i32::MAX as u32 + 1;
    assert!(run_to_cli(&oversized)
        .unwrap_err()
        .to_string()
        .contains("burn"));
}

const RUNSPEC_TEMPLATE: &str = "cligen_runspec: 1\n\
    station: { par: fixtures/new-meadows-id/id106388.par }\n\
    mode: continuous\n\
    simulation: { begin_year: 1, years: 2 }\n\
    output: { cli: wepp.cli }\n";

#[test]
fn runspec_accepts_the_knob_and_fails_closed_on_misuse() {
    let off = format!("{RUNSPEC_TEMPLATE}qc_filter: off\n");
    let document = RunspecDocument::parse(&off).unwrap();
    document.validate().unwrap();

    let faithful = format!("{RUNSPEC_TEMPLATE}qc_filter: faithful\n");
    RunspecDocument::parse(&faithful)
        .unwrap()
        .validate()
        .unwrap();

    let unknown = format!("{RUNSPEC_TEMPLATE}qc_filter: sometimes\n");
    assert!(RunspecDocument::parse(&unknown).is_err());

    let with_v0 = format!("{RUNSPEC_TEMPLATE}generation_profile: fast_batch_v0\nqc_filter: off\n");
    let error = RunspecDocument::parse(&with_v0)
        .unwrap()
        .validate()
        .unwrap_err();
    assert!(error.to_string().contains("fast_batch_v0"), "{error}");
}
