# A10 Neural Candidate Research Interfaces, Revision 2

Status: research-only

Revision: 2 (A10M5R3, 2026-07-18)

## Authority and non-promotion boundary

This revision extends only the A10 research surface. It does not replace the
revision-1 checkpoint or stream contracts, introduce a public generation
profile, or change faithful CLIGEN. ADR-0005, the refinement trajectory, and
the prospective A10M5R3 design freeze govern this screen.

Only the accepted A10M1 `candidate_fit` role may affect weights, normalization,
or the splice threshold. `fit_validation` is gradient-free. Development-
selection and confirmation bytes remain sealed. N3 and elevation expansion are
outside this revision.

## Conditional wet-day amount families

Occurrence remains Bernoulli and the positive amount is conditional on a wet
day (`precipitation >= 1 mm`). Exactly three amount families are legal:

- `lognormal_wet_v2`: lognormal location and positive scale;
- `gamma_wet_v2`: gamma shape and positive scale; and
- `lognormal_body_gpd_excess_v2`: a normalized mixture of a lognormal body
  truncated to `(0, 20 mm]` and a GPD excess above 20 mm. The predicted tail
  mass is explicit, GPD shape is constrained to `(0, 0.25)`, and scale is
  positive, so support and the first moment are finite.

The 20 mm threshold is a prospective physical threshold. It is not estimated
from validation or protected roles. The former whole-wet-day GPD identity is
not representable.

Every producer must test analytic expectation against deterministic empirical
sampling, predicted 0.95 quantiles against the empirical CDF, positive support,
finite likelihood, finite gradients, and order-independent Philox generation.
Family-specific expectation and quantile arithmetic is used by both training
and evaluation; a lognormal surrogate is forbidden for gamma or splice rows.

## Model and result records

[`a10-model-v2.schema.json`](a10-model-v2.schema.json) is the strict model
record. All rows use `N0_complete`; the family screen fixes L64/W128/D2. The
capacity screen uses one winning family and the following frozen ladder:

| capacity | latent | width | depth | nominal target |
|---|---:|---:|---:|---:|
| P0 | 32 | 128 | 2 | 35,000 |
| P1 | 80 | 160 | 2 | 100,000 |
| P2 | 144 | 288 | 2 | 300,000 |
| P3 | 272 | 544 | 2 | 1,000,000 |
| P4 | 480 | 960 | 2 | 3,000,000 |

The producer records the exact family-dependent parameter count; 50 million
remains an absolute ceiling. [`a10-capacity-screen-v2.schema.json`](a10-capacity-screen-v2.schema.json)
is the strict terminal row surface.

## Frozen selection arithmetic

Registered seeds are `147031`, `271828`, and `314159`. Family ranking is the
ascending tuple of mean validation proper NLL, mean 0.95 wet-amount log error,
mean latent stability, population standard deviation of proper NLL, then
family ID. A family is eligible only if all three rows pass all scientific and
operational gates. The first eligible family wins; the second is retained only
as diagnostic context.

The five P0--P4 seed-147031 rows are filtered by hard gates and nondominance in
validation proper NLL, CPU runtime, clean-process RSS, export bytes, GPU fit
wall time, and parameter count. The lower frontier is ordered by parameter
count. For each nonterminal frontier point, normalized quality-versus-log-
parameter curvature is its perpendicular distance below the line joining the
frontier endpoints. Maximum curvature, then lower proper NLL, then smaller
parameter count selects the knee. Its immediately larger frontier neighbor is
the second retained capacity. Fewer than two frontier points is a hold.

Both retained capacities then run the other two registered seeds. The pair is
ready only when every row passes and each capacity has population standard
deviation at most 0.15 proper-NLL units. The selector is executable,
content-bound, deterministic, and may read only allowlisted predecessor rows.

## Engineering boundaries

Retained rows keep the revision-1 250 MiB export, 2 GiB clean RSS, 15-second
cold-load, 10/30-second 30/100-year generation, 5x warning, and 10x failure
boundaries. Runtime ratios are evidence, not the family primary score. All
compute uses canonical `lemhi-a10-py311-l40-v1`, one L40, deterministic CUDA,
the accepted offline corpus, and canonical toolkit revision 2.
