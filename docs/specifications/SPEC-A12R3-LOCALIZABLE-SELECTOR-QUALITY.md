# SPEC-A12R3-LOCALIZABLE-SELECTOR-QUALITY — Corpus-wide selector comparison

Status: revision 1; prospective; fit-validation only; exploratory; no default change or confirmation authority

## Purpose

A12R3 answers the selector question left reachable by A12R2: among donors that
can complete the existing ordinary PRISM localization algebra, does the
wepppy-derived current rank-sum heuristic or the elevation/PRISM reference
heuristic improve observed climate descriptors over choosing the closest
localizable station? It does not evaluate or generalize dry-month repair.

## Frozen authority and corpus

The immutable feasibility authority is A12R2 closure commit
`9b7fd39bf1cec21a2307c8851bc393cf538deb8c`, source commit
`866d0401ab757708d80a58ad9dda5683f6e000bc`, evaluator SHA-256
`cc1ec0b5474e506a98514fc8f23fcf0791ae06cc75bb2ffd932e9dd2bdebfe5d`,
and feasibility-evidence file SHA-256
`9523b1a27d09affd755fde1c701ae6b26f7d31be883e054c78b99aee5a84d508`.
The A12R3 evaluator must authenticate these identities before importing
predecessor code or reading predecessor evidence.

Use only the 240 A10 `fit_validation` objects. Apply
`daymet_official_365_v1` on the inclusive 1980-01-01 through 2009-12-31 axis:
10,958 rows, 10,950 observed rows, and the eight leap-year December 31 rows
masked. Masks and gaps break transition chains. Confirmation targets are
prohibited.

## Frozen arms and selection

Compare exactly:

- `closest_localizable_v1`;
- `cligen_prism_rank_sum_localizable_v1`;
- `elevation_prism_reference_localizable_v1`.

At each site, construct the nearest-ten pool and all A12 ranks/scores over all
ten before filtering. Evaluate complete ordinary localization, including F6.2
render/reparse and encoded constraints, for every candidate. Then choose the
lowest-ranked eligible candidate for each selector: distance/station-id for
closest, current score/distance/station-id for current, and reference
score/distance/station-id for reference. Never rerank after filtering.

A12R3 must independently reproduce every candidate identity, source `.par`
SHA-256, eligibility result, score, rank, and selected donor recorded by A12R2.
Any mismatch is a provenance failure, not an estimand result.

## Estimand and decision

Use A12's six post-localization monthly-median errors: wet-day precipitation
SD relative absolute error, wet-day skew scaled absolute error, PWW absolute
error, PWD absolute error, Tmax SD relative absolute error, and Tmin SD
relative absolute error. Their unweighted mean is the site composite.

### Prospective estimand-eligibility amendment

The first source-bound run completed feasibility but failed before publishing
at the first observed descriptor with fewer than three wet days. A complete
fit-validation diagnostic found exactly two such month cells: June at
`p+3350_-11625` (one wet day) and `p+3375_-11625` (two wet days). Both have
eligible wet/dry transition denominators. For wet-day precipitation SD and skew
only, exclude a site-month with fewer than three wet days from that family's
monthly median; require at least 11 eligible months per site/family. PWW, PWD,
Tmax SD, and Tmin SD continue to use all 12 months. This mask is common to all
three arms and is not an imputation. Any other descriptor ineligibility or
fewer than 11 eligible months fails closed. The authenticated diagnostic is
part of the evaluation manifest. The first staged attempt published no quality
artifact, so the amended source remains prospective to the resulting scores.

Compare current and reference independently with closest using paired site
deltas. A selector is supported only when the paired composite median is less
than zero, the upper endpoint of the domain-separated 10,000-replicate Philox
site-bootstrap 95% interval is less than zero, strict site win fraction is
greater than 0.5, and no family median is more than 5% above closest.

Disposition is `CURRENT_HEURISTIC_APPROPRIATE` when current is supported and
reference is unsupported or current has the lower arm median composite;
otherwise `ELEVATION_REFERENCE_BETTER` when reference is supported; otherwise
`CLOSEST_PREFERRED`. Report both pairwise comparisons regardless. This is an
exploratory recommendation only: no runtime default changes and confirmation
remains sealed.

## Provenance, replay, and review

Bind the exact source commit, locked toolchain, evaluator runtime, cligen
executable SHA-256, station archive and extracted tree, every selected source
`.par` SHA-256, PRISM cache, Daymet inputs, calendar preflight, evidence, and
decision. Recompute feasibility rather than trusting predecessor rows, then
require exact equality with the authenticated A12R2 evidence. First execution
and separately staged replay evidence and decision must be byte-identical.
Independent review must reproduce selection, metrics, inference, disposition,
and cryptographic chains with no unresolved P0/P1 finding.
