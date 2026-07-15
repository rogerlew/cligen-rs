# Daily precipitation-structure gaps in faithful CLIGEN output

Report ID: `a7a-daily-precipitation-structure`
Status: `ACCEPTED`
Date: 2026-07-14
Revision: 1
Authors: cligen-rs project contributors
Evidence mode: Mixed
Experiment record: [A7a work package](../work-packages/20260714-a7a-daily-precipitation-structure-baseline/package.md)
Evidence snapshot: [report manifest](a7a-daily-precipitation-structure-report.manifest.json)
Review record: [consolidated internal review](../work-packages/20260714-a7a-daily-precipitation-structure-baseline/artifacts/review.md)

## Abstract

A7a measured five daily precipitation-structure families in faithful CLIGEN
output against an existing 17-station Daymet corpus, with eight available
GHCN-Daily point series as shared-lineage sensitivity evidence. The experiment
regenerated 272 nested 100-year streams and evaluated 544 30- and 100-year
horizon records across two QC arms and eight deterministic burn offsets. A
family qualified only if its observed distance exceeded the maximum
leave-one-trajectory-out distance at prescribed station counts on Daymet-off,
Daymet-faithful, and GHCN-off surfaces at both horizons. Seasonal spell
structure and higher-order occurrence residuals qualified; the terminal result
is `DAILY-PRECIPITATION-GAP-MEASURED`. Wet-amount dependence ranked first by
breadth but did not qualify because its 30-year GHCN-off count was 0/8. The
study justifies a separate analytic feasibility study; it does not identify a
causal mechanism or predict that an A7b candidate will succeed. [E07] [E08]

## Introduction

Foundational stochastic weather generators combine Markov-chain precipitation
occurrence with wet/dry-conditioned models for other daily variables [R01].
Simple daily precipitation models can reproduce means while understating
interannual variability, and published single-site decomposition work has
examined higher-order occurrence and wet-amount dependence as contributors to
that overdispersion problem [R02]. These results motivate diagnostics, but they
do not define faithful CLIGEN behavior or establish the cause of a gap in this
implementation. The vendored Fortran remains the faithful-mode authority
[E01].

Earlier cligen-rs work established a fixed 17-station corpus and broad quality
metrics but did not isolate daily precipitation sequence structure. A7a asks a
narrower question: whether five predeclared daily families show repeatable
distance beyond the spread of eight deterministic CLIGEN trajectories, with
enough GHCN sensitivity support to warrant mechanism feasibility work. The
package is measurement-only; it changes no generator, station format, or
profile [E03] [E15].

## Hypotheses

All four hypotheses are `amended`. Amendment 003 specified conservative
handling of below-minimum component cells after component availability had
been accessed. Internal extraction later found three analysis discrepancies;
post-analysis amendment 005 corrected pooled severity, zero-null treatment,
and null component support after the first terminal result was known. Thus no
hypothesis is described as confirmatory [E04] [E05] [E06].

