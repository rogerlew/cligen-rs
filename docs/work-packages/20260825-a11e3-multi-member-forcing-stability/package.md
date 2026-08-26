# A11E3 — Multi-Member Forcing Stability

Status: `SCAFFOLDED`

Date: 2026-08-25

Evidence mode: prospective source; observed development execution pending

Starting branch and push target: current `origin/main`, push `main`

## Objective

Execute the A11E2-recommended bounded stability screen: compare the frozen
regional-median and nearest-candidate forcing adapters under eight common-RNG
members and determine whether both primary across-site median improvements
persist for every member.

## Scope

Included: source publication, exact A11E1/A11E2 dependency binding, repeated
calendar/role/selector/location preflight, members 0–7, 320 complete cells,
member-0 replay authentication, frozen primary decision arithmetic,
deterministic replay, independent review, repository gates, and terminal
reconciliation.

Excluded: selector or model tuning, new forcing locations, distance/elevation
rules, fallbacks, new annual or daily laws, altered metrics, confirmation,
selection, promotion, production, WEPP, or faithful-mode changes.

## Authority

- [SPEC-A11-MULTI-MEMBER-FORCING-STABILITY](../../specifications/SPEC-A11-MULTI-MEMBER-FORCING-STABILITY.md)
- A11E1 published source and closed member-0 regional evidence
- A11E2 published source, exact selector/location receipts, and closed member-0
  nearest-candidate evidence

## Frozen hypothesis

For every member 0–7, nearest-candidate forcing must have a strictly lower
across-site median for both primary metrics than regional-median forcing.
`STABLE_FOR_EXPLORATION` requires all 16 inequalities plus complete finite
evidence, zero invariants, exact member-0 replay, and a sealed confirmation
role. A valid miss is `NOT_STABLE_FOR_EXPLORATION`; integrity failures HOLD.
Neither scientific outcome authorizes selection, promotion, or confirmation.

## Data calendar and missingness preflight

Before generation, repeat the A11E1/A11E2 preflight for all 1,440 fit objects
and 20 development objects. Record the `daymet_official_365_v1` source
transform, `daymet_mask_normalized_month_v1` estimator, 1980–2009 fit and
2010–2025 development bounds, normalized axis and observed/masked counts,
leap-year and boundary fixtures, required-field masks, month/year eligibility,
roles, and confirmation=false. Do not infer completeness from the axis.

## Plan

1. Freeze manifest, schema, member-aware evaluator, decision rule, and tests.
2. Independently review prospective source and publish it to `origin/main`.
3. Authenticate inputs, preflight calendars/RNG identities, fit once, and run
   the 320-cell grid.
4. Require exact member-0 parity, evaluate all 16 strict inequalities, and
   emit atomic receipts.
5. Replay scientific outputs byte-identically, independently review evidence,
   run repository gates, and reconcile package/catalog/spec/roadmap records.

## Gates

- strict manifest/schema and synthetic contract tests;
- exact published source and complete A11E1/A11E2 dependency identities;
- complete calendar, role, selector, location, and RNG preflight;
- 320 unique finite cells and zero daily invariant failures;
- exact member-0 metric and stream-summary replay;
- deterministic scientific-output replay;
- independent review with no unresolved P0/P1;
- `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, `cargo test`;
- `git diff --check` and changed-document link validation.

No production Rust function changes occur, so coverage/CRAP is not triggered.

## Resource bound

One development execution and one authentication replay are authorized. Each
is bounded to 320 strategy/site/member cells on local CPU, with compact JSON
evidence only. No scarce accelerator or external service is used.

## Artifacts

- `artifacts/execution-manifest-v1.json` and strict schema
- `artifacts/execute.py` and `artifacts/test_execute.py`
- prospective review and test records
- calendar/RNG/fit preflight, development evidence, decision, and execution
  receipts after authorized execution
