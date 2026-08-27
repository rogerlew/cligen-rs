# SPEC-A11-DIRECTIONAL-ERROR-ATTRIBUTION

Status: research-only revision 1

## Purpose

This specification repairs a diagnostic information gap in A11E5. A11E5
stored absolute log variance-ratio and absolute dependence errors, which show
distance from observation but discard whether generated variability is too
large or too small. A11E5D replays the identical development grid and records
directional quantities without changing either stochastic law or its decision.

## Frozen replay

Replay the exact A11E5 20-station by eight-member by two-arm grid from its
published implementation and inputs. Each regenerated arm must reproduce its
closed A11E5 metric object and stream-summary SHA-256 exactly. The arms remain
Gaussian control and circular-block treatment with frozen A11E2 nearest forcing.

## Directional evidence

For precipitation and temperature, retain generated variance, observed
variance, and
`signed_log_variance_ratio = log(generated_variance / observed_variance)` for
each month and annual aggregate. Positive values mean overdispersion; negative
values mean underdispersion. Variances use `ddof=1` and the inherited `1e-12`
floor only for the logarithm.

Retain generated and observed annual lag-one correlations and their signed
residual, plus generated and observed period-at-least-four-year power fractions
and their signed residual. The inherited safe-correlation and spectral rules
remain unchanged.

## Summaries

For annual precipitation variance, annual temperature variance, pooled monthly
precipitation variance, and pooled monthly temperature variance, report for
each arm: mean and median signed log ratio, mean absolute log ratio, the
absolute-mean/mean-absolute bias fraction, and over/under/within-five-percent
counts. Also report treatment-versus-control signed log variance ratios,
geometric-mean and median variance ratios, counts more/less/within five percent,
and the most over- and under-dispersed cases.

This is descriptive attribution. It has no pass threshold, does not alter the
A11E5 disposition, and cannot authorize a hybrid, router, confirmation,
production profile, or CLI surface.

## Integrity

Published source, exact A11E5 closure dependencies, canonical calendar and
role preflight, 320 finite invariant-clean streams, exact closed-stream replay,
confirmation=false, and byte-identical scientific-output replay are mandatory.
Integrity failure is a HOLD.
