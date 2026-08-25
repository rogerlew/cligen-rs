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

## Observed execution and closure gates

- Published execution source: `105c29b0efa3feccd27db37914bcaa60693cd828`.
- Calendar/role preflight: PASS, 1,440 fit-corpus objects and 20 development
  objects; exact eight/four leap-year December 31 masks.
- Fit/CV: PASS, six regimes and both registered integrated strategies.
- Development generation: PASS, 40/40 unique streams and zero invariant
  failures.
- Confirmation target access: false.
- Receipt/output hash and size recomputation: PASS.
- Evidence self-hash, decision medians, and bootstrap recomputation in
  independent review: PASS.
- Deterministic replay: PASS; the five scientific output SHA-256 hashes were
  byte-identical. The execution receipt's elapsed time is operational and was
  regenerated.
- Final synthetic suite: PASS, 13 tests.
- Repository Rust gates: PASS (`cargo fmt --check`,
  `cargo clippy --all-targets -- -D warnings`, and `cargo test`).
- `git diff --check`: PASS.
- Independent evidence review: no P0; closure-record P1 reconciled.
