# A9d successor development and locked-confirmation decision

Report ID: `a9d-successor-development-confirmation`
Status: `ACCEPTED`
Date: 2026-07-15
Revision: 1
Authors: cligen-rs project contributors
Evidence mode: Mixed
Experiment record: [A9d work package](../work-packages/20260715-a9d-successor-development-confirmation/package.md)
Evidence snapshot: [report manifest](a9d-successor-development-confirmation-report.manifest.json)
Review record: [consolidated internal review](../work-packages/20260715-a9d-successor-development-confirmation/artifacts/review.md)

## Abstract

A9d tested whether either of two stochastic climate-generator classes could
produce a development candidate that improved on faithful CLIGEN without any
material degradation on the prospectively accepted 92-cell evidence surface.
Eighteen fresh configurations entered a staged 18/4/2 evaluation at 30- and
100-year horizons. All fits were valid, both classes remained structurally
distinct, and 720 strict short-prefix context audits had zero support
violations. The two eight-burn finalists were complete, but the renewal
finalist retained three material-degradation rows and the latent finalist
retained 17. The unchanged selector therefore sealed no candidate and returned
`HOLD-A9D-NO-SELECTABLE-CANDIDATE` [E06] [E07] [E10] [E11]. The conditional
18-site confirmation was not run and no confirmation target series was
accessed. The result rejects no model class generally; it says that no member
of this bounded grid passed this development rule on this panel and evidence
surface.

## Introduction

A9a defined a joint occurrence, amount, storm, and event-context successor
family, while A9b supplied its calibration and evaluation harness. A9c through
A9c4 progressively established the observed-data boundary. A9c4 ultimately
found 92 retained mandatory objective/stratum cells and 19 excluded former-
mandatory cells per horizon. A9d prospectively accepted that incomplete but
explicit surface rather than adding more roster floors, fallback layers, or
selector complexity [E01] [E04] [E12].

The bounded question was whether the frozen alternating-renewal and three-
state latent-regime classes could be fit with physically supported event
contexts and pass the unchanged no-material-degradation selector. Locked
confirmation was conditional: target series could be consumed only after one
complete development candidate was sealed. This report covers the completed
development path and the resulting unreached confirmation path; it makes no
confirmation-performance claim.

## Hypotheses

H3's operational rule was amended before any A9d fit or candidate output. The
other hypotheses retain their preregistered provenance [E01] [E02].

