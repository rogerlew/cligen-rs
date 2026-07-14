# A5d0 Monthly-Constrained Successor Feasibility and Calibration

Status: `EXECUTED-HOLD-CONTRACT-INCOMPLETE`
Date: 2026-07-14
Evidence mode: Mixed (derived fixtures, static authority/corpus audit, and ran verification)

## Objective

Determine whether a state-conditioned whole-year/block candidate can improve
CLIGEN's interannual dispersion, dependence, and low-frequency behavior while
preserving the fitted monthly surface and daily/storm structure. Repair and
calibrate the A5 evaluation contract prospectively, define an untouched
confirmation corpus, and issue a reviewed `GO` or `HOLD` before any A5d
candidate confirmation output is generated.

## Scope

Included:

- derive the monthly and annual variance budget for the proposed candidate;
- distinguish dependence added by sequencing from marginal annual variance;
- specify a constrained state-conditioned year/block selector using
  Fourier/EOF features without applying a multiplicative daily overlay;
- test analytic and synthetic feasibility on development-only inputs;
- propose SPEC-A5-EVALUATION revision 4, including faithful-clone null
  calibration, observation-scaled preservation guards, uncertainty-availability
  rules, an explicit downstream WEPP criterion, and intervention-rate guards;
- define coefficient-fitting, development, and untouched confirmation roles;
- conduct a power/false-failure analysis for station and replicate counts;
- outline an experimental coefficient bundle, deterministic selector contract,
  provenance, calendar handling, common-prefix behavior, and reuse policy;
- produce a reviewed `GO` or `HOLD` decision and, on `GO`, a freeze-ready
  handoff for a separately dispatched implementation/campaign package.

Excluded:

- fitting or executing the A5d candidate on confirmation data;
- producing candidate climate or WEPP response results for model selection;
- changing faithful generation, the legacy `.par` format, or any accepted
  station-document, runspec, generation-profile, provenance, or typed-output
  surface;
- selecting among multiple confirmation candidates;
- wet/dry-conditioned radiation, subdaily forcing, multisite/spatial
  generation, external storm benchmarking, and deprecated single-storm work.

## Authority

- [ADR-0002](../../decisions/0002-quality-metrics-authority.md) makes the
  quality vector the authority for extensions.
- [ADR-0004](../../decisions/0004-a5b-interannual-no-promotion.md) requires a
  new prospective study, analytic feasibility, variance reallocation,
  integrated or preserved daily precipitation structure, null-calibrated
  guards, and explicit downstream/intervention criteria.
- [SPEC-A5-EVALUATION revision 3](../../specifications/SPEC-A5-EVALUATION.md)
  remains the current accepted evaluation contract until a separately reviewed
  revision 4 is frozen.
- The accepted [experiment report](../../reports/interannual-candidate-exp-001-report.md)
  and its [post-acceptance advisory](../20260714-interannual-candidate-exp-001-report/artifacts/post-acceptance-advisory-review.md)
  are development evidence only; their exposed candidate outcomes may not be
  reused as confirmatory model-selection evidence.
- ADR-0001 and the vendored Fortran remain the authority for the unchanged
  faithful pool generator. This package neither interprets nor edits faithful
  generator code.

## Candidate thesis to evaluate

The preferred successor uses Fourier/EOF scores to describe annual climate
state, not to scale daily fields. It generates a deterministic library from
`faithful_5_32_3 + qc_filter: off`, then selects or orders complete,
calendar-compatible years/blocks through a persistent transition process.
Stationary weights and finite-horizon constraints must preserve required
monthly sufficient statistics. Selected daily values and storm sequences must
remain numerically unchanged.

A simple permutation can change lag dependence and low-frequency power but
cannot increase one-year marginal variance. A `GO` therefore requires either:

1. a constrained selector shown to improve the complete annual target vector
   while preserving the monthly/daily contract; or
2. a justified handoff to an analytically moment-compensated conditional
   occurrence/amount/temperature model because selection alone is infeasible.

The second outcome is a design `HOLD`, not permission to substitute an
unregistered candidate during execution.

## Plan

### Phase 1 — Evidence and exposure lock

1. Hash the accepted A5b/A5c authorities, report, advisory, and calibration
   inputs.
