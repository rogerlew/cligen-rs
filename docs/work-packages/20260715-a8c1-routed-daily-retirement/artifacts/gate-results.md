# A8c1 gate results

Status: `PASS`  
Executed: 2026-07-15  
Worktree basis: `main` at dispatch commit
`49a67775d22f0452bbf65f0a1ad35435e0d340f9` plus the reviewed retirement diff

## Package-specific gates

| Command / check | Result | Evidence |
|---|---|---|
| `python3 artifacts/verify-a8c1.py` | PASS | 27 removal surfaces dispositioned; 148 preserved records verified; history/LFS and package surface clean |
| comparator byte check against `046eba3` | PASS | all 22 shared/current-interface files equal their pre-A8c blobs; four A8c-only files absent |
| current-interface retired-token scan | PASS | no A8c profile, model, fit, route, or extension-RNG token outside the historical specification/records |
| schema-mirror comparison | PASS | provenance-v1 and quality-report-s2-m3 documentation/runtime pairs are byte-identical |
| `cargo metadata --no-deps --format-version 1` | PASS | workspace resolves; no retired target/module |
| `cargo package --list --allow-dirty -p cligen` | PASS | no retired identifier or file in package contents |
| `git lfs fsck --objects HEAD` | PASS | local LFS object store valid |
| `git lfs ls-files -l` plus historical pointer inspection | PASS | archive object `ee50d033...edae`, size 27,481,991 bytes |
| historical reachability | PASS | `fdd35f6` and `046eba3` exist; `fdd35f6` is an ancestor of `HEAD` |

The release-exposure gate returned `REMOVAL-SUPPORTED`; details and official
source links are in `release-exposure-audit.md`.

## Repository gates

| Command | Result | Summary |
|---|---|---|
| `git diff --check` | PASS | no whitespace errors |
| `cargo fmt --check` | PASS | no formatting differences |
| `cargo clippy --all-targets -- -D warnings` | PASS | zero warnings |
| `cargo test` | PASS | 192 passed, 0 failed, 10 ignored |
| `cargo llvm-cov --workspace --lcov --output-path target/lcov.info` | PASS | LCOV generated after the full test suite |
| `cargo llvm-cov report --summary-only` | PASS | 89.71% lines; 88.66% regions; 80.92% functions |
| `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above` | PASS | 730 functions; 0 above CRAP 30; maximum 25.0 |

The ignored tests are pre-existing large local-evidence or external-catalog
gates with explicit ignore reasons. The ordinary suite includes faithful
golden byte parity and revision-1 station-document parity.

## Terminal

All required gates pass with no allow-list or waiver. Terminal:
`A8C-ROUTED-DAILY-RUNTIME-RETIRED`.
