# A11E1 test results

Date: 2026-08-25

## Prospective source gates

- Bundled Python 3.12.13 / NumPy 2.3.5 synthetic suite: PASS, 13 tests after
  adding the zero-daily/positive-monthly range fixture.
- Strict runtime manifest validation: PASS; canonical digest
  `469cd52cb8fcee7d19e07106b8fd728d827c758e8f50e3517cd4ee0ca8063d84`.
- `cargo fmt --check`: PASS.
- `cargo clippy --all-targets -- -D warnings`: PASS.
- `cargo test`: PASS (repository-declared ignored evidence tests remain ignored).
- `git diff --check`: PASS.

These gates precede observed execution. Runtime and final review results will be
appended after the source commit is published and executed.

## Pre-output runtime finding

The first source-bound run failed before writing evidence because one candidate
day had `Tmax == Tmin`. The executor had imposed an undeclared strictly positive
daily range constraint. The corrected and tested implementation accepts a zero
daily range when the monthly mean is positive and uses 0.01 °C only inside the
daily log-texture estimator. No authoritative output preceded this correction.
