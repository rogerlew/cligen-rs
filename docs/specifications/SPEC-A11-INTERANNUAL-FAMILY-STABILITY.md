# SPEC-A11-INTERANNUAL-FAMILY-STABILITY

Status: research-only revision 1

## Purpose

This specification compares the two registered A11E annual/monthly stochastic
laws over repeated development members while holding the nearest-candidate
forcing adapter and conditional daily core fixed. It answers whether the
circular fixed-block law improves the full evaluated interannual family, not
merely monthly climatological levels.

No result from this specification authorizes confirmation, production, a
public generation profile, or automatic routing.

## Frozen arms and evidence

The control is `gaussian_latent_ar1_physical_core_v1`; the treatment is
`circular_fixed_block_physical_core_v1`. Both use the A11E2 frozen
nearest-candidate location for each of the 20 development stations, the A11E1
candidate-fit models, years 2010--2025, and member identifiers 0--7. Strategy
domains are independently deterministic; member identifiers are paired, but
the two different laws are not claimed to consume identical random draws.

The canonical A10 calendar transform and mask-normalized observed arrays are
revalidated before generation. Confirmation access is false.

## Interannual metric family

All metrics are errors for which smaller is better:

1. mean across-month absolute log variance-ratio error for precipitation;
2. mean across-month absolute log variance-ratio error for temperature;
3. annual precipitation absolute log variance-ratio error;
4. annual temperature absolute log variance-ratio error;
5. precipitation cross-month correlation RMSE over the 66 off-diagonal pairs;
6. temperature cross-month correlation RMSE over the same pairs;
7. annual precipitation lag-one correlation absolute error;
8. annual temperature lag-one correlation absolute error;
9. annual precipitation period-at-least-four-year power-fraction absolute error;
10. annual temperature period-at-least-four-year power-fraction absolute error.

Variance floors are `1e-12`. Undefined correlations from a constant series are
represented by zero using the inherited safe-correlation rule. Low-frequency
power excludes the zero-frequency component and returns zero for zero total
nonzero-frequency power. The station/member family score is the arithmetic mean
of the ten errors. These are deliberately compact 16-year development
diagnostics, not asymptotic climate claims.

## Frozen decision

For each of the 160 station/member pairs, treatment is materially improved when
its family score is at most 95% of control, materially worse when it exceeds
105% of control, and neutral otherwise. For each metric, aggregate
noninferiority requires the treatment median over all 160 pairs to be at most
105% of the control median.

- `VIABLE_AS_UNIVERSAL_EXPLORATION`: at least one third of pairs materially
  improve, no pair materially worsens, and every metric is aggregate-noninferior.
- `MIXED_REQUIRES_ROUTING`: at least one third materially improve and every
  metric is aggregate-noninferior, but one or more pairs materially worsen.
- `NOT_VIABLE_ON_FROZEN_CRITERION`: either the one-third benefit threshold or
  any aggregate noninferiority condition fails.

The exact counts and station/member classifications are always reported. A
mixed result motivates only a separately prospective routing study; target
outcomes cannot be used to choose an arm in this package.

## Integrity and replay

The exact 20 by 8 by 2 grid, finite metrics, zero daily invariant failures,
published source identity, authenticated dependencies, sealed confirmation,
and byte-identical scientific-output replay are mandatory. Integrity failure
is a HOLD rather than a scientific disposition.
