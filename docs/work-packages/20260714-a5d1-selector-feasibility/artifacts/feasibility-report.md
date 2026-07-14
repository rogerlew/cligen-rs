# A5d1 Development-Library Selector Feasibility Report

Report ID: `a5d1-selector-feasibility`
Status: `ACCEPTED`
Date: 2026-07-14
Revision: 1
Authors: Codex lead; independent accuracy, scientific-validity, and consistency reviewers
Evidence mode: Mixed
Experiment record: [A5d1 work package](../package.md)
Evidence snapshot: [detailed-evidence manifest](detailed-evidence-manifest-v1.json)
Review record: [consolidated review](review.md)

## Abstract

A5d1 tested whether complete-year blocks from unchanged CLIGEN output can be
reweighted and ordered to improve interannual precipitation and temperature
structure without changing any daily physical payload. The controlling v6
experiment was frozen after four disclosed, invalidated development attempts
and before its own outcomes were opened (E01, E02). At the 256-year pool,
stationary constrained weights passed the amended marginal contract at all
17 exposed development stations and reduced normalized centered annual
variance/covariance distance to 0.352–0.817 of the uniform-library distance
(median 0.611). The smaller 128-year pool passed at 13/17 stations (E05, E07).
None of 306 station × pool × algorithm × seed paths passed the complete finite
contract. At the eligible 256-year pool, 151/153 cells first failed empirical
30-/100-year marginal realization and the remaining two first failed
dependence noninferiority (E06, E09). All 306 paths preserved exact physical
rows and the 30-year physical prefix (E08). The result is therefore
`EXECUTED-HOLD-PATH-INFEASIBILITY`: the stationary selector is feasible, but
the three registered bounded path algorithms do not reliably realize it at
finite horizons. This is not evidence that all complete-block selectors are
impossible, and it authorizes neither a candidate nor confirmation work
(E10).

## Introduction

The rejected A5b multiplier candidates showed that changing annual state can
improve some low-frequency quantities while damaging the fitted monthly and
daily climate surface. A5d0 consequently required a constructive selector
test: retain complete faithful-output years and alter only which year supplies
each destination year. Under that mechanism, all precipitation, temperature,
radiation, wind, dewpoint, and storm fields remain source-block values.

A5d1 separates stationary feasibility from finite realization. The stationary
question asks whether a common constrained-weight rule can move annual
centered variance and covariance toward exposed Daymet development targets.
The path question asks whether bounded algorithms can realize those weights,
dependence targets, calendar classes, reuse limits, and cross-year behavior in
one 100-year sequence whose first 30 years are the reported 30-year sequence.
Both questions must pass for structural feasibility (E01).

Daymet V4 R1 supplied the exposed 1980–2009 annual development series under
the accepted A5a/A5b data contract; it is not an untouched confirmation source
(R01). A5d1 accessed no confirmation object, target score, or WEPP response
(E11).

## Hypotheses

All hypotheses are amended development hypotheses. Their v6 forms were frozen
prospectively, but earlier development outcomes had already been inspected and
invalidated. They are not confirmatory.

| ID | Scope and decision rule | Provenance | Outcome | Result |
|---|---|---|---|---|
| H1 | One global pool rule yields stationary weights passing every preservation, exact-mean, centered-component noninferiority, and ≥5% aggregate-improvement rule at all 17 stations. | Amended before v6 outcomes; prior v2–v5 outcomes disclosed in E02. | Supported for pool 256; not for pool 128. | Marginal results |
| H2 | At least one registered pool/algorithm combination passes every seed at all 17 stations at 30 and 100 years. | Amended before v6 outcomes. | Not supported; 0/306 complete cells passed. | Finite-path results |
| H3 | Selected paths preserve calendar/reuse rules, select no zero-weight block, introduce no physical intervention, and reproduce the separately rendered 30-year physical prefix exactly. | Amended before v6 outcomes. | Supported; every listed invariant passed 306/306. | Invariants and physical identity |
| H4 | Structural feasibility is declared only if H1 and H2 both hold under one global contract; otherwise issue the narrowest registered hold. | Retrospective mapping of the frozen selection rule. | `HOLD-PATH-INFEASIBILITY`. | Decision |

## Methods

### Study identity

