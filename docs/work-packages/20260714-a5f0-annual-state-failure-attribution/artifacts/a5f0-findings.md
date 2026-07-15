# A5f0 Annual-State Failure Attribution

## Abstract

A5f0 reanalyzed the retained, hash-verified A5e0 products without new 
climate generation or coefficient fitting. The result is descriptive evidence 
for the already exposed three-station development surface, not a prospective 
climate test or a population claim.

## Findings

- At 30 years, `cross_month_dependence` supplied 70.6% of summed positive H1 family degradation.
- At 100 years, `cross_month_dependence` supplied 67.9% of summed positive H1 family degradation.
- `ca042319`: the leading component represented 16.5% of standardized 1980–2009 annual-feature variance; the rank-one correlation residual was 0.785.
- `co051660`: the leading component represented 14.5% of standardized 1980–2009 annual-feature variance; the rank-one correlation residual was 0.839.
- `ms227840`: the leading component represented 11.9% of standardized 1980–2009 annual-feature variance; the rank-one correlation residual was 0.883.
- Across 96 active station-month loadings, the realized/expected median response ratio was 0.994, with 100.0% sign agreement.
- Same uniquely worst seam counts across the six station-horizon cells: occurrence=0, amount=1, tmax=0, tmin=0.

## Decision

`RETIRE-SCALAR-IID-MECHANISM` under rule `RETIRE_STRUCTURAL_OVERCOUPLING`.

cross-month dependence dominates positive H1 degradation at both horizons, one component captures less than half of fit-period annual-feature variance at every station, and generated features respond to the encoded state in the expected aggregate direction and scale.

This disposition applies only to `a5e0_direct_annual_state_v1` with `a5e0_direct_monthly_loading_fit_v1`. It neither rejects annual-state models generally nor authorizes an implementation follow-on.

## Interpretation limits

The stations and A5e0 outcome were exposed before A5f0 was designed. Generated `.cli` values are formatted outputs, so response slopes include output quantization. The seam-distance diagnostic is a derived aid and does not replace the frozen A5e0 quality vector. No significance test, causal claim, confirmation claim, or promotion claim is made.
