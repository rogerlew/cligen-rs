# SPEC-A11-FAITHFUL-TEMPERATURE-QC-ATTRIBUTION

Status: research-only revision 1

## Purpose

Quantify how much faithful CLIGEN's cumulative `RANSET` conditioner contributes
to annual-temperature underdispersion on the A11 development corpus, separating
that contribution from the fixed-monthly-parameter model structure.

## Frozen comparison

Observed data remain the target. Compare `faithful_5_32_3` with
`qc_filter: faithful` (operational control) against the same backend with
`qc_filter: off` (ablation). The off arm retains source RANDN streams and all
downstream temperature equations; only batch acceptance/retry is removed.

Use the exact A11E6 20-station `.par` roster, 16-year horizon, and 32 frozen
burns per station. The first eight burns reproduce A11E6. Emit quality reports
so actual temperature-column retries and off-arm counterfactual rejection
verdicts are authenticated.

## Estimands

Primary estimands are the QC-off/QC-on ratio of annual generated temperature
variance, change in absolute log variance error against observation, and the
off/observed residual. Secondary temperature metrics are monthly dispersion,
monthly mean error, annual lag one, annual low-frequency power, and cross-month
correlation RMSE.

QC relief is material when the median off/on annual variance ratio is at least
1.10 and the median off absolute-log variance error is at most 95% of on.
Monthly temperature mean is noninferior when its off median error is at most
105% of on. A structural deficit remains when the off median generated/observed
annual variance ratio is below 0.95.

The descriptive disposition is one of
`QC_MATERIAL_AND_STRUCTURAL_DEFICIT_REMAINS`, `QC_DOMINANT`,
`QC_MATERIAL_WITH_CLIMATOLOGY_COST`, `QC_NOT_MATERIAL`, or `QC_MIXED`.
It cannot promote QC-off, alter defaults, authorize an overlay, or access
confirmation data.

## Integrity

Published source, exact dependencies, observed calendar/missingness preflight,
station and source `.par` identity, fresh locked release binary identity, exact
20×32×2 grid, A11E6 eight-burn faithful replay, finite metrics, authenticated
quality/process evidence, confirmation=false, and byte-identical replay of
scientific outputs are mandatory. Integrity failure is a HOLD.
