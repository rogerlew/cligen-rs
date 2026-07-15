# A7a Analysis Amendment 003

Status: accepted after component-availability access and before a family
distance, ranking, or decision artifact was written
Date: 2026-07-14
Prior freeze: `pre-analysis-freeze-v3.json`

## Trigger

Generation, raw daily metrics, and retained-report overlap checks completed in
memory. Comparison construction then stopped because at least one
`wet_amount_dependence` cell had four finite common seasonal components, below
the frozen minimum of six. The exception exposed component availability but no
family distance, material flag, ranking, propagation result, or terminal
decision.

## Bounded correction

Retain every frozen minimum-common-component value. A cell below its family
minimum is now explicitly `available: false`, with null distance/severity and
`material: false`. It therefore counts against, never toward, a systemic
breadth threshold. Summary tables report both available and expected station
counts. QC comparisons record an unavailable count, and propagation composites
use the remaining available core-family distances at that station.

No threshold is lowered, no component is imputed, and no observed or generated
value is changed. Because the missing-cell disposition was clarified after
component-availability access, H1–H4 are classified `amended` rather than
confirmatory.

