# Pre-reservation disposition

Disposition: `HOLD-A10M5R15-ENGINEERING-INCOMPLETE`

The published-source preflight at commit
`679755627cc19e579dc0d704e11c910df9904a83` authenticated the exact PRISM
runtime grid and all 1,440 accepted A10M1 Daymet calendar surfaces. It then
applied the frozen containing-cell query with no fallback or interpolation.

Seventy-four corpus coordinates resolve to masked or out-of-coverage PRISM
cells: 60 `candidate_fit` and 14 `fit_validation`. The failures are confined
to the cold and hot-arid regimes:

| Regime | candidate_fit | fit_validation |
|---|---:|---:|
| cold | 19 | 3 |
| hot_arid | 41 | 11 |

All six temporal sites resolve to valid cells. The complete coordinate-level
record is
`artifacts/preflight/normal-conditioning-preflight-failure.json`.

The package required 1,200/240 valid corpus queries and explicitly prohibited
fallbacks. Therefore normalizer construction, candidate output, toolkit
authority, and GPU reservation did not occur. GPU authorization does not waive
this scientific input gate.

Continuing requires one prospective data decision that changes the frozen
claim: issue a new corpus/cohort with deterministic PRISM-coverage eligibility
and balanced replacement selection, adopt a specified valid-cell fallback, or
adopt a different complete normals source. Reusing the remaining 1,366 points
without a new cohort contract would silently unbalance the cold/hot-arid
regimes and is not authorized.
