# A10M5R15R1 — PRISM-Eligible Balanced Cohort

Status: `SCAFFOLDED`
Date: 2026-07-21
Starting branch and push target: current `main`, push `main`

## Objective

Repair the A10M5R15 input prerequisite without weakening its containing-cell
contract. Preserve every valid A10M1 v2 location, replace only the 74
masked/out-of-coverage locations, and restore exactly 200 `candidate_fit` and
40 `fit_validation` locations in each of the six frozen regimes.

## Authority

The operator authorized the recommended deterministic, PRISM-eligible,
regime-balanced backfill after A10M5R15 stopped at
`HOLD-A10M5R15-ENGINEERING-INCOMPLETE`. This package is a new prospective data
identity; it does not rewrite the accepted A10M1 corpus or the A10M5R15 HOLD.

## Frozen selection

1. Authenticate the A10M1 v2 selection, partition lattice, tile repair,
   original access ledger, A10M5R15 failure record, and PRISM runtime grid.
2. Retain the 1,366 selected v2 points that return a valid containing PRISM
   cell.
3. For each regime/role deficit, scan the original candidate-blind
   `(regime, role, order)` lattice, excluding confirmation/development points
   already removed by A10M1, conflicted tiles, selected points, and invalid
   PRISM cells.
4. Prefer already accepted, locally authenticated Daymet series. These cover
   38 replacements. The remaining frozen deficit is eight cold and 28
   hot-arid `candidate_fit` points.
5. Request only the published queue, in order, stopping when those 36 slots
   have accepted 1980–2009 Daymet series. At most 72 new requests are allowed.
6. Publish a new 1,440-point selection and corpus identity. No target climate
   value, PRISM normal value, model output, or confirmation information enters
   ordering or role assignment.

The original 200/40 counts, tile-level role separation, regime definitions,
calendar transform, variables, years, and missingness semantics remain exact.
PRISM eligibility is the sole prospective inclusion change.

## Gates

- exact predecessor and source hashes in `artifacts/cohort-contract.json`;
- 1,366 retained, 38 accepted-local replacements, and 36 newly accepted
  replacements;
- final 200/40 counts in every regime and no point/tile role collision;
- all 1,440 coordinates return one valid containing PRISM cell;
- all Daymet objects retain 10,950 source rows and the canonical 10,958-row
  Gregorian axis with leap-year December 31 structural nulls;
- candidate-fit-only normalization is recomputed for the new corpus;
- confirmation roles and series remain sealed;
- source is published on `main` before new requests;
- repository formatting, clippy, tests, Python verification, and diff checks.

## Resources and exit

This data remedy uses no GPU. It may issue at most 72 Daymet single-pixel
requests from the frozen queue. Success is `A10M5R15R1-COHORT-READY`; failure
to fill any cell within the queue is
`HOLD-A10M5R15R1-PRISM-ELIGIBLE-COHORT-UNAVAILABLE`.

On success, execution continues under a separately published A10M5R15R2 job
source/authority identity. Confirmation, solar, spatial, and production roles
remain sealed.
