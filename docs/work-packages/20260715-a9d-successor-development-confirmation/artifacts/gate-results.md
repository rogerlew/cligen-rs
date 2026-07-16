# A9d gate results

Date: 2026-07-15
Terminal: `HOLD-A9D-NO-SELECTABLE-CANDIDATE`

## Package and report

- `python3 -m research.a9d.campaign verify-development` — PASS: 18 fits, 24
  staged evaluations, 92 retained/19 excluded former-mandatory cells per
  horizon, named terminal.
- `python3 -m unittest discover -s research/a9d/tests -v` — PASS: 4/4.
- `python3 -m py_compile research/a9d/campaign.py research/a9d/tests/test_campaign.py`
  — PASS.
- `python3 docs/reports/verify-report.py --internal-review ...` — PASS before
  acceptance.
- `python3 docs/reports/verify-report.py ...` — PASS after acceptance.
- `python3 docs/reports/verify-report.py --self-test` — PASS.
- Three read-only report lenses — ACCEPT for accuracy, scientific validity,
  and consistency/public safety; zero open P1/P2/P3 findings after disposition.

## Repository

- `git diff --check` — PASS.
- `cargo fmt --check` — PASS.
- `cargo clippy --all-targets -- -D warnings` — PASS.
- `cargo test` — PASS; all executed tests passed, with only the repository's
  explicitly ignored evidence/data-dependent tests skipped.
- Coverage/CRAP — not triggered: no production function under `crates/`
  changed.

## Evidence and LFS

- 22/22 predecessor manifest paths, byte counts, and SHA-256 identities —
  PASS by independent extraction and package verification.
- 18/18 compact fit/detail identity pairs — PASS.
- 160/160 faithful comparator run identities and engineering checks — PASS.
- 1,040/1,040 candidate engineering attempt identities — PASS.
- 18/18 fit-detail files match the A9d Git LFS attribute and are staged as
  version-1 LFS pointers — PASS.
- `git lfs fsck --pointers` — PASS: local objects and pointers valid.
- Confirmation target-series artifacts — correctly absent; access flag false.

The recorded strict context-support gate is intentionally bounded to 720
short-screen 30-year prefixes. Its zero violations do not extend H2 to all
later-stage streams; the accepted report records H2 as partially supported.
