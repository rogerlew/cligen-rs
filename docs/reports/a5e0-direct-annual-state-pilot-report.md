# Direct annual-state pilot for CLIGEN

Report ID: `a5e0-direct-annual-state-pilot`
Status: `ACCEPTED`
Date: 2026-07-14
Revision: 1
Authors: cligen-rs project contributors
Evidence mode: Mixed
Experiment record: [A5e0 work package](../work-packages/20260714-a5e0-direct-annual-state-pilot/package.md)
Evidence snapshot: [report manifest](a5e0-direct-annual-state-pilot-report.manifest.json)
Review record: [consolidated internal review](../work-packages/20260714-a5e0-direct-annual-state-pilot/artifacts/review.md)

## Abstract

A5e0 tested one research-only CLIGEN extension in which a single independent
standard-normal state per synthetic year perturbed monthly precipitation
occurrence, wet-day amount, maximum-temperature mean, and minimum-temperature
mean at three exposed stress stations. Eight paired substreams produced 48
primary 100-year runs and 96 arm/horizon cells at 30 and 100 years. The
exploratory intended-signal ratio, defined as candidate error divided by the
paired research-baseline error, had a three-station median of 1.208 at 30 years
and 1.266 at 100 years; its continuation limit was 0.90. Every station ratio
exceeded 1.0 at both horizons, so the mechanism worsened rather than improved
the targeted composite in these runs. Preservation passed at 30 years but
failed the 100-year monthly-contract bound. However, the named execution-base
commit does not contain the exact specification, fitter, implementation, or
analyzer, and several predeclared H4 checks were not demonstrated in their
required form. The terminal package decision is therefore
`EXECUTED-HOLD-PROSPECTIVE-BOUNDARY`, not a formal `CLOSE-MECHANISM`. A5e1 is
not authorized. [E07] [E08] [E10]

## Introduction

CLIGEN's compact monthly parameterization drives daily stochastic weather.
Aggregated precipitation variance can be deficient for reasons involving
both occurrence and amount structure, so adding low-frequency conditioning
does not by itself guarantee an improvement [R01]. A5e0 asked a deliberately
narrow question: can one annual scalar, installed inside the daily generator
without changing faithful defaults, improve selected interannual dispersion
and dependence while preserving monthly, daily, winter, and storm-descriptor
surfaces?

The extension is outside faithful CLIGEN. Faithful behavior remains governed
by the vendored Fortran and the repository source-authority decision; the
pilot specification owns only the declared research seams. [E01] [E02]

Coefficients used Daymet V4 R1 for 1980--2009 and evaluation used 2010--2025
from the same already-exposed product [R02]. Daymet is a 1-km gridded estimate,
not point-station truth, and its construction and uncertainty depend on the
observing network and interpolation [R03]. The exact retained source objects
and their third-party terms are recorded in the A5a source manifest and data
notice. [E03] [E04]

## Hypotheses

The table treats all outcomes as exploratory. The committed scaffold contains
the broad mechanism, matrix, and thresholds, but the exact spec and analyzer
were not immutably sealed at the claimed boundary. The provisional climate
mapping is retained because it is reproducible and useful for diagnosis; it
does not acquire prospective status after the fact. [E07] [E13]

