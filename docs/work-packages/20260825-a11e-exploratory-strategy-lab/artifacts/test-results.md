# A11E implementation gate results

Date: 2026-08-25

Evidence class: Ran locally from `/Users/roger/src/cligen-rs` on `main`.

| Gate | Result | Evidence |
|---|---|---|
| Package synthetic suite | PASS | Python 3.12.13 / NumPy 2.3.5; 18 passed in 0.248 s |
| Manifest runtime validation | PASS | Canonical manifest plus unknown-field, duplicate/missing-ID, capability, and support mutations |
| Schema/runtime identity comparison | PASS (bounded) | Exact capability, stage, evaluator, metric-set, and uncertainty constants compared; no Draft 2020-12 validator was present in the pinned runtime |
| 48-field / 30-year target generation | PASS | Both registered annual strategies fit a valid two-site, 30-year-per-site cohort and emitted shape `(30, 48)` |
| Population covariance evidence | PASS | Gaussian law is analytic; block law uses fitted uniform-row population moments; long-run and prefix-consistency fixtures passed; finite-run covariance is labeled diagnostic |
| Daily structural invariants | PASS | Exact wet count and precipitation total, exact temperature mean/sample SD, positive exact-mean range, ordered Tmax/Tmin, retained texture, replay |
| RNG/domain preflight | PASS | Philox domain replay/separation, key binding, no aliased core streams, invalid target/core request consumes no draw |
| `cargo fmt --check` | PASS | No output |
| `cargo clippy --all-targets -- -D warnings` | PASS | Finished successfully |
| `cargo test` | PASS | Workspace suite passed; ignored evidence-only/environment-bound tests remained ignored |
| `git diff --check` | PASS | No output |
| Changed-document relative-link check | PASS | All local relative Markdown targets resolved |

No observed data, confirmation data, public profile, Rust production function,
or reference Fortran source was consumed or changed. Coverage/CRAP was not
triggered because no production function under `crates/` changed.

