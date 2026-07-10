use std::path::{Path, PathBuf};
use std::process::Command;

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .unwrap()
}

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

#[test]
fn cligen_binary_runs_all_golden_runspecs_byte_identically() {
    let root = repo_root();
    let binary = env!("CARGO_BIN_EXE_cligen");
    let output_dir = root.join("target/runspec-goldens");
    std::fs::create_dir_all(&output_dir).unwrap();
    for case in GOLDENS {
        let inp = root
            .join("crates/cligen/tests/fixtures/runspec")
            .join(case)
            .join("inp.yaml");
        let output = output_dir.join(format!("{case}.cli"));
        let _ = std::fs::remove_file(&output);
        let validation = Command::new(binary)
            .args(["validate", inp.to_str().unwrap()])
            .output()
            .unwrap();
        assert!(
            validation.status.success(),
            "{case}: validate failed: {}",
            String::from_utf8_lossy(&validation.stderr)
        );
        assert!(
            !output.exists(),
            "{case}: validate must not create or stat the output"
        );
        let run = Command::new(binary)
            .args(["run", inp.to_str().unwrap()])
            .output()
            .unwrap();
        assert!(
            run.status.success(),
            "{case}: run failed: {}",
            String::from_utf8_lossy(&run.stderr)
        );
        let golden = std::fs::read(
            root.join("docs/work-packages/20260709-golden-fixture-harness/artifacts/goldens")
                .join(format!("{case}.cli")),
        )
        .unwrap();
        assert_eq!(std::fs::read(&output).unwrap(), golden, "{case}");
        std::fs::remove_file(output).unwrap();
    }
}
