# A11E8 — Deterministic Cohort Joint-Model Foundation

Status: `SCAFFOLDED`

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

Execution is not authorized by this scaffold. The prospective executor and
synthetic tests are frozen here. A later kickoff must start from the
then-current `origin/main` and invoke the executor with that exact
forty-character source commit before any further source edit.

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
- `artifacts/review.md` — pending execution review surface.
