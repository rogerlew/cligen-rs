# Gate Results

Date: 2026-07-12
Evidence mode: Ran + Static

## Repository gates

Run from `/Users/roger/src/cligen-rs` after the specification review findings
were dispositioned:

| Command | Result |
|---|---|
| `cargo fmt --check` | PASS, exit 0 |
| `cargo clippy --all-targets -- -D warnings` | PASS, exit 0 |
| `cargo test` | PASS, exit 0; 108 passed, 0 failed, 9 intentionally ignored full-capture/sweep gates |
| `git diff --check` | PASS, exit 0 |

The package changes no production function, so the production-function
coverage/CRAP gates are not triggered. The only crate edit corrects the
existing `r5p`/`tymax` rustdoc units from depth to the Fortran-declared mm/h.

## Package-specific evidence gates

Static checks and independent review established:

- all 13 `DailyRow` fields map to source lines, Rust owners, state/RNG, units,
  and recorded identity evidence;
- all ten RNG streams and nine monthly batch columns are mapped;
- continuous and observed branch tables cover all eight `.prn` sentinel
  combinations, EOF, year-end latch, cap termination, and first divergence
  seams;
- all typed legacy station fields are classified as live daily, header-only,
  retained/dead, or deferred-mode inputs;
- shared daily storm descriptors are included while standalone `iopt=4/7`
  orchestration remains excluded; and
- the independent review closed every High/Medium finding without requiring a
  new reference capture.

Existing full reference captures were not rerun. Their recorded evidence is
cited by the traceability artifact; this documentation package makes Static
claims over those Ran port-package records.
