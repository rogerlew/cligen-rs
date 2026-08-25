# A11E1 independent review

Reviewer: subagent `a11_scaffold_review`

Date: 2026-08-25

## Initial scaffold disposition: HOLD

The reviewer found one P0 and five P1 issues before observed execution:

- base strategy IDs were reused with changed forcing/evaluation semantics;
- the positive-only inverse removed dry-month support;
- `fit_validation` objects were relabeled as development;
- leap-year December totals compared different observed/generated supports;
- the six-site roster carried stale shard identities; and
- authentication did not bind all source and cohort identities.

P2 findings covered unconstrained nested schema objects, full-cohort adapter
surfaces reused in CV, undeclared texture clipping, single-member uncertainty,
PRISM-period mismatch, and an unregistered bootstrap RNG domain.

No confirmation target bytes were read in review.

## Disposition in corrected source

- New integrated IDs bind the adapter, evaluator, metric, role, and uncertainty
  semantics while retaining the published annual-law implementations.
- A registered empirical dry hurdle precedes the positive continuous inverse.
- All 20 inherited `development` objects replace the validation alias.
- `daymet_mask_normalized_month_v1` compares 30.4375-day equivalent
  precipitation, observed-day means, and wet fractions.
- The stale roster and PRISM archive are removed. Location is a declared
  candidate-region pooled statistic with development moments excluded.
- Runtime requires the source commit to equal `origin/main` and authenticates
  its blobs, the normalized/cohort/shard manifests, every shard, the development
  manifest, and every selected object.
- Nested schema surfaces are strict. Cross-validation is explicitly scoped as
  annual-strategy-only conditional on the full candidate adapter. Texture
  bounds, the single-member limitation, and a dedicated Philox bootstrap domain
  are prospective contract terms.

## Corrected-source publication disposition

The first corrected-source pass retained four P1s: flattened persistence pairs
crossed site/field boundaries, February count support was not conditioned on
28 versus 29 generated days, hurdle RNG derivation was not fully frozen, and
the four-test suite did not exercise the publication contract deeply enough.

The executor now pools same-field year-to-year pairs within each site, filters
count support by generated month length, freezes and tests the NUL-delimited
Philox/BLAKE2b hurdle key, and passes 12 synthetic tests covering source
rejection, nested identity mutations, exact masks/windows, role isolation,
dry-month generation, February support, both annual laws, replay, and bootstrap.

Final scoped re-review disposition: **GO for source publication**. No unresolved
P0/P1 remains in the prospective source. The reviewer did not access observed
values or confirmation evidence.
