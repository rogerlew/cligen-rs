# A11E6 — Faithful Baseline Comparison

Status: `EXECUTED-COMPLETE — MIXED_VS_FAITHFUL`

Date: 2026-08-27

Evidence mode: prospective observed-target development comparison; confirmation sealed

Starting branch and push target: current `origin/main`, push `main`

## Objective

Determine whether the circular-block experiment is better than the existing
faithful/legacy cligen-rs implementation against observed development data.

## Authority

- [SPEC-A11-FAITHFUL-BASELINE-COMPARISON](../../specifications/SPEC-A11-FAITHFUL-BASELINE-COMPARISON.md)
- closed A11E3, A11E5, and A11E5D evidence
- A8A exact parameter identities
- operator authorization to scaffold and execute

## Scope

Included: exact faithful release build, 160 faithful streams, 14-metric paired
comparison, directional variance context, cryptographic provenance, replay,
review, gates, and record reconciliation.

Excluded: generator changes, selector changes, tuning, Gaussian decision
baseline, confirmation, production, CLI changes, and WEPP claims.

## Plan and gates

1. Freeze the specification, manifest, schema, executor, and arithmetic tests.
2. Publish the exact source on `origin/main`.
3. Build and run faithful CLIGEN on the frozen 20-by-eight grid.
4. Replay scientific outputs byte-identically, review, run repository gates,
   and reconcile records.

Required gates are strict source and dependency identity, calendar/missingness
preflight, exact station and `.par` identity, fresh locked release build, 160
finite faithful rows, exact circular evidence replay, full cryptographic
receipts, confirmation=false, deterministic replay, review without P0/P1,
standard Cargo gates, `git diff --check`, and link validation. No production
Rust function changes occur, so coverage/CRAP is not triggered.

## Resource bound

One execution and one replay, each bounded to 160 local CPU streams. No
external service or scarce accelerator is used.

## Exit

Close with the frozen comparative disposition or an exact integrity HOLD.

## Outcome

Published source `2ae1d5d9204781a54e6f3762624d215958b26597`
built release `cligen` binary SHA-256
`9dc8d7a1699b2ee3941903dcb472819500e54755ea6dbf3e7c3b911b309dd9d7`
twice and generated the exact 160 faithful streams. Each evidence row binds the
binary and its source `.par`, runspec, `.cli`, and provenance sidecar. The
calendar/missingness preflight passed, confirmation access remained false, and
all three scientific outputs replayed byte-identically.

Circular block materially improves five of ten interannual median errors over
faithful: monthly and annual temperature dispersion, annual temperature lag
one and low-frequency behavior, and annual precipitation low-frequency
behavior. The gains are especially large for temperature dispersion: circular
monthly and annual median errors are 0.299 and 0.202 times faithful.

The treatment is materially worse on five of fourteen metrics: monthly and
annual precipitation dispersion (2.65 and 2.68 times faithful), monthly
precipitation mean (2.71 times), monthly temperature mean (3.33 times), and
monthly range mean (1.16 times). Wet fraction, both cross-month correlation
metrics, and annual precipitation lag one are noninferior.

Directional evidence explains the annual-temperature advantage: faithful is
strongly underdispersed against observation, with geometric-mean and median
annual variance ratios 0.0810 and 0.0821, versus circular's previously measured
0.802 and 0.780. Faithful annual precipitation variance is mildly
underdispersed in aggregate (geometric mean 0.646; median 0.631), while circular
remains strongly overdispersed (geometric mean 5.80; median 5.69).

The frozen disposition is `MIXED_VS_FAITHFUL`. Circular is a useful exploratory
source of temporal-structure improvements, but it is not a faithful replacement
as currently integrated. The next bounded work should isolate those temporal
gains from its damaged monthly means and precipitation dispersion, using
faithful—not Gaussian—as the operational control.
