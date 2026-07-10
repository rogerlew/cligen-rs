use std::path::{Path, PathBuf};

use cligen::profile::GenerationProfile;
use cligen::runspec::{load_runspec_file, RunspecDocument, RunspecError};

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .unwrap()
}

const CONTINUOUS: &str = r#"
cligen_runspec: 1
station: { par: fixture.par }
mode: continuous
simulation: { begin_year: 1, years: 1 }
output: { cli: wepp.cli }
"#;

const SINGLE_STORM: &str = r#"
cligen_runspec: 1
station: { par: fixture.par }
mode: single_storm
single_storm:
  date: { month: 6, day: 15, year: 12 }
  amount_in: 2.25
  duration_h: 6.0
  time_to_peak_fraction: 0.4
  max_intensity_in_per_h: 1.5
output: { cli: wepp.cli }
"#;

const DESIGN_STORM: &str = r#"
cligen_runspec: 1
station: { par: fixture.par }
mode: design_storm
design_storm:
  date: { month: 6, day: 15, year: 12 }
  amount_in: 2.25
output: { cli: wepp.cli }
"#;

fn document(yaml: &str) -> RunspecDocument {
    RunspecDocument::parse(yaml).unwrap()
}

fn assert_validation_path(yaml: &str, expected: &str) {
    let error = document(yaml).validate().unwrap_err();
    match error {
        RunspecError::Validation { field_path, .. } => assert_eq!(field_path, expected),
        other => panic!("expected validation error at {expected}, got {other}"),
    }
}

fn continuous_with(output_cli: &str, interpolation: &str) -> String {
    format!(
        "cligen_runspec: 1\nstation: {{ par: fixtures/new-meadows-id/id106388.par }}\nmode: continuous\nsimulation: {{ begin_year: 1, years: 1, interpolation: {interpolation} }}\noutput: {{ cli: {output_cli} }}\n"
    )
}

#[test]
fn schema_artifact_is_json_with_the_runspec_version_constraint() {
    let schema: serde_yaml::Value = serde_yaml::from_str(include_str!(
        "../../../docs/specifications/runspec.schema.json"
    ))
    .unwrap();
    assert_eq!(schema["properties"]["cligen_runspec"]["const"], 1);
    assert_eq!(
        schema["$defs"]["generationProfile"]["default"],
        "faithful_5_32_3"
    );
    assert_eq!(
        schema["$defs"]["stormDate"]["x-cligen-source-calendar"],
        "For a February 29 date, the Rust boundary applies wxr_gen:3758-3763 exactly: leap iff year - year/400*400 == 0 OR (year - year/4*4 == 0 AND year - year/100*100 == 0)."
    );
}

#[test]
fn runspec_rejects_every_scalar_field_invariant_with_its_path() {
    let cases = [
        (
            CONTINUOUS.replace("cligen_runspec: 1", "cligen_runspec: 2"),
            "cligen_runspec",
        ),
        (
            CONTINUOUS.replace("par: fixture.par", "par: ''"),
            "station.par",
        ),
        (CONTINUOUS.replace("cli: wepp.cli", "cli: ''"), "output.cli"),
        (
            CONTINUOUS.replace("begin_year: 1", "begin_year: 0"),
            "simulation.begin_year",
        ),
        (
            CONTINUOUS.replace("years: 1", "years: 0"),
            "simulation.years",
        ),
        (
            CONTINUOUS.replace(
                "output: { cli: wepp.cli }",
                "rng: { burn: -1 }\noutput: { cli: wepp.cli }",
            ),
            "rng.burn",
        ),
        (
            SINGLE_STORM.replace("month: 6", "month: 13"),
            "single_storm.date.month",
        ),
        (
            SINGLE_STORM.replace("month: 6, day: 15", "month: 4, day: 31"),
            "single_storm.date.day",
        ),
        (
            SINGLE_STORM.replace("amount_in: 2.25", "amount_in: 0"),
            "single_storm.amount_in",
        ),
        (
            SINGLE_STORM.replace("duration_h: 6.0", "duration_h: 0"),
            "single_storm.duration_h",
        ),
        (
            SINGLE_STORM.replace("time_to_peak_fraction: 0.4", "time_to_peak_fraction: 0"),
            "single_storm.time_to_peak_fraction",
        ),
        (
            SINGLE_STORM.replace("max_intensity_in_per_h: 1.5", "max_intensity_in_per_h: 0"),
            "single_storm.max_intensity_in_per_h",
        ),
        (
            DESIGN_STORM.replace("amount_in: 2.25", "amount_in: 0"),
            "design_storm.amount_in",
        ),
        (
            DESIGN_STORM.replace("amount_in: 2.25", "amount_in: 3.5e+39"),
            "design_storm.amount_in",
        ),
    ];
    for (yaml, path) in cases {
        assert_validation_path(&yaml, path);
    }
}

