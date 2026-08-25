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
| Exact source publication | PASS | `b842430cb665a1219e01061312357688e04e6c62` equaled `origin/main` at publication check |

Published source artifact identities:

| Artifact | SHA-256 |
|---|---|
| `strategy-manifest-v1.json` | `fb9dd3771e130ed58b1146af6ac5d360bf2afe3d2b3b30293c547f4a80339a53` |
| `strategy-manifest-v1.schema.json` | `71bd330e2510843c36b08e0af4b87e6d7fb792274cf2893cd5b245ade7d145ba` |
| `strategy_lab.py` | `af5691361bf278ef6adbb4c4e56fa35d017bc33677284836ee008396190b2de4` |
| `test_strategy_lab.py` | `265d116c579949df164e3c6b8d7e71af506725fb321d6c7ea90dcde1ca2c0059` |

No observed data, confirmation data, public profile, Rust production function,
or reference Fortran source was consumed or changed. Coverage/CRAP was not
triggered because no production function under `crates/` changed.
