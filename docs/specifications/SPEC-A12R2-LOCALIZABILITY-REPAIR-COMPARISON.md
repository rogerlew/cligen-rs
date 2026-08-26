# SPEC-A12R2-LOCALIZABILITY-REPAIR-COMPARISON — Prospective Corpus Comparison

Status: revision 1; prospective; fit-validation only; no default change or confirmation authority

## Purpose and authority

A12R2 evaluates the two bounded remedies retained by A12R1: keep the donor
chosen by a raw selector and explicitly repair eligible all-dry months, or
exclude donors that cannot complete ordinary localization. It uses the A12
observed-descriptor estimand and A12R1 production algebra. This is an
exploratory comparison, not a promotion trial.

The immutable predecessors are A12 source commit
`d94f6eab53c9103c797b332ae51aea3a87341bcb`, its failure-receipt file SHA-256
`ba103ab7d50fbc510910f980181aec9f3a8c188a05cdbee2b7780f7ce567fa7f`, and
A12R1 implementation source commit
`de1502ad4d80a7205ac128c24e1851a42380f5b7`.

## Corpus and preflight

Use only the authenticated 240-point A10 `fit_validation` roster. Each object
must use `daymet_official_365_v1`, span the inclusive normalized axis
1980-01-01 through 2009-12-31 (10,958 rows), mark exactly the eight leap-year
December 31 rows unobserved, and contain 10,950 observed rows. Month
descriptors and transition counts use the explicit source-observed mask;
masked rows and date gaps break transition chains. Confirmation target series
must not be accessed.

Use the registered PRISM runtime and `us-2015@2026.07` station archive. For
each site, take exactly the nearest ten donors by great-circle distance and
station-id tie break. Compute the A12 distance, latitude, precipitation,
temperature, and elevation ranks over all ten once; filtering never reranks.

## Frozen arms

Cross the three A12 selector families with two localization strategies, for
six arms:

- `closest_independent_repair_v1`
- `cligen_prism_rank_sum_independent_repair_v1`
- `elevation_prism_reference_independent_repair_v1`
- `closest_localizable_v1`
- `cligen_prism_rank_sum_localizable_v1`
- `elevation_prism_reference_localizable_v1`

The repair arms retain each raw selector's winner and apply only A12R1's
explicit `independent-prism-v1` repair. The localizable arms choose the
lowest-ranked ordinarily eligible candidate for that same selector: distance
order for closest, current all-ten rank-sum score for current, and the A12
all-ten elevation/PRISM reference score for reference. Score ties retain the
A12 distance and station-id tie breaks.

## Feasibility and localization gates

Run the complete ordinary production six-row localization algebra, F6.2
render, f32 reparse, and encoded constraints for every site-candidate pair.
Publish the 240 by 10 matrix with station id, distance, fixed ranks/scores,
source `.par` SHA-256, eligibility, and first failure month/reason. Publish
per-policy raw winner, filtered winner, displacement distance, and whether the
winner changed. If any site has no ordinarily eligible donor in its ten, stop
at `HOLD-NO-ELIGIBLE-TEN` before scoring. If any raw winner cannot complete the
explicit repair profile, stop at `HOLD-REPAIR-INELIGIBLE` before scoring.

For the current raw selector, execute `cligen prism run` with the explicit
repair flag at every site. Require exact Python/Rust candidate and winner
parity, exact localized parameter parity, a v2 receipt binding the source
`.par` and cligen executable SHA-256, and the declared extension profile.
When Python classifies the current raw winner as repair-ineligible, require the
production command to fail nonzero and publish no output directory instead.

## Quality estimand and inference

Use A12's six post-localization monthly-median errors: wet-day precipitation
SD relative absolute error, wet-day skew scaled absolute error, PWW absolute
error, PWD absolute error, Tmax SD relative absolute error, and Tmin SD
relative absolute error. The site composite is their unweighted mean.

Within each localization strategy, compare current and reference selectors to
that strategy's closest arm. For each selector family, compare its localizable
arm to its repaired-donor arm. A candidate is supported over its paired
baseline only when all four A12 conditions hold: paired composite median is
below zero, the upper endpoint of a domain-separated 10,000-replicate Philox
site-bootstrap 95% interval is below zero, strict site win fraction exceeds
0.5, and no family median is more than 5% above baseline. Reverse-direction
support is evaluated by reversing the paired delta and safeguard baseline.

Report selector dispositions separately for repaired and localizable strata.
Declare `LOCALIZABILITY_FILTER_PREFERRED` when filter-over-repair is supported
for all three selector families, or `SELECTED_DONOR_REPAIR_PREFERRED` when the
reverse is supported for all three. If neither direction has universal support
but at least one matched comparison has support, report
`STRATEGY_EFFECT_MIXED`; if none has support, report
`NO_UNIFORM_STRATEGY_ADVANTAGE`. Selector-stratum dispositions inherit the
exact A12 closest-preferred mapping. No outcome changes a runtime default or
opens confirmation.

## Provenance, replay, and review

Bind the exact published source commit; source hashes; locked toolchain;
evaluator runtime; cligen executable; station archive and extracted tree;
every candidate source `.par`; PRISM files; Daymet manifests, shards, objects,
calendar preflight; evidence; decision; and replay hashes. Scientific evidence
and decision must replay byte-identically using separately staged and published
replay artifacts; the first terminal artifacts are immutable. A feasibility
HOLD still publishes the authenticated complete 2,400-cell census before its
failure receipt. Independent review must reproduce
feasibility, selection, metrics, inference, and disposition with no unresolved
P0/P1 finding.
