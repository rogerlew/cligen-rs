# A10M5R14 — Continuous Distribution-Head Factorial

Status: `SCAFFOLDED-AUTHORIZED`
Date: 2026-07-20
Evidence mode: Prospective development comparison
Starting branch and push target: current `main`, push `main`

## Objective

Execute the smallest matched portfolio that addresses the two structural
limitations exposed by A10M5R13 while preserving its successful continuous
time design. The four P2/K2 arms form a 2x2 factorial:

| Arm | Smooth uncentered climatology | Centered OU scale heads |
|---|---|---|
| A | no | no |
| B | yes | no |
| C | no | yes |
| D | yes | yes |

Arm A is the R13 flexible structural baseline. B adds a small bounded smooth
correction from sine/cosine day of year and latitude/longitude/elevation into
heads 0/1/3/5. C gives the same eight medium and four slow OU factors access
to scale heads 2/4/6. D includes both mechanisms. This separates ensemble
climatological calibration, stochastic dispersion, and their interaction.

## Continuous-nature freeze

The stochastic state remains an exact daily discretization of stationary
continuous-time OU dynamics. It has eight medium and four slow factors and is
never reset at month or year boundaries. Calendar months and years are masked
aggregation domains only. The deterministic correction consumes continuous
day-of-year sine/cosine coordinates; it has no month ID, month table, yearly
cell, or discontinuous boundary. This directly addresses the operator's
monthly-quantization concern without removing the monthly and annual evidence
that the selector actually measures.

All arms retain the same 16-year Daymet windows: 5,844 normalized Gregorian
rows, 5,840 observed core rows, exactly 365 observations per year, 15 adjacent
annual pairs, and 13 eligible origins. February 29 is observed in leap years;
December 31 is the inserted structural null. Eligibility is mask-based under
`daymet_official_365_v1_to_proleptic_gregorian_daily`.

## Objective alignment

The training and checkpoint objective is prospectively aligned to all 188
finite selector metrics: 108 monthly precipitation, 60 monthly temperature,
13 annual, and seven occurrence metrics. Each has a registered differentiable
counterpart, selector scale, and distribution-head reachability row in
`artifacts/objective-selector-coverage.json`. The loss is the unweighted mean
of the same 188 scaled component residuals in training and checkpointing.
Daily proper NLL and paired daily-pattern loss remain zero-weight diagnostics.

Regularization uses a fixed registry. Medium and slow OU states are summed
once; location-OU, optional scale-OU, and optional climatology offsets are
summed. An absent factorial mechanism contributes an exact zero, so adding a
mechanism cannot dilute a mean over diagnostic keys.

## Matched controls and firewalls

- Frozen P2 backbone, K2 capacity, seeds 147031/271828/314159, sites, windows,
  generated members, counter-based random fields, selector, bootstrap, and
  thresholds are inherited unchanged.
- The four arms share exact common initialization and random fields; optional
  paths are zero-output initialized.
- No shared rank-one slow-state arm advances.
- Solar, confirmation, and all protected roles remain sealed. Later solar work
  remains a procedural latitude/day-of-year envelope plus a stochastic
  weather-coupled residual.

## Resources and authorization

One 30-minute L40 control precedes four concurrent 240-minute L40 candidate
roles. Five recovery minutes are reserved. The fresh ceiling is 995 GPU
minutes, one attempt per role, no retry. Candidate bootstrap remains
serialized only until the shared setup-ready receipt exists; all four science
jobs then run concurrently. The operator has authorized this exact portfolio,
under the xlarge evidence profile (the v2 provider contract with a 256 MB
expanded-evidence ceiling), subject to published source, fresh authority, calendar preflight before
reservation, and per-submit admission materialization.

## Exit

The exact inherited A10M5R13 temporal selector and its 1.25 bootstrap-upper
and 1.5 maximum-ratio gates decide eligibility. At least one eligible arm
emits `A10M5R14-TEMPORAL-READY`; none emits
`HOLD-A10M5R14-NO-TEMPORALLY-ELIGIBLE-CANDIDATE`. Passing arms still require
the ratified random-origin sensitivity successor before promotion.
