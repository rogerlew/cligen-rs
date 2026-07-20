# Scaffold gates

Status: `PASS`

Ran locally on 2026-07-20:

- `python3 artifacts/verify_freeze.py --science-python
  <pinned-science-python>` — PASS
- `python3 artifacts/verify_freeze.py --parent-assets
  <authenticated-r13r1-parent-assets>`
  — PASS against the exact 46-asset parent manifest
- objective-selector coverage: exactly 188 unique rows and complete A/B/C/D
  reachability
- exact 16-year Daymet leap/window boundary fixtures
- exact OU recurrence and no month/year reset tests
- matched common initialization and common random fields
- zero-output optional mechanism initialization
- fixed regularization registry identity
- four-role plan/admission/concurrency matrix
- `cargo fmt --check` — PASS
- `cargo clippy --all-targets -- -D warnings` — PASS
- `cargo test` — PASS
- `python3 -m unittest discover -s research/a10/lemhi_toolkit/tests -p
  'test_*.py'` — PASS (84/84), including acceptance of the new xlarge profile

The science verifier emitted `A10M5R14-FREEZE-VERIFY-PASS`, including the
calendar, 188-metric gradient, semantic-plan replay authentication, inherited exact OU recurrence,
factorial initialization, common random field, and fixed regularization
self-tests. No GPU job was submitted.
