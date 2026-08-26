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
