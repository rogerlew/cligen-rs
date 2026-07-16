# A9c3 two-site grouped observed-development comparison

Report ID: `a9c3-two-site-grouped-observed-comparison`
Status: `ACCEPTED`
Date: 2026-07-15
Revision: 1
Authors: cligen-rs project contributors
Evidence mode: Mixed
Experiment record: [A9c3 work package](../work-packages/20260715-a9c3-two-site-grouped-observed-comparison/package.md)
Evidence snapshot: [report manifest](a9c3-two-site-grouped-observed-comparison-report.manifest.json)
Review record: [consolidated internal review](../work-packages/20260715-a9c3-two-site-grouped-observed-comparison/artifacts/review.md)

## Abstract

A9c3 resumed observed-development comparison of two stochastic climate-
generator classes after replacing A9c's arbitrary hot-arid storm support
floors with an equal-weight estimator over Yuma and Stovepipe Wells. The
amended four-objective estimator was finite for the sites' actual 136 and 97
development events. Eight fresh configurations were fit; four alternating-
renewal and two latent-regime configurations were eligible for screening. A
fresh Rust faithful comparator passed all 160 station/burn engineering checks.
All six candidates then failed the short-screen physical-support invariant.
Every one of 240 configuration/site/burn prefixes had a retained violation
within its first 112 days; examples include negative solar radiation,
negative wind speed, and humidity outside 0--100 percent. No configuration
advanced to 100-year full development or Pareto replay, no candidate was
sealed, and the terminal is `HOLD-A9C3-NO-SELECTABLE-CANDIDATE` [E05] [E06]
[E08] [E09] [E15]. This is a bounded engineering/development hold, not a
rejection of either class or evidence that faithful CLIGEN is superior.

## Introduction

A9c's first observed comparison stopped because two hot-arid USCRN stations
did not meet uncalibrated per-station storm-event floors. A9c2 then found that
the exact confirmation-safe roster still contained only Yuma and Stovepipe
Wells. The operator accepted those two locations as functionally adequate for
research continuation while retaining their spatial limitation and actual
event frequencies [E13].

A9c3 returned to the model question. Before new candidate output, it froze an
equal-station storm estimator, reran candidate-blind uncertainty calibration,
refit both registered classes under a fresh campaign identity, and registered
a staged comparison against faithful CLIGEN [E01] [E02] [E03] [E04]. The
question was whether either class could produce a selectable research
candidate on the exposed six-regime development surface—not whether either
class is universally valid.

Daymet V4 R1 supplied gridded daily precipitation and temperature, while NOAA
USCRN Subhourly01 supplied observed storm and compound-context records [R01]
[R02]. The exact five-minute format and OAP 2.1.1 archive lineage come from
NOAA's lowercase Subhourly01 documentation [R03]; USCRN network context is
described by Diamond et al. [R04]. Product citations provide context, while
the experiment's exact station-period bytes and derived objects are governed
by repository hashes [E11].

## Hypotheses

H1, H3, and H4 were preregistered in the A9c3 design freeze. H2 is the
prospective grouped-storm amendment adopted after A9c2 and before A9c3
candidate output. H3 is only a selector-safety result when zero candidates
reach selection; it is not evidence of candidate adequacy.

