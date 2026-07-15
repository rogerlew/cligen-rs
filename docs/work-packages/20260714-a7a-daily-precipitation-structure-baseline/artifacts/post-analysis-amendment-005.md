# A7a Post-Analysis Amendment 005

Status: accepted during internal accuracy review and before public report drafting
Date: 2026-07-14
Prior post-analysis freeze: `post-analysis-freeze-v1.json`

## Trigger

Independent evidence and methods reviews reproduced the first canonical result
and identified three discrepancies between the measurement contract and the
implementation:

1. The ranking tie-break used the median of two horizon medians instead of the
   frozen pooled median across available Daymet-off station-horizon cells.
2. Cells with an exactly zero null ceiling were available but silently omitted
   from severity aggregation.
3. Two GHCN higher-order-occurrence comparisons at 100 years calculated their
   trajectory null on 15 generated-common components while their observed
   distances used the 13 components also available in the observation.

The terminal decision and the identities of the qualifying families were
already known when this discrepancy was found.

## Bounded correction

- Calculate the ranking severity tie-break from the pooled available
  Daymet-off station-horizon cells, exactly as the contract specifies.
- Represent a positive observed distance over a zero null ceiling as the
  extended-real value `infinity`; represent zero over zero as `0.0`. This keeps
  every available cell in severity aggregation without introducing an
  arbitrary denominator. JSON stores the extended-real value as the string
  `"infinity"` so machine evidence remains standards-compliant.
- Restrict every leave-one-trajectory null distance to the same
  observation-supported component set used by its corresponding observed
  distance.

The same-support correction changes two GHCN 100-year
`higher_order_occurrence` material flags from false to true. It does not change
the limiting 30-year GHCN breadth, the family rank order, the qualifying
families, or the terminal decision. Hypotheses H1--H4 remain classified
`amended`; no confirmatory status is restored.

Acceptance requires a full rerun, independent arithmetic checks for pooled
severity and component support, and a successor post-analysis freeze that
preserves the first-result identities while binding the corrected outputs.
