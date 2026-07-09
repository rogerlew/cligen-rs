# Review: Golden Fixture Harness

Evidence mode: Static + Ran
Date: 2026-07-09

## Scope Reviewed

- Reference build provenance and flag profile.
- Fixture matrix selection, generated outputs, determinism rerun, and
  manifest.
- `SPEC-CLI-DIFF` and the Rust `.cli` differ implementation.
- Package closeout updates.

## Findings

No blocking findings.

## Residual Risks

- Interior deviate-stream taps are intentionally deferred to the
  RNG/deviates package. That package must add a recorded tap patch outside
  `reference/cligen532/` before claiming bit-identity of RNG/deviate
  internals.
- The observed production cross-reference files differ from pinned
  goldens at row 1 due to output formatting precision. They remain useful
  cross-references but are not acceptance goldens.

## Evidence Checked

- `cargo fmt --check`
- `cargo clippy --all-targets -- -D warnings`
- `cargo test`
- `cargo llvm-cov --workspace --lcov --output-path target/lcov.info`
- `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above`
- Full fixture determinism comparison by byte identity.