#[test]
fn runspec_uses_the_source_storm_calendar_rule_before_jdt() {
    assert_validation_path(
        &SINGLE_STORM.replace("month: 6, day: 15, year: 12", "month: 2, day: 29, year: 12"),
        "single_storm.date.day",
    );
    document(&SINGLE_STORM.replace(
        "month: 6, day: 15, year: 12",
        "month: 2, day: 29, year: 100",
    ))
    .validate()
    .unwrap();
}

#[test]
fn runspec_fails_closed_for_unknown_wrong_type_and_wrong_mode_blocks() {
    let unknown = RunspecDocument::parse(
        &CONTINUOUS.replace("mode: continuous", "mode: continuous\nextra: 1"),
    )
    .unwrap_err();
    assert!(unknown.to_string().contains("extra"));
    let wrong_type =
        RunspecDocument::parse(&CONTINUOUS.replace("begin_year: 1", "begin_year: no")).unwrap_err();
    assert!(wrong_type.to_string().contains("simulation.begin_year"));
    let wrong_overwrite =
        RunspecDocument::parse(&CONTINUOUS.replace("cli: wepp.cli", "cli: wepp.cli, overwrite: 1"))
            .unwrap_err();
    assert!(wrong_overwrite.to_string().contains("output.overwrite"));
    let unknown_profile = RunspecDocument::parse(&CONTINUOUS.replace(
        "mode: continuous",
        "generation_profile: unsupported\nmode: continuous",
    ))
    .unwrap_err();
    assert!(unknown_profile.to_string().contains("generation_profile"));
    assert_validation_path(
        &CONTINUOUS.replace(
            "output: { cli: wepp.cli }",
            "observed: { prn: fixture.prn }\noutput: { cli: wepp.cli }",
        ),
        "observed",
    );
    assert_validation_path(
        &SINGLE_STORM.replace("mode: single_storm", "mode: observed"),
        "observed",
    );
}

#[test]
fn generation_profile_defaults_to_faithful_and_marks_fast_batch_output() {
    let root = repo_root();
    let output = root.join("target/runspec-vectors/fast-profile.cli");
    let faithful_yaml = continuous_with(&output.to_string_lossy(), "none");
    let faithful = document(&faithful_yaml).resolve(&root).unwrap();
    assert_eq!(faithful.generation_profile, GenerationProfile::Faithful5323);

    let fast_yaml = faithful_yaml.replace(
        "cligen_runspec: 1\n",
        "cligen_runspec: 1\ngeneration_profile: fast_batch_v0\n",
    );
    let fast = document(&fast_yaml).resolve(&root).unwrap();
    assert_eq!(fast.generation_profile, GenerationProfile::FastBatchV0);
    let output = fast.generate().unwrap();
    assert!(output.contains("--generation-profile fast-batch-v0"));
}

#[test]
fn mode_conditional_blocks_are_required_and_observed_paths_are_nonempty() {
    let cases = [
        (
            "cligen_runspec: 1\nstation: { par: fixture.par }\nmode: continuous\noutput: { cli: wepp.cli }\n",
            "simulation",
        ),
        (
            "cligen_runspec: 1\nstation: { par: fixture.par }\nmode: observed\noutput: { cli: wepp.cli }\n",
            "observed",
        ),
        (
            "cligen_runspec: 1\nstation: { par: fixture.par }\nmode: single_storm\noutput: { cli: wepp.cli }\n",
            "single_storm",
        ),
        (
            "cligen_runspec: 1\nstation: { par: fixture.par }\nmode: design_storm\noutput: { cli: wepp.cli }\n",
            "design_storm",
        ),
        (
            "cligen_runspec: 1\nstation: { par: fixture.par }\nmode: observed\nobserved: { prn: '' }\noutput: { cli: wepp.cli }\n",
            "observed.prn",
        ),
    ];
    for (yaml, path) in cases {
        assert_validation_path(yaml, path);
    }
}