| Fact | Value |
|---|---|
| Source commit | `f676a8e6ab09f4e399b27afe57bcd30938bb592f` |
| Controlling freeze | `dd38484dca7da633ed30854c16074fa66b2a7a7fdd53b05253277125cdd99d22` |
| Stations | 17 exposed A5a/A5b development stations |
| Observed fit period | Daymet 1980–2009 |
| Generator | `faithful_5_32_3`, `qc_filter: off`, continuous mode, burn 0 |
| Canonical library | 256 complete years per station; nested pools 128 and 256 |
| Library realizations | One (`canonical-burn-0`), not an independent replicate |
| Algorithms | Guarded replacement, weighted permutation/depletion, state-persistent different-block selection |
| Path seeds | 104729, 130363, 155921 |
| Horizons | 30 and 100 years; 30 is the exact prefix of 100 |
| Matrix | 17 × 2 × 1 × 3 × 3 = 306 unique cells |
| Confirmation exposure | Zero |

### Evidence freeze and chronology

The source binary, authorities, 17 station parameter files, Daymet inputs,
Fourier/EOF development identities, tools, dependency versions, strict
contract/schema, fixtures, matrix, and resource ceilings were hash-locked
(E01, E02). V1 was superseded before solver outcomes because duplicate output
paths contaminated whole-file repeat comparison. V2 was invalidated for an
incorrect uniform-reference denominator; v3 for centered-target, detrending,
finite-prefix, boundary, and render defects; v4 for omitting realized January
1 transitions from the fitted monthly replay; and partial v5 for applying an
overrestrictive boundary-subset probability rather than the accepted aggregate
January statistic. V5 stopped after 65/306 detailed paths and issued no matrix,
aggregate, or decision. V6 combined within-block January counts with actual
December 31→January 1 pairs and was frozen before any v6 outcome (E02, E12).

### Library and features

For each station, the release Rust binary generated a continuous 256-year
faithful-off library twice using the same canonical output path. Climate,
quality, and provenance bytes matched between repeats. Complete years were
partitioned without modifying their daily physical suffixes; retained
libraries totaled 112,875,835 bytes outside ordinary Git (E03).

Each block supplied monthly counts and raw sums for precipitation occurrence,
amount bins, temperature, daily cross-products, and storm duration,
time-to-peak, and peak-ratio descriptors, plus annual precipitation and mean
temperatures. Annual Daymet precipitation, Tmax, and Tmin series were linearly
detrended before centered variances/covariances were calculated (E04).

### Stationary marginal solver

Thirty-four binary64 HiGHS linear programs covered 17 stations × two nested
pools. Weights were nonnegative, summed to one, were capped at 0.01, and
assigned exactly 0.24 mass to leap-class blocks. Annual precipitation, Tmax,
and Tmin means were fixed to their uniform-pool means. The objective minimized
normalized L1 distance to six centered detrended-Daymet variance/covariance
targets. Every component had to be no worse than the uniform library within
the numerical guard, and aggregate distance had to be at most 0.95 of the
uniform distance. Monthly fitted-surface and unparameterized daily/storm
preservation inequalities remained hard constraints. A second bounded solve
provided deterministic index-weighted tie resolution (E01, E05, E07).

Unordered stationary weights do not define which block precedes another.
Their transition constraints therefore cover within-block pairs attributed to
the destination month. Finite paths own realized cross-block pairs. At each
horizon, the path replay adds actual January 1 numerators and denominators to
within-block January counts and tests the aggregate January `P(W|D)` and
`P(W|W)` against the fitted surface. Boundary-only ratios are retained as
diagnostics. A separate hard vector preserves directional DD, DW, WD, and WW
boundary fractions plus wet/dry spell-continuation contributions against the
chronological faithful-off prefix (E01).

### Finite path construction

Each algorithm built one calendar-compatible 100-year path per station, pool,
and seed. Guarded replacement sampled positive-weight blocks with cooldown and
reuse caps; weighted permutation used a weighted without-replacement order by
calendar class; and state-persistent selection favored a different compatible
block near the current annual state. A deterministic 1,500-iteration swap
search minimized, in order, finite-prefix marginal violation, boundary-vector
violation, and detrended dependence distance. Exact block reuse was capped at
two and cooldown was five years (E01, E06, E07).

Dependence comprised lag-1 correlation and low-frequency spectral fraction for
annual precipitation, Tmax, and Tmin at both horizons. Target, chronological
baseline, and candidate series used the same OLS linear detrend. The exposed
30-year Daymet fit statistic was reused as the target at both generated
horizons; no 100-year observed record was implied. Each component had to be
noninferior to the chronological baseline and aggregate distance had to improve
by at least 5% (E01).

## Analysis

The stationary result was computed independently at each station and pool;
the global selection rule allowed a pool only if all 17 stations passed. The
finite matrix contained all 306 frozen tuples with no missing, duplicate, or
unexpected cell. A path passed only if its stationary marginal certificate,
both finite-prefix replays, dependence rules, directional boundary/spell
vector, calendar, reuse/cooldown, positive-weight selection, physical identity,
and exact prefix all passed (E05, E06, E09).

