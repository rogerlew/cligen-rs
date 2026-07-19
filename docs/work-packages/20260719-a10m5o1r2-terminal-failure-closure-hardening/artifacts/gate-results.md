# Gate results

Evidence mode: local fixtures on `rmm`, 2026-07-19; no allocation.

- Positive terminal-stop lifecycle, sparse collect, exact cleanup, close, and
  recovery-reserve release: PASS.
- Stop rejection for unexhausted, unsettled, retry-eligible, tampered,
  unreconciled, and concurrent-submission cases: PASS.
- Sparse archive partition, regular-file equality, missing/mutated attempt and
  recovery evidence, symlink, hardlink, FIFO, parent-path, and temp-root
  defenses: PASS.
- Global planned/recovery gate-versus-stream collision and duplicate stream
  ownership checks, including amendments: PASS.
- Idempotent matrix-stop receipt republication without remote dependencies:
  PASS.
- `python3 -m unittest research.a10.lemhi_toolkit.tests.test_hardening
  research.a10.lemhi_toolkit.tests.test_toolkit`: PASS, 79 tests.
- `sh -n research/a10/lemhi_toolkit/remote/pack_evidence.sh`: PASS.
- `git diff --check`: PASS.
- `cargo fmt --check`: PASS.
- `cargo clippy --all-targets -- -D warnings`: PASS.
- `cargo test`: PASS.

Coverage/CRAP was not required because no production function under `crates/`
changed.