2. Classify every station, year, and product as coefficient-fit, development,
   calibration-only, or untouched confirmation evidence.
3. Record a prohibition on candidate confirmation output before the final
   package review and freeze.

### Phase 2 — Analytical feasibility

1. Derive the law-of-total-variance allocation for monthly daily values and
   annual aggregates.
2. Derive stationary-selection and finite-prefix constraints at 30 and 100
   years.
3. Show how the transition process can change lag covariance and low-frequency
   power without silently changing one-year marginals.
4. Bound pool size, duplicate/reuse behavior, leap/calendar classes, runtime,
   and memory.
5. Exercise synthetic counterexamples that must force `HOLD`.

### Phase 3 — Evaluation revision 4 calibration

1. Replace Gate 3/4 ratios to faithful residuals with absolute,
   observation-scaled preservation measures and hard bounds.
2. Use faithful-clone null runs to estimate gate-level and familywise false
   failure at both horizons.
3. Repair Gate 1/4 bootstrap-cell availability and require a minimum usable
   replicate fraction.
4. Register a downstream WEPP reference and numeric decision rule, or record a
   scientifically explicit reason that blocks promotion.
5. Register per-station-day intervention ceilings; the preferred whole-year
   selector has a zero-new-physical-value-intervention target.

### Phase 4 — Corpus, fitting, and power plan

1. Keep the exposed A5a/A5b stations in development/calibration roles.
2. Specify Daymet coefficient fitting and hierarchical/regional pooling so the
   model is not estimated independently from only 30 annual vectors per
   station.
3. Qualify a new spatially and climatically balanced confirmation corpus and
   an independent long-record sensitivity surface where feasible.
4. Determine station and replicate counts from the null false-failure and
   candidate-effect power analysis rather than inheriting A5b's counts.
5. Freeze source licenses, retrievals, hashes, missingness rules, exclusions,
   regimes, and leakage checks.

### Phase 5 — Candidate contract and review

1. Complete the experimental coefficient-bundle and selector-contract outline.
2. Pin independent station-model and generation-profile candidate IDs without
   adding them to accepted public enums.
3. Specify domain-separated seeds, common prefixes, calendar remapping,
   duplicate/reuse policy, strict parsing, provenance, and failure behavior.
4. Conduct scientific-validity, numerical-contract, data-leakage, and
   consistency reviews.
5. Issue `GO` only if every exit criterion below is supported; otherwise issue
   the specific `HOLD` outcome and first corrective action.

## Execution & dispatch

The package was executed from the repository root on `main`, starting
from source commit `8d00f8c2108910f257b29c02341c0e1fca9e4dd9`. The A5c decision
and this package were present as uncommitted operator-directed work; their
exact authority bytes are hash-locked rather than represented as part of the
source commit. The default push target remains `main`; this package does not
commit or push without a separate operator request.

Three read-only review lenses were dispatched under the scientific authoring
protocol; the lead retained sole edit authority and reconciled their findings
in the consolidated review. Candidate confirmation climate or WEPP results
were forbidden and none were generated. The only numeric probe is the labeled
deterministic synthetic fixture.

## Gates

Repository gates at package closure:

- `cargo fmt --check`
- `cargo clippy --all-targets -- -D warnings`
- `cargo test`

Package-specific gates to implement and record during execution:

- strict evidence-lock and duplicate/nonfinite JSON verification;
- exposure-ledger closure with zero confirmation-data access;
- analytical identities checked against deterministic synthetic fixtures;
- faithful-clone calibration and mutation tests for every proposed gate;
- bootstrap-availability threshold met under the proposed evaluation contract;
- coefficient-fit/development/confirmation partition disjoint by source hash,
  station, and time rule as registered;
- candidate contract passes determinism, common-prefix, calendar-class,
  preservation, seed-domain, provenance, and fail-closed review vectors;
- report-standard accuracy, scientific-validity, and consistency reviews;
- `git diff --check` and package link/registry verification.

The coverage/CRAP gate applies only if execution adds or changes production
functions in `crates/`. This feasibility package is not authorized to do so.

## Exit criteria

### `EXECUTED-COMPLETE` with `GO`

All of the following must be true:

- the candidate class is analytically capable of improving the complete
  interannual target without violating the monthly variance budget;
