# Gate results

- Published source on `main`: PASS, `c63ab18c3bc883e302104a0c77aa1d33085ae2c0`.
- Independent scaffold review: ACCEPT after both findings were corrected.
- Package tests: PASS, 20 tests.
- Toolkit tests: PASS, 79 tests.
- Science identity and portable-bootstrap freeze verifiers: PASS.
- Full 1,440-object calendar replay: PASS and byte-identical, SHA-256
  `7f58a20eae635d9453ea86a473072b9e2597195ffc1d71660184d3e70b130a68`.
- Asset preparation, staging, and exact remote verification: PASS.
- Authority/plan initialization: PASS, `f08dd107…` / `a0fa878e…`.
- Control admission: PASS, 16/16 gates.
- Portable compute bootstrap and ready setup: PASS.
- Control materialization: HOLD; the archive was nested one level below the
  corpus root supplied to the frozen control program.
- Candidate admission/submission/science: NOT RUN; all ten roles were stopped
  as `NOT_EXECUTED_UPSTREAM_FAILURE`.
- Authenticated sparse collection: PASS, 13 present / 140 absent.
- Job-local and exact remote cleanup: PASS.
- Recovery reserve release and toolkit closure: PASS.
- Final independent execution review: ACCEPT, no findings.
- `git diff --check`, `cargo fmt --check`,
  `cargo clippy --all-targets -- -D warnings`, and `cargo test`: PASS after
  record reconciliation.

Coverage/CRAP was not required because no production function under `crates/`
changed.
