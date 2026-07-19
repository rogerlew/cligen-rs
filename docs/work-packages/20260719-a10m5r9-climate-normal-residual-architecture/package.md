# A10M5R9 — Climate-Normal Residual Architecture

Status: `EXECUTED-HOLD-RESIDUAL-ARCHITECTURE-NOT-SUPPORTED`
Date: 2026-07-19
Evidence mode: Mixed
Starting branch and push target: current `main`, push `main`

## Objective

Test whether separating transferable monthly climate location from a small
stochastic residual state resolves A10M5R8's dispersion-versus-location trade.

## Scope

Included: exact P1 context reconstruction; candidate-fit-only regime/month
baseline; baseline-only versus frozen-baseline-plus-six-dimensional monthly
latent residual ablation; exact eight-year masked calendars; all-240 final
fit-validation scoring; one training seed; one bounded single-L40 execution;
role, evidence, accounting, and cleanup closure.

Excluded: fit-validation target features or gradients, daily weather feedback,
station embeddings, baseline mutation during residual fitting, scale-head
residuals, alternate dimensions or seeds, solar radiation, expanded sources,
development-selection, confirmation, production, and public profiles.

## Authority

The operator authorized the recorded A10M5R8 scientific successor. Authority
is bounded by `SPEC-A10-CLIMATE-NORMAL-RESIDUAL`, the revision-2 A10 corpus
calendar contract, and one 60-minute L40 primary plus one five-minute exact-node
cleanup reserve. No retry is authorized.

## Plan

1. Freeze the architecture, objective, random fields, roles, calendar, and
   decision before outcome access.
2. Verify calendar, baseline/residual separation, centering, persistence, and
   decision fixtures locally.
3. Publish the source identity and initialize one package-scoped resource
   authority.
4. Reconstruct P1, fit baseline, freeze it, fit residual, and score all arms.
5. Collect and authenticate evidence, clean exact roots, close the disposition,
   reconcile records, run repository gates, and push `main`.

## Data calendar and missingness preflight

The run must replay `a10-daymet-calendar-profile-v1.json`, verify 10,958/10,950
fit-period axis/observed counts and the eight absent leap-year December 31
dates, construct exclusive-end 2,922-label/2,920-observed representative
windows, and require at least 28 jointly observed core rows per year-month
before reserving the GPU.

## Execution & dispatch

Codex executes from `/Users/roger/src/cligen-rs`, starting from current `main`
and pushing only `main`. Private state lives below
`/Users/roger/.cache/cligen-rs/a10m5r9-climate-normal-residual/`; the remote run
root is exact and package-specific.

## Gates

- frozen contract and calendar-profile verification
- baseline-only has no stochastic state
- residual baseline parameters remain byte-identical after residual training
- innovation centering and deterministic replay
- exact P1 reconstruction
- 1,200 fit / 240 fit-validation calendar eligibility
- fit-validation gradient-free and protected roles sealed
- all-240 paired final comparison and deterministic decision
- toolkit accounting, collection, exact cleanup, and close
- `cargo fmt --check`
- `cargo clippy --all-targets -- -D warnings`
- `cargo test`

## Exit criteria

`EXECUTED-COMPLETE` requires an authenticated architecture decision, regardless
of scientific pass or hold, plus exact accounting and cleanup. Infrastructure,
identity, calendar, role, support, evidence, or cleanup failure holds without
retry. A scientific hold does not authorize an outcome-time architecture edit.

## Artifacts

- `artifacts/architecture-contract.json` — prospective machine contract
- `artifacts/verify_freeze.py` — local contract/calendar verifier
- `artifacts/verify_corpus_calendar.py` — immutable corpus preflight
- `artifacts/jobs/` — immutable experiment and dispatch sources
- `artifacts/comparison-summary.json` — authenticated all-240 comparison
- `artifacts/execution-disposition.md` — scientific terminal and successor
- `artifacts/resource-ledger.md` — requested/actual resource settlement
- `artifacts/toolkit-records.md` — receipt and evidence identities
- `artifacts/review.md` — scientific, evidence, and operational review
- `artifacts/gate-results.md` — package and repository gate record
- `artifacts/verify_result.py` — committed result/decision verifier