| ID | Provenance | Scope and comparison | Decision rule | Outcome | Result |
|---|---|---|---|---|---|
| H1 | preregistered | Fresh fits preserve two actual, distinct candidate classes | Each class has at least one valid fit and the structural audit rejects isomorphism | Supported: four renewal and two latent configurations were fit-valid; structural audit passed | [Results](#fit-and-structural-results) |
| H2 | amended | Equal-weight Yuma/Stovepipe storm estimation is finite without an event-count roster floor | All four grouped estimators are finite and precision/power are reported diagnostically | Supported: all estimators were finite from 136 and 97 development events; 2,000 grouped bootstrap replicates and 14 thresholds were recorded | [Results](#grouped-calibration) |
| H3 | preregistered | Frozen selector returns at most one class after hard-failure, completeness, and degradation filters | Seal zero or one replay candidate | Supported as a selector-safety claim: six short-screen candidates hard-failed, so zero advanced and zero were selected | [Results](#short-screen-terminal) |
| H4 | preregistered | Confirmation targets remain sealed | Zero locked confirmation station-year target-series access | Supported: zero locked confirmation target-series access was recorded | [Results](#confirmation-firewall) |

## Methods

### Study identity

| Fact | Registered value |
|---|---|
| Source commit | a0e24f0866f4536c168bfd809cb957d91e6d8bf3 |
| Candidate classes | 2 |
| Fresh configurations | 8 |
| Fit valid configurations | 6 |
| Daymet development stations | 20 |
| Uscrn development stations | 12 |
| Hot arid grouped stations | 2 |
| Hot arid development events | 136, 97 |
| Grouped station weights | 0.5, 0.5 |
| Grouped bootstrap replicates | 2,000 |
| Family horizon thresholds | 14 |
| Threshold calibration replicates | 7,000 |
| Faithful baseline burns | 8 |
| Faithful baseline runs | 160 |
| Candidate short burns | 2 |
| Candidate short horizon years | 30 |
| Candidate short configurations | 6 |
| Candidate attempt records | 240 |
| Prefix support failures | 240 |
| Parent stream support violations | 609,654 |
| Full development configurations | 0 |
| Pareto replay configurations | 0 |
| Selected configurations | 0 |
| Confirmation target series accessed | false |
| Campaign wall seconds | 2531.4380139559507 |
| Evaluation maximum rss bytes | 2,154,168,320 |
| Terminal | HOLD-A9C3-NO-SELECTABLE-CANDIDATE |

### Observed roles and grouped estimator

The frozen source roles were reused without reacquisition or reassignment.
Daymet V4 R1 / dataset version 4.1 comprised 20 coefficient-fit objects for
1980--2009 and 20 development objects for 2010--2025 under the project's
`daymet_official_365_v1` calendar. USCRN Subhourly01 format 01 / OAP 2.1.1
comprised 12 coefficient-fit objects for 2010--2017 and 12 development objects
for 2018--2024. Daily comparisons used Daymet development; storm comparisons
used USCRN development [E11].

The amended hot-arid estimator retained Yuma's 136 and Stovepipe Wells' 97
development events at their actual within-station frequencies and gave each
station weight 0.5. Complete-record transformed summaries covered storm
duration, time to peak, peak ratio, and joint dependence. For each objective,
the generated and observed equal-weight group vectors were differenced,
divided componentwise by candidate-blind bootstrap scales lower-bounded at
0.02, and reduced by root mean square. The storm-family row used the maximum
of the four objective distances. The amendment explicitly replaced A9c's
site-season support construct and is exploratory with respect to the original
A9a storm hypotheses [E03].

Calibration used 2,000 station-year bootstrap replicates for grouped
precision and sensitivity. Separately, seven families at 30- and 100-year
horizons used 500 candidate-blind paired replicates per cell, producing 7,000
replicate identities and 14 thresholds. Power was descriptive, not a roster
or selection gate [E02] [E05].

### Candidate fitting and comparator

The renewal grid crossed pooling strengths 50/150 with tail quantiles
0.95/0.90. The latent grid crossed three/four states with the two paired
pool/tail settings (50, 0.95) and (150, 0.90). Fit applicability, structural
cross-recovery, and an uncertainty-adjusted monthly Monte Carlo reconciliation
were evaluated before development scoring [E06] [E07]. The reconciliation
records use independent target and heldout draws plus a 3.290527-standard-error
allowance; they are not claims of agreement within 0.5 percent [E15].

The comparator was the Rust `faithful_5_32_3` profile with faithful QC, freshly
built in an isolated release target at the source commit. It ran 20 station
parameters under eight burns for 100 years each. A9c3 did not execute a new
Fortran comparator. Faithful semantics remain governed by the vendored
Fortran source under ADR-0001 [E08] [E14].

### Stages and engineering rules

All six fit-valid configurations entered a short screen using all 20 Daymet
development locations, two burns, 30-year scientific prefixes, all seven
family summaries, and all 31 objective IDs. A candidate with any failed hard
engineering invariant could not advance. Within each class, at most two
hard-failure-free configurations could enter the 100-year, four-burn full
stage; at most one per class could then enter eight-burn Pareto replay before
lexicographic selection [E02] [E04].

The implementation generated nested 100-year streams and correctly computed
short scientific objectives from their 30-year prefixes. It mistakenly
computed the short-stage calendar/support total over each parent 100-year
stream. This outcome-time methods deviation is recorded rather than silently
corrected. Every attempt's first retained violation occurred within its first
112 days, so all 240 frozen 30-year prefixes still fail and the terminal is
unchanged. The 609,654 total is used only as a parent-stream diagnostic [E09]
[E12] [E15].

## Analysis

Grouped-calibration checks separately verified station estimates, pooled
estimates, seasonal diagnostics, either-site-removal sensitivity, and finite
components. The 24 component diagnostics had minimum detectable standardized
shifts from 2.693 to 2.802. This supports finiteness but indicates limited
precision; the calibration was not used to remove either site [E05].

Fit evidence was checked by configuration and class. The two four-state latent
fits were ineligible at `ca042713`; the four renewal and two three-state latent
fits were retained. All eight records report passing monthly reconciliation,
and the cross-fit structural audit reports no factorization bijection or
degenerate intersection [E06] [E07]. Per-month-length reconciliation moments,
standard errors, and tolerances were hashed but not persisted, so independent
numeric audit requires deterministic re-execution [E15].

Each short-screen configuration produced 156 stratum/objective rows spanning
31 unique objective IDs: 95 available, 60 unavailable, and one failed hard
invariant. The hard failure was always `eng_calendar_and_support`; deterministic
replay/prefix and provenance invariants passed in all 240 attempts. Each
configuration also had 19 unavailable mandatory rows and 8--18 material-
degradation family rows. Those are short-stage diagnostics, not final 100-year
selector results [E09].

The retained first-100 violation prefixes contain only solar-support,
humidity-support, and wind-speed-support labels. Because 585,654 of the
609,654 total violations have no retained label and multiple violations may
occur on one row, the analysis makes neither exact field totals nor a unique-
day count. It uses the maximum first-retained index of 111 only to establish
that every 30-year prefix independently contains a support failure [E09]
[E15].

## Results

### Grouped calibration

H2 is supported within its amended construct. All four grouped storm
estimators and all 24 components were finite using the exact 136 Yuma and 97
Stovepipe Wells development events. Eight station-season diagnostic cells
were finite, and no time-to-peak clipping occurred. The candidate firewall
remained closed during calibration [E05]. This result removes A9c's arbitrary
per-station event-count blocker; it does not establish strong precision or
broad hot-arid representativeness.

### Fit and structural results

H1 is supported operationally. All four alternating-renewal configurations
and both three-state latent-regime configurations were fit-valid. Both four-
state latent configurations were ineligible because one Daymet coefficient-
fit station series, `ca042713`, failed fit applicability. Both classes
nevertheless retained valid members and passed the registered structural/
recovery audit. All eight fit records report an uncertainty-adjusted monthly-
reconciliation pass [E06] [E07].

### Faithful baseline

The fresh faithful Rust baseline produced 160 runs, each with 36,524 daily
rows. All 160 passed calendar/support, deterministic byte replay, and
provenance checks. The 160 output hashes were unique across the registered
station/burn identities [E08]. Candidate failures therefore do not invalidate
the comparator baseline.

### Short-screen terminal

All six fit-valid configurations reached the short screen, and none advanced.
The table reports parent 100-year-stream support-violation totals; these are
not 30-year totals. Every configuration represents 40 site/burn streams, all
of whose 30-year prefixes contain at least one retained support violation.
`Mandatory unavailable` and `material degradation` are counts of short-stage
stratum/objective or family rows [E09] [E15].

| Configuration | Class | Parent-stream support violations | Mandatory unavailable | Material degradation |
|---|---|---:|---:|---:|
| renewal-p050-q095 | alternating renewal | 99,705 | 19 | 8 |
| renewal-p150-q095 | alternating renewal | 98,877 | 19 | 12 |
| renewal-p050-q090 | alternating renewal | 99,591 | 19 | 9 |
| renewal-p150-q090 | alternating renewal | 98,901 | 19 | 14 |
| latent-k3-p050-q095 | latent regime | 106,422 | 19 | 17 |
| latent-k3-p150-q090 | latent regime | 106,158 | 19 | 18 |

The hard-failure rule excluded every configuration before full development.
Full-development, Pareto-replay, frontier-item, selected-configuration, and
candidate-freeze counts are all zero. H3 is therefore supported only as the
registered at-most-one selector-safety property; the actual replay selector
received no candidate and made no comparative choice [E09].

The grouped storm result itself was not the stopping mechanism. All six
candidates materially improved the storm-descriptor family in all six strata,
or 36 of 36 screened storm-family rows, relative to the faithful comparator.
That 30-year finding cannot be promoted into a 100-year adequacy claim because
the hard engineering gate correctly stopped the campaign [E09].

### Confirmation firewall

H4 is supported as recorded. Calibration reports no candidate input, the
evaluation reports `confirmation_series_accessed: false`, and no candidate
freeze exists. Confirmation roster metadata were available to enforce role
separation, but no locked confirmation station-year target series was
accessed. A9d remains unauthorized [E01] [E09] [E11].

## Limitations and validity

Internal validity is strong for the bounded non-promotion result: design,
amendment, calibration, fits, baseline, evaluation, and implementation are
hash-bound; all 240 prefixes have a retained early support failure; and the
package verifier reproduces the stage and objective dimensions. The short-
horizon validation deviation prevents treating 609,654 as a 30-year total but
does not alter the hard-failure decision [E10] [E15]. The fit-closeout record
also discloses pre-score schema and replay-harness corrections; none accessed
a candidate score before the prospective boundary [E10].

Monthly reconciliation is less independently auditable than the other gates.
Its canonical records retain summaries and identities, not the component
moments and Monte Carlo standard errors needed to recompute each pass without
rerunning the deterministic harness. The report therefore accepts only the
recorded uncertainty-adjusted status and makes no 0.5-percent agreement claim
[E06] [E15].

Construct validity is limited by the unbounded generated context variables:
retained failures show negative solar radiation, negative wind speed, and
out-of-range humidity. These are physical-support defects in the evaluated
implementation, not evidence that the occurrence/amount/event class structures
are impossible. Conversely, the 19 unavailable mandatory rows show that even
after the grouped-storm amendment, the short development evidence did not
populate every original A9 mandatory cell. Neither issue can be treated as a
favorable zero.

External validity is limited to 20 Daymet daily-development locations, 12
USCRN storm-development locations, two burns, and the specific role periods.
Daymet is a 1-km gridded estimate and USCRN is a point network; the frozen
storm comparison is unpaired group-to-group evidence. Hot-arid storm inference
is limited to Yuma and Stovepipe Wells. No 100-year candidate full-development
climate-objective stage, eight-burn replay, locked confirmation, production
Rust profile, openWEPP, or WEPPcloud behavior was evaluated.

## Conclusions

A9c3 achieved the intended campaign correction: it replaced the arbitrary
hot-arid event floors with a finite, candidate-blind, equal-weight two-site
estimator and returned to actual candidate generation. The grouped storm
mechanism improved its screened family rows, but all six eligible candidates
generated physically invalid context values and were stopped before full
development. The correct terminal is
`HOLD-A9C3-NO-SELECTABLE-CANDIDATE` [E05] [E09].

The next scientific step should remain narrow but has two prerequisites. First,
decompose the 19 unavailable mandatory rows into observed-data, faithful-
baseline, and candidate causes, then establish that the frozen evidence
surface can produce a complete candidate or prospectively amend that surface
before any new candidate outcome. Second, define solar radiation and wind on
nonnegative support and humidity on bounded support inside both candidate
models. Holding the occurrence, amount, and event mechanisms fixed for that
rerun would be a controlled diagnostic-isolation choice, not an adequacy
judgment; the 8--18 short-stage degradation rows remain unresolved and may
motivate later mechanism changes. Realized-output clipping, a runtime fallback,
threshold relaxation, more selector machinery, A9d, and consumer integration
do not follow from this result [E09] [E12] [E15].

## Reproducibility and data availability

The A9c3 package retains the design and evaluator freezes, grouped calibration,
eight compact/detail fit pairs, structural audit, faithful baseline,
evaluation, correction history, claim ledger, and verifier. Canonical report
evidence E01--E15 and exact SHA-256 identities are registered in the report
manifest. The full campaign used one worker for 2,531.438 seconds; evaluation
peak resident memory was 2,154,168,320 bytes [E05] [E06] [E09].

Normalized Daymet and USCRN observed objects are managed through Git LFS and
retain compressed and logical hashes. Raw USCRN annual bytes are URL/hash
identified but not redistributed. The repository's Apache-2.0 license does
not relicense provider data. Public DOI and provider links are used instead of
copyrighted local reading copies [E11] [R01] [R02] [R03] [R04].

## References

- [R01] Thornton, M. M., R. Shrestha, Y. Wei, P. E. Thornton, and S-C. Kao.
  (2022). *Daymet: Daily Surface Weather Data on a 1-km Grid for North
  America, Version 4 R1*. Version 4.1. ORNL Distributed Active Archive Center.
  DOI [10.3334/ORNLDAAC/2129](https://doi.org/10.3334/ORNLDAAC/2129).
  Accessed 2026-07-15.
- [R02] Palecki, M. A., J. H. Lawrimore, R. D. Leeper, J. E. Bell, S. Embler,
  and N. Casey. (2015). *U.S. Climate Reference Network Processed Data from
  USCRN Database Version 2* [Subhourly01 format 01/OAP 2.1.1 subsets]. NOAA
  National Centers for Environmental Information. DOI
  [10.7289/V5MS3QR9](https://doi.org/10.7289/V5MS3QR9). Accessed 2026-07-15.
- [R03] NOAA National Centers for Environmental Information. *USCRN/USRCRN
  Subhourly01 files: data-version/status updates, file organization, and field
  formats*. No DOI. [Official lowercase
  README](https://www.ncei.noaa.gov/pub/data/uscrn/products/subhourly01/readme.txt).
  Accessed 2026-07-15.
- [R04] Diamond, H. J., et al. (2013). "U.S. Climate Reference Network after
  One Decade of Operations: Status and Assessment." *Bulletin of the American
  Meteorological Society*, 94(4), 485--498. DOI
  [10.1175/BAMS-D-12-00170.1](https://doi.org/10.1175/BAMS-D-12-00170.1).
- [E01] A9c3 execution dispatch and source-commit boundary.
- [E02] A9c3 prospective design, hypotheses, stages, and terminal freeze.
- [E03] A9c3 grouped two-site storm-objective amendment.
- [E04] A9c3 pre-score objective-evaluator freeze.
- [E05] A9c3 candidate-blind grouped calibration.
- [E06] A9c3 fresh fit-execution inventory and reconciliation summaries.
- [E07] A9c3 structural non-isomorphism and recovery audit.
- [E08] A9c3 fresh faithful Rust comparator baseline.
- [E09] A9c3 canonical evaluation, attempt inventory, and terminal.
- [E10] A9c3 pre-score fit/replay correction record.
- [E11] A9c exact observed-source and role manifest reused by A9c3.
- [E12] A9c3 deterministic research implementation and verifier.
- [E13] A9c2 post-acceptance two-site operator disposition.
- [E14] ADR-0001 faithful-mode source-authority decision.
- [E15] A9c3 outcome-time short-horizon and reconciliation disclosure.
