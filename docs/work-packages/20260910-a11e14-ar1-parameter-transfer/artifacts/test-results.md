# A11E14 test results

Date: 2026-09-10

- Python 3.12.14 / NumPy 2.3.5 tests: PASS, 4 tests.
- Manifest digest:
  `5c69d48f0a79fe195bfd7d5c43bdd9a6fc6db68f65bca87473d8e62765810537`.
- Exact-source analysis and independent replay: PASS; preflight, fit,
  evidence, and decision artifacts were byte-identical.
- Candidate-fit/development role firewall, calendar masks, 1,200/20 object
  counts, two complete 640-row downstream grids, four cohorts per estimator,
  finite estimates, evidence self-hash, input/output hashes, JSON, links, and
  confirmation=false: PASS.
- `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, `cargo test`,
  and `git diff --check`: PASS.
- Coverage/CRAP not triggered; no production function changed.