| ID | Provenance | Scope and comparison | Decision rule | Outcome | Result |
|---|---|---|---|---|---|
| H0 | exploratory | Analytic feasibility of all station, month, and seam budgets | Every loading, solve, probability, residual variance, and reconstruction check meets its intended bound | Passed analytically; exploratory only | [Analytic feasibility](#analytic-feasibility) |
| H1 | exploratory | Candidate versus research-baseline interannual dispersion and dependence at each horizon | Three-station median ratio at most 0.90 and no station above 1.25 | Failed at both horizons; exploratory only | [Intended signal](#intended-signal) |
| H2 | exploratory | Monthly, mean, precipitation-structure, thermodynamic, and cold-winter preservation | Family-specific median and station limits pass at each horizon | Passed at 30 years and failed at 100 years; exploratory only | [Preservation](#preservation) |
| H3 | exploratory | Dependence, low-frequency, and storm-descriptor catastrophic-regression guards | Registered ratio limits and both descriptor-rule readings pass | Passed under both rule readings; exploratory only | [Regression guards](#regression-guards) |
| H4 | exploratory | Prospective identity, strict intake, conformance, RNG proof, evidence, and repository gates | Every predeclared engineering obligation is demonstrated | Failed; prospective boundary and required evidence were not demonstrated | [Engineering and evidence](#engineering-and-evidence) |

## Methods

### Authority and access history

The execution started from commit
`27e5e7754bdfafcca649a71d0f5576910433d0d3` on `main`. That commit contains
the work-package scaffold, but not the exact pilot specification or execution
code. The specification file existed before coefficient fitting and reached
its current pre-campaign form before candidate climate output, but it was not
committed or independently hash-sealed. It was corrected after H0 output to
use the exact faithful-stream skip multiplier. The analyzer reached its
recorded form after the matrix. The post-output implementation-tree snapshot
records the bytes that actually produced and analyzed the retained campaign;
it explicitly has no implementation commit. [E02] [E07]

This access history prevents a claim of immutable preregistration. It also
prevents outcome-time fixes from promoting the run. The lead preserved the
outputs, made no coefficient or mechanism tuning, and used the independent
review findings to select an evidence-integrity hold. [E10] [E12] [E13]

### Study identity

| Fact | Registered value |
|---|---|
| Research profile | a5e0_direct_annual_state_v1 |
| Source commit | 27e5e7754bdfafcca649a71d0f5576910433d0d3 |
| Implementation commit | none; post-output tree snapshot only |
| Stations | 3 |
| Arms | 2 |
| Replicates | 8 |
| Primary runs | 48 |
| Horizons years | 30, 100 |
| Arm horizon cells | 96 |
| Fit period | 1980--2009 |
| Evaluation period | 2010--2025 |
| Decision | EXECUTED-HOLD-PROSPECTIVE-BOUNDARY |
| Confirmation objects accessed | 0 |
| Raw products committed | false |

### Coefficient fit and annual mechanism

The fitter formed 48 annual monthly features per station: wet fraction,
pseudocount log wet-day mean, mean Tmax, and mean Tmin. Signs came from an
oriented leading eigenvector of the feature correlation matrix. Magnitudes
represented positive excess over approximated base sampling variance. A
32-node Gauss--Hermite calculation solved occurrence intercepts and
occupancy-weighted wet-amount centering; residual amount and temperature
variance was reallocated instead of added. The retained three-station bundle
contains 144 finite loadings. [E05] [E06]

The implementation drew one domain-separated SplitMix64/Box--Muller normal
per candidate year. That scalar changed the four monthly parameter surfaces
before daily draws. The same effective occurrence probabilities reached both
precipitation consumers, the Tmin anomaly also moved dew-point mean, and
storm-shape setup remained based on the unmodified station. The research
baseline used the same segmented faithful stream starts but installed no
annual extension. Neither arm is a newly accepted public generation profile.
[E02] [E07]

The fit specification stated chronological `math.fsum` except for named
NumPy/SciPy operations, but the fitter used NumPy reductions in additional
loading calculations. Runtime intake also validates claimed occurrence and
amount diagnostics without independently reconstructing every derived value.
These discrepancies are H4 failures; the report does not claim fit-byte
conformance or production-ready coefficient intake. [E07] [E13]

### Stations, runs, and targets

The purposive stress cells were Death Valley, California (`ca042319`, dry),
Climax, Colorado (`co051660`, cold), and Saucier Experimental Forest,
Mississippi (`ms227840`, wet). They are not a representative sample. For each
station, eight fixed master seeds selected nonoverlapping faithful-stream
segments and paired the research-baseline and candidate arms. The campaign
ran each arm for 100 years and also produced deterministic 30-year prefix
views. Formatted daily rows matched the first 30 years in all 48 arm/replicate
pairs. This is a formatted-row check, not the stronger typed-row evidence name
used in the scaffold. [E07]

Most climate distances targeted 2010--2025 Daymet. Daily temperature range
also targeted Daymet, dew-point mean targeted the base station contract
because Daymet has no dew-point field, and storm descriptors measured
candidate departure from the paired research baseline. Therefore a descriptor
PASS is not observational validation. [E02] [E08]

### RNG and conformance evidence

Independent replay reproduced the 24 segment starts, 960 final stream states,
candidate annual-state prefixes, and the canonical faithful-stream periods.
The largest observed 100-year consumption was 457,201 raw updates, below the
500,000-update segment size. The all-zero candidate reproduced the baseline
formatted rows and final seeds and consumed no extension states. These are
strong realized checks, but the package requested a prospective conservative
upper bound on stream use; observed consumption is not that proof. [E07]

## Analysis

The canonical analysis expanded 1,211 registered quality bindings and used
the inherited eligible-cell rules. Within an arm, station, and family, it
averaged eligible cell distances for each replicate, took the conventional
median of eight replicate values, formed candidate/research-baseline ratios,
and then took the middle of the three station ratios. Ratios above 1 mean the
candidate was farther from its target. Exact zero divided by zero was defined
as 1; a positive candidate divided by zero was unbounded and failing. No
required cell was missing or nonfinite. [E08]

H1 equally weighted four groups: annual dispersion, monthly dispersion,
cross-month dependence, and cross-variable dependence. H2 applied separate
family limits. H3 applied ratio guards to annual dependence and low-frequency
behavior. The descriptor wording differed between a single equal-weight
three-subfamily composite and separate subfamily gates. A post-output audit
computed both readings without modifying the analysis; both passed by wide
margins. [E08] [E09]

No confidence interval or significance test was used. The eight streams are
deterministic pseudorandom substreams, the three stations are selected stress
cases, and the study's operational thresholds—not sampling inference—define
the exploratory outcomes.

## Results

### Analytic feasibility

All 144 loadings were finite. Joint occurrence count errors were at most
`2.84e-14` day, quadrature-node occurrence probabilities remained strictly
inside `(0,1)`, and the recorded amount and temperature residual budgets and
moment reconstructions passed their intended tolerances. Thus H0 mapped to
PASS in the exploratory records. [E05] [E06]

### Intended signal

Candidate/research-baseline ratios for H1 were:

| Horizon | Dry | Cold | Wet | Three-station median | Median limit | Maximum-station limit | Outcome |
|---:|---:|---:|---:|---:|---:|---:|---|
| 30 years | 1.198 | 1.371 | 1.208 | 1.208 | 0.90 | 1.25 | FAIL |
| 100 years | 1.266 | 1.491 | 1.228 | 1.266 | 0.90 | 1.25 | FAIL |

Every station ratio exceeded 1.0 at both horizons. The annual-state candidate
therefore moved the targeted composite away from the registered target in all
six station/horizon comparisons. This is the clearest scientific observation
from the campaign, but it remains exploratory because H4 failed. [E08]

### Preservation

The table reports three-station median candidate/research-baseline ratios;
the cold-winter value is the single cold-station ratio.

| Family | 30 years | 100 years | Applicable median limit | Outcome |
|---|---:|---:|---:|---|
| Monthly station contract | 1.087 | 1.145 | 1.10 | PASS / FAIL |
| Interannual mean contract | 1.035 | 0.973 | 1.10 | PASS / PASS |
| Precipitation structure | 1.022 | 1.046 | 1.10 | PASS / PASS |
| Daily thermodynamic contract | 1.005 | 1.056 | 1.25 | PASS / PASS |
| Cold winter proxies | 0.883 | 0.872 | 1.25 | PASS / PASS |

H2 passed at 30 years. At 100 years, its monthly-station-contract median was
1.145, above 1.10; the cold station also reached 1.205 within that family.
H2 therefore failed at 100 years. [E08]

### Regression guards

Annual-dependence median ratios were 1.028 and 0.966 at 30 and 100 years;
low-frequency ratios were 1.080 and 1.041. All were below their limit of 2.0,
and no station exceeded 3.0. Composite descriptor medians were 0.0186 and
0.0137, below 0.50. Under the literal per-subfamily reading, the largest
station medians across both horizons were 0.00152 for time to peak, 0.119 for
peak-intensity ratio, and 0.0162 for descriptor dependence, each below 0.75.
H3 passed under both readings. [E08] [E09]

### Engineering and evidence

The retained evidence verifier validates strict JSON, schemas, hashes, the 48-
run matrix, run identities, realized RNG partitions, extension-state use, and
the terminal hold. Repository format, lint, test, coverage, and CRAP checks
also pass in the final gate record. Those mechanical successes do not repair
the missing prospective identity or the predeclared fit, intake, typed-prefix,
and conservative-bound obligations. H4 failed. [E07] [E11]

The canonical analysis contains `climate_decision=CLOSE-MECHANISM` because it
maps H1--H3 only. The complete campaign record adds H4 and controls the package
decision: `EXECUTED-HOLD-PROSPECTIVE-BOUNDARY`. [E07] [E08]

## Limitations and validity

Internal validity is limited primarily by the absent immutable pre-output
specification/analyzer identity. The report therefore does not call any
hypothesis preregistered or ratify the provisional climate decision. Fit
arithmetic and runtime intake differed from their stated obligations, and two
engineering checks were demonstrated only in weaker realized forms. These are
documented failures, not silently repaired after outcome access. [E13]

Construct validity is limited by mixed targets and calendars. Daymet provides
gridded estimates rather than station truth; dew point uses the station
contract, and descriptors measure paired-baseline departure. The analytic
occurrence and amount preservation equations use a fixed no-leap 365-day
recurrence, while generated CLIGEN years include Gregorian leap days. A5a's
no-leap normalization is also a project transform rather than Daymet's
official civil calendar. [E02] [E03]

External validity is narrow: three purposive stations, eight deterministic
substreams, one scalar-IID mechanism, and one fitted coefficient bundle. No
GHCN, PRISM, gridMET, WEPP, or independent confirmation object was evaluated.
The result cannot reject annual-state climate generation generally. It only
shows that this exact exploratory implementation did not improve its intended
composite in these runs.

Residual uncertainty includes untested BLAS/LAPACK portability of a dormant
eigenvector tie rule and the lack of a locked Python numerical environment.
The independent extraction ledger records these claim boundaries and all
material finding dispositions. [E13]

## Conclusions

The exploratory numerical result is unfavorable: H1 worsened at every station
and both horizons, and H2 added a 100-year monthly-contract failure. Nothing
in H3 counterbalances the missing intended signal. If the evidence boundary
had been valid, H1 alone would have mapped to `CLOSE-MECHANISM`.

It was not valid. The correct terminal decision is
`EXECUTED-HOLD-PROSPECTIVE-BOUNDARY`. This does not authorize A5e1, public
profile exposure, production coefficients, or confirmation access. The
simplest next action is to stop this line unless an operator later decides
that the exact mechanism merits a clean, committed, prospectively frozen
reproduction. This package does not create such a successor. [E07] [E10]

## Reproducibility and data availability

The campaign record binds the execution-base commit, a post-output
implementation-tree manifest, Cargo lockfile, exact fitter/analyzer/verifier,
specifications, schemas, three station inputs, three Daymet extracts,
coefficient and feasibility records, 48 primary run records, conformance
products, canonical analysis, and descriptor audit. `verify-a5e0.py --self-test`
checks strict parsing, schema rejection, hashes, matrix closure, and terminal
disposition. [E07]

Raw `.cli`, quality, and diagnostic files total about 207 MiB under ignored
`target/a5e0/`. They are locally reproducible working evidence, not committed
public artifacts. No A5e0 Git LFS object is needed. Daymet extracts remain
third-party data governed by their notice, not by the repository's Apache-2.0
license. [E04]

The exact repository gates and report checks are retained in the gate record;
the consolidated review covers accuracy, scientific validity, and
consistency/public safety. [E11] [E12]

## References

### Publications and datasets

- **R01.** Katz, R. W., and M. B. Parlange. 1998. “Overdispersion Phenomenon in Stochastic Modeling of Precipitation.” *Journal of Climate* 11:591--601. [DOI](https://doi.org/10.1175/1520-0442(1998)011%3C0591:OPISMO%3E2.0.CO;2).
- **R02.** Thornton, M. M., et al. 2022. *Daymet: Daily Surface Weather Data on a 1-km Grid for North America, Version 4 R1*. ORNL DAAC. [DOI](https://doi.org/10.3334/ORNLDAAC/2129).
- **R03.** Thornton, P. E., et al. 2021. “Gridded Daily Weather Data for North America with Comprehensive Uncertainty Quantification.” *Scientific Data* 8:190. [DOI](https://doi.org/10.1038/s41597-021-00973-0).

### Repository records and reproducibility artifacts

- **E01.** [ADR-0001](../decisions/0001-source-code-authority-port.md) — faithful source-authority boundary.
- **E02.** [A5e0 pilot specification](../specifications/SPEC-A5E0-PILOT.md) — intended mechanism, fit, matrix, and decision rules with access disclosure.
- **E03.** [A5a source manifest](../work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts/corpus/source-manifest-v1.json) — exact Daymet source identities and periods.
- **E04.** [Third-party data notice](../../references/observed/a5a-v1/THIRD_PARTY_DATA_NOTICE.md) — Daymet citation, terms, and license boundary.
- **E05.** [Coefficient bundle](../work-packages/20260714-a5e0-direct-annual-state-pilot/artifacts/a5e0-coefficients-v1.json) — fitted values and diagnostics.
- **E06.** [Feasibility record](../work-packages/20260714-a5e0-direct-annual-state-pilot/artifacts/a5e0-feasibility-v1.json) — exploratory H0 result.
- **E07.** [Campaign evidence](../work-packages/20260714-a5e0-direct-annual-state-pilot/artifacts/a5e0-campaign-evidence-v1.json) — complete retained run identity and terminal hold.
- **E08.** [Canonical analysis](../work-packages/20260714-a5e0-direct-annual-state-pilot/artifacts/a5e0-analysis-v1.json) — H1--H3 values and provisional climate mapping.
- **E09.** [Descriptor-rule audit](../work-packages/20260714-a5e0-direct-annual-state-pilot/artifacts/a5e0-descriptor-rule-audit-v1.json) — post-output comparison of both H3 readings.
- **E10.** [A5e0 work package](../work-packages/20260714-a5e0-direct-annual-state-pilot/package.md) — terminal scope and authorization boundary.
- **E11.** [Gate record](../work-packages/20260714-a5e0-direct-annual-state-pilot/artifacts/gate-results.md) — mechanical and scientific gate outcomes.
- **E12.** [Consolidated review](../work-packages/20260714-a5e0-direct-annual-state-pilot/artifacts/review.md) — three-lens review and dispositions.
- **E13.** [Claim and finding ledger](../work-packages/20260714-a5e0-direct-annual-state-pilot/artifacts/claim-evidence-ledger.md) — independent extraction, accepted claims, and residual uncertainty.