Failure localization uses the frozen criterion order. Consequently, a first
failure does not imply that later criteria would have passed; diagnostic counts
for later criteria are reported separately. Ratios below use candidate
normalized centered annual distance divided by uniform-library distance.
Counts are exact; ranges are rounded to three decimals only in prose/tables.
No uncertainty interval was used because the seeds are required matrix cells,
not statistical replicates.

Daily render identity was audited separately from the path producer. The audit
reconstructed destination-date rows from source blocks, compared physical
suffix bytes, and compared independently rendered 30- and 100-year segments
(E08).

## Results

### Marginal feasibility

| Pool years | Passing stations | Global marginal pass |
|---:|---:|:---:|
| 128 | 13/17 | no |
| 256 | 17/17 | yes |

At pool 256, the selected weight vectors used 103–118 positive blocks with
inverse-Simpson effective support 101.070–104.804. Maximum weight was exactly
0.01, maximum annual-mean equality residual was `9.1e-13`, and maximum leap-
mass error was `5.6e-17`. Candidate/uniform centered-distance ratios ranged
0.352–0.817 with median 0.611, so every station exceeded the registered 5%
aggregate improvement while passing component noninferiority (E05, E07).

### Complete finite-path decision

| Pool | Algorithm | Passing cells | First-failure distribution |
|---:|---|---:|---|
| 128 | Guarded replacement | 0/51 | 12 stationary; 39 finite-prefix |
| 128 | Weighted permutation | 0/51 | 12 stationary; 36 finite-prefix; 3 boundary |
| 128 | State-persistent different block | 0/51 | 12 stationary; 39 finite-prefix |
| 256 | Guarded replacement | 0/51 | 51 finite-prefix |
| 256 | Weighted permutation | 0/51 | 49 finite-prefix; 2 dependence-noninferior |
| 256 | State-persistent different block | 0/51 | 51 finite-prefix |

Across both pools, first failures were 36 stationary-marginal, 265 finite-
prefix, three boundary-vector, and two dependence-noninferiority failures. At
the globally marginal-feasible 256-year pool, 151/153 cells first failed
finite-prefix realization and two first failed dependence noninferiority.
No registered algorithm/pool combination passed all stations and seeds (E06,
E09).

### Diagnostic decomposition

| Pool | Finite 30 pass | Finite 100 pass | Both finite | January 30 pass | January 100 pass | Boundary pass | Dependence noninferior |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 128 | 10/153 | 10/153 | 4/153 | 146/153 | 143/153 | 23/153 | 69/153 |
| 256 | 7/153 | 8/153 | 2/153 | 144/153 | 150/153 | 4/153 | 63/153 |

The aggregate January correction is therefore not the dominant obstruction:
most paths pass that component, but only six of 306 pass the complete finite-
marginal replay at both horizons. The table also shows why first-failure counts
must not be treated as a full diagnostic vector: boundary and dependence are
evaluated for all paths even when an earlier finite rule fails (E06, E07).

### Invariants and resources

All 306 cells passed calendar and reuse/cooldown rules, selected zero
zero-weight blocks, used no physical-value intervention, passed independent
physical-row suffix comparison at both horizons, and produced an exact
30-year physical prefix. The retained detailed archive contains 34 marginal
certificates and 306 paths in deterministic order (E07, E08).

The v6 path run took 558.81 seconds total; summed per-cell time was 555.28
seconds and the slowest cell took 4.27 seconds. Path-run peak resident memory
was 206,389,248 bytes; the maximum across the first execution stages was
400,883,712 bytes. Retained library storage was 112,875,835 bytes. All were
below the frozen 2 GiB memory, 1 GiB storage, 120-second solver-cell, and
7,200-second total ceilings. These are development-host measurements, not
performance guarantees (E03, E06, E13).

## Limitations and validity

Internal validity is limited by the amendment history. Review found and
invalidated several material defects before terminal closure. V6 is the only
controlling result, and its lock/freeze precede its own outcomes, but the study
is amended development evidence rather than an independent prospective
confirmation. Deterministic replay and numerical reconstruction reduce, but
do not erase, risks from implementation error (E02, E12, E13).

The 5% improvement rule and preservation tolerances are feasibility rules, not
calibrated promotion gates. A finite path can exist outside the three
algorithms or beyond the 1,500-iteration search. Therefore 0/306 rejects only
the exact registered algorithms and bounds; it does not prove mathematical
infeasibility of complete-block selection.

