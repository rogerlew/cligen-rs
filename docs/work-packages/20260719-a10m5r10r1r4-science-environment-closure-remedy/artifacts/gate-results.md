# Gate results

- Published source on `main`: PASS,
  `decbe1ababddaf54a3c0cbd88b6f5b1cdb847937`.
- Independent scaffold review: ACCEPT, no findings.
- Package tests: PASS, 27 tests.
- Toolkit tests: PASS, 79 tests.
- Science identity, freeze, real corpus-layout, shell-syntax, JSON, and
  whitespace verifiers: PASS.
- Full 1,440-object calendar replay: PASS and byte-identical, SHA-256
  `7f58a20eae635d9453ea86a473072b9e2597195ffc1d71660184d3e70b130a68`.
- Authority and plan initialization: PASS, `0b9bc396…` / `cdce8b81…`.
- Control materialization: PASS, job `1014057`, all six controls exact.
- Parent science-environment closure: PASS in control and all ten candidate
  jobs.
- Candidate matrix: PASS, ten roles, 30 seed rows, all registered execution
  gates true.
- Frozen selector self-test and decision: PASS,
  `A10M5R10-PORTFOLIO-READY`.
- Selector repeatability: PASS, all four result files byte-identical on the
  second raw-evidence replay.
- Confirmation firewall: PASS, no protected role opened.
- Authenticated collection: PASS, 153 present / zero absent, archive SHA-256
  `aa83f2d…`.
- Resource accounting: PASS, 396 actual GPU-minutes under the 935-minute
  ceiling; no retry or recovery execution.
- Job-local and exact durable-root cleanup, recovery release, and toolkit
  closure: PASS.
- Final independent execution review: ACCEPT, no findings.
- Result verifier: PASS, `A10M5R10R1R4-PORTFOLIO-RESULT-VERIFIED`.
- Repository gates: PASS (`cargo fmt --check`, `cargo clippy --all-targets --
  -D warnings`, and `cargo test`).

Coverage/CRAP was not required because no production function under `crates/`
changed.
