# A11E2 independent review

Date: 2026-08-25

## Initial prospective disposition: HOLD

The independent reviewer found no P0 and three P1 publication blockers:

- the inherited A11E strategy implementation and manifest were not rechecked
  before lazy import;
- invariant failure was inconsistently described as both HOLD and
  `NOT_SUPPORTED`; and
- tests did not directly prove the only-location/common-RNG contract or
  dependency-drift failure.

## Disposition in corrected source

The executor now verifies working and `b842430` git blobs for the inherited
strategy lab before import and receipts those identities. Invariant failures
raise a fail-closed execution error; `NOT_SUPPORTED` is available only to
numerically valid streams missing a primary improvement. The wrapper enforces a
shallow adapter copy with only `location` replaced, passes the A11E1 reference
strategy and unchanged site ordinal to the inherited evaluator, and records the
exact annual, hurdle, and five daily RNG identities. Eleven synthetic tests
cover these boundaries, including dependency drift.

Corrected-source disposition: **GO for publication**. The reviewer confirmed
all three P1s resolved, reran 11/11 synthetic tests, and found no unresolved
P0/P1. No raw observed or confirmation values were accessed in review.

## Completed-evidence review

Independent disposition: **evidence accepted; GO to close after terminal
reconciliation**. Source `e15369a`, all source/dependency/input/output hashes,
the evidence self-hash, selector mapping, A11E1 baselines, common-RNG contracts,
and decision computations reproduced. The 20 unique member-0 streams were
finite with zero invariant failures and confirmation false.

The primary medians reproduce exactly: precipitation 0.909285 to 0.748092 and
temperature 3.064101 to 1.999233 °C. `SUPPORTED_FOR_EXPLORATION` is correct
under the preregistered median rule. It is not stationwise dominance: both
primary metrics improve at 8/20 stations and composite improves at 12/20. The
descriptive composite bootstrap mean is -2.633 with 5/50/95
-6.649/-2.464/+0.325, so it crosses zero and cannot imply selection.

The sole closure P1 was missing replay/final-gate and terminal reconciliation
records. Scientific outputs replayed byte-identically and those records are
now reconciled. Final closure disposition: **GO**, with no remaining P0/P1.
The reviewer recommends the bounded fixed-selector multi-member stability
successor recorded in the package and roadmap.
