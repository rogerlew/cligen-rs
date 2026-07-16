# A9c4 context-support and evidence-completeness correction

Report ID: `a9c4-context-support-completeness`
Status: `ACCEPTED`
Date: 2026-07-15
Revision: 1
Authors: cligen-rs project contributors
Evidence mode: Mixed
Experiment record: [A9c4 work package](../work-packages/20260715-a9c4-context-support-completeness/package.md)
Evidence snapshot: [report manifest](a9c4-context-support-completeness-report.manifest.json)
Review record: [consolidated internal review](../work-packages/20260715-a9c4-context-support-completeness/artifacts/review.md)

## Abstract

A9c4 asked whether the A9c3 successor comparison could be made complete before
correcting physically unsupported event-context output. A pre-output audit
decomposed 111 originally applicable A9c3 mandatory 30-year cells by observed,
faithful, and historical-candidate availability. Ninety-two cells were
retained under the applicable candidate-blind rules: 68 non-storm cells had
the required observed/faithful common support, and 24 storm cells used the
inherited grouped-contributor policy. Nineteen cells became explicit
`report_only_not_evaluated` cells; each lacked the required two observed
Daymet contributors, with 15 having zero and four having one. The faithful
comparator removed no additional non-storm cell. The resulting mask lacked
any retained wet-amount or compound-
context objective in the arid-boundary, hot-arid, and monsoonal-transition
regimes, failing six frozen family/regime breadth requirements. The campaign
therefore stopped at `HOLD-A9C4-COMPLETENESS-SURFACE` before any corrected
A9c4 fit, output, or selection [E02] [E04] [E05]. This result identifies an
evidence-surface limitation; it does not assess the proposed context laws or
either model class.

## Introduction

A9c3 found finite grouped storm descriptors but stopped because every
candidate prefix violated physical support for event-context solar radiation,
wind speed, or relative humidity. Its accepted review also required the 19
unavailable mandatory rows to be attributed before another candidate was
generated [E07] [E08]. A9c4 was deliberately ordered around that requirement:
audit evidence completeness first, then fit bounded context laws only if a
broad comparison remained possible [E01] [E02].

The daily development observations are normalized Daymet V4 R1 records
[R01]. USCRN supplies the inherited storm/context source identity and grouped
storm construct [R02] [R03] [R04], but A9c4 did not reread USCRN station-year series.
The new audit read Daymet development records and accepted predecessor
metadata/evidence only [E09] [E10]. Exact project object identities, rather
than product descriptions, govern the result.

## Hypotheses

All five rules were frozen before the availability outcome. A hypothesis not
reached after the early hold is reported as not evaluated, not as supported by
an empty candidate set.

