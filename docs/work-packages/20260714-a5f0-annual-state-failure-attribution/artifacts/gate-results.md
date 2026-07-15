# A5f0 gate results

Status: `FINAL`
Date: 2026-07-14
Decision: `RETIRE-SCALAR-IID-MECHANISM`

## Package evidence gates

| Command or check | Result | Evidence |
|---|---|---|
| pre-freeze Python AST and strict JSON parse | PASS | Analyzer, freezer, verifier, and contract parsed before the freeze was written. |
| `python .../freeze-a5f0.py` | PASS | Five analysis-source identities and four retained-input identities were frozen before derived attribution. |
| `python .../analyze-a5f0.py` | PASS | Returned `RETIRE-SCALAR-IID-MECHANISM` under `RETIRE_STRUCTURAL_OVERCOUPLING`. |
| `python .../verify-a5f0.py` | PASS | All frozen hashes, 48 runs, 288 products, scope exclusions, decision consistency, and byte-for-byte derived-artifact reproduction passed. |
| 30-/100-year prefix check | PASS | All 48 parsed 30-year annual-feature matrices exactly equal their corresponding 100-year prefixes. |
| retained daily-row parse | PASS | 2,279,088 formatted daily rows were parsed across the two horizons. |
| attribution arithmetic review | PASS | H1-family sums, covariance spectra, runtime-response aggregation, and seam-localization counts agree with the machine artifact. |
| claim and boundary review | PASS | `ACCEPT`; no open findings, causal claim, independent-confirmation claim, or scope expansion. |
| production/public surface exclusion | PASS | No production function, `.cli`, coefficient, public schema, profile, default, or provenance surface changed. |

The raw A5e0 matrix remains a hash-indexed retained `target/` dependency. The
derived artifacts reproduce locally and disclose that exact public
reproduction requires those products or hash-identical recovery.

## Repository gates

| Command | Result | Evidence |
|---|---|---|
| `cargo fmt --check` | PASS | No formatting difference. |
| `cargo clippy --all-targets -- -D warnings` | PASS | Workspace and all targets completed without warnings. |
| `cargo test` | PASS | Full unit/integration suite exited 0; faithful `.cli` golden parity passed and declared evidence-only tests remained ignored. |
| `git diff --check` | PASS | No whitespace error. |

Coverage and CRAP gates were not run because A5f0 changes no production
function under `crates/`.

## Terminal disposition

All execution and review gates pass. The package is
`EXECUTED-COMPLETE`, with the exact A5e0 scalar-IID mechanism retired from
further investment and no follow-on work package authorized.