| ID | Provenance | Scope and comparison | Decision rule | Outcome | Result |
|---|---|---|---|---|---|
| H1 | amended | At least one core daily family is systemic across Daymet-off, Daymet-faithful, and GHCN-off surfaces at 30 and 100 years | At least 12/17, 10/17, and 5/8 material stations, respectively, at both horizons | Supported; gap terminal reached | [Results](#terminal-decision-and-ranking) |
| H2 | amended | The fixed rule orders the five core families | Lexicographic minimum Daymet-off breadth, faithful breadth, GHCN-off breadth, pooled Daymet-off severity, then identifier | Ranking produced; stability not tested | [Results](#terminal-decision-and-ranking) |
| H3 | amended | Daily-family distance co-locates with monthly and annual dispersion distance | Report cross-station Spearman association and joint-material counts; no pass/fail bound | Positive descriptive associations; no pass/fail | [Results](#propagation-diagnostics) |
| H4 | amended | QC-off and faithful arms differ in daily-family observed distance | Count smaller, equal, larger, and unavailable station pairs at each horizon | Mixed directional differences; no materiality test | [Results](#qc-arm-diagnostics) |

## Methods

### Study identity

| Fact | Registered value |
|---|---|
| Analysis id | a7a_daily_precipitation_structure_v1 |
| Source commit | d27a008e91a4853044aed5207d02a3aeb631ac8c |
| Generation profile | faithful_5_32_3 |
| Observed period | 1980--2025 |
| Stations | 17 |
| Ghcn sensitivity stations | 8 |
| Qc arms | 2 |
| Burn offsets | 8 |
| Horizons years | 30, 100 |
| Generated 100 year streams | 272 |
| Nested horizon records | 544 |
| Retained quality reports | 544 |
| Quality report overlap checks | 24,480 |
| Observed overlap checks | 1,125 |
| Wet day threshold mm | 1.0 |
| Core families | 5 |
| Qualifying families | spell_structure, higher_order_occurrence |
| Terminal decision | DAILY-PRECIPITATION-GAP-MEASURED |

### Data and execution

Daymet V4 R1 supplied the primary gridded daily precipitation surface at all
17 purposively selected A5a locations [R03]. The archived A5a corpus supplied
eight available GHCN-Daily Version 3 point series as sensitivity evidence
[R05]. GHCN-Daily integrates and quality-screens station records but is dynamic
and not homogenized for all reporting-practice changes [R04]. It is not an
independent confirmation source here because GHCN-Daily observations are also
inputs to Daymet. Exact archived identities and access dates, rather than the
mutable product locators alone, are authoritative for this experiment [E10]
[E11].

The Daymet archive was interpreted through the A5a project's `noleap_365`
civil-date transform. Official Daymet documentation instead states that its
leap-year ordinal sequence includes February 29 and omits December 31 [R06].
Generated and GHCN sequences use proleptic Gregorian calendars. The resulting
calendar mismatch is treated as a construct-validity limitation rather than
describing the project transform as native Daymet behavior.

The analyzer rebuilt the frozen release binary, extracted exact station
parameters from the retained A5a baseline, and generated 17 stations × 2 QC
arms × 8 burns = 272 100-year streams. Each 30-year record is the exact prefix
of its corresponding 100-year stream, yielding 544 horizon records. Burns
`0`, `17`, `101`, `503`, `1009`, `5003`, `10007`, and `50021` are deterministic
trajectory offsets, not IID replicates. The regenerated metrics passed 24,480
overlap checks against 544 retained quality reports; 1,125 observed overlap
checks passed against the archived corpus targets [E07] [E09].

### Daily families

A day is wet when rendered precipitation is at least 1.0 mm. Missing observed
dates break spells, adjacent pairs, triples, and rolling windows; no values are
imputed. Whole wet and dry spells are assigned to the season in which they
start. Higher-order occurrence uses seasonal residuals
`P(W_t | W_{t-2}, W_{t-1}) - P(W_t | W_{t-1})` for DD, DW, WD, and WW
histories. Wet-amount dependence uses seasonal Pearson and average-tie
Spearman correlations for consecutive wet/wet days. Upper-tail components are
seasonal wet-day p95 and p99. Multi-day extremes are p50, p90, and p95 across
complete-year 1-, 3-, and 5-day annual maxima. Monthly and annual
precipitation-total sample SDs are propagation diagnostics, not terminal
families [E02].

## Analysis

The center for each station, horizon, QC arm, source, and family is the
componentwise conventional median across eight trajectories. Positive
families use absolute natural-log-ratio component differences; signed
occurrence and dependence families use absolute component differences. A
family distance is the conventional median of the components shared by the
observation and all generated comparisons, subject to frozen minimum counts.
Each null distance compares one trajectory with the componentwise median of
the other seven on that same observation-supported component set. The null
ceiling is the maximum of the eight distances. A cell is operationally
`material` only when its observed distance exceeds that ceiling by more than
`1e-12`; this is neither a p-value nor a confidence interval [E02] [E05].

Severity is observed family distance divided by null ceiling. A positive
distance over an exactly zero ceiling is the extended-real value `infinity`;
zero over zero is `0.0`. Unavailable cells have no severity and are
conservatively non-material. Ranking uses, in order, the minimum Daymet-off
material count across horizons, the corresponding faithful minimum, the GHCN-
off minimum, the pooled median severity across available Daymet-off
station-horizon cells, and family identifier [E05] [E08].

The QC diagnostic pairs Daymet-off and faithful observed distances and counts
which is numerically smaller, equal within `1e-12`, or larger. It has no
scientific effect-size bound. Propagation takes each station's median
available distance across the five core families and reports its cross-station
Spearman association with monthly and annual dispersion distance, plus joint-
material counts. Because the daily composite mixes log-ratio and absolute-
difference scales, the associations are descriptive only. Counts are exact;
correlations are rounded to three decimal places and severity ratios to three
significant figures [E02] [E07].

## Results

### Execution integrity and availability

The canonical matrix contains 544 generated records, 25 observed records (17
Daymet and eight GHCN), 700 station-source-horizon-QC-family comparisons, and
56 comparison summaries. Generated records contain 10,957 daily rows at 30
years and 36,524 at 100 years. Daymet contributes 285,430 archived rows and
GHCN 124,728. Nine of 700 comparisons were unavailable: five
wet-amount-dependence cells fell below their six-component minimum, and four
GHCN annual-dispersion cells lacked a complete annual component. Every
unavailable cell was non-material [E07].

### Terminal decision and ranking

The frozen breadth rule produced `DAILY-PRECIPITATION-GAP-MEASURED`.
`spell_structure` and `higher_order_occurrence` each met all three guards at
both horizons. Wet-amount dependence had the widest Daymet miss but failed the
30-year GHCN-off guard at 0/8, illustrating why rank alone is not qualification
[E07] [E08].

| Rank | Family | Daymet-off material, 30/100 yr | Faithful material, 30/100 yr | GHCN-off material, 30/100 yr | Available Daymet-off cells | Pooled median severity | Qualifies |
|---:|---|---:|---:|---:|---:|---:|---|
| 1 | `wet_amount_dependence` | 16/15 | 15/17 | 0/5 | 33 | 2.22 | no |
| 2 | `spell_structure` | 14/16 | 15/16 | 5/7 | 34 | infinity | yes |
| 3 | `higher_order_occurrence` | 12/14 | 11/16 | 5/7 | 34 | 1.53 | yes |
| 4 | `wet_amount_upper_tail` | 7/14 | 11/17 | 0/2 | 34 | 1.47 | no |
| 5 | `multiday_extremes` | 4/9 | 6/12 | 2/6 | 34 | 0.861 | no |

The severity column is the pooled median of observed-distance/null-ceiling
ratios over the stated available Daymet-off station-horizon cells. Spell
structure has 18 positive/zero-ceiling cells and one zero/zero cell; under the
registered extended-real rule its pooled median is `infinity`. Severity is a
tie-break after breadth, not a population effect size [E05] [E07].

### QC-arm diagnostics

QC-off effects were not uniform. For example, the off arm had a smaller
wet-amount-dependence distance at 14/17 stations at 30 years and 16/17 at 100
years, while it had a smaller upper-tail distance at only 4/17 at each
horizon. These are directional comparisons, not material-change findings
[E07].

| Family | Horizon (yr) | Off smaller | Equal | Off larger | Unavailable |
|---|---:|---:|---:|---:|---:|
| Spell structure | 30 | 12 | 1 | 4 | 0 |
| Spell structure | 100 | 5 | 7 | 5 | 0 |
| Higher-order occurrence | 30 | 8 | 0 | 9 | 0 |
| Higher-order occurrence | 100 | 8 | 0 | 9 | 0 |
| Wet-amount dependence | 30 | 14 | 0 | 1 | 2 |
| Wet-amount dependence | 100 | 16 | 0 | 1 | 0 |
| Wet-amount upper tail | 30 | 4 | 0 | 13 | 0 |
| Wet-amount upper tail | 100 | 4 | 0 | 13 | 0 |
| Multi-day extremes | 30 | 11 | 0 | 6 | 0 |
| Multi-day extremes | 100 | 10 | 0 | 7 | 0 |

### Propagation diagnostics

All eight daily-family/dispersion Spearman coefficients were positive, ranging
from 0.093 to 0.696, but no propagation bound was registered. Joint-material
counts varied by horizon and QC arm. The measurements support co-location in
this station set, not causal propagation from a daily miss to aggregated
dispersion [E07].

| Horizon (yr) | QC arm | Monthly Spearman | Annual Spearman | Joint daily/monthly | Joint daily/annual |
|---:|---|---:|---:|---:|---:|
| 30 | faithful | 0.581 | 0.696 | 14/17 | 7/17 |
| 30 | off | 0.213 | 0.093 | 4/17 | 4/17 |
| 100 | faithful | 0.419 | 0.326 | 15/17 | 13/17 |
| 100 | off | 0.306 | 0.355 | 11/17 | 9/17 |

## Limitations and validity

Internal validity is limited by eight deterministic burn offsets, which bound
only observed trajectory spread and are not IID uncertainty. The 30-year
records are nested within the 100-year records. Observations cover one fixed
46-year window while generated metrics use 30 or 100 years; the null does not
model observed-sample uncertainty or unequal record length. Parent A5a
evidence and broad summaries were already exposed, and post-outcome amendment
005 corrected real implementation defects. H1--H4 are therefore amended,
not confirmatory [E04] [E05] [E06].

Construct validity is limited by the R1mm threshold, complete-period rules,
component minimums, mixed family-distance scales, and the Daymet calendar
transform. The project's no-leap mapping can shift official Daymet civil-date
labels by one day from March through December in leap years, affecting
seasonal attribution near boundaries [R06]. Daymet is a gridded estimate, not
point truth. GHCN is incomplete, dynamically reprocessed, not homogenized for
all reporting changes, and shares observing-system lineage with Daymet [R03]
[R04] [R05]. Missingness is broken rather than modeled.

External validity is limited to the purposive 17-station set, including one
fixture-labelled location, the eight available U.S. Cooperative GHCN series,
the archived 1980--2025 products, the `faithful_5_32_3` profile, and rendered
precipitation. Results do not identify the responsible CLIGEN mechanism,
prove first-order Markov causation, evaluate storm descriptors or winter
physics, reject CLIGEN generally, or predict A7b performance [E10] [E12].

## Conclusions

A7a measured a bounded daily precipitation-structure priority. Seasonal spell
structure and higher-order occurrence residuals exceeded deterministic
trajectory spread across every required Daymet, faithful, and GHCN sensitivity
breadth guard at both horizons. This supports the package terminal
`DAILY-PRECIPITATION-GAP-MEASURED` and permits a separately scoped A7b analytic
feasibility study. It does not authorize implementation or promotion of a new
precipitation mechanism. A7b may evaluate mechanisms motivated by the
qualifying families, but A7a neither selects a mechanism nor predicts success
before any production Rust or station-format commitment [E08] [E15].

## Reproducibility and data availability

The experiment started from source commit
`d27a008e91a4853044aed5207d02a3aeb631ac8c`. The pre-analysis and successor
post-analysis freezes preserve the access/amendment chain and bind the
corrected analyzer, verifier, inputs, and outputs [E04] [E06]. The canonical
analysis SHA-256 is
`45342c8763c3d079c81f8a9b3910882bdd82f2557dfb420a80d5a4bfefa2b1ad`;
the terminal decision SHA-256 is
`c5aab286d5fffb8a61bb3bb50ac228f636d6da97f6e0880973f478073e0b1c0f`
[E07] [E08].

No new A7a artifact uses Git LFS; the canonical JSON remains ordinary,
diffable Git content [E07]. The reused A5a baseline archive is also existing
regular Git content and is hash-pinned by the freeze and baseline manifest
[E06] [E09]. Daymet and GHCN data retain their upstream terms and repository
third-party notice; no local copyrighted reading copy is linked [E11]. The
reference audit preserved the frozen R04 identity and appended R05/R06 without
rewriting the access history [E16]. The
consolidated review and exact final gate commands are repository records
[E13] [E14].

## References

### Publications and datasets

- **R01.** Richardson, C. W. 1981. Stochastic simulation of daily
  precipitation, temperature, and solar radiation. *Water Resources Research*
  17(1):182--190. [DOI](https://doi.org/10.1029/WR017i001p00182).
- **R02.** Katz, R. W., and M. B. Parlange. 1998. Overdispersion phenomenon in
  stochastic modeling of precipitation. *Journal of Climate* 11(4):591--601.
  [DOI](https://doi.org/10.1175/1520-0442(1998)011%3C0591:OPISMO%3E2.0.CO;2).
- **R03.** Thornton, M. M., R. Shrestha, Y. Wei, P. E. Thornton, and S.-C. Kao.
  2022. *Daymet: Daily Surface Weather Data on a 1-km Grid for North America,
  Version 4 R1*. Version 4.1 [17 single-pixel extracts]. ORNL Distributed
  Active Archive Center. Accessed 2026-07-12.
  [DOI](https://doi.org/10.3334/ORNLDAAC/2129).
- **R04.** Menne, M. J., I. Durre, R. S. Vose, B. E. Gleason, and T. G.
  Houston. 2012. An overview of the Global Historical Climatology Network-
  Daily database. *Journal of Atmospheric and Oceanic Technology*
  29(7):897--910. [DOI](https://doi.org/10.1175/JTECH-D-11-00103.1).
- **R05.** Menne, M. J., I. Durre, B. Korzeniewski, S. McNeill, K. Thomas,
  X. Yin, S. Anthony, R. Ray, R. S. Vose, B. E. Gleason, and T. G. Houston.
  2012. *Global Historical Climatology Network--Daily (GHCN-Daily), Version
  3* [eight-station U.S. Cooperative Network subset]. NOAA National Climatic
  Data Center. Accessed 2026-07-12.
  [DOI](https://doi.org/10.7289/V5D21VHZ).
- **R06.** ORNL DAAC. 2026. Daymet Daily V4 R1 guide. No DOI.
  [Official guide](https://daac.ornl.gov/DAYMET/guides/Daymet_Daily_V4R1.html).

### Repository records and reproducibility artifacts

- **E01.** [ADR-0001](../decisions/0001-source-code-authority-port.md) —
  faithful source-authority boundary.
- **E02.** [Measurement contract](../work-packages/20260714-a7a-daily-precipitation-structure-baseline/artifacts/measurement-contract-v1.json) —
  frozen metrics, null, ranking, and decision rules.
- **E03.** [Design boundary](../work-packages/20260714-a7a-daily-precipitation-structure-baseline/artifacts/design.md) —
  measurement scope and interpretation limits.
- **E04.** [Pre-analysis freeze](../work-packages/20260714-a7a-daily-precipitation-structure-baseline/artifacts/pre-analysis-freeze-v4.json) —
  final pre-outcome source/input freeze and amendment chain.
- **E05.** [Post-analysis amendment 005](../work-packages/20260714-a7a-daily-precipitation-structure-baseline/artifacts/post-analysis-amendment-005.md) —
  internal-review arithmetic and component-support corrections.
- **E06.** [Post-analysis freeze v2](../work-packages/20260714-a7a-daily-precipitation-structure-baseline/artifacts/post-analysis-freeze-v2.json) —
  corrected output identities and preserved first-result hashes.
- **E07.** [Canonical analysis](../work-packages/20260714-a7a-daily-precipitation-structure-baseline/artifacts/a7a-analysis-v1.json) —
  complete generated, observed, comparison, QC, and propagation evidence.
- **E08.** [Terminal decision](../work-packages/20260714-a7a-daily-precipitation-structure-baseline/artifacts/a7a-decision-v1.json) —
  ranked families, qualifiers, and terminal result.
- **E09.** [A5a baseline manifest](../work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts/baseline-run-manifest-v1.json) —
  retained stream/report identities and membership.
- **E10.** [Observed source manifest](../work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts/corpus/source-manifest-v1.json) —
  archived Daymet/GHCN identities, availability, periods, and hashes.
- **E11.** [Third-party data notice](../../references/observed/a5a-v1/THIRD_PARTY_DATA_NOTICE.md) —
  dataset citation and public-use boundary.
- **E12.** [Frozen claim-evidence ledger](../work-packages/20260714-a7a-daily-precipitation-structure-baseline/artifacts/claim-evidence-ledger.md) —
  permitted and prohibited claim scope.
- **E13.** [Consolidated review](../work-packages/20260714-a7a-daily-precipitation-structure-baseline/artifacts/review.md) —
  three-lens findings, dispositions, and residual uncertainty.
- **E14.** [Gate results](../work-packages/20260714-a7a-daily-precipitation-structure-baseline/artifacts/gate-results.md) —
  exact package, report, repository, and safety gate results.
- **E15.** [A7a work package](../work-packages/20260714-a7a-daily-precipitation-structure-baseline/package.md) —
  objective, authorization, scope, and terminal closure record.
- **E16.** [Reference-corpus amendment 006](../work-packages/20260714-a7a-daily-precipitation-structure-baseline/artifacts/reference-corpus-amendment-006.md) —
  stable R04 identity and audited R05/R06 additions.
