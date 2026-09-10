# SPEC-A11-THERMAL-MEAN-REGRESSION-ATTRIBUTION

Status: research-only revision 1

Owning work package:
`docs/work-packages/20260910-a11e9-thermal-mean-regression-attribution/`

## Purpose and boundary

A11E9 attributes A11E8's monthly-temperature mean regression without adding
model factors or selector behavior. It uses the same development observations,
stations, burns, loadings, seeds, faithful QC, and temperature-only overlay.
Confirmation and production remain unauthorized.

## Frozen arms

Each of the 640 A11E8 identities is scored as faithful plus four diagnostics:

1. `raw_rendered`: the exact A11E8 integer-tenths overlay.
2. `centered_rendered`: subtract the chronological binary64 mean from the 16
   annual states before integer-tenths rounding.
3. `centered_balanced_rendered`: start from centered unrounded deltas, round
   ties-to-even, then make each month's 16 integer deltas sum exactly to zero.
   Unit adjustments minimize absolute error from the unrounded tenths; ties use
   chronological year order. Repeat until the sum is zero.
4. `centered_unquantized`: add the centered binary64 monthly delta directly to
   parsed monthly mean-temperature aggregates. This arm is diagnostic only and
   never emits a climate file.

Rendered arms add the same delta to Tmax, Tmin, and dewpoint and preserve all
other bytes and both rendered temperature differences exactly. Nonfinite data,
overflow, incomplete calendars, or identity drift fail closed.

## Data and preflight

Observed Daymet uses `daymet_official_365_v1` and
`daymet_mask_normalized_month_v1` under SPEC-A10-CORPUS. Execution pins 20
development objects, 5,844 normalized axis rows, 5,840 observed rows, and the
four masked dates per object. A11E8's evidence, decision, manifest, contract,
and loading bundle are hash-bound inputs.

## Decision

For each arm, compute the six A11E8 temperature metrics and median arm/faithful
ratios over 640 records. A viable remedy requires annual-temperature dispersion
error at most `0.90`, every other temperature metric at most `1.05`, at least
one third of paired annual-dispersion errors improved, and no station median
annual-error ratio above `1.25`.

The disposition is:

- `CENTERING_REMEDY_SUPPORTED` when `centered_balanced_rendered` passes;
- `QUANTIZATION_BLOCKS_CENTERING_REMEDY` when only
  `centered_unquantized` passes;
- `RANK_ONE_THERMAL_FORMULATION_REJECTED` otherwise.

Raw and centered rendered arms are attribution surfaces, not selectable model
alternatives. No outcome authorizes confirmation or production.

## Replay and provenance

The first exact-source execution generates the 640 faithful streams and writes
an authenticated compact input bundle containing parsed monthly matrices,
loadings, and states. Independent replay re-runs all arm construction, scoring,
and decisions from that bundle under the same pinned runtime. Evidence,
decision, and preflight must be byte-identical. The bundle exists to avoid a
second redundant CLIGEN generation; its complete source and binary lineage is
bound by SHA-256.
