# A5d1 Development-Library Selector Feasibility Report

Decision: `HOLD`
Terminal status: `EXECUTED-HOLD-PATH-INFEASIBILITY`
Evidence class: exposed development evidence only

## Abstract

A5d1 tested whether complete years drawn without physical modification from
faithful CLIGEN libraries could correct the interannual variance and dependence
deficits identified by A5b. Seventeen exposed stations each received one
deterministic 256-year `faithful_5_32_3 + qc_filter: off` library. Constrained
nonnegative weights were fitted at nested 128- and 256-year pools, followed by
three bounded 100-year path constructors at three fixed seeds. The corrected
v3 marginal solver passed all 17 stations at 256 years and reduced normalized
annual raw-moment distance to 10.2–85.3% of the uniform baseline (median
47.4%). However, none of the three path algorithms passed all 51 station-seed
cells. At the eligible 256-year pool only 24/153 algorithm cells passed; 128
failed the frozen cross-boundary guard and 10 failed component-level dependence
noninferiority. Calendar, reuse/cooldown, exact 30-year prefix, physical-row
identity, and zero-intervention invariants all passed. A5d1 therefore closes on
`EXECUTED-HOLD-PATH-INFEASIBILITY`. The next experiment should diagnose and
then prospectively test a boundary-aware finite-path objective using the now-
feasible frozen marginal-weight construction.

## 1. Question and scope

The experiment asked two deliberately separate questions:

1. Can stationary nonnegative complete-block weights improve the full annual
   precipitation/temperature marginal vector while preserving the accepted
   monthly surface and unparameterized faithful-off daily/storm structure?
2. Can a finite calendar-compatible path realize the required 30- and
   100-year dependence while preserving reuse, boundary, prefix, and exact
   physical-row invariants?

A pass required one common pool and one common algorithm to pass all 17
stations and every preregistered path seed. Station-specific fitted weights and
paths were permitted outputs of that common rule. The work did not inspect a
confirmation object, run WEPP, mutate a daily physical value, change faithful
generation, or create a public candidate/profile identifier.

## 2. Hypotheses and decision rules

The marginal feasibility hypothesis was that a bounded convex reallocation of
complete faithful years could reduce aggregate normalized L1 distance to six
Daymet annual raw-moment targets by at least 5%, with no component worse than
the uniform baseline and with all preservation inequalities satisfied.

The path feasibility hypothesis was that at least one of three fixed
alternatives—guarded replacement, weighted permutation/depletion, or
state-persistent different-block selection—could pass every station and all
three seeds at one globally selected nested pool. Every path had to improve
aggregate dependence distance by at least 5%, preserve component-level
noninferiority, and remain within 0.04 of the chronological faithful reference
for the registered cross-boundary wet/dry-continuity statistic.

Failure of the marginal hypothesis at every pool would be a structural-
infeasibility hold. Marginal success without a globally passing path would be
a path-infeasibility hold. Smaller pools were allowed to fail; no per-station
pool, algorithm, or seed selection was allowed.

## 3. Inputs and prospective freeze

The controlling v3 freeze is
`61e557154cd3e4e4b6ee31b068c0e7b61e9df04d2880d7cd25d27dd2e83d45fc`.
It binds 17 A5a station identities, their accepted `.par` hashes, exposed
Daymet 1980–2009 fit records, A5b Fourier/EOF identities, the release Rust
binary, contract/schema/tool hashes, two nested pools, one burn-0 library
realization, three algorithms, and three seeds. Its matrix contains exactly
306 unique cells (17 × 2 × 1 × 3 × 3).

The first freeze was amended before feature or solver results because output
pathnames are embedded in CLI headers; repeat runs must use the same canonical
pathname for whole-file identity. A complete v2 execution was later invalidated
when phase-I replay found a denominator implementation defect: rare-month
uniform bin/descriptor sums were divided by `max(mean_wet_days, 1)` instead of
their actual positive wet-day denominator. Amendment 002 corrected only that
formula and failed closed on a zero denominator. It did not change any target,
tolerance, algorithm, seed, pool, objective, or selection rule. The invalidated
v2 identities and rationale are retained separately and excluded here.