| ID | Provenance | Scope and comparison | Decision rule | Outcome | Result |
|---|---|---|---|---|---|
| H1 | preregistered | Source-specific evidence completeness | Decompose all applicable cells and freeze a breadth-complete observed/faithful mask | Not supported: decomposition completed, but the frozen mask failed its breadth guard | [Completeness result](#completeness-result) |
| H2 | preregistered | Structural event-context support | Every corrected output passes solar, wind, and humidity support without repair | Not evaluated: no corrected A9c4 event-context output was generated | [Early-stop result](#early-stop-result) |
| H3 | preregistered | Fresh fit applicability and class distinction | Both classes retain a valid A9c4 fit and remain non-isomorphic | Not evaluated: no A9c4 configuration was fit or structurally audited | [Early-stop result](#early-stop-result) |
| H4 | preregistered | Frozen selector safety and result | Execute the registered filters and seal at most one candidate | Not evaluated: no candidate entered A9c4 evaluation or selector execution | [Early-stop result](#early-stop-result) |
| H5 | preregistered | Confirmation firewall | Executed audit path has no locked confirmation target-series access | Supported as recorded: the audit path had no confirmation-series load | [Confirmation firewall](#confirmation-firewall) |

## Methods

### Study identity

| Fact | Registered value |
|---|---|
| Source commit | 08d1bf84989bb057537648c65b9ed0e9df104883 |
| Campaign id | a9c4-context-support-completeness-v1 |
| Audit horizon years | 30 |
| Audit burns | 0, 101 |
| Daymet development stations | 20 |
| Originally applicable mandatory cells | 111 |
| Retained mandatory cells | 92 |
| Report only cells | 19 |
| Historical a9c3 candidates | 6 |
| Historical status records | 666 |
| Historical status mismatches | 0 |
| Historical count label discrepancies | 96 |
| Failed family regime combinations | 6 |
| Fresh a9c4 fits | 0 |
| Corrected a9c4 output streams | 0 |
| Full development configurations | 0 |
| Pareto replay configurations | 0 |
| Selected configurations | 0 |
| Confirmation target series accessed | false |
| Audit wall seconds | 252.2390944575891 |
| Faithful audit binary sha256 | c16f633bd3ebdc099e7ee41c53077322763b82c368555a7c6b120ecc2a34f6d9 |
| Terminal | HOLD-A9C4-COMPLETENESS-SURFACE |

### Prospective boundary

The package hash-bound 11 accepted predecessor files, its source commit, and
the candidate-blind mask rule before the audit [E01] [E02] [E03]. The mask
could use observed and faithful availability only. Historical A9c3 candidate
availability was required for cause diagnosis but prohibited from deciding
which cells were retained. Missing evidence could not receive a favorable
value. A breadth guard required each originally applicable family/regime to
retain at least one mandatory cell; winter objectives applied only to the cold
regime [E02].

### Data and objective population

The executed audit loaded the 20 Daymet development objects for 2010--2025.
It did not reload the coefficient-fit role, acquire data, or read USCRN or
confirmation station-year series. The A9c manifest remains the authority for
normalized object roles and hashes [E09] [E10].

The population was 111 originally applicable A9c3 mandatory cells at the
30-year horizon: 18 non-winter objective IDs across six regimes plus three
winter objective IDs in cold only. Engineering hard invariants were not part
of this availability mask. For a non-storm cell, a station was common-support
eligible when its observed feature was available and its faithful feature was
available in both burns 0 and 101. A cell was retained at two or more common
stations. Storm cells instead retained A9c3's accepted grouped-contributor
policy; they were not recomputed through the non-storm feature rule [E02]
[E04] [E13].

### Faithful and historical diagnostic generation

The audit built the unchanged Rust `faithful_5_32_3` comparator in a fresh
isolated release target and ran the selected station parameters at the two
audit burns. The executed binary hash and Rust tool versions are recorded in
the audit. No Fortran binary was executed; the vendored Fortran remains the
semantic authority under ADR-0001 [E04] [E11].

Six A9c3-valid historical fits were regenerated for 30 years at the same two
burns. Their 522 non-storm statuses were recomputed: 408 available and 114
unavailable, with zero mismatch against A9c3. The 144 storm statuses were
copied from A9c3 under the inherited grouped policy rather than recomputed.
All 666 stored values therefore match A9c3, but only the non-storm subset is a
recomputation result. These streams were diagnostic inputs, not mask-selection
inputs and not corrected A9c4 output. The audit did not retain the streams or
their hashes [E04] [E09] [E13].

### Planned context correction and stop rule

Had the completeness gate passed, A9c4 would have refit the same eight
configurations with event air temperature Gaussian in identity space, solar
radiation and wind speed lognormal, and relative humidity logit-normal. Solar
and wind observed zeros and humidity boundaries had a frozen `1e-6` transform
epsilon. Generation would use inverse transforms, with no realized-output
clipping or repair. No other model mechanism was to change [E02]. These laws
were specified but never fit or tested because the mask's breadth guard failed
first.

## Analysis

Availability was evaluated as a Boolean feature property, not a distance or
score. For every non-storm objective/regime cell, the audit recorded observed-
available station identities and the subset available in both faithful burns.
The prospective role was `mandatory` at two or more common stations and
`report_only_not_evaluated` otherwise. Excluded cells retained their counts
and identities but no favorable selection value [E04] [E05].

For diagnosis, the audit stored six historical configurations × 111 cells, or
666 statuses, alongside the accepted A9c3 short-screen record. It recomputed
522 non-storm statuses with zero mismatch and copied 144 available storm
statuses under the inherited policy. The resulting stored totals are 552
available and 114 unavailable. An independent recheck also found 96 storm
count-label discrepancies: for six configurations × four objectives × four
four-contributor regimes, A9c4 stored the generated-contributor count of four
where A9c3 stored the observed-group count of two. The copied status stayed
available in both records. This does not affect the mask or terminal, but it
prevents claims of complete independent status or count reproduction [E04]
[E07] [E13].

After the audit file was written, the first run encountered a Python `false`
versus `False` typo while constructing the mask. A deterministic closeout
loaded the unchanged audit and applied the already frozen rule; it did not
regenerate results or access corrected output [E06] [E09].

## Results

### Completeness result

H1 was not supported. The audit successfully decomposed all 111 cells. It
retained 68 non-storm cells through the common-support rule and 24 storm cells
through the inherited grouped policy; 19 non-storm cells became report-only.
For all non-storm cells, observed and faithful-all-burn station counts were
identical; faithful generation removed no additional cell. Thus every
exclusion lacked the required two observed contributors under A9c3's
registered estimands [E04] [E05].

| Family | Originally applicable cells | Retained | Report only |
|---|---:|---:|---:|
| Aggregate | 24 | 24 | 0 |
| Compound context | 6 | 3 | 3 |
| Extreme | 6 | 6 | 0 |
| Occurrence spell | 24 | 22 | 2 |
| Storm descriptor | 24 | 24 | 0 |
| Wet amount | 24 | 10 | 14 |
| Winter proxy | 3 | 3 | 0 |
| **Total** | **111** | **92** | **19** |

The excluded-cell table gives observed/faithful-all-burn station counts. Each
row is at the 30-year audit horizon [E04].

| Objective | Regime(s), observed/faithful count |
|---|---|
| Wet-spell survival | hot arid 0/0 |
| Dry-spell survival | hot arid 0/0 |
| Monthly wet mean | arid boundary 0/0; hot arid 0/0; monsoonal transition 1/1 |
| Monthly wet CV | arid boundary 0/0; hot arid 0/0; monsoonal transition 1/1 |
| Adjacent wet dependence | arid boundary 0/0; hot arid 0/0; monsoonal transition 0/0; non-monsoonal semi-arid 0/0 |
| Upper tail | arid boundary 0/0; hot arid 0/0; monsoonal transition 0/0; non-monsoonal semi-arid 0/0 |
| Wet/dry temperature context | arid boundary 1/1; hot arid 0/0; monsoonal transition 1/1 |

The 19 exclusions were 14 wet-amount, three compound-context, and two
occurrence-spell cells. By regime, they were five arid-boundary, seven hot-
arid, five monsoonal-transition, and two non-monsoonal-semi-arid cells. The
breadth guard failed in six combinations: wet amount and compound context in
each of arid boundary, hot arid, and monsoonal transition [E04] [E05] [E12].

### Historical status comparison

For each historical configuration, the 87 recomputed non-storm cells contained
68 available and 19 unavailable statuses; all matched A9c3. The 24 storm
statuses per configuration were copied as available under the inherited
grouped policy. Consequently, each stored 111-cell vector contains 92
available and 19 unavailable values, and all 666 stored values match A9c3,
but only 522 are recomputation evidence [E04] [E07]. The 96 storm contributor-
count label discrepancies described in Analysis remain a disclosed artifact
defect, not a status or terminal discrepancy [E13].

### Early-stop result

The mask records `status: hold` and
`HOLD-A9C4-COMPLETENESS-SURFACE`. The campaign did not fit either corrected
class, generate corrected A9c4 context output, execute support checks, enter
full development or replay, invoke the selector, or seal a candidate. H2, H3,
and H4 therefore were not evaluated. The specified log/logit support laws
cannot be described as successful or unsuccessful [E02] [E05].

### Confirmation firewall

H5 is supported as a bounded implementation claim. The hash-bound audit code
loads Daymet development objects and accepted predecessor artifacts; it has no
USCRN or confirmation-series load path. Confirmation metadata remained
available only to enforce the inherited firewall. This is not an operating-
system file-access audit [E02] [E09] [E10].

## Limitations and validity

Internal validity is strongest for the mask and terminal: predecessor hashes
passed, all 111 keys are unique, the mask partitions them 92/19 without
overlap, and the 522 recomputed non-storm statuses match A9c3. The 144 storm
statuses are inherited rather than an independent check. Exact feature
recomputation still requires the inherited LFS observations and parameter archive. Per-burn
historical candidate availability and diagnostic stream hashes were not
retained.

The storm rows are a construct exception: their availability is inherited
from grouped-contributor policy rather than measured with the non-storm common-
support rule. Ninety-six storm count fields are mislabeled relative to A9c3,
although their statuses and retention are unchanged [E13]. Historical non-
storm counts use A9c3's any-burn union semantics; they do not test the stronger
future rule requiring candidate availability in every stage burn.

The audit covers 30 years and two burns only. It establishes neither 100-year
availability nor fit, physical support, monthly reconciliation, degradation,
selection, or confirmation behavior. A9c3's 8--18 material-degradation rows
remain unresolved [E08].

The proposed lognormal laws cannot represent an exact zero mass, and the
`1e-6` solar/wind substitutions and humidity boundary clamp have no sensitivity
analysis. Overflow, underflow, and realized support were not tested. No
scientific suitability claim follows from the mathematical support proposal.

External validity remains limited to the frozen six-regime development panel,
Daymet 2010--2025 feature availability, the inherited grouped-storm construct,
and A9c3's objective definitions. The hold does not imply that either candidate
class is inadequate or that faithful CLIGEN is superior.

## Conclusions

A9c4 answered the prerequisite question and stopped in the right place. The
19 A9c3 unavailable mandatory cells are not created by the successor models;
all lacked the required two observed contributors under the registered
estimands. Simply fixing solar, wind, and humidity support would leave wet-
amount and compound-context evaluation missing in three dry-transition
regimes.

A9c4 is closed at this hold; its failed breadth guard and H1 outcome cannot be
overridden or relabeled. The next action must therefore be a separately
identified, prospectively frozen successor campaign before any new candidate
output. That successor may accept the 92-cell surface with its named regime/
family limitations, replace sparse-data estimands while preserving their
scientific questions, or expand observed evidence. It should not add selector
or model complexity. Only after the successor freezes that decision should it
fit and test the bounded context-law correction.

## Reproducibility and data availability

The execution boundary is commit
`08d1bf84989bb057537648c65b9ed0e9df104883` on `main`. Run
`python -m research.a9c4.audit` from the repository root to reproduce the audit
and deterministic mask closeout in an empty A9c4 artifact state; the first-run
closeout correction and the independent count-label deviation are preserved
instead of hidden [E06] [E09] [E13]. The report evidence freeze and claim
ledger bind the report inputs [E12].

Inherited normalized observations use Git LFS, and their identities are
checked against the A9c source manifest. A9c4 created no new large data
object. Raw USCRN annual files remain URL/hash identified and are not
redistributed. Apache-2.0 licensing of repository code does not relicense
Daymet or NOAA data. Copyrighted local reading copies are not public report
dependencies [E10].

The faithful audit comparator was Rust, freshly built from a generator tree
verified equivalent to A9c3's recorded comparator source. No new Fortran
binary evidence was produced; faithful semantics remain governed by the
vendored Fortran under ADR-0001 [E03] [E04] [E11].

## References

### Publications and datasets

- **R01.** Thornton et al. (2022). *Daymet: Daily Surface Weather Data on a
  1-km Grid for North America, Version 4 R1*. Dataset version 4.1. Accessed
  2026-07-15. [DOI](https://doi.org/10.3334/ORNLDAAC/2129).
- **R02.** Palecki et al. (2015). *U.S. Climate Reference Network Processed
  Data from USCRN Database Version 2* [Subhourly01 format 01/OAP 2.1.1
  subsets]. Accessed 2026-07-15.
  [DOI](https://doi.org/10.7289/V5MS3QR9).
- **R03.** NOAA NCEI. *USCRN/USRCRN Subhourly01 file documentation*. No DOI.
  Accessed 2026-07-15.
  [Official documentation](https://www.ncei.noaa.gov/pub/data/uscrn/products/subhourly01/readme.txt).
- **R04.** Diamond et al. (2013). *U.S. Climate Reference Network after One
  Decade of Operations: Status and Assessment*.
  [DOI](https://doi.org/10.1175/BAMS-D-12-00170.1).

### Repository records and reproducibility artifacts

- **E01.** [Execution dispatch](../work-packages/20260715-a9c4-context-support-completeness/artifacts/execution-dispatch-v1.json) — authorization and source boundary.
- **E02.** [Design freeze](../work-packages/20260715-a9c4-context-support-completeness/artifacts/design-freeze-v1.json) — prospective correction, mask, hypotheses, and terminals.
- **E03.** [Predecessor manifest](../work-packages/20260715-a9c4-context-support-completeness/artifacts/predecessor-manifest-v1.json) — accepted input identities.
- **E04.** [Availability audit](../work-packages/20260715-a9c4-context-support-completeness/artifacts/availability-audit-v1.json) — canonical source-specific cell evidence.
- **E05.** [Evidence mask](../work-packages/20260715-a9c4-context-support-completeness/artifacts/evidence-mask-v1.json) — retained/report-only cells, breadth gate, and terminal.
- **E06.** [Mask closeout correction](../work-packages/20260715-a9c4-context-support-completeness/artifacts/post-audit-closeout-correction.md) — exact execution chronology.
- **E07.** [A9c3 evaluation](../work-packages/20260715-a9c3-two-site-grouped-observed-comparison/artifacts/evaluation-v1.json) — accepted historical statuses.
- **E08.** [A9c3 accepted report manifest](a9c3-two-site-grouped-observed-comparison-report.manifest.json) — predecessor scientific boundary.
- **E09.** [Audit implementation](../../research/a9c4/audit.py) — source-specific audit and closeout code.
- **E10.** [Observed source manifest](../work-packages/20260715-a9c-observed-development/artifacts/observed-source-manifest-v1.json) — exact object roles and hashes.
- **E11.** [ADR-0001](../decisions/0001-source-code-authority-port.md) — faithful source authority.
- **E12.** [Claim-evidence ledger](../work-packages/20260715-a9c4-context-support-completeness/artifacts/claim-evidence-ledger.md) — frozen report crosswalk.
- **E13.** [Availability-label deviation](../work-packages/20260715-a9c4-context-support-completeness/artifacts/post-outcome-methods-deviation.md) — 96 count-label discrepancies and bounded consequence.
