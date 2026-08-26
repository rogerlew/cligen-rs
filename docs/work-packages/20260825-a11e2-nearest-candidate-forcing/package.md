# A11E2 — Nearest Candidate-Fit Forcing

Status: `ACTIVE`

Date: 2026-08-25

Evidence mode: observed development; confirmation sealed

Starting branch and push target: current `origin/main`, push `main`

## Objective

Test the A11E1-recommended single-factor hypothesis: whether replacing the
circular-block arm's regional-median forcing location with a prospectively
selected nearest candidate-fit climatology reduces both precipitation and
temperature level error on the same development stations.

## Scope

Included: source publication, metadata-only nearest-neighbor selection,
complete inherited input/calendar authentication, unchanged candidate-only fit,
20 common-random-number development streams, exact A11E1 paired comparison,
descriptive bootstrap, replay, independent review, repository gates, terminal
records, and roadmap/catalog reconciliation.

Excluded: new annual laws, altered covariance/scales/daily texture, selector
tuning, elevation weights, fallbacks, extra members, confirmation, production,
WEPP, or faithful-mode changes.

## Frozen hypothesis

`SUPPORTED_FOR_EXPLORATION` requires zero invariant failures and strict
improvement over the A11E1 circular-block baseline in both across-site median
monthly equivalent-precipitation relative error and monthly temperature MAE.
Numerically valid streams that miss either improvement are `NOT_SUPPORTED`.
Invariant or other execution failures fail closed on HOLD and do not produce a
scientific disposition. Neither scientific disposition is promotion.

## Gates

- strict manifest and synthetic selector/comparison tests;
- exact published execution source and predecessor evidence binding;
- complete inherited A10/A11E1 identity and calendar preflight;
- 20 unique station-keyed metadata selections and 20 complete streams;
- zero invariant failures and finite metrics;
- deterministic scientific-output replay;
- independent review with no unresolved P0/P1;
- `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, `cargo test`;
- `git diff --check` and changed-document link validation.

No production Rust function changes occur, so coverage/CRAP is not triggered.

## Artifacts

- `artifacts/execution-manifest-v1.json` and strict schema
- `artifacts/execute.py` and `artifacts/test_execute.py`
- selection, calendar, fit, development, decision, and execution receipts
- `artifacts/review.md` and `artifacts/test-results.md`
