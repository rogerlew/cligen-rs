# Gate results

- Fresh source commit published on `main`: PASS (`9bdee723…`).
- Successor admission tests: PASS, 7 tests.
- Operational/authority tests, including real temporary authority
  initialization: PASS, 8 tests.
- Science identity verifier: PASS, 12 dependencies.
- Successor freeze and shell syntax verifiers: PASS.
- Full 1,440-object calendar replay: PASS and byte-identical; SHA-256
  `7f58a20e…`.
- Asset preparation, staging, and exact remote verification: PASS.
- Login `/usr/bin/python3.11`: PASS, Python 3.11.13, exact binary identity
  recorded.
- Control admission: PASS, 16/16 gates.
- Control execution: HOLD; job `1014053` failed in one second because compute
  node03 has no `/usr/bin/python3.11`.
- Candidate admission/submission/science: NOT RUN.
- Job-local cleanup: PASS through the supervisor.
- Toolkit observe/matrix-stop/collect/close: HOLD because no registered control
  gate receipt could be authored without the missing interpreter.
- Exact durable-root cleanup: PASS; independently absent.
- Toolkit tests: PASS, 79 tests.
- `git diff --check`, `cargo fmt --check`,
  `cargo clippy --all-targets -- -D warnings`, and `cargo test`: PASS on the
  executed source; rerun after final record reconciliation.

Coverage/CRAP was not required because no production function under `crates/`
changed.
