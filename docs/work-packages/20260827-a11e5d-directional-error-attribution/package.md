# A11E5D — Directional Error Attribution

Status: `EXECUTED-COMPLETE — DIRECTIONAL_ERROR_ATTRIBUTED`

Date: 2026-08-27

Evidence mode: observed development replay; confirmation sealed

Starting branch and push target: current `origin/main`, push `main`

## Objective

Determine whether A11E5's dispersion errors are systematically over- or
under-dispersed, distinguish bias from scatter, and quantify whether circular
block produces more or less variance than Gaussian.

## Authority

- [SPEC-A11-DIRECTIONAL-ERROR-ATTRIBUTION](../../specifications/SPEC-A11-DIRECTIONAL-ERROR-ATTRIBUTION.md)
- closed A11E5 evidence and exact execution source
- operator authorization to run the directional diagnostic before hybrid design

## Scope

Included: exact A11E5 replay, signed monthly and annual variance ratios, signed
annual persistence and low-frequency residuals, bias/scatter decomposition,
treatment/control dispersion comparison, deterministic replay, review, gates,
and reconciliation.

Excluded: changing either generator, fitting or selecting a hybrid, routing,
new data, confirmation, production, CLI changes, and WEPP claims.

## Plan and gates

1. Freeze specification, manifest, source, schema, and synthetic arithmetic.
2. Publish the exact diagnostic source on `origin/main`.
3. Replay 320 streams and require exact A11E5 metrics and stream hashes.
4. Replay outputs byte-identically, review the directional attribution, run
   repository gates, and reconcile records.

Required gates are strict manifest/schema tests, published source and closed
A11E5 identity, canonical calendar preflight, exact 160-pair replay, finite
directional evidence, zero daily invariants, confirmation=false,
byte-identical scientific outputs, review without P0/P1, standard Cargo gates,
`git diff --check`, and changed-document link validation. No production Rust
function changes occur, so coverage/CRAP is not triggered.

## Resource bound

One execution and one replay, each limited to the exact 320 local CPU streams.
No external service or scarce accelerator is used.

## Exit

Close with descriptive directional findings or an exact integrity HOLD. The
package cannot alter A11E5's scientific disposition.

## Outcome

Published source `a5e896a61db61d0b057684859c2b78ef2576d86e`
replayed all 320 A11E5 streams. Every metric object and stream-summary SHA-256
matched the closed A11E5 evidence exactly, all directional values were finite,
daily invariant failures remained zero, and confirmation access was false. The
three scientific outputs replayed byte-identically.

Annual temperature variance is directionally biased low under circular block,
not merely noisier. Its geometric-mean generated/observed variance ratio is
0.802 and its median ratio is 0.780; 100/160 pairs are underdispersed by more
than 5%, 50 are overdispersed, and 10 are within 5%. Gaussian is also mildly
underdispersed but closer to neutral (geometric mean 0.912, median 0.936).
Circular block has 0.878 times Gaussian annual temperature variance
geometrically and 0.857 at the median. Its net-bias fraction is 0.429 versus
0.223 for Gaussian, so both systematic underdispersion and residual scatter
contribute.

Monthly temperature variance does not show the same arm difference: circular
block has 0.991 times Gaussian variance geometrically and 0.997 at the median.
Both are mildly overdispersed relative to observation (1.128 and 1.139
geometric ratios). This localizes the annual regression to cross-month/annual
aggregation rather than monthly marginal variance, without yet identifying a
specific covariance term.

Precipitation is systematically overdispersed in both arms. Gaussian annual
variance is 167 times observed geometrically (median 184), whereas circular
block is 5.80 times observed (median 5.69). Circular block therefore reduces
annual precipitation variance to 0.0347 times Gaussian geometrically, a large
improvement that still leaves material excess. Monthly precipitation shows the
same direction at smaller scale: 7.58 times observed for Gaussian versus 1.23
for circular block geometrically.

The science status is `DIRECTIONAL_ERROR_ATTRIBUTED`; A11E5 remains
`NOT_VIABLE_ON_FROZEN_CRITERION`. Before designing a hybrid, the recommended
bounded successor is an authenticated covariance decomposition using these
closed streams and fitted annual weights to separate monthly marginal variance
from cross-month covariance contributions. No hybrid, confirmation, or
production change is authorized here.