#[test]
fn fixture_unreachable_design_and_interpolation_vectors_resolve() {
    let root = repo_root();
    for interpolation in ["linear", "monthly_mean_preserving"] {
        let prepared = document(&continuous_with(
            "target/runspec-vectors/linear.cli",
            interpolation,
        ))
        .resolve(&root)
        .unwrap();
        assert_eq!(prepared.iopt, 5);
        assert_eq!(
            prepared.interpolation,
            if interpolation == "linear" { 1 } else { 3 }
        );
    }
    let design = DESIGN_STORM
        .replace("fixture.par", "fixtures/new-meadows-id/id106388.par")
        .replace("cli: wepp.cli", "cli: target/runspec-vectors/design.cli");
    let prepared = document(&design).resolve(&root).unwrap();
    assert_eq!(prepared.iopt, 7);
    assert_eq!(prepared.storm.unwrap().damt, 2.25);
    assert_eq!(prepared.storm.unwrap().usdur, 0.0);

    let observed = r#"
cligen_runspec: 1
station: { par: fixtures/mt-wilson-ca/ca046006.par }
mode: observed
simulation: { begin_year: 1991, years: 2 }
observed: { prn: fixtures/mt-wilson-ca/ws.prn }
output: { cli: target/runspec-vectors/observed.cli }
"#;
    let prepared = document(observed).resolve(&root).unwrap();
    assert_eq!(prepared.iopt, 6);
    assert_eq!(prepared.begin_year, Some(1991));
    assert_eq!(prepared.years, Some(2));
}

#[test]
fn canonical_echo_and_overwrite_policy_vectors_are_deterministic() {
    let root = repo_root();
    let canonical = r#"
cligen_runspec: 1
station: { par: fixtures/mt-wilson-ca/ca046006.par }
mode: observed
simulation: { interpolation: monthly_mean_preserving }
rng: { burn: 17 }
observed: { prn: fixtures/mt-wilson-ca/ws.prn }
output: { cli: target/runspec-vectors/alternate.cli }
"#;
    let prepared = document(canonical).resolve(&root).unwrap();
    assert_eq!(
        prepared.command_echo,
        "-r17 -ifixtures/mt-wilson-ca/ca046006.par -Ofixtures/mt-wilson-ca/ws.prn -otarget/runspec-vectors/alternate.cli -t6 -I3"
    );

    let output = root.join("target/runspec-vectors/existing.cli");
    std::fs::create_dir_all(output.parent().unwrap()).unwrap();
    std::fs::write(&output, b"preserve this file").unwrap();
    let existing = output.to_string_lossy();
    let prepared = document(&continuous_with(&existing, "none"))
        .resolve(&root)
        .unwrap();
    let error = prepared.generate_and_write().unwrap_err();
    assert!(matches!(error, RunspecError::OutputCollision { .. }));
    assert_eq!(std::fs::read(&output).unwrap(), b"preserve this file");
    let allowed = continuous_with(&existing, "none").replace(
        &format!("output: {{ cli: {existing} }}"),
        &format!("output: {{ cli: {existing}, overwrite: true }}"),
    );
    document(&allowed)
        .resolve(&root)
        .unwrap()
        .generate_and_write()
        .unwrap();
    assert_ne!(std::fs::read(&output).unwrap(), b"preserve this file");
    std::fs::remove_file(output).unwrap();
}

#[test]
fn validation_resolution_never_stats_or_creates_the_output_path() {
    let root = repo_root();
    let parent = root.join("target/runspec-vectors/no-output-stat");
    let _ = std::fs::remove_dir_all(&parent);
    let output = parent.join("wepp.cli");
    let yaml = continuous_with(&output.to_string_lossy(), "none");
    document(&yaml).resolve(&root).unwrap();
    assert!(!parent.exists());
}

#[cfg(unix)]
#[test]
fn file_loader_resolves_against_the_invoked_runspec_directory() {
    let root = repo_root();
    let base = root.join("target/runspec-vectors/symlink-base");
    let _ = std::fs::remove_dir_all(&base);
    let invoked_dir = base.join("invoked");
    let target_dir = base.join("target");
    let inputs = invoked_dir.join("inputs");
    std::fs::create_dir_all(&inputs).unwrap();
    std::fs::create_dir_all(&target_dir).unwrap();
    std::fs::copy(
        root.join("fixtures/new-meadows-id/id106388.par"),
        inputs.join("station.par"),
    )
    .unwrap();
    std::fs::write(
        target_dir.join("inp.yaml"),
        "cligen_runspec: 1\nstation: { par: inputs/station.par }\nmode: continuous\nsimulation: { begin_year: 1, years: 1 }\noutput: { cli: output/wepp.cli }\n",
    )
    .unwrap();
    std::os::unix::fs::symlink(target_dir.join("inp.yaml"), invoked_dir.join("inp.yaml")).unwrap();
    let prepared = load_runspec_file(&invoked_dir.join("inp.yaml")).unwrap();
    assert_eq!(prepared.output_path, invoked_dir.join("output/wepp.cli"));
    std::fs::remove_dir_all(base).unwrap();
}
