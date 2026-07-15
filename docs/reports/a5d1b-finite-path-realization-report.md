# Finite-path realization after stationary selector feasibility

Report ID: `a5d1b-finite-path-realization`
Status: `ACCEPTED`
Date: 2026-07-14
Revision: 1
Authors: cligen-rs project contributors
Evidence mode: Mixed
Experiment record: [A5d1b work package](../work-packages/20260714-a5d1b-finite-path-realization/package.md)
Evidence snapshot: [report manifest](a5d1b-finite-path-realization-report.manifest.json)
Review record: [consolidated internal review](../work-packages/20260714-a5d1b-finite-path-realization/artifacts/review.md)

## Abstract

A5d1 produced valid stationary constrained weights for a 256-year CLIGEN
development library at 17 stations, but none of its 306 finite paths passed the
complete contract. A5d1b separated integer-count construction from path
ordering. Derived replay of the 153 eligible predecessor paths showed that 151
first failures included a count-dependent failure and that only two existing
multisets passed count-only replay at both 30 and 100 years. The controlling
bounded integer search retained and independently validated every available
HiGHS incumbent, regardless of optimality status. It produced one exact nested
30-/100-year witness (`wy485345`) and therefore did not meet the registered
17/17 gate. Among the other 16 stations, separate 30-year searches retained no
incumbent, while separate 100-year searches retained 15 incumbents, 14 of which
passed independent linear and exact nonlinear replay. Ordering was consequently
skipped. The terminal status is `EXECUTED-HOLD-COUNT-SEARCH-BOUNDED`: a global
construction was not demonstrated under the registered bound, but
infeasibility was not proved. Confirmation and candidate promotion remain
unauthorized. [E12] [E13] [E14] [E15] [E16] [E17]

## Introduction

The proposed successor to CLIGEN's fixed interannual structure selects and
orders complete faithful generated years rather than modifying daily physical
values. A5d1 showed that fractional stationary weights could preserve the
registered monthly and unparameterized surfaces while improving centered
annual variance/covariance targets at every development station. A finite
30- or 100-year realization additionally needs integer reuse counts, an exact
common prefix, Gregorian calendar compatibility, and an order that preserves
boundary and serial behavior. [E19] [E20] [E21] [E22]

A5d1's path search swapped positions inside an already chosen 100-year
multiset. It could change the first 30 positions but could not repair a
deficient 100-year count vector. Its finite-path hold therefore established a
failure of the tested constructions, not the absence of some other integer
multiset. A5d1b isolates that count question before authorizing another
ordering heuristic. The predecessor narrative report has a dispositioned
review-hash mismatch and is contextual only; the cited A5d1 machine results and
decision are controlling. [E20] [E21] [E22] [E23] [E26]

The climate targets derive from exposed Daymet V4 R1 daily estimates for
1980–2009 at these 17 stations. Daymet is a gridded product rather than
point-observation truth, and this package neither changes the target period nor
expands the station population. [R01]

## Hypotheses

The scientific questions and decision rules were recorded before A5d1b
actual-station outcomes. A5d1 results were already exposed development
evidence. The hypotheses remained unchanged, but the controlling count
implementation was corrected after a flawed v3 outcome had been exposed; the
corrected run is therefore not presented as a pristine confirmatory test.
[E01] [E03] [E08] [E10]

