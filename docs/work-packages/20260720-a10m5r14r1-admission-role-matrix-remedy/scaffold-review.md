# Scaffold review

Disposition: `ACCEPT-PENDING-INDEPENDENT-REVIEW`
Date: 2026-07-20

## Finding

The R14 abort was operational and occurred before submission. The immediate
cause was the incomplete capacity-contract schema. Review of the inherited
checker also found a latent two-member same-wave assumption that would have
rejected the third and fourth admissions even after the schema repair.

## Disposition

Publish the complete four-role contract and the corrected checker as exact
R14R1 source. For candidate position `i`, all and only earlier same-wave roles
must be present. A `SUBMITTED` predecessor requires an authenticated setup
receipt; a `RESULT_VALIDATED` predecessor requires an authenticated passed
job/cleanup receipt and must not provide setup input. Intermediate states,
prefix gaps, future roles, noncanonical attempt keys, and extra setup inputs
fail closed.

This generalization preserves the ratified four-candidate concurrent wave and
one-at-a-time bootstrap without altering any architecture, data, objective,
seed, selector, evidence profile, resource ceiling, or science terminal.

No HPC execution is part of this scaffold review.
