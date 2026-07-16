# A9d pre-output fit amendment

Date: 2026-07-15
Access boundary: after metadata/predecessor preparation; before any A9d fit or
candidate output artifact

The initial analytic fit attempt reached no candidate write. It established
that the proposed exact monthly occurrence calibration was incompatible with
the already frozen model-class supports:

- the renewal implementation has a finite positive-duration alternating
  wet/dry support and therefore a positive lower wet-frequency bound;
- the latent class requires strictly interior state wet probabilities; and
- the coefficient-fit corpus contains at least one structural zero-wet month.

A9d therefore removes exact monthly occurrence calibration rather than adding
a zero-month gate, duration extension, fallback, or class-specific exception.
Occurrence parameters remain those fitted by the two inherited model classes.
The deterministic fit amendment is narrowed to positive-amount mean scaling in
months with observed wet days. Structural zero-wet months remain unaltered and
are evaluated honestly. Bounded event-context transforms are unchanged.

This correction reduces scope and model complexity. It changes no observed
role, evidence mask, threshold, configuration, selector, burn, confirmation
rule, or production surface. The amendment is hash-bound by every A9d fit and
verification record.
