# A10M4 gate results

Run 11's structured receipt verdict is `PASS`; every recorded gate is true.

- Corpus: all 98 accepted objects and 223,799,545 aggregate source bytes were
  verified; intentional masked Daymet rows were excluded rather than imputed.
- Roles: only `candidate_fit` contributed normalization and gradients;
  `fit_validation` remained diagnostic-only.
- Model/training: `N0-l32-w128-d2-lognormal` instantiated 33,352 parameters,
  exactly one L40 was visible, the update was finite, and parameters changed.
- Restart: the 427,285-byte atomic checkpoint includes every required state;
  a fresh process reproduced loss `2.7546536922454834` and every parameter
  exactly from window offset 366.
- Generation: the Philox known vector, smoke generation, order independence,
  physical supports, Gregorian 36,524-row 100-year streams, and exact 30-year
  prefixes passed for all six regimes.
- CPU export: reload was exact with the GPU hidden; export size was 148,482
  bytes, cold start 1.3538 seconds, and peak RSS 477,437,952 bytes.
- Benchmark: all 12 station/horizon rows completed on one pinned CPU, after two
  warmups and nine alternating samples of at least one second. Maximum
  MAD/median was 0.001950 for the candidate and 0.004190 for faithful Rust.
- Operations: canonical configuration, offline hash installation, job
  completion, structured evidence collection, job-local cleanup, exact remote
  absence, and toolkit close passed.

The raw timing ratios range from 2.3514 to 18.5454 and are retained only as
qualification diagnostics. A10M4 neither applies the A10M3 5x/10x selector
classification nor treats this untrained qualification model as a candidate.

## Repository closure gates

- Python compilation for the asset builder, qualification harness, and package
  verifier — PASS.
- `sh -n` over `qualify.sh` — PASS.
- `verify-a10m4.py` — PASS.
- Lemhi toolkit suite — PASS, 23 tests.
- A10M3 contract suite and verifier — PASS, 15 vectors and all frozen
  authorities/schemas.
- Sanitized publication scan — PASS; no controller-private or Ceph path is
  present.
- Independent Lemhi audit — PASS; all `r1`--`r11` remote roots absent and no
  package job live.
- `git diff --check` — PASS.
- `cargo fmt --check` — PASS.
- `cargo clippy --all-targets -- -D warnings` — PASS.
- `cargo test` — PASS; all non-ignored library, binary, integration, and doc
  tests passed, with registered evidence-only tests still ignored.

Coverage/CRAP did not run because no production function under `crates/`
changed.
