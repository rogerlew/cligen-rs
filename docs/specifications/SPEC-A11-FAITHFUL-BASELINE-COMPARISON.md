# SPEC-A11-FAITHFUL-BASELINE-COMPARISON

Status: research-only revision 1

## Purpose

Evaluate the A11E circular-block experiment against the operationally relevant
legacy/faithful CLIGEN implementation. Observations define the target;
`faithful_5_32_3` is the control; circular block with frozen A11E2 nearest
forcing is the treatment. Gaussian results are context and have no decision
role.

## Frozen corpus and execution

Use the 20 development stations and exact source `.par` SHA-256 identities in
the A8A panel. Generate years 1 through 16 for burns 0, 101, 1009, 10007,
100003, 1000003, 10000019, and 100000007. Build `cligen` in release mode with
`--locked` from the published package source. Record the source commit, source
tree, Cargo inputs, toolchain, binary SHA-256, station database SHA-256, and,
for every stream, the source `.par`, runspec, `.cli`, and provenance-sidecar
SHA-256 identities.

Generated calendar months are reduced to the inherited A11 observed statistic:
precipitation is the monthly total scaled by 30.4375 divided by actual generated
days; temperature and diurnal range are daily means; wet fraction is wet-day
count divided by generated days. Observed inputs retain the canonical
`daymet_official_365_v1` and `daymet_mask_normalized_month_v1` contract.

## Metrics and decision

Lower error is better. Compare ten A11E5 interannual-family metrics plus four
monthly preservation metrics: mean precipitation relative absolute error,
temperature mean absolute error, range mean relative absolute error, and wet
fraction mean absolute error. The circular metrics and stream identities must
replay the closed A11E3/A11E5 evidence exactly.

A metric is materially improved when its circular median is at most 95% of its
faithful median, noninferior when at most 105%, and materially worse otherwise.
The exploratory treatment is `BETTER_THAN_FAITHFUL_FOR_EXPLORATION` only when
at least four of ten interannual metrics materially improve and all fourteen
metric medians are noninferior. It is `MIXED_VS_FAITHFUL` when the improvement
count is met but any metric is materially worse, otherwise
`NOT_BETTER_THAN_FAITHFUL`.

The result is development-only. It cannot promote a profile, alter faithful
mode, authorize confirmation, or make a WEPP performance claim.

## Integrity

Published source, exact dependency identities, calendar and missingness
preflight, 160 faithful streams, finite metrics, zero parse/calendar failures,
confirmation=false, and byte-identical replay of scientific outputs are
mandatory. Any integrity failure is a HOLD.
