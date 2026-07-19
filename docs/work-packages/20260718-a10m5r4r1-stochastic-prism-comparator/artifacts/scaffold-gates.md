# A10M5R4 / A10M5R4R1 scaffold gates

Date: 2026-07-18
Evidence mode: Ran locally on `main`

| Gate | Result |
|---|---|
| A10M5R4 `artifacts/verify.py` | pass; `A10M5R4-HOLD-VERIFIED` |
| A10M5R4R1 `artifacts/verify_scaffold.py` | pass; `A10M5R4R1-SCAFFOLD-VERIFIED` |
| Python compile of both package verifier trees | pass |
| `git diff --check` | pass |
| `cargo fmt --check` | pass |
| `cargo clippy --all-targets -- -D warnings` | pass |
| `cargo test` | pass; 192 passed, 0 failed, 10 ignored evidence/collection gates |

Coverage/CRAP was not triggered: this close adds package/specification records
only and changes no production function under `crates/`.

The current official PRISM terms page was checked during scaffolding. It says
gridded data may be freely reproduced and distributed and requires the PRISM
name, URL, and access date in descriptions. The current normals page identifies
Norm91m 1991--2020 as the CONUS 30-year normals surface. Those live pages must
be rechecked and captured again before release-asset publication:

- https://prism.oregonstate.edu/terms/
- https://prism.oregonstate.edu/normals/
