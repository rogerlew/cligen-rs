# SPEC-A11-DETERMINISTIC-COHORT-JOINT-FOUNDATION

Status: research-only revision 1

Owning work package:
`docs/work-packages/20260904-a11e8-deterministic-cohort-joint-foundation/`

## Purpose and boundary

A11E8 establishes the first nested component of a deliberately simple joint
residual model around faithful CLIGEN and evaluates a deterministic
generate-score-select cohort routine. The retained-model question and the
runtime-selection question are separate: an unselected candidate cohort must
beat faithful before selection can make the component retainable.

This is an exposed-development feasibility experiment. It does not add a
public generation profile, runspec field, CLI command, default, or production
claim. Confirmation remains sealed.

## Evidence inherited

A11E7 established that removing faithful temperature QC raises median annual
temperature variance by 29.4%, but the result still has only 10.2% of observed
variance. A11E8 therefore retains faithful QC and adds missing year-scale
state instead of treating QC-off as the foundation.

A5e0/A5f0 retired the exact `a5e0_direct_annual_state_v1` mechanism because a
single state coupled precipitation occurrence, precipitation amount, Tmax,
and Tmin and damaged cross-month dependence. A11E8 does not revive that
mechanism: it changes only a twelve-month mean-air-temperature residual,
leaves precipitation untouched, and measures cross-month dependence as an
explicit noninferiority surface.

## Frozen models and data

The operational control is `faithful_5_32_3` with `qc_filter: faithful`. The
research candidate is `a11_joint_residual_thermal_rank1_v1`. Both use the
exact A11E7 twenty-station roster, source `.par` identities, sixteen-year
horizon, and thirty-two burns.

The thirty-two burns form four ordered cohorts of eight as recorded in
`execution-manifest-v1.json`. Each station therefore has 32 faithful base
streams, 32 derived thermal candidates, four mixed-model selections, and four
faithful-only selected comparators. One execution contains 640 CLIGEN runs,
640 deterministic derived candidates, 1,280 scored records, and 80 selections.

Observed Daymet development data use the `daymet_official_365_v1` source
transform and `daymet_mask_normalized_month_v1` statistic from
SPEC-A10-CORPUS. A complete calendar/missingness preflight is mandatory before
generation. The selector target is the authenticated development target and
is therefore an oracle research input, not a deployable default.

## Rank-one thermal residual

For each station, construct sixteen-by-twelve observed monthly mean-air
temperature matrix `O`. For each faithful burn `b`, construct the matching
matrix `G_b`. All covariance matrices use sample denominator fifteen and
chronological binary64 accumulation.

Define

`R = symmetric(Cov(O) - mean_b(Cov(G_b)))`.

Use `numpy.linalg.eigh` under the pinned Python, NumPy, operating-system,
machine, and single-threaded linear-algebra runtime. Select the largest
eigenpair. More than one positive eigenvalue within
`1e-12 * max(1, abs(lambda_max))` of the maximum is an ambiguous fit and fails
closed. Orient the unique vector so its sum is positive; if the sum is exactly
zero, orient its lowest-index nonzero component positive. When
`lambda_max <= 0`, the eigenvector and loading are exactly zero. Otherwise the
twelve Celsius loadings are

`loading = sqrt(lambda_max) * eigenvector`.

There is no multiplier, cap, second factor, refit after candidate output, or
outcome-driven routing.

For candidate year `y` and month `m`, compute

`delta[y,m] = loading[m] * z[y]`

and round `10 * delta[y,m]` to an integer with the score contract's
ties-to-even rule. Add that same integer-tenths Celsius delta to every parsed
daily Tmax, Tmin, and dewpoint value after faithful generation and before
final candidate serialization. This preserves the two rendered temperature
differences exactly. Precipitation,
duration, peak timing/intensity, radiation, wind, dates, and wet/dry state are
byte-identical to the paired faithful daily rows. Nonfinite values, ordering
failure, or fixed-width overflow fail the candidate closed.

## Deterministic state and cohort identity

The annual-state generator is `splitmix64_box_muller_v1`, inherited only as a
versioned deterministic algorithm from A5e0. A11E8 uses the new ASCII domain
including its terminal NUL:

