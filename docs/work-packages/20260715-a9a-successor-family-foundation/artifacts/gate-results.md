# A9a gate results

Status: `PASS`
Executed: 2026-07-15
Worktree basis: clean `main`/`origin/main` dispatch commit
`5c7f5d271b93e953986b88f7987044c5270d6c61` plus the reviewed A9a research-
documentation diff

## Package-specific gates

| Command / check | Result | Evidence |
|---|---|---|
| `python3 artifacts/capture-a9a-authorities.py` | PASS | captured 25 authority files, 10 exposed source records, and 37 exposed station IDs |
| `python3 artifacts/verify-a9a.py` | PASS | exact authorities/exposure, 18-site metadata-only confirmation roster, 31 objectives, 20 fixtures, links, history, and zero runtime/reference changes verified |
| Draft 2020-12 `check_schema` | PASS | fit-artifact, objective-registry, and data-role schemas valid |
| objective-registry schema validation | PASS | canonical 31-objective instance validates; all IDs unique; mandatory metric families and finite baseline-zero floors present |
| authority identity | PASS | all 25 file byte lengths/SHA-256 values reproduce; dispatch commit is an ancestor; A8c1 terminal present |
| exposure identity | PASS | all 10 source-record hashes reproduce; 37 prior station IDs and 14 model IDs remain development-only |
| confirmation metadata audit | PASS | 18 unique active CRN sites; three per six strata; nearest exposed distance >=75 km; within-stratum separation >=150 km; target-series access false |
| NOAA metadata/document capture | PASS | official station, product, Subhourly01 README, and header document hashes recorded; no station-year target object read |
| class independence static review | PASS | explicit alternating observed-spell state differs from hidden semi-Markov joint-emission state; degenerate intersection excluded; executable A9b hold defined |
| source/metric coverage review | PASS | `wet0`/`r1mm`, event time-to-peak, monthly budgets, 1/3/5-day extremes, compound variables, winter proxies, availability, and source lineage explicit |
| local Markdown link check | PASS | all package/specification registry local links resolve |
| runtime/reference diff and token scan | PASS | no path under `crates/` or `reference/cligen532/` changed from dispatch; no research class/runtime ID appears in production crates |
| canonical JSON and trailing-whitespace scan | PASS | manifests and objective registry reproduce canonical bytes; new A9 files contain no trailing whitespace |

The official NOAA documents are metadata/source documentation, not target
station-year series. Target objects remain prohibited until a future A9d seal.

## Repository gates

| Command | Result | Summary |
|---|---|---|
| `git diff --check` plus untracked-file whitespace scan | PASS | no whitespace errors |
| `cargo fmt --check` | PASS | no formatting differences |
| `cargo clippy --all-targets -- -D warnings` | PASS | zero warnings |
| `cargo test` | PASS | 192 passed, 0 failed, 10 ignored |

Ignored tests are the pre-existing local evidence, exhaustive formatter,
external collection, or full tap-stream gates with explicit ignore reasons.
Executed tests include faithful `.cli` golden byte parity and modern-station
parity.

Coverage/CRAP was not triggered: A9a changes no production function under
`crates/`.

## Review gate

The consolidated review verdict is `ACCEPT` with zero open P1/P2 findings.
Three review findings were corrected before closure: wet-threshold ambiguity,
pooling-hierarchy incompleteness, and confirmation-state wording.

## Terminal

All required gates pass without waiver. Terminal: `FOUNDATION-READY-A9B`.
A9b remains unscaffolded and requires a separate operator dispatch.
