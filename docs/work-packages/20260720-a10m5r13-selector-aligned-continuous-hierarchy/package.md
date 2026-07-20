# A10M5R13 — Selector-Aligned Continuous Hierarchy

Status: `SCAFFOLDED`
Date: 2026-07-20
Evidence mode: Prospective development comparison
Starting branch and push target: current `main`, push `main`

## Objective

Test whether the A10M5R12 hierarchy failed because its eight-year training
surface and objective did not expose the annual lag and complete annual
cross-field relationships used by the frozen temporal selector. Compare two
matched long-window continuous hierarchies:

1. `selector-aligned-continuous-hierarchy-k2`: the existing K2 medium-plus-slow
   OU hierarchy, trained on contiguous 16-calendar-year windows with an added
   selector-aligned annual aggregate loss; and
2. `selector-aligned-shared-slow-climate-state-k2`: the same model, windows,
   loss, seeds, controls, and random field, with the first existing slow factor
   dedicated to a rank-one joint climate coordinate rather than decoded as a
   fourth flexible factor.

This is a matched architecture comparison, not a threshold search. Both arms
retain the P2 control, eight medium factors, four slow factors, three seeds,
six development sites, eight 100-year generated members, and exact inherited
A10M5R12 temporal selection protocol.

## Scientific freeze

Daily latent evolution remains the exact daily discretization of stationary
continuous-time OU dynamics. State is never reset at calendar-month or
calendar-year boundaries. Months and years are used only to aggregate the
loss and the inherited selector. The 16-year window is long enough to expose
annual dispersion and 15 adjacent annual pairs without turning the latent
process into a calendar-indexed state model.

The added annual objective replaces the inherited annual location and
dispersion blocks with the exact four equal-weight selector families. Annual
location contains precipitation mean and q95 plus tmax and tmin means;
dispersion contains the three annual standard deviations; lag contains the
three member-wise lag-1 correlations; and complete cross-field dependence
contains all three member-wise annual correlations. Precipitation statistics
use `|log(g+0.1)-log(o+0.1)|/0.25`, temperature means use raw degrees C,
temperature standard deviations use `/0.5`, and correlations use `/0.1`
(squared residuals in training, absolute residuals at validation). The monthly
families remain active. Conditional-member daily NLL and paired daily-pattern
loss remain zero-weight diagnostics.

The shared-state arm dedicates the first of the same four slow OU factors to
one explicit rank-one climate coordinate and retains the other three as
flexible slow factors. It does not add a fifth state. The dedicated coordinate
is applied jointly to the generator's precipitation-occurrence,
positive-amount-location, temperature-mean-location, and log-DTR-location
heads through one smooth scalar loading and a four-field vector. Its OU
innovations and all inherited common parameters are matched exactly to the
base arm; the only added parameter is the four-element rank-one field vector.

## Firewalls

- Development roles only; confirmation remains sealed.
- Solar is not opened or fitted. The downstream solar design remains a
  procedural latitude/day-of-year envelope plus stochastic cloud/clearness
  residual coupled to generated precipitation and temperature.
- No temporal threshold, bootstrap seed, comparator, site, generation member,
  or protected role changes.
- No GPU job is authorized by the scaffold alone. Execution requires published
  source, fresh package authority, admission materialization before every
  submit, and the large-evidence profile.

## Resources

One 30-minute control role precedes two concurrent 240-minute L40 candidate
roles. Five recovery minutes remain reserved. The fresh ceiling is 515 GPU
minutes, with one attempt per role and no retry. Three training seeds execute
serially inside each candidate role; the two candidate roles execute in
parallel after the control and serialized bootstrap are authenticated.

## Gates and exit

Calendar/missingness preflight follows `SPEC-A10-CORPUS` before resource
reservation and pins 13 eligible origins, each with a 5,844-row 16-year
normalized Gregorian axis and 5,840 source-observed core rows. Every year has
365 observations; leap-year February 29 is observed and December 31 is the
single inserted null row. Package tests exercise leap/window boundaries, exact
continuous recurrence, annual loss coverage, matched initialization, shared
state coupling, frozen inheritance, firewalls, and execution-plan shape.

The exact A10M5R12 selector and thresholds decide eligibility. At least one
eligible arm yields `A10M5R13-TEMPORAL-READY`; no eligible arm yields
`HOLD-A10M5R13-NO-TEMPORALLY-ELIGIBLE-CANDIDATE`. Passing candidates require
the already-ratified random-origin rolling-window sensitivity successor before
promotion.
