# Gate results

Evidence mode: local on `rmm`, 2026-07-19, plus read-only inspection of the
retained private A10M5O2 quarantine.

- Trigger isolation: only `slurm/dual-rank-failure.0.err` contained a raw
  reserved-looking token, PyTorch's `<NO_OTHER_FAILURES>` placeholder.
- Registered forbidden values: the same log contained the already-frozen
  durable root and identity; no other private file contained a forbidden or
  reserved-looking value.
- Exact projection regression: PASS; placeholder escaped and counted, durable
  path replaced, and no forbidden path remained.
- Adapter policy label is sourced from the projector version constant; it can
  no longer drift independently from the transformation receipt.
- Invalid UTF-8, unknown forbidden value, duplicate JSON key, NaN/Infinity,
  and sibling-prefix defenses: PASS.
- `python3 -m unittest discover -s research/a10/lemhi_toolkit/tests -v`:
  PASS, 56 tests.
- Remote shell `sh -n`: PASS.
- `artifacts/verify.py`: `A10M5O1R1_VERIFY_PASS`.
- `git diff --check`: PASS.
- `cargo fmt --check`: PASS.
- `cargo clippy --all-targets -- -D warnings`: PASS.
- `cargo test`: PASS.

Coverage/CRAP was not required because no production function under `crates/`
changed.