| ID | Provenance | Scope and comparison | Decision rule | Outcome | Result |
|---|---|---|---|---|---|
| H1 | preregistered | Accepted A9c4 evidence surface at both horizons | Preserve 92 retained and 19 excluded former-mandatory cells exactly | Supported: the 92/19 accepted surface was preserved at both horizons | [Surface result](#surface-and-structural-gates) |
| H2 | preregistered | Structural support of corrected event contexts | Every corrected solar, wind, and humidity output is strictly in support without clipping or repair | Partially supported: 720 strict short-prefix audits passed, but later-stage output lacked the same strict audit | [Support result](#surface-and-structural-gates) |
| H3 | amended | Fresh fit, monthly calibration/reconciliation, and class distinction | Both classes retain a valid fit, pass the amended rule, and remain non-isomorphic | Supported under the pre-output amended amount-only calibration rule | [Fit result](#surface-and-structural-gates) |
| H4 | preregistered | Development selector safety and outcome | Seal at most one candidate after rejecting hard failure, incomplete retained evidence, or any material degradation | Supported as safety rule and outcome: zero candidates qualified for sealing | [Selector result](#staged-development-and-selector) |
| H5 | preregistered | Confirmation firewall | No target-series access without sealed candidate and confirmation manifests | Supported: zero confirmation target-series access | [Firewall result](#confirmation-firewall) |
| H6 | preregistered | Conditional one-shot confirmation | If a candidate seals, return exactly one pass or final-failure terminal without tuning feedback | Not evaluated: no development candidate sealed | [Firewall result](#confirmation-firewall) |

## Methods

### Study identity

| Fact | Registered value |
|---|---|
| Source commit | 1d0350eed8549067eca41047c0eef43949822c69 |
| Campaign id | a9d-successor-development-confirmation-v1 |
| Candidate classes | 2 |
| Configuration grid | 18 |
| Fresh valid fits | 18 |
| Accepted retained cells per horizon | 92 |
| Excluded former mandatory cells per horizon | 19 |
| Report only objective rows per horizon | 61 |
| Development horizons years | 30, 100 |
| Development burns | 8 |
| Development daily sites | 20 |
| Development storm role objects | 12 |
| Short screen configurations | 18 |
| Full development configurations | 4 |
| Pareto replay configurations | 2 |
| Strict context audit prefixes | 720 |
| Strict context violations | 0 |
| Engineering attempt streams | 1,040 |
| Faithful baseline runs | 160 |
| Renewal replay degradation rows | 3 |
| Latent replay degradation rows | 17 |
| Selected candidates | 0 |
| Candidate freezes | 0 |
| Confirmation target series accessed | false |
| Accounted campaign wall seconds | 8599.665161916986 |
| Maximum rss bytes | 5,652,234,240 |
| Terminal | HOLD-A9D-NO-SELECTABLE-CANDIDATE |

### Prospective boundary and amendments

The design froze the 18-configuration grid, 92/19 evidence surface, two model
classes, eight development burns, 30/100-year horizons, stage limits,
candidate-blind thresholds, selector, resource bounds, confirmation firewall,
and confirmation rule before corrected candidate output [E01]. The predecessor
manifest binds 22 accepted repository authorities. An omitted faithful-
parameter archive identity was appended after fitting but before any faithful
baseline or candidate score existed; no model or decision input changed [E03]
[E04].

The initial design proposed exact monthly occurrence calibration. A pre-output
analytic check showed that this was incompatible with finite positive renewal
durations, interior latent wet probabilities, and a structural zero-wet
station-month. A prospective amendment withdrew occurrence calibration instead
of adding exceptions. Fitted occurrence remained unchanged; deterministic
positive-amount mean scaling remained [E02]. H3 is therefore amended, not a
claim that the original occurrence-calibration proposal passed.

Closeout found multiple stale A9c3-derived descriptive fields in the hash-
bound runtime record. The preserved record still governs inherited evaluator
mechanics, but the A9d design governs its grid, pooling values, stage caps,
resource caps, and terminal vocabulary; executed fit/evaluation artifacts
govern actual identities and results [E08] [E14]. The exact research adapter is
retained for deterministic reexecution [E13].

### Data and model classes

The daily development role used 20 normalized Daymet V4 R1 sites for
2010--2025 [R01]. Twelve normalized USCRN development-role objects supplied
storm evidence under the accepted grouped construct; hot-arid storm summaries
used Yuma and Stovepipe Wells at equal weight and actual event frequency
[R02] [R03] [R04]. The 19 excluded former-mandatory cells remained report-only
at both horizons. Together with 36 secondary and six natively report-only
objective rows, this produced 61 report-only objective rows per horizon and
configuration [E01] [E10] [E12].

The two classes were `alternating_renewal_marked_v1` and
`latent_regime_marked_v1`. Each combined precipitation occurrence and amount
with event air temperature in identity/Gaussian space, solar radiation and
wind speed in log/lognormal space, and relative humidity in logit/logit-normal
space. The grid crossed class with pooling strengths 10, 25, and 50 and tail
quantiles 0.90, 0.95, and 0.98. All fits used coefficient-fit roles only [E01]
[E06].

### Comparator and execution

The development comparator was a freshly built `faithful_5_32_3` Rust binary
using the frozen station-parameter archive. Twenty stations by eight burns
produced 160 distinct 100-year faithful outputs, all passing calendar/support,
replay, and provenance checks. Faithful semantics remain governed by the
vendored Fortran under the repository source-authority decision [E09] [E20].

Candidate stages reused nested streams: the 30-year result was the exact prefix
of its 100-year stream. The short screen used two burns for all 18
configurations; full development used four burns for two configurations per
class; replay used all eight burns for one configuration per class. No failed
or unfavorable burn was replaced [E08] [E10].

The confirmation roster and nearest-parameter comparator crosswalk were
prepared from public metadata, but no confirmation target series was acquired
or parsed. Eighteen selected parameter files were archived solely for the
conditional faithful comparator [E18] [E19]. A pre-access correction aligns
the unused conditional Daymet fit endpoint with A9a's authoritative
2009-12-31 endpoint [E15].

## Analysis

### Calibration and structural checks

Each of the 18 fits stored 240 station-month calibration records, for 4,320
records total. Eighteen records repeat the one structural-zero station-month;
4,302 positive-mean records were scaled. The maximum positive-amount mean
relative error was 4.587989480529896 × 10^-16, a deterministic
scaling identity rather than validation accuracy. Occurrence was not
calibrated; the largest fitted-versus-observed wet-fraction discrepancy was
0.2283727629263901 [E02] [E06].

Monthly reconciliation compared two independent draws of 200,160 full-process
paths per fit each across 28/29/30/31-day months. The registered pass rule
used the larger of absolute tolerance, 0.005 relative tolerance, and 3.290527
times the combined Monte Carlo standard error. All 18 fits passed that rule,
but raw maximum absolute and relative discrepancies were 1385.28596160785 and
0.3348603027204908. This is an uncertainty-adjusted consistency decision, not
agreement within 0.5%; exact component-level audit requires deterministic
reexecution [E06] [E08].

### Objective distances and selector

At replay, each candidate had 62 retained family/stratum/horizon rows: 31 at
each horizon. For each row, material degradation meant candidate distance
minus faithful-baseline distance exceeded the frozen candidate-blind family/
horizon threshold. Boundary equality was non-degradation. A materially
improved family had at least one improvement at both horizons and no
degradation row. The complete Pareto vector was published before selection.
The selector then rejected hard failures, incomplete retained evidence, and
any material degradation; survivors, if any, would be ordered by the registered
lexicographic rule [E05] [E08] [E10].

The 14 family/horizon thresholds were calibrated from 500 candidate-blind null
replicates each; grouped storm scales used 2,000 station-year bootstrap
replicates. These controls apply within registered family/horizon constructions.
They are not a single 95% campaign-wide test over families, configurations,
stages, and burns. Finalist results are selection-conditioned development
statistics [E05].

### Support and engineering checks

The strict context audit covered 18 configurations by 20 sites by two short-
screen burns: 720 30-year prefixes. It required positive solar/wind and
strictly interior relative humidity, and found zero violations without
clipping or repair. All 1,040 staged 100-year attempt identities separately
passed deterministic replay, exact 30-year prefix, provenance, calendar, and
an inclusive physical validator. Because the inclusive validator permits
boundary values, it does not extend the strict H2 result to every later-stage
stream [E10] [E13].

## Results

### Surface and structural gates

H1 was supported: evaluation preserved 92 retained and 19 excluded former-
mandatory cells at both horizons. Every staged record had zero unavailable
retained cells. The broader report-only count was 61 objective rows per horizon
after secondary and native report-only objectives were included [E01] [E10].

H2 was partially supported. All 720 strict short-prefix audits passed, but no
equivalent strict audit covers all later-stage output. The result establishes
the tested transformed laws' short-screen structural support, not their upper-
tail realism or full climate-context quality [E10].

H3 was supported under its amended rule. All 18 configurations produced valid
fits, nine per class, and passed the uncertainty-adjusted reconciliation rule.
The structural audit found no exact observable-law identity or factorization
bijection; both recovery simulations passed [E06] [E07].

| Class | Valid fits | Effective parameters per fit | Maximum wet-fraction discrepancy |
|---|---:|---:|---:|
| Alternating renewal | 9 | 3,558 | 0.107965 |
| Latent regime, three states | 9 | 7,578 | 0.228373 |

### Staged development and selector

All stage records were complete with zero hard failures and zero unavailable
retained cells. Distances below are dimensionless registered normalized
family distances; counts are family/stratum/horizon rows. Values are rounded
to six decimals from the canonical evaluation [E10].

| Stage | Configurations | Burns | Horizon(s), years | Selected/promoted identities |
|---|---:|---:|---|---|
| Short screen | 18 | 2 | 30 | Renewal: p010-q090, p025-q095; latent: p010-q090, p025-q090 |
| Full development | 4 | 4 | 30, 100 | renewal-p010-q090; latent-k3-p010-q090 |
| Pareto replay | 2 | 8 | 30, 100 | No candidate sealed |

| Replay configuration | Degradation rows | Improvement rows | Improved families | Median normalized distance |
|---|---:|---:|---:|---:|
| renewal-p010-q090 | 3 | 19 | 2 | 0.698690 |
| latent-k3-p010-q090 | 17 | 18 | 2 | 1.357161 |

The renewal finalist's three material degradations were all hot-arid. Distances
and thresholds are dimensionless; values are rounded to six decimals [E10].

| Family | Horizon, years | Faithful distance | Candidate distance | Candidate minus faithful | Threshold |
|---|---:|---:|---:|---:|---:|
| Aggregate | 30 | 0.388738 | 1.181860 | 0.793122 | 0.658426 |
| Aggregate | 100 | 0.392989 | 1.068776 | 0.675787 | 0.392334 |
| Extreme | 100 | 0.323602 | 0.778094 | 0.454491 | 0.403397 |

The latent finalist's 17 degradation rows comprised ten occurrence, three
extreme, two aggregate, one wet-amount, and one compound-context row. Both
finalists counted storm descriptor and winter proxy as improved families, but
improvements could not offset any degradation under the frozen rule [E10].

H4 was supported as a safety property and produced a null selection outcome.
Both finalists lay on the two-item replay Pareto set, but each failed the
earlier zero-degradation filter. Selected class and configuration remained
null, no candidate-freeze artifact was created, and the terminal was
`HOLD-A9D-NO-SELECTABLE-CANDIDATE` [E10] [E11].

### Confirmation firewall

H5 was supported as a bounded artifact and execution-path claim. The result
records `confirmation_series_accessed=false`; no candidate freeze, sealed/
consumed confirmation manifest, target-series object, confirmation fit, or
confirmation evaluation exists. Public roster metadata and the faithful
parameter crosswalk are not target-series evidence [E11] [E18] [E19].

H6 was not evaluated because no candidate sealed. The prepared 18-station,
12-burn protocol supplied no scientific confirmation result and did not feed
back into development [E01] [E15].

## Limitations and validity

Internal validity is bounded by two prospective corrections. Exact occurrence
calibration was withdrawn before output, so the experiment does not test that
proposal. The faithful-parameter predecessor row was added after fits but
before baseline or scoring; the chronology is preserved rather than silently
rewritten [E02] [E03] [E16]. Multiple stale descriptive runtime fields are
also retained under an explicit authority precedence because executed evidence
hash-binds that file [E14].

Construct validity is limited by the accepted 92-cell surface. Nineteen former-
mandatory cells remained excluded, including missing wet-amount and compound-
context coverage in dry-transition regimes. Hot-arid storm descriptors are an
equal-weight two-site construct at actual event frequency, not a universal
hot-arid population estimate. Strict context support was checked on 720 short
prefixes only; lognormal/logit-normal support does not itself establish correct
zero mass, tails, or dependence [E01] [E10] [E12].

Statistical validity is bounded by adaptive stage promotion on one development
surface and nested burns. Thresholds are familywise constructions, not a
campaign-wide error guarantee. The near-zero amount-mean error follows from
deterministic scaling. Monthly-reconciliation pass uses a Monte Carlo-
uncertainty allowance despite raw discrepancies above the nominal relative
tolerance. Candidate streams are not retained, so component-level or strict
later-stage rechecks require deterministic regeneration [E05] [E06] [E10].

External validity is limited to the two registered classes, 18 configurations,
20 Daymet daily sites, 12 USCRN storm-role objects, six strata, 2010--2025
development period, accepted objective mask, faithful comparator, and frozen
burns. No locked confirmation data were evaluated. The result does not prove
that either model class is generally inadequate, that faithful CLIGEN is
generally superior, or that a nearby configuration cannot pass [E10] [E17].

## Conclusions

A9d completed the intended bounded successor development without adding a
fallback, selector exception, or intermediate work package. Both classes were
fit and evaluated, but neither replay candidate satisfied the unchanged zero-
material-degradation rule. The correct terminal is
`HOLD-A9D-NO-SELECTABLE-CANDIDATE`; no candidate is confirmation-ready and no
A9e production work follows from this result [E10] [E11].

The most useful bounded finding is diagnostic: the better renewal finalist
cleared most of the accepted surface and improved storm and winter families,
yet retained three hot-arid aggregate/extreme degradations. That identifies the
remaining behavior on this development panel; it is not authority to relabel
the finalist, relax the selector, or claim general class failure.

## Reproducibility and data availability

The experiment started from source commit
`1d0350eed8549067eca41047c0eef43949822c69`. The report evidence freeze binds
the prospective design, amendments, predecessor identities, calibration, 18
compact/detail fits, structural audit, faithful baseline, evaluation, compact
terminal, exact adapter/tests, correction records, claim ledger, and prepared
confirmation-comparator metadata [E16] [E17]. The public report contains no
raw confirmation target series.

Run `python3 -m research.a9d.campaign verify-development` for the package
verifier and `python3 -m unittest discover -s research/a9d/tests -v` for the
adapter tests [E13]. The 18 fit-detail JSON files use Git LFS; pointer and
object identities are checked at closure. The small confirmation comparator
archive is regular Git content and retains its exact SHA-256; repository
licensing does not relicense third-party station data or parameter provenance
[E18] [E19]. The frozen claim ledger is retained in the work package [E17];
the linked review record contains exact gate and lens dispositions.

## References

### Publications and datasets

- **R01.** Thornton et al. 2022. Daymet: Daily Surface Weather Data on a 1-km
  Grid for North America, Version 4 R1. [DOI](https://doi.org/10.3334/ORNLDAAC/2129).
- **R02.** Palecki et al. 2015. U.S. Climate Reference Network Processed Data
  from USCRN Database Version 2. [DOI](https://doi.org/10.7289/V5MS3QR9).
- **R03.** NOAA NCEI. USCRN/USRCRN Subhourly01 file documentation. No DOI.
  [Authoritative documentation](https://www.ncei.noaa.gov/pub/data/uscrn/products/subhourly01/readme.txt).
- **R04.** Diamond et al. 2013. U.S. Climate Reference Network after One
  Decade of Operations: Status and Assessment. *Bulletin of the American
  Meteorological Society*. [DOI](https://doi.org/10.1175/BAMS-D-12-00170.1).

### Repository records and reproducibility artifacts

- **E01.** [A9d design freeze](../work-packages/20260715-a9d-successor-development-confirmation/artifacts/design-freeze-v1.json) — prospective grid, evidence surface, hypotheses, selector, resources, and confirmation firewall.
- **E02.** [Pre-output fit amendment](../work-packages/20260715-a9d-successor-development-confirmation/artifacts/pre-output-fit-amendment.md) — prospective removal of incompatible occurrence calibration.
- **E03.** [Pre-score predecessor closeout](../work-packages/20260715-a9d-successor-development-confirmation/artifacts/pre-score-predecessor-closeout.md) — parameter-archive manifest correction chronology.
- **E04.** [Predecessor manifest](../work-packages/20260715-a9d-successor-development-confirmation/artifacts/predecessor-manifest-v1.json) — exact 22-file authority identity.
- **E05.** [Candidate-blind calibration](../work-packages/20260715-a9d-successor-development-confirmation/artifacts/calibration-v1.json) — thresholds, storm scales, and diagnostic resampling.
- **E06.** [Fit execution](../work-packages/20260715-a9d-successor-development-confirmation/artifacts/fit-execution-v1.json) — 18 fit identities, calibration/reconciliation summaries, and resources.
- **E07.** [Structural audit](../work-packages/20260715-a9d-successor-development-confirmation/artifacts/structural-audit-v1.json) — class distinction and recovery evidence.
- **E08.** [Development runtime](../work-packages/20260715-a9d-successor-development-confirmation/artifacts/development-runtime-v1.json) — inherited evaluator definitions and hash-bound mechanics, subject to E14.
- **E09.** [Faithful baseline](../work-packages/20260715-a9d-successor-development-confirmation/artifacts/development-faithful-baseline-v1.json) — fresh build provenance and 160 output identities.
- **E10.** [Development evaluation](../work-packages/20260715-a9d-successor-development-confirmation/artifacts/development-evaluation-v1.json) — canonical stage results, engineering attempts, support audit, selector, and terminal.
- **E11.** [Development result](../work-packages/20260715-a9d-successor-development-confirmation/artifacts/development-result-v1.json) — compact selection, access, and terminal record.
- **E12.** [A9c4 accepted report manifest](a9c4-context-support-completeness-report.manifest.json) — predecessor evidence-surface authority.
- **E13.** [A9d research adapter](../../research/a9d/campaign.py) — exact executed preparation, fit, evaluation, and verification code.
- **E14.** [Runtime-field disclosure](../work-packages/20260715-a9d-successor-development-confirmation/artifacts/post-outcome-runtime-metadata-discrepancies.md) — authority precedence for stale inherited fields.
- **E15.** [Pre-confirmation protocol correction](../work-packages/20260715-a9d-successor-development-confirmation/artifacts/pre-confirmation-protocol-correction.md) — unused fit-period endpoint correction before target access.
- **E16.** [Report evidence freeze](../work-packages/20260715-a9d-successor-development-confirmation/artifacts/report-evidence-freeze-v1.json) — source identities and access chronology.
- **E17.** [Claim-evidence ledger](../work-packages/20260715-a9d-successor-development-confirmation/artifacts/claim-evidence-ledger.md) — frozen claim and hypothesis crosswalk.
- **E18.** [Confirmation comparator crosswalk](../work-packages/20260715-a9d-successor-development-confirmation/artifacts/confirmation-baseline-crosswalk-v1.json) — metadata-only nearest-parameter preparation.
- **E19.** [Confirmation comparator parameter archive](../work-packages/20260715-a9d-successor-development-confirmation/artifacts/confirmation-baseline-parameters-v1.tar.gz) — 18 selected faithful comparator parameter files.
- **E20.** [ADR-0001](../decisions/0001-source-code-authority-port.md) — faithful-mode source-authority hierarchy.
