# A10M5R8 — Climate-Statistics Training Objective

Status: `SCAFFOLDED`
Date: 2026-07-19
Evidence mode: Mixed
Starting branch and push target: clean `main` at `6458b8c`, push `main`

## Objective

Determine whether the accepted P1 architecture can reproduce free-running
stochastic precipitation/Tmax/Tmin climate when its training and checkpoint
objective directly measures calendar-month and calendar-year statistics and
their dispersions, before introducing a new architecture.

## Scope

Included: one exactly reconstructed P1 seed-147031 control; one same-
architecture climate-statistics treatment; exact eight-year windows;
differentiable training ensembles; hard arm-paired validation ensembles;
monthly and annual location/dispersion, within-month variability, occurrence,
wet amount, and precipitation-temperature dependence; a low-weight daily
proper-score guard; full fit-validation evaluation; one bounded L40 attempt;
and exact toolkit cleanup.

Excluded: paired-day trajectory error in the climate score, architecture or
capacity changes, generated feedback, solar radiation fitting, other weather
fields, N3/elevation expansion, spatial selection, development-selection,
confirmation, public runtime, production code, and faithful behavior.

## Authority

The operator directed this package on 2026-07-19 after agreeing to the bounded
core-first sequence. The research interface is
`docs/specifications/SPEC-A10-CLIMATE-STATISTICS-TRAINING.md`; the living plan
is `docs/exec-plans/20260719-a10-climate-statistics-training.md`.

The package receives a new development-only ceiling of 65 GPU-minutes: one
single-attempt L40 primary of at most 60 minutes and one exact-node cleanup
recovery reserve of at most five minutes. No retry, second treatment seed,
second architecture, or solar-radiation arm is authorized under this budget.

## Plan

1. Freeze the statistic registry, stochastic sampling, objective weights,
   checkpoint subset, comparison thresholds, identities, and firewall.
2. Publish and locally test the executable source and immutable asset builder.
3. Commit and push the exact source, initialize one toolkit authority, and run
   the control reconstruction, treatment fit, and paired final evaluation.
4. Replay the decision, reconcile resource and cleanup state, record review and
   gates, and close roadmap/catalog/ExecPlan state.

## Execution & dispatch

Execution is by Codex from `/Users/roger/src/cligen-rs`, starting from current
`origin/main` and pushing only `main`. Lemhi execution uses canonical toolkit
revision 2, the current single-L40 designation, and package-scoped private
state beneath `/Users/roger/.cache/cligen-rs/a10m5r8-climate-objective/`.

## Gates

- `python3 artifacts/verify_freeze.py`
- exact accepted-control reconstruction identity
- complete eight-year calendar windows and all 240 fit-validation points
- finite gradients/statistics and physical support
- deterministic replay of the terminal decision
- protected roles opened equals `[]`
- authority, scheduler, collection, accounting, and exact cleanup reconcile
- `cargo fmt --check`
- `cargo clippy --all-targets -- -D warnings`
- `cargo test`

No `crates/` production function changes are planned, so coverage/CRAP gates
are not triggered.

## Exit criteria

`EXECUTED-COMPLETE` with terminal `A10M5R8-CORE-OBJECTIVE-READY` requires at
least 15% lower full fit-validation climate score, no block worse by over 10%,
daily proper NLL no worse by over 10%, complete evidence, and all operational
gates.

Legitimate holds include objective nonimprovement, block degradation,
proper-score degradation, support failure, resource exhaustion, identity
failure, protected-role access, or incomplete operational cleanup. Scientific
failure does not authorize a retry or post-hoc statistic/weight change.

## Artifacts

- `artifacts/climate-objective-contract.json` — executable frozen experiment
- `artifacts/jobs/` — immutable training/evaluation and Lemhi sources
- `artifacts/verify_freeze.py` — local contract/source verifier
- terminal evidence, review, resource ledger, toolkit records, and gate log
