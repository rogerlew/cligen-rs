# A11E8 — Deterministic Cohort Joint-Model Foundation

Status: `EXECUTED-COMPLETE — THERMAL_COMPONENT_REJECTED`

Date: 2026-09-04

Evidence mode: prospective observed-target development experiment;
confirmation sealed

Starting branch and push target: current `origin/main`, push `main`

## Objective

Test the first minimal component of a nested joint residual model against
faithful CLIGEN and determine whether a deterministic generate-score-select
cohort adds useful runtime conditioning without hiding an inferior underlying
model.

## Scope

Included: one rank-one annual thermal residual, faithful paired controls, four
ordered eight-member cohorts per station, deterministic state derivation,
integer-quantized lexicographic selection, full-cohort evidence, observed
temperature scoring, calendar/missingness preflight, cryptographic provenance,
replay, review, and record reconciliation.

Excluded: precipitation state, thermal–hydro coupling, temporal persistence,
seasonal factor expansion, QC changes, station selection changes, public Rust
or CLI integration, confirmation, promotion, defaults, and WEPP claims.

## Authority

- [SPEC-A11-DETERMINISTIC-COHORT-JOINT-FOUNDATION](../../specifications/SPEC-A11-DETERMINISTIC-COHORT-JOINT-FOUNDATION.md)
- A11E7 faithful-temperature QC attribution
- A5f0 retirement of the distinct overcoupled A5e0 scalar mechanism
- operator direction that the end goal is a simple incremental joint model
  demonstrably better than faithful and that cohort selection must be
  deterministic

## Plan

1. Freeze the research specification, manifest/schema, deterministic contract
   reference, test vectors, and living ExecPlan.
2. Validate the package-local fitter, overlay, scorer, executor, and evidence
   validators without accessing candidate output.
3. Publish that exact prospective execution source on `origin/main`, then run the bounded
   development grid and one independent replay.
4. Review model retention separately from selector usefulness, run all gates,
   and reconcile the package, catalog, and roadmap.

## Data calendar and missingness preflight

A11E8 consumes the same twenty-station Daymet development observations as
A11E7. Before generation, execution must repeat the
`daymet_official_365_v1` to `daymet_mask_normalized_month_v1` preflight under
SPEC-A10-CORPUS, pin the sixteen-year axis and observed/masked counts, exercise
leap-year and window-boundary fixtures, and require mask-based complete-month
and complete-year eligibility. Confirmation-target access must remain false.

## Execution and dispatch

Execution was authorized on 2026-09-06 and ran from exact published commit
`00babe13e88c2af90b10b89e71728155a8a999bb`. The prospective executor and
synthetic tests remained unchanged through both complete executions.

The bounded grid contains 640 fresh faithful CLIGEN streams and 640 derived
thermal candidates per execution. Four cohorts by twenty stations yield 80
mixed-model selections and 80 faithful-only comparator selections. One replay
is required. No external service or scarce accelerator is used.

## Gates

- strict manifest/schema and deterministic reference-vector tests;
- execution-order-invariant selection and exact tie-break tests;
- exact calendar/missingness and twenty-station source identity;
- complete 32-burn, two-model record grid and 80 selections;
- faithful paired-row identity outside Tmax, Tmin, and dewpoint;
- exact Tmax-minus-Tmin and Tmin-minus-dewpoint preservation;
- finite metrics and independent unselected-model/selector decisions;
- SHA-256 identity at every input, candidate, selection, and output step;
- byte-identical scientific replay and review without unresolved P0/P1;
- `cargo fmt --check`;
- `cargo clippy --all-targets -- -D warnings`;
- `cargo test`; and
- `git diff --check` plus changed-document link validation.

Coverage/CRAP becomes mandatory if execution changes a production function in
`crates/`. The current scaffold changes no production function.

## Exit criteria

Close with one frozen scientific disposition or an exact integrity HOLD. A
retained thermal component authorizes only the next nested hydroclimate-state
development package. Selector usefulness does not promote a public runtime,
and selection cannot rescue a rejected component.

## Artifacts

- `artifacts/execution-manifest-v1.json` and schema — frozen experiment.
- `artifacts/contract.py` and `test_contract.py` — deterministic reference
  semantics and vectors.
- `artifacts/execute.py` and `test_execute.py` — prospective executor and
  candidate-blind synthetic validation.
- `artifacts/scaffold-validation.md` — prospective test and repository-gate
  record.
- `artifacts/review.md` — completed execution review.
- `artifacts/replay-receipt-v1.json` — exact scientific replay record.
- `artifacts/test-results.md` — execution and repository gate record.

## Outcome

Both complete executions generated 640 faithful streams and 640 derived
thermal candidates, scored all 1,280 records, and produced 80 mixed-model and
80 faithful-only selections. The calendar/missingness preflight authenticated
20 development stations with 5,844 normalized axis rows, 5,840 observed rows,
and the four expected masked dates per object. Confirmation access remained
false.

The thermal component substantially reduced annual-temperature dispersion
error: its median candidate/faithful ratio was `0.16088`, and 639 of 640 paired
records improved. It failed the frozen monthly-temperature mean gate at
`1.09564` times faithful, above `1.05`, so the terminal disposition is
`THERMAL_COMPONENT_REJECTED`. Selection cannot rescue that result.

The mixed selector chose thermal in all 80 cells and reduced selected annual
temperature dispersion error to `0.05454` of the faithful-only selector, but
it was independently not useful. Selected annual precipitation dispersion and
lag-one errors were `1.19026` and `1.06846` times faithful-only, and annual
temperature lag-one error was `1.07148`; all exceed the frozen `1.05` bound.

The calendar preflight, loading bundle, full evidence, and decision replayed
byte-identically. Review closed GO with no unresolved P0/P1. No model,
selector, confirmation, public runtime, production behavior, or default is
promoted. A successor must first isolate the monthly-mean regression without
adding hydroclimate state or selector complexity.
