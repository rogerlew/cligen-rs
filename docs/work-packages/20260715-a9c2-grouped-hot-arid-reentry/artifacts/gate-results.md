# A9c2 scaffold gate results

Date: 2026-07-15
Status: `SCAFFOLDED`; execution unauthorized

## Review gates

- PASS — independent evidence extraction confirmed that A9c's 150/200 event
  floors were prospective rules, not empirically calibrated hot-arid support
  minima.
- PASS — independent methods reconstruction confirmed the five-location
  metadata floor, equal-station grouped estimator, fit-side versioning, full
  refit/null/comparison rerun, and unchanged confirmation firewall.
- PASS — independent consistency/public-safety review dispositioned seasonal
  aggregation, zero-event cells, material power alternatives, exposed-object
  reuse, partition-versus-independence language, specification versioning,
  naming, links, hashes, and package-local LFS.
- PASS — the consolidated revision-2 review has exactly one `ACCEPT` terminal
  and zero open P1/P2 findings.

## Evidence and scaffold gates

- PASS — 17 predecessor files reproduce exact byte counts and SHA-256 hashes.
- PASS — A9c report revision 2 verifies against its strict manifest.
- PASS — A9c retains `HOLD-A9C-GATE-CALIBRATION`, 64 observed objects, 180
  source accesses, 7,000 null replicates, five fits, three frozen-rule failed
  cells, and zero candidate-score/confirmation/runtime access.
- PASS — A9c2 is scaffold-only and contains no newly acquired station metadata
  or station-year evidence.
- PASS — the context contract requires at least five hot-arid locations, a
  complete metadata census, equal station mass within registered seasonal
  aggregation, explicit zero-event behavior, heterogeneity and spatial-
  dependence diagnostics, at least 0.80 power against predeclared material
  perturbations, and symmetric versioned fit-side rules.
- PASS — the locked confirmation roster remains metadata-only; execution,
  A9d, and A9e remain unauthorized.
- PASS — package-local `artifacts/large/**` resolves to Git LFS without
  changing A9c's hash-bound root `.gitattributes`.

## Commands

```text
python3 docs/reports/verify-report.py --self-test
python3 docs/reports/verify-report.py \
  docs/reports/a9c-observed-development-availability-report.manifest.json
python3 docs/work-packages/20260715-a9c-observed-development/artifacts/verify-a9c.py
python3 docs/work-packages/20260715-a9c2-grouped-hot-arid-reentry/artifacts/verify-scaffold.py
python3 -m unittest discover -s research/a9c/tests -v
git diff --check
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
```

All commands passed. An authored-file trailing-whitespace scan also passed.
`git diff -- crates reference/cligen532` is empty. Coverage/CRAP is not
triggered because no production function under `crates/` changed.