| ID | Provenance | Scope and comparison | Decision rule | Outcome | Result |
|---|---|---|---|---|---|
| H1 | preregistered | At all 17 stations, the pool-256 stationary support admits nested 30-/100-year integer counts under the unchanged order-independent A5d1 finite rules | Independently replayed exact joint witnesses pass both horizons at 17/17 stations | Not demonstrated globally under the registered bound; 1/17 exact joint witnesses | [Count construction](#count-construction) |
| H2 | preregistered | Conditional on H1, one globally frozen count-first ordering construction passes the complete A5d1 path contract across all stations and three seeds | All 51 conditional path cells pass | Not evaluated; the H1 all-station gate failed and ordering was skipped | [Conditional ordering](#conditional-ordering) |
| H3 | preregistered | Conditional on construction, every path preserves calendar, reuse, cooldown, positive support, physical rows, and the exact 30-year prefix | Every constructed cell passes every invariant with zero physical intervention | Not evaluated; no A5d1b ordered path was constructed | [Conditional ordering](#conditional-ordering) |

## Methods

### Authority and access boundary

The accepted A5d1 contract v4 remained the finite-climate authority. Its 534
preservation inequalities, centered annual component and aggregate rules,
January transition accounting, boundary vector, dependence rules, and physical
identity invariants were not relaxed. A5d1b added a development-only
realization procedure, not a production profile or interface. [E01] [E19]

The evidence lock binds the source commit, contract and schema, 17 feature
files, 17 pool-256 marginal certificates, faithful-off libraries, synthetic
fixtures, and conditional matrices. It records zero confirmation exposure.
[E02]

### Freeze and correction chronology

The root v1 freeze preceded every A5d1b result. Two pre-result serialization
failures then required append-only amendments: amendment 001 made a missing
`mip_gap` nullable, freeze v2 rebound the tools, amendment 002 made a missing
`mip_node_count` nullable, and freeze v3 rebound them again. Neither failure
emitted a count certificate or aggregate. [E03] [E04] [E05] [E06] [E07]

The completed v3 run was invalidated after independent review found that it
equated `OptimizeResult.success` with feasibility. That discarded one joint
and six separate-100 time-limit incumbents without extracting their counts.
Post-outcome amendment 003 explicitly records an implementation change:
acceptance now requires independent integrality, bound, and primal-constraint
replay of any retained incumbent, irrespective of solver optimality status,
followed by exact count replay. The v3 outputs and tool bytes remain hash-bound
history. [E08]

Freeze v4 preceded the corrected station solves. All 17 v4 station
certificates were written, after which aggregate construction failed on a
missing import. Those certificates were archived and invalidated. Post-outcome
amendment 004 added only the missing aggregate import; it changed no scientific
calculation, algorithm, tolerance, or matrix. Freeze v5 preceded the complete
controlling rerun. [E09] [E10] [E11]

### Inherited-path decomposition

For every eligible pool-256 A5d1 station-algorithm-seed cell, A5d1b
reconstructed 30- and 100-year empirical count vectors. Monthly and annual
preservation, centered annual noninferiority/improvement, temperature
ordering, calendar totals, maximum reuse, and positive support were classified
as count-dependent. Realized January cross-block transitions,
boundary/spell behavior, cooldown, and detrended dependence remained
order-dependent. [E12]

### Joint count construction

Each station model used integer vectors `c30` and `c100` for 256 source years.
It required `0 <= c30[i] <= c100[i] <= 2`, zero count outside positive
stationary support, totals 30 and 100, and exact Gregorian totals of 23 common
plus seven leap years at 30 years and 76 common plus 24 leap years at 100
years. The original 534 unscaled preservation inequalities were applied at
each horizon. Stationary exact-mean and leap-mass equalities were intentionally
excluded because A5d1 finite replay did not impose them. [E01] [E13] [E19]

The mixed-integer objective minimized L1 distance from stationary weights with
a small deterministic scalar index perturbation. This was not a separate
lexicographic optimization. Centered variances/covariances are nonlinear in
empirical means, so the bounded sequential procedure linearized their mean
products, solved, recomputed exact binary64 metrics, and repeated for at most
12 iterations when an incumbent existed. Every incumbent was independently
replayed before use. If a joint witness did not pass, separate 30- and
100-year models supplied localization diagnostics. [E01] [E13] [E14]

HiGHS received a three-second `time_limit` option per call. That option is not
a hard process-wall ceiling: wrapper and solver overhead can make recorded wall
time slightly larger. Calls were scheduled within 120 seconds per station; the
registered total, peak-memory, and retained-artifact limits were checked
separately. [E25]

### Conditional ordering

The frozen ordering stage could run only after exact joint witnesses at all 17
stations. It would place the 30-year multiset and 70-year suffix with
calendar/cooldown backtracking, then apply fixed-count, same-calendar swaps
under three inherited seeds. The count gate failed, so this stage produced no
path or physical climate output. [E01] [E15]

### Study identity

| Fact | Registered value |
|---|---|
| Stations | 17 |
| Horizons years | 30, 100 |
| Inherited eligible path cells | 153 |
| Inherited count only both horizon passes | 2 |
| Count station cells | 17 |
| Joint raw incumbents | 1 |
| Joint independently accepted incumbents | 1 |
| Joint exact count witnesses | 1 |
| Separate 30 year exact witnesses | 0 |
| Separate 100 year raw incumbents | 15 |
| Separate 100 year independently accepted incumbents | 14 |
| Separate 100 year exact witnesses | 14 |
| Ordered path cells executed | 0 |
| Path seeds | 3 |
| Confirmation objects accessed | 0 |

## Analysis

The inherited diagnostic sampling unit was one station-algorithm-seed path
cell. The count decision unit was one station. H1 required 17 exact joint
witnesses, so a pass at one station could establish local feasibility but not
the global decision rule. The three conditional path seeds were sensitivity
cells, not independent climate replicates. [E01] [E12] [E13]

An accepted linear incumbent had to satisfy independent integer, bound, and
primal-constraint replay. An exact count witness additionally had to pass
integer, nesting, reuse, support, calendar, unscaled preservation, temperature
ordering, and nonlinear centered replay. The closure audit repeated every
joint and separate-horizon witness and mutation-tested the single-witness
replay path. Solver status alone was never a climate pass. [E13] [E14]

The report distinguishes four quantities: status-0 optimal solver results, raw
time-limit incumbents, independently accepted linear incumbents, and exact
nonlinear witnesses. A status without a repository-checkable certificate is a
bounded search outcome, not a proof of infeasibility. No uncertainty interval
is applicable because this is a deterministic bounded construction matrix, not
an estimate from sampled replicates. [E13] [E14]

The all-station count gate preceded ordering. Consequently, the absence of path
cells is a registered conditional outcome. The terminal decision follows the
machine result, while the review disposition refines the successor action to
start with integer-feasibility scaling and work allocation before nonlinear
localization. [E15] [E16] [E17] [E24]

## Results

### Inherited failure decomposition

Derived replay covered 153/153 eligible A5d1 paths. Of these, 151 first failed
finite-prefix marginal replay and two first failed dependence
noninferiority. Every one of the 151 finite-prefix first failures contained a
count-dependent failure. Only two cells passed count-only replay at both
horizons. At 30 years, seven cells passed base preservation and seven passed
complete count-only replay; at 100 years, nine passed base preservation and
eight passed count-only replay. Reordering those same A5d1 multisets could not
repair their first blocker. [E12]

### Count construction

All 17 controlling joint initial calls ended with HiGHS status 1. One call,
for `wy485345`, retained an independently valid incumbent; its counts passed
the complete exact 30- and 100-year replay at iteration 0. The other 16 joint
calls retained no incumbent. Thus the global observation is 1/17 exact joint
witnesses, not zero witnesses and not an infeasibility result. [E13] [E14]

Separate diagnostics ran for the 16 unresolved stations. For the initial
30-year calls, 15 ended with status 1 and one with status 2; none retained an
incumbent. For the initial 100-year calls, nine ended optimally with status 0,
six ended at status 1, and one ended at status 2. Fifteen retained a raw
incumbent; 14 passed independent
linear replay and all 14 also passed exact nonlinear replay. The remaining raw
incumbent failed the independent acceptance test. [E13] [E14]

Across the controlling count run there were 52 solver calls: 10 status 0, 40
status 1, and two status 2. Forty recorded call walls exceeded three seconds;
the maximum was 3.009906 seconds, consistent with the solver-option versus
process-wall distinction. Maximum station wall time was 11.638102 seconds,
total wall time was 138.488182 seconds, and measured peak RSS was 562,397,184
bytes. [E25]

H1 was not demonstrated globally because its decision rule required 17/17 and
the bounded procedure produced 1/17. The one joint witness and 14 separate
100-year witnesses establish that exact finite count realization is possible
for some registered station/horizon cases. They do not establish feasibility
for the unresolved joint or 30-year cases. [E13] [E14]

### Conditional ordering

The count precondition failed, so ordered execution was recorded as skipped
with zero actual cells and zero path passes. H2 and H3 were not evaluated. No
A5d1b daily climate output was produced and no physical value was modified.
[E15] [E16]

### Decision

The machine decision is `HOLD` with terminal status
`EXECUTED-HOLD-COUNT-SEARCH-BOUNDED`. No structural algorithm was selected;
A5d4, confirmation, and public candidate creation remain unauthorized. The
reviewed first follow-on is a prospective integer-count localization package:
audit row scaling, retain and replay every incumbent, allocate more of the
existing station budget to feasibility, and compare an alternative
formulation before diagnosing nonlinear replay. Ordering remains blocked until
all 17 joint exact witnesses exist. [E16] [E17] [E24]

## Limitations and validity

Internal validity is strengthened by the root pre-outcome design, exact input
hashes, independent witness replay, mutation rejection, and conditional
execution barrier. It is weakened by four amendments. Amendments 001/002 were
pre-result serialization repairs. Amendment 003 was a material post-outcome
implementation correction after v3 discarded incumbents; amendment 004 was a
post-outcome aggregate-only import repair after v4 certificates had been
written. Both exposed runs are preserved and invalidated rather than silently
overwritten. The controlling result should therefore be treated as a
transparent corrected development experiment, not pristine confirmation.
[E03] [E04] [E05] [E06] [E07] [E08] [E09] [E10] [E11]

Construct validity is limited by the formulation and work allocation. Sixteen
joint searches and all 16 separate 30-year searches ended without an accepted
incumbent, so most unresolved branches never reached nonlinear centered
replay. The status-2 results have no repository-checkable infeasibility
certificate. A better-scaled formulation, different integer solver, or
different prospective allocation of the 120-second station budget may find
additional witnesses. [E13] [E14] [E24]

Resource evidence is bounded to the solver process and retained repository
artifacts. Peak RSS was measured for the controlling Python process, and final
retained bytes were checked, but no fine-grained per-library allocation or
external OS pressure trace was collected. The three-second value is a HiGHS
option, not a hard wall-time assertion. [E25]

External validity is limited to 17 exposed development stations, one burn-0
256-year faithful-off library per station, Daymet 1980–2009 targets, A5d1
tolerances, and the tested SciPy/HiGHS formulation and bounds. It does not
establish behavior on untouched confirmation data, other library burns,
different target products, or other selector families. [E01] [E13] [R01]

Because ordering was skipped, the study supplies no new evidence that exact
counts can be arranged to satisfy January transitions, boundaries, cooldown,
and dependence simultaneously. The one joint count witness is not an ordered
path and is not a public candidate. [E14] [E15] [E17]

## Conclusions

A5d1b sharpens the finite-path hold. The dominant predecessor failures were
count-dependent for their existing multisets, supporting a count-first
successor. Corrected incumbent handling then found one exact joint nested
witness and 14 additional exact 100-year-only witnesses. Those positive cases
rule out a blanket claim that finite integer realization is impossible, while
the 1/17 joint result fails the global construction gate.

The defensible terminal decision is a bounded count-search hold. The next work
package should first improve and diagnose linear integer-feasibility search,
row scaling, incumbent retention, and use of the registered station budget.
Only branches with a count vector should proceed to nonlinear centered replay.
Ordering, confirmation, and candidate promotion remain unauthorized until one
prospectively frozen method yields independently replayed exact joint witnesses
at all 17 stations. [E16] [E17] [E24]

## Reproducibility and data availability

The experiment started from accepted source commit
`08db78cb5365b2f961599421826a600dae1c765a`. The contract, evidence lock,
v1–v5 freeze/amendment chronology, controlling aggregates, witness replay,
machine decision, and review disposition are repository records. Seventeen
controlling count certificates are stored in a deterministic Git LFS archive;
the detailed manifest binds its content and every member hash. Invalidated v3
and v4 evidence remains separately named and hash-bound. [E01] [E02] [E03]
[E04] [E05] [E06] [E07] [E08] [E09] [E10] [E11] [E13] [E14] [E18]

The ignored A5d1 working features, marginal certificates, and faithful-off
libraries were admitted only after their bytes matched committed A5d1
manifests. They can be regenerated by the accepted A5d1 workflow. No
confirmation object, secret, operator-specific absolute path, copyrighted
reading copy, production source change, or public candidate output is included.
[E02] [E23] [E26]

## References

### Publications and datasets

- **R01.** Thornton, M. M., Shrestha, R., Wei, Y., Thornton, P. E., Kao,
  S.-C., and Wilson, B. E. 2022. *Daymet: Daily Surface Weather Data on a
  1-km Grid for North America, Version 4 R1*. ORNL DAAC.
  [DOI 10.3334/ORNLDAAC/2129](https://doi.org/10.3334/ORNLDAAC/2129).

### Repository records and reproducibility artifacts

- **E01.** [A5d1b contract v1](../work-packages/20260714-a5d1b-finite-path-realization/artifacts/finite-path-realization-contract-v1.json) — prospective constraints, matrices, resources, algorithms, and selection rule.
- **E02.** [Evidence lock](../work-packages/20260714-a5d1b-finite-path-realization/artifacts/evidence-lock-inputs-v1.json) — source/input identities and access boundary.
- **E03.** [Root freeze v1](../work-packages/20260714-a5d1b-finite-path-realization/artifacts/pre-outcome-freeze-v1.json) — prospective design identity before all outcomes.
- **E04.** [Amendment 001](../work-packages/20260714-a5d1b-finite-path-realization/artifacts/pre-outcome-freeze-amendment-001.json) — nullable `mip_gap` serialization correction.
- **E05.** [Freeze v2](../work-packages/20260714-a5d1b-finite-path-realization/artifacts/pre-outcome-freeze-v2.json) — intermediate amended-tool identity.
- **E06.** [Amendment 002](../work-packages/20260714-a5d1b-finite-path-realization/artifacts/pre-outcome-freeze-amendment-002.json) — nullable node-count serialization correction.
- **E07.** [Freeze v3](../work-packages/20260714-a5d1b-finite-path-realization/artifacts/pre-outcome-freeze-v3.json) — pre-v3-run tool identity.
- **E08.** [Post-outcome amendment 003](../work-packages/20260714-a5d1b-finite-path-realization/artifacts/post-outcome-correction-amendment-003.json) — v3 invalidation and incumbent-acceptance correction.
- **E09.** [Corrected execution freeze v4](../work-packages/20260714-a5d1b-finite-path-realization/artifacts/corrected-execution-freeze-v4.json) — corrected tool identity before v4 certificates.
- **E10.** [Post-outcome amendment 004](../work-packages/20260714-a5d1b-finite-path-realization/artifacts/post-outcome-correction-amendment-004.json) — v4 aggregate-only missing-import correction.
- **E11.** [Controlling execution freeze v5](../work-packages/20260714-a5d1b-finite-path-realization/artifacts/corrected-execution-freeze-v5.json) — tool identity before the complete controlling rerun.
- **E12.** [Inherited path diagnostics](../work-packages/20260714-a5d1b-finite-path-realization/artifacts/inherited-path-diagnostics-v1.json) — 153-cell count/order decomposition.
- **E13.** [Count feasibility results](../work-packages/20260714-a5d1b-finite-path-realization/artifacts/count-feasibility-results-v1.json) — controlling 17-station solver and replay aggregate.
- **E14.** [Count witness replay audit](../work-packages/20260714-a5d1b-finite-path-realization/artifacts/count-witness-replay-audit-v1.json) — independent joint/separate replay and mutation rejection.
- **E15.** [Ordered-path results](../work-packages/20260714-a5d1b-finite-path-realization/artifacts/ordered-path-results-v1.json) — conditional-stage skip record.
- **E16.** [Aggregate result](../work-packages/20260714-a5d1b-finite-path-realization/artifacts/a5d1b-results-v1.json) — terminal cross-stage result.
- **E17.** [Machine decision](../work-packages/20260714-a5d1b-finite-path-realization/artifacts/a5d1b-decision-v1.json) — hold and authorization boundaries.
- **E18.** [Detailed evidence manifest](../work-packages/20260714-a5d1b-finite-path-realization/artifacts/detailed-evidence-manifest-v1.json) — deterministic archive membership and hashes.
- **E19.** [A5d1 contract v4](../work-packages/20260714-a5d1-selector-feasibility/artifacts/selector-feasibility-contract-v4.json) — inherited finite/path/invariant authority.
- **E20.** [A5d1 marginal results](../work-packages/20260714-a5d1-selector-feasibility/artifacts/marginal-results-v1.json) — controlling stationary feasibility evidence.
- **E21.** [A5d1 path results](../work-packages/20260714-a5d1-selector-feasibility/artifacts/path-results-v1.json) — controlling predecessor finite-path evidence.
- **E22.** [A5d1 decision](../work-packages/20260714-a5d1-selector-feasibility/artifacts/a5d1-decision-v1.json) — predecessor hold and authorization boundaries.
- **E23.** [Inherited A5d1 hash advisory](../work-packages/20260714-a5d1b-finite-path-realization/artifacts/inherited-a5d1-hash-advisory.md) — contextual-report hash disposition and machine-authority rule.
- **E24.** [Next-action disposition](../work-packages/20260714-a5d1b-finite-path-realization/artifacts/next-action-disposition-v1.json) — reviewed successor ordering and refined first action.
- **E25.** [Resource audit](../work-packages/20260714-a5d1b-finite-path-realization/artifacts/resource-audit-v1.json) — solver-call, wall-time, memory, and retained-byte checks.
- **E26.** [Inherited advisory addendum](../work-packages/20260714-a5d1b-finite-path-realization/artifacts/inherited-a5d1-hash-advisory-addendum.md) — append-only qualification of the unreplayable predecessor textual delta.
