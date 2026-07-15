# A5f0 Review

Verdict: `ACCEPT`
Date: 2026-07-14

## Scope and boundary

- The package is derived-only: no production file, `.cli`, coefficient, public
  schema, profile, or default changed.
- The freeze is correctly described as prospective only for the A5f0 derived
  algorithm. It does not claim that A5e0 outcomes or stations were sealed.
- The retirement target is narrow: `a5e0_direct_annual_state_v1` with
  `a5e0_direct_monthly_loading_fit_v1`. The record does not generalize to all
  annual-state models.

## Integrity and reproducibility

- The freeze pins five analysis-source files and four retained parent inputs.
- The verifier rechecked all 48 matrix records and 288 indexed products, parsed
  2,279,088 daily rows across the 30- and 100-year products, and confirmed all
  30-year annual-feature matrices equal their 100-year prefixes.
- A fresh analyzer pass reproduced the attribution, decision, and findings
  byte-for-byte.
- The matrix remains a retained `target/` dependency rather than a committed
  corpus. The findings disclose that exact reproduction needs those products
  or hash-identical recovery; the derived evidence is therefore not presented
  as a self-contained public fixture.

## Arithmetic review

Independent extraction from the A5e0 family medians confirmed the frozen
positive-degradation sums:

| Horizon | Annual dispersion | Monthly dispersion | Cross-month | Cross-variable | Cross-month share |
|---:|---:|---:|---:|---:|---:|
| 30 | 0.079508 | 0 | 0.863601 | 0.279506 | 70.6356% |
| 100 | 0.173444 | 0 | 0.948067 | 0.274484 | 67.9133% |

The recomputed fit-period correlation spectra give leading-component shares
0.165379, 0.145380, and 0.119356. All are below the frozen 0.5 ceiling. The
96 active loading cells have 100% realized-response sign agreement and median
realized/expected slope ratio 0.994239, satisfying the frozen 0.75 and
0.5–1.5 response bounds.

Only Death Valley at 30 years met the unique-worst diagnostic, for the amount
feature family; one of six is below the five-of-six seam-localization rule.
That cell has no active amount loading, so the derived feature label must not
be read as a causal amount-parameter attribution. The structural retirement
rule does not depend on this cell or on a seam-causal claim.

## Consistency and interpretation review

- Machine attribution, decision artifact, generated findings, package summary,
  and roadmap use the same decision and boundary.
- The response calculation uses formatted `.cli` values; the findings disclose
  quantization and do not call the 0.994 ratio an internal-bit identity.
- Negative Tmax/Tmin seam-distance deltas show that marginal annual-feature SD
  distance often improved even while cross-month dependence worsened. This is
  consistent with structural overcoupling and prevents the old variance-deficit
  shorthand from being revived.
- No p-values, causal estimates, independent-confirmation claims, or promotion
  claims appear.

## Disposition

The frozen priority is satisfied at
`RETIRE_STRUCTURAL_OVERCOUPLING`. No bounded seam ablation is justified. The
exact A5e0 mechanism is closed to further investment; any materially different
annual-state structure starts only by a new operator decision and a new
prospectively frozen package.
