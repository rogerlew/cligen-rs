# SPEC-A11-THERMAL-SUCCESSOR-LAW-FREEZE

Status: research-only revision 1

Owning package:
`docs/work-packages/20260910-a11e13-thermal-successor-law-freeze/`

## Boundary and retirement

A11E13 retires `a11_centered_balanced_thermal_rank1_v1` and its IID
predecessor. No package may promote, transfer, or extend those identifiers.
Faithful CLIGEN remains the operational control.

Finite-horizon accept/reject conditioning of IID state sequences is rejected as
a successor because it makes simulation horizon and candidate selection part
of the law. The only tested successor is a station-fitted AR(1) annual thermal
state, evaluated for oracle feasibility before any transfer claim.

## Frozen AR(1) feasibility law

For each station, compute annual observed mean-air temperature with fixed
calendar-month weights and fit `phi` as its sample lag-one correlation, clipped
to `[-0.75, 0.75]`. For every A11E10 identity, reuse its independent standard
normal innovations. Set `z[0] = e[0]`, then
`z[t] = phi*z[t-1] + sqrt(1-phi^2)*e[t]`. Center the 16 values and divide by
their sample standard deviation. Apply the A11E9 exact zero-sum tenths rule and
the A11E10 station loading. Degenerate or nonfinite inputs fail closed.

This is an exposed-development oracle because `phi` uses observed target data.
It is not a runtime parameterization.

## Decision

Score all 640 paired records with the six A11E10 temperature metrics. Apply the
same overall gates and require all four cohorts independently to meet annual
ratio `0.90`, other ratios `1.05`, and one-third improvement.

The disposition is `AR1_FEASIBLE_TRANSFER_REQUIRED` only when all gates pass;
otherwise `AR1_NOT_FEASIBLE_RETIRE_THERMAL_CAMPAIGN`. Neither outcome changes
production. A passing result authorizes only parameter-transfer feasibility.

## Replay

Hash-bind all A11E10/A11E12 inputs. Execution and replay must produce
byte-identical evidence and decision without confirmation access.