- finite 30-/100-year prefixes, calendar behavior, reuse, and computational
  cost have enforceable bounds;
- proposed evaluation revision 4 is fully numeric, null-calibrated,
  uncertainty-available, and frozen before candidate confirmation output;
- the WEPP and intervention decisions are explicit and executable;
- coefficient, development, and confirmation datasets are disjoint and
  hash-frozen, with adequate power;
- exactly one confirmation candidate version and all comparison/null identities
  are freeze-ready;
- independent reviews find no unresolved P1/P2 issue;
- no accepted public compatibility surface changed.

### Legitimate holds

- `EXECUTED-HOLD-STRUCTURAL-INFEASIBILITY` — the selector cannot jointly
  improve annual behavior and preserve required marginal/daily surfaces;
- `EXECUTED-HOLD-EVALUATION-UNCALIBRATED` — false-failure, uncertainty, WEPP,
  or intervention rules cannot be made defensible before candidate access;
- `EXECUTED-HOLD-CONFIRMATION-CORPUS` — an untouched, adequately powered
  confirmation surface cannot be frozen;
- `EXECUTED-HOLD-CONTRACT-INCOMPLETE` — deterministic calendar, prefix,
  reuse, seed, provenance, or fail-closed behavior remains underspecified;
- `EXECUTED-HOLD-EXPOSURE` — candidate confirmation values were accessed
  before the preregistration and evidence freeze.

Every hold must name the failed criterion and the first follow-on action. It
must not silently substitute another model family.

## Result

The package closes `HOLD-CONTRACT-INCOMPLETE`. A constructive fixture proves
that complete-year selection can reallocate variance in some libraries. The
simple stationary kernel has a 0.6778 same-block repeat probability but no
prospectively adjudicated reuse ceiling, and a counterexample proves
feasibility is not guaranteed for arbitrary faithful libraries. The actual
blocker is the absence of an actual-library constrained solution and a bounded
repeat-safe, calendar-safe, 30-/100-year common-prefix selector demonstrated on
the exposed development stations.

Two secondary holds are recorded: the successor evaluation is not executable
or null-calibrated and has no numeric WEPP response rule, and no untouched
confirmation corpus is present. The exposure ledger is clean. No candidate ID,
production function, accepted specification, public schema, profile, default,
legacy `.par`, provenance, or typed-output surface changed.

The first follow-on action is a development-only constrained-weight and
repeat-safe path solver package on regenerated, hash-bound A5a/A5b faithful-off
libraries. It may not use confirmation data.

## Artifacts

- [`artifacts/feasibility-analysis.md`](artifacts/feasibility-analysis.md) —
  variance budget, selector mathematics, synthetic checks, and feasibility
  verdict.
- [`artifacts/evaluation-revision-4-plan.md`](artifacts/evaluation-revision-4-plan.md) —
  proposed gate changes and calibration record.
- [`artifacts/validation-corpus-plan.md`](artifacts/validation-corpus-plan.md) —
  fit/development/confirmation partition and power plan.
- [`artifacts/candidate-contract-outline.md`](artifacts/candidate-contract-outline.md) —
  experimental payload and runtime contract to freeze on `GO`.
- [`artifacts/exposure-ledger.md`](artifacts/exposure-ledger.md) — data and
  response-access record.
- [`artifacts/go-hold-decision.md`](artifacts/go-hold-decision.md) — reviewed
  terminal recommendation and implementation-package handoff.
- [`artifacts/a5d0-decision-v1.json`](artifacts/a5d0-decision-v1.json) —
  machine-readable terminal disposition.
- [`artifacts/feasibility-fixtures-v1.json`](artifacts/feasibility-fixtures-v1.json)
  and [`artifacts/run-feasibility-fixtures.py`](artifacts/run-feasibility-fixtures.py)
  — deterministic derivations, counterexample, and power arithmetic.
- [`artifacts/data-role-inventory-v1.json`](artifacts/data-role-inventory-v1.json)
  — exposed-input and absent-confirmation inventory.
- [`artifacts/evidence-lock-inputs-v1.json`](artifacts/evidence-lock-inputs-v1.json)
  — immutable accepted authorities and development inputs.
- `artifacts/verify-a5d0-package.py`, consolidated review, closure evidence,
  and gate results complete the executed record.
