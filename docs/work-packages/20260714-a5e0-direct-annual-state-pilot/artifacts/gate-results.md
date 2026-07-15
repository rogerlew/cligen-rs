# A5e0 gate results

Status: `FINAL`
Date: 2026-07-14
Decision: `EXECUTED-HOLD-PROSPECTIVE-BOUNDARY`

## Repository and production-function gates

| Command | Result | Evidence |
|---|---|---|
| `cargo fmt --check` | PASS | No formatting difference. |
| `cargo clippy --all-targets -- -D warnings` | PASS | Workspace and all targets completed without warnings. |
| `cargo test` | PASS | Unit/integration suite passed; faithful `.cli` goldens remained byte-identical. Long evidence-only sweeps retained their declared ignored status. |
| `cargo llvm-cov --workspace --lcov --output-path target/lcov.info` | PASS | Full workspace tests completed and LCOV was written. |
| `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above` | PASS | 788 production functions analyzed; none exceeded CRAP 30. |
| `git diff --check` | PASS | No whitespace error. |

## Package evidence gates

| Command or check | Result | Evidence |
|---|---|---|
| `python3 docs/work-packages/20260714-a5e0-direct-annual-state-pilot/artifacts/verify-a5e0.py --self-test` | PASS | Strict JSON, schemas, artifact mutations, 48-run closure, hashes, realized RNG partitions, annual-state use, and terminal hold validated. |
| coefficient schema validation | PASS | The three-station bundle validates and contains 144 finite loadings. |
| H0 diagnostics | PASS | Recorded occurrence, amount, and temperature feasibility limits pass. |
| matrix and hash replay | PASS | 48 primary runs, 96 arm/horizon cells, and 288 product identities reproduced. |
| zero-bundle conformance | PASS (realized) | Formatted daily rows and final faithful states match; candidate consumed zero extension states. |
| 30-/100-year prefix | PASS (formatted rows) | All 48 standalone 30-year row sequences match the corresponding 100-year prefix. The stronger typed-row evidence name was not demonstrated. |
| faithful RNG partition | PASS (realized), prospective proof FAIL | Starts, final states, periods, annual-state prefixes, and observed counts replay; maximum observed use was 457,201 below 500,000. The required conservative pre-output upper-bound proof was not supplied. |
| descriptor-rule reconciliation | PASS | Composite and literal per-subfamily readings both pass at both horizons. |

## Report and review gates

| Command or check | Result |
|---|---|
| `python3 docs/reports/verify-report.py docs/reports/a5e0-direct-annual-state-pilot-report.manifest.json` | PASS |
| `python3 docs/reports/verify-report.py --self-test` | PASS |
| independent accuracy lens | ACCEPT |
| independent scientific-validity lens | ACCEPT |
| consistency/public-safety lens | ACCEPT |
| open material findings | zero P1, zero P2 after disposition |

## Scientific disposition

Mechanical gates passing does not make H4 pass. The exact specification,
fitter, implementation, and analyzer are absent from the named execution-base
commit and were not independently hash-sealed at the claimed prospective
boundary. The fitter arithmetic, runtime intake, typed-prefix evidence, and
conservative RNG-bound proof also did not satisfy every predeclared H4
obligation. The report correctly preserves H0--H3 as exploratory and records
H4 as FAIL. The campaign decision remains
`EXECUTED-HOLD-PROSPECTIVE-BOUNDARY`; A5e1 and public promotion are
unauthorized.
