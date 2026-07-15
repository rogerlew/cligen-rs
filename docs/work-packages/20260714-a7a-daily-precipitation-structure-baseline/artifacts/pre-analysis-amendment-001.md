# A7a Pre-Analysis Amendment 001

Status: accepted before any A7a-derived outcome
Date: 2026-07-14
Prior freeze: `pre-analysis-freeze-v1.json`

## Trigger

The first execution built the release binary and generated daily files, but
stopped on the first completed worker before parsing any daily row or producing
an A7a analysis, decision, or findings artifact. The parser required 12
whitespace-separated fields. A CLIGEN daily row actually contains 13 fields:
day, month, year, and ten weather values.

## Bounded correction

Change only the structural row-width guard in `parse_cli` from 12 to 13.
Metric definitions, station/horizon/QC/burn membership, numeric rules, null,
thresholds, ranking, and terminal decision remain unchanged.

Update the verifier to bind the successor freeze. No generated climate value
was inspected beyond confirming the field count of the first lines needed to
diagnose the parser failure.

## Access statement

No seasonal aggregation, higher-order occurrence residual, family distance,
trajectory-null result, gap ranking, propagation diagnostic, or terminal
decision existed when this amendment was made.

