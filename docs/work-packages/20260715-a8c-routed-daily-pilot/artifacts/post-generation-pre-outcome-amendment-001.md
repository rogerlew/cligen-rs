# A8c post-generation, pre-outcome amendment 001

Date: 2026-07-15

The first frozen analysis attempt terminated with `KeyError: 'budget'` before
writing `a8c-analysis-v1.json`, `a8c-decision-v1.json`, or `findings.md`. No
scientific result or gate summary was exposed. Candidate generation had
completed and its bytes remain unchanged.

Cause: the A8a parent omits the cached `budget` object from June–August for
the explicit fallback station `ca040442`, because those analytic candidate
cells were infeasible. A8c nevertheless evaluates the unchanged legacy route
against the legacy monthly variance target. The sufficient legacy inputs
(`days`, `pww`, `pwd`, wet mean, and wet SD) remain present.

Bounded correction: when
`budget.legacy_target_dimensionless_variance` exists, retain it and verify it
against the first-order Markov identity. When it is absent, reconstruct that
same target as

`Var(N_wet) + days * wet_fraction * (wet_sd / wet_mean)^2`,

where `Var(N_wet)` uses stationary wet fraction
`pwd / (1 - pww + pwd)` and lag correlation `pww - pwd`. This is the parent
A7b `baseline_occurrence` calculation in closed form. It changes no threshold,
station, route, horizon, burn, wet-day definition, daily metric, or terminal
rule. The correction and retained generation evidence are rebound by
`pre-analysis-freeze-v2.json` before analysis resumes.