`cligen-rs/a11e8/thermal-state-v1\0`.

The SHA-256 seed preimage is, in exact order:

1. domain bytes;
2. ASCII station ID and one NUL;
3. ASCII model ID and one NUL;
4. cohort root seed as unsigned 64-bit big-endian bytes; and
5. candidate index as unsigned 32-bit big-endian bytes.

Digest bytes zero through seven, interpreted unsigned big-endian, initialize
SplitMix64. Each annual normal consumes two consecutive open-interval
uniforms `((u64 >> 11) + 0.5) / 2^53`, returns the cosine Box-Muller value,
and discards the sine mate. Sixteen years consume exactly sixteen normals.
The state never reads or advances CLIGEN's `k1` through `k10`.

Candidate identities and seeds are assigned before work begins. Parallel
execution may finish in any order, but records are sorted by cohort, model
ordinal, and candidate index before scoring. No shared RNG, clock, host name,
process ID, directory enumeration order, or thread completion order enters a
scientific value.

## Deterministic scoring and selection

All score inputs are finite nonnegative binary64 metrics. Convert each to an
integer score with exact round-to-nearest, ties-to-even of
`metric * 1_000_000_000`. Overflow and nonfinite input fail closed.

For each station/cohort, sort the eight faithful integer monthly-temperature
mean-error scores, average the two middle integers exactly, multiply that
rational value by `1.05`, and round to an integer with the same ties-to-even
rule. An otherwise valid record is eligible when its integer monthly-mean
error is at most that threshold.

Select the lexicographic minimum among eligible faithful and thermal records:

1. annual-temperature dispersion error;
2. temperature cross-month correlation RMSE;
3. annual-temperature lag-one error;
4. annual-temperature low-frequency error;
5. model ordinal (`faithful` is zero, thermal is one); and
6. candidate index.

The faithful-only comparator applies the identical rule to the eight faithful
records. Because faithful members define the eligibility threshold, an
eligible record always exists. Duplicate identities, missing metrics, invalid
model ordinals, or incomplete cohorts fail closed.

The selector is invariant to candidate input order. Increasing cohort size,
changing model order, quantization, metric order, eligibility, or tie-breaking
creates a new selector version.

## Decision rules

Component retention is decided from all unselected paired records, never from
the selected winners. The thermal component passes when:

- median annual-temperature dispersion error is at most 0.90 of faithful;
- monthly-temperature mean error and each of monthly dispersion, cross-month
  correlation, annual lag-one, and annual low-frequency errors are at most
  1.05 of faithful;
- at least one third of paired records have lower annual-temperature
  dispersion error; and
- no station's median annual-temperature error ratio exceeds 1.25.

The deterministic selector is useful when, across the 80 station/cohort
cells, its median annual-temperature dispersion error is at most 0.95 of the
faithful-only selector, every one of the ten A11E5 interannual metrics plus
monthly-temperature mean absolute error is noninferior at 1.05, and at least
one third of selections choose the thermal model.

The terminal disposition is one of:

- `THERMAL_COMPONENT_RETAINED_SELECTOR_USEFUL`;
- `THERMAL_COMPONENT_RETAINED_SELECTOR_NOT_USEFUL`; or
- `THERMAL_COMPONENT_REJECTED`.

Integrity failure produces an exact HOLD rather than a scientific
disposition. Selection cannot rescue a rejected component. None of these
outcomes authorizes confirmation, production, public CLI integration, or a
default change.

## Provenance and replay

The execution receipt binds the source commit/tree, Rust toolchain and build
command, CLIGEN binary, Cargo inputs, station database, every source `.par`, observed target, thermal
loading bundle, cohort manifest, selector contract, faithful `.cli`, derived
candidate, metric record, and selected output with SHA-256. Every selected
record names its complete integer score tuple and deterministic tie-break.

The canonical ordered cohort manifest authenticates all candidates, not only
the winners. Independent execution must reproduce the loading bundle, latent
states, score records, selections, decision, and scientific evidence
byte-for-byte under the same frozen runtime and architecture. Operational
elapsed time is excluded from scientific replay.