External validity is limited to 17 exposed stations, one burn-0 faithful-off
library realization, two nested pool sizes, and Daymet 1980–2009 development
targets. Seeds are required sensitivity cells, not independent climate
replicates. The same 30-year observed dependence statistic serves both
generated horizons. No untouched confirmation corpus, calibrated null,
independent sensitivity set, future climate, spatial dependence, WEPP response,
or candidate promotion was evaluated.

Construct validity is strongest for exact-block physical preservation and the
registered annual/marginal quantities. It is weaker for the selected
dependence and boundary summaries, which are compact proxies rather than a
complete description of low-frequency climate or storm sequencing. The
stationary transition stage intentionally lacks predecessor coupling; only
realized paths are evaluated on complete January-destination transitions.

## Conclusions

H1 is supported at the 256-year pool: a common constrained-weight rule can
reallocate complete faithful-output years toward the exposed centered annual
target vector at all 17 development stations while retaining the registered
stationary preservation surface. H2 is not supported: none of the three
bounded path algorithms realizes the complete contract across all required
stations and seeds. H3 is supported: all registered calendar, reuse,
positive-weight, physical identity, and prefix invariants pass. The frozen
decision rule nevertheless requires H1 and H2 together and therefore yields
`EXECUTED-HOLD-PATH-INFEASIBILITY` (E09, E10).

The first corrective action is A5d1b: diagnose why empirical 30-/100-year
frequencies fail to realize otherwise feasible 256-year weights, using the
151 finite-prefix first failures as the primary surface and the two dependence
failures as secondary cases. That diagnosis should distinguish unavoidable
finite-sample discreteness from search-objective or construction defects
before another path algorithm is frozen. A5d2 evaluation calibration and A5d3
confirmation-corpus qualification remain independent required packages; A5d4
remains blocked on a structurally feasible selector, and confirmation remains
unauthorized (E10).

## Reproducibility and data availability

The controlling contract, strict schema, lock, freeze, manifests, aggregate
results, machine decision, review, and gates are repository artifacts. The
340 detailed JSON records are retained in `detailed-evidence-v1.tar.gz` under
a package-specific Git LFS rule; its content SHA-256 is
`18c2be90b1d431ca1dd4bf031b274b0413c3363fa0ebf0c01d1580c34cdc73b0`.
The 113 MB reproducible daily libraries remain under ignored `target/` storage
and are not repository data. `git lfs fsck`, archive-member hashes, strict JSON
mutation tests, a retained tolerance-checked semantic path replay, numerical
reconstruction, and repository gates are recorded in E13. The replay changed
no structural field and no numeric field beyond `2e-10`; the maximum absolute
difference across 141,064 comparisons was `3.11e-15`.

Daymet files retain their upstream terms and identities. No copyrighted local
reading copy, credential, absolute operator path, confirmation object, or
public candidate is included.

## References

### Repository evidence

- E01 — [Selector feasibility contract v4](selector-feasibility-contract-v4.json)
  and [strict schema](selector-feasibility-contract-v4.schema.json).
- E02 — [V6 pre-solver freeze](pre-solver-freeze-v6.json) and
  [v6 input lock](evidence-lock-inputs-v6.json).
- E03 — [Development-library manifest](development-library-manifest-v1.json).
- E04 — [Year-feature manifest](year-feature-manifest-v1.json).
- E05 — [Marginal aggregate results](marginal-results-v1.json).
- E06 — [Path aggregate results](path-results-v1.json).
- E07 — [Detailed-evidence manifest](detailed-evidence-manifest-v1.json) for
  the LFS-managed certificate/path archive.
- E08 — [Independent physical-row identity audit](physical-row-identity-audit-v1.json).
- E09 — [Cross-station selector result](selector-feasibility-results-v1.json).
- E10 — [A5d1 machine decision](a5d1-decision-v1.json).
- E11 — [V6 exposure ledger](exposure-ledger-v6.md).
- E12 — [Consolidated review and dispositions](review.md), including the
  retained [v4](invalidated-v4-execution-disposition.md) and
  [v5](invalidated-v5-execution-disposition.md) correction records.
- E13 — [Gate and deterministic-replay results](gate-results.md).

### Governance and external source

- [ADR-0002 — Quality metrics authority](../../../decisions/0002-quality-metrics-authority.md).
- [ADR-0004 — A5b no-promotion decision](../../../decisions/0004-a5b-interannual-no-promotion.md).
- R01 — Thornton, M. M., Shrestha, R., Wei, Y., Thornton, P. E., Kao, S.-C.,
  and Wilson, B. E. (2022). *Daymet: Daily Surface Weather Data on a 1-km
  Grid for North America, Version 4 R1*. ORNL DAAC.
  [DOI 10.3334/ORNLDAAC/2129](https://doi.org/10.3334/ORNLDAAC/2129).
