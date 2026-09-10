# SPEC-A11-COHORT-TEMPORAL-INSTABILITY-ATTRIBUTION

Status: research-only revision 1

Owning work package:
`docs/work-packages/20260910-a11e11-cohort-temporal-instability-attribution/`

## Purpose and boundary

A11E11 attributes the A11E10 cohort failures without changing its decision or
generating new stochastic outcomes. It consumes the authenticated A11E10 replay
bundle and evidence. Confirmation, model selection, and promotion are excluded.

## Diagnostics

For each record reconstruct annual faithful, candidate, observed, and rendered
thermal-signal series. Record signed lag-one correlation differences, signed
low-frequency-fraction differences, absolute-error changes, and the signal's
own lag-one and low-frequency statistics. Summarize each cohort and metric by
medians, worsening fraction, number of stations whose median worsens, and the
smallest number of stations accounting for half of positive deterioration.

Threshold failure is denominator-sensitive when the cohort candidate median
exceeds `1.05` times faithful but its absolute excess above that bound is at
most `0.02`. A failing surface is broad when at least ten stations have worse
median candidate error and at least one third of its 160 pairs worsen. It is
station-concentrated when five or fewer stations account for half of positive
deterioration.

## Disposition

Evaluate only the three A11E10 failing surfaces. The disposition is:

- `RATIO_DENOMINATOR_INSTABILITY` when every failure is denominator-sensitive;
- `BROAD_IID_TEMPORAL_INSTABILITY` when every failure is broad;
- `STATION_CONCENTRATED_LOADING_INSTABILITY` when every failure is
  station-concentrated;
- `MIXED_TEMPORAL_INSTABILITY` otherwise.

The diagnostic may recommend a new falsifiable temporal law or retirement, but
cannot revise A11E10 or authorize confirmation or production.

## Replay and provenance

Execution and replay run the same deterministic analysis from hash-pinned
A11E10 inputs. Evidence and decision must be byte-identical.