## 4. Methods

### 4.1 Library regeneration and features

The accepted release Rust generator produced one 256-year continuous library
per station with burn 0, interpolation off, the faithful profile, and QC off.
Each station was generated twice to one canonical output pathname; all 17
whole CLI files were byte-identical on repeat. The retained libraries total
112,875,835 bytes. Daily rows were parsed into complete 365-/366-day blocks.

Monthly sufficient statistics included day and wet-day counts; precipitation,
Tmax, and Tmin first/second raw sums; wet transitions; four precipitation
amount bins; three daily cross-products; wet-day duration, time-to-peak, and
peak-ratio moments; and temperature-ordering violations. Annual statistics
contained precipitation total, mean Tmax/Tmin, their raw second moments, and
their three raw cross moments. Boundary state retained first- and last-day
wetness. No Fourier/EOF coefficient or selector altered a physical value.

### 4.2 Marginal feasibility

SciPy 1.13.1 HiGHS solved binary64 linear programs with weights summing to one,
weights in `[0, 0.05]`, and independent primal residual replay. Fitted monthly
targets came from the accepted station surface; unparameterized bins,
cross-products, descriptors, and boundary references came from uniform
faithful-off pools; annual improvement targets came from detrended exposed
Daymet fit-period variation. A second bounded solve supplied deterministic
index-weighted tie resolution within `1e-9` of the primary optimum.

### 4.3 Finite paths

For each frozen cell the constructor built one 100-year path, then defined the
30-year result as its exact prefix. Destination and source years had to share
Gregorian 365-/366-day class. Exact source blocks could appear at most twice
and not within a five-year cooldown. Each initial path received 1,500
same-calendar-class local-swap attempts minimizing the registered dependence
distance. The six dependence components at each horizon were lag-one Pearson
correlation and period-at-least-four-year power fraction for annual
precipitation, Tmax, and Tmin.

Physical evidence was rendered by concatenating the unchanged source payload
tokens. The independently rendered 30-year payload hash had to equal the first
30 years of the 100-year payload hash plan. Dates/index bookkeeping were kept
separate from physical tokens.

## 5. Results

### 5.1 Marginal weights

| Pool | Passing stations | Global marginal pass |
|---:|---:|:---:|
| 128 | 13/17 | no |
| 256 | 17/17 | **yes** |

The four 128-year failures were component-noninferiority failures, not solver
ambiguity. At 256 years, all 17 primal certificates passed independent
residual, normalization, nonnegativity, maximum-weight, component-
noninferiority, and strict-improvement replay. Effective inverse-Simpson
support was at least 23.95 years and the largest fitted weight was the frozen
0.05 cap. The median annual aggregate-distance ratio was 0.474; the range was
0.102–0.853. This is a clear feasibility result for variance reallocation at
the larger pool, not an independent performance estimate.

### 5.2 Finite paths

| Pool | Algorithm | Passing station-seed cells | Global path pass |
|---:|---|---:|:---:|
| 128 | `guarded_replacement` | 17/51 | no |
| 128 | `weighted_permutation` | 15/51 | no |
| 128 | `state_persistent_different_block` | 12/51 | no |
| 256 | `guarded_replacement` | 6/51 | no |
| 256 | `weighted_permutation` | 13/51 | no |
| 256 | `state_persistent_different_block` | 5/51 | no |

At the globally marginal-feasible 256-year pool, 24/153 path cells passed.
Every cell met aggregate strict improvement, but 10 violated at least one
dependence component's noninferiority rule. The dominant failure was the
cross-boundary guard: 128/153 cells exceeded its absolute tolerance. Even the
best alternative, weighted permutation, passed only 13/51 cells; 38 of its 51
cells failed the boundary guard, two failed component dependence
noninferiority, and only nine stations had any passing seed. Because every
registered seed must pass, isolated passing station/seed outcomes cannot be
selected.

