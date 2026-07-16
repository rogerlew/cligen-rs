# A9c2 execution gate results

Date: 2026-07-15
Branch: `main`
Source commit: `493f8c4cb66f3db2b4eb227d615f33e31b2b5cf7`
Terminal: `HOLD-A9C2-HOT-ARID-ROSTER`

## Scientific and package gates

| Command or check | Result |
|---|---|
| `python3 artifacts/inventory-a9c2-roster.py` | PASS — byte-identical census reproduction; 113 metadata-base sites, 2 accepted of 5 required |
| `python3 artifacts/verify-scaffold.py` | PASS — 17 exact predecessors, A9c revision 2, preserved scaffold authorities, local LFS rule |
| `python3 artifacts/verify-a9c2.py` | PASS — exact predecessors, census, terminal, access boundary, report, production/reference nonchange, and LFS rule |
| `python3 docs/reports/verify-report.py docs/reports/a9c2-hot-arid-roster-feasibility-report.manifest.json` | PASS — accepted report and hash-bound review |
| `python3 docs/reports/verify-report.py --self-test` | PASS |
| Independent report review | ACCEPT — zero open P1/P2 findings after bounded recheck |
| Locked confirmation series access | PASS — false; only station IDs and coordinates from the metadata roster were read |
| A9c2 candidate development-output access | PASS — false |
| Daily/subdaily station-series access | PASS — false |
| Production or vendored-reference change | PASS — none relative to the source commit |
| New artifact at or above 10 MiB | PASS — none; no new Git LFS object required |

The complete reason ledger is 17 locked confirmation IDs in the metadata base,
94 hot-arid descriptor nonmatches, and 2 accepted sites, totaling 113. Three
sites matched the descriptor screen; Mercury was the locked confirmation
match. The frozen minimum of five therefore fails without station-series
access, and all downstream grouping, calibration, fit, comparison, and
confirmation gates are not reached by design.

## Repository gates

| Command | Result |
|---|---|
| `git diff --check` | PASS |
| untracked authored-text final-newline and trailing-whitespace scan | PASS |
| `cargo fmt --check` | PASS |
| `cargo clippy --all-targets -- -D warnings` | PASS |
| `cargo test` | PASS |

Coverage and CRAP gates were not triggered: execution changed no production
function under `crates/`.

Final result: `EXECUTED-HOLD-HOT-ARID-ROSTER` with accepted public report and
no authorization for roster repair, A9d confirmation, A9e runtime work, or
consumer integration.
