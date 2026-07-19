# A10M5R4R1 final gates

Date: 2026-07-18
Evidence mode: Ran locally on `main`

| Gate | Result |
|---|---|
| `artifacts/verify.py` | PASS; `A10M5R4R1-STOCHASTIC-PRISM-READY` |
| Python compile and strict JSON parse | PASS |
| independent deterministic bundle rebuild | PASS; runtime and source outer archives byte-identical |
| air-gap sync and 36-value Rasterio differential | PASS |
| atomic end-to-end repeatability | PASS; complete trees byte-identical, no staging residue |
| prospective 100-year monthly ensemble gate | PASS; 36/36 cells |
| `cargo package --allow-dirty --no-verify` | PASS; 104 files, 1.2 MiB unpacked, 290.9 KiB compressed; no map payload |
| `git diff --check` | PASS |
| `cargo fmt --check` | PASS |
| `cargo clippy --all-targets -- -D warnings` | PASS |
| `cargo test` | PASS; 0 failed; only declared evidence/collection tests ignored |
| `cargo llvm-cov --workspace --lcov --output-path target/lcov.info` | PASS |
| `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above` | PASS; 825 production functions, 0 above CRAP 30 |

The first complexity audit exposed 18 uncovered/over-complex new functions.
The implementation was decomposed along grid-intake, archive-entry,
localization, and artifact-publication boundaries and direct tests were added;
no allow-list was used.