Across all 306 cells there were no calendar, reuse/cooldown, common-prefix, or
physical-payload failures and zero physical-value interventions. Thus the hold
is localized to finite-path climate constraints, not block integrity or
calendar mechanics.

### 5.3 Resource observations

Duplicate library generation consumed 6.31 summed station-seconds (maximum
0.39 seconds per station); feature construction took 5.76 seconds; 34 marginal
solves consumed 3.67 summed solve-seconds (maximum 0.27 seconds); and the path
matrix took 61.88 seconds (maximum 0.23 seconds per cell). A complete semantic
replay produced the same runtime-stripped path fingerprint and used a maximum
resident set of 306,741,248 bytes. The target workspace occupied approximately
195 MB. These observations are below the 1 GiB storage and 2 GiB memory
ceilings. No bounded selector exhausted its calendar or reuse domain.

## 6. Interpretation and limitations

The result separates marginal feasibility from path feasibility exactly as
intended. Complete-year reweighting has enough support at 256 years to move
the registered annual dispersion/covariance vector substantially toward
Daymet without modifying daily rows. Finite ordering remains unresolved.

The present local-swap objective optimized lag/low-frequency distance but did
not explicitly optimize the registered cross-boundary wet/dry-continuity
residual. The high boundary-failure rate is therefore actionable evidence
about the path objective, not evidence that exact-block selection is generally
impossible. It would be equally premature to relax the boundary tolerance or
declare success from the 24 passing cells: the global all-station/all-seed rule
was prospective and remains binding.

This is development evidence from the same exposed 17 stations used to form
the targets. It does not estimate generalization, null false-failure,
bootstrap availability, or WEPP response. A5d2, A5d3, and A5d4 remain
mandatory; A5d5 remains unauthorized.

## 7. Conclusion and corrective action

The marginal feasibility hypothesis passes at the 256-year pool. The finite-
path hypothesis fails for every registered algorithm, so A5d1 closes as
`EXECUTED-HOLD-PATH-INFEASIBILITY` with no selected research contract.

The first corrective action is an A5d1b diagnostic package that holds the v3
marginal weights fixed and determines whether boundary-aware swaps or
construction can satisfy the existing boundary and dependence rules without
altering physical blocks. Only after that diagnosis should a new path
algorithm be prospectively specified. No confirmation work or public profile
work is authorized by this result.

## References

1. [A5d1 package](../package.md), development-library selector-feasibility
   contract and exit rules.
2. [Selector feasibility contract](selector-feasibility-contract-v1.json),
   version 1.
3. [ADR-0002](../../../decisions/0002-quality-metrics-authority.md), observed
   climate and fitted monthly-surface authority.
4. [ADR-0004](../../../decisions/0004-a5b-interannual-no-promotion.md), A5b
   non-promotion and successor-study requirements.
5. [A5d0 feasibility analysis](../../20260714-a5d0-successor-feasibility-calibration/artifacts/feasibility-analysis.md),
   successor-family analytic basis.
6. Thornton, M. M., et al. (2022). *Daymet: Daily Surface Weather Data on a
   1-km Grid for North America, Version 4 R1*. ORNL DAAC.
   https://doi.org/10.3334/ORNLDAAC/2129.

## Evidence identities

- v3 pre-solver freeze:
  `61e557154cd3e4e4b6ee31b068c0e7b61e9df04d2880d7cd25d27dd2e83d45fc`
- Aggregate result: `8d2260da45e06b62a3b54b18ebe974812e73d326e42558c1f92d0f7b7468d481`
- Reproducible target path matrix:
  `16da995e1808d84988d514f034aa3c83042435ce64993d5cf684b504dc6fa74e`
