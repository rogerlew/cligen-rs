# Interannual Candidate Experiment 001 Claim-Evidence Ledger

Status: frozen for report revision 2
Freeze date: 2026-07-14
Source commit: `7273829517121011edd8bb815ff72fefd3742bcb`

## Authority order

1. Exact candidate behavior: `SPEC-A5B-CANDIDATES` revision 1.
2. Evaluation, aggregation, and decision rules: `SPEC-A5-EVALUATION`
   revision 3 and the A5b preregistration.
3. Exact measurements: canonical climate and WEPP analyses identified by
   `analysis-evidence-v1.json`.
4. Human-readable results: accepted A5b `results.md`, checked against the
   machine analyses.
5. Access boundary and disposition: A5b amendments, package, and independent
   review.
6. Scientific context: primary external publications and datasets, bounded to
   the model version or product they actually describe.
7. Prospective interpretation: the post-acceptance advisory, after checking
   each derivation against the frozen specification and canonical counts.

## Frozen study facts

| Claim | Class | Evidence | Accepted wording or constraint |
|---|---|---|---|
| Primary fit source and period | Static | E01, E04 | Daymet V4 R1 gridded estimates, 17 archived objects, 1980–2009 |
| Primary target | Static | E01, E02 | Held-out Daymet 2010–2025 under project `noleap_365`; not station truth |
| Point-record comparison | Static | E02, E04 | Separately scored GHCN sensitivity; not statistically independent of Daymet |
| Candidate matrix | Ran | E05, E06, E08 | 7 × 17 × 2 × 8 = 1,904 candidate climates |
| WEPP matrix | Ran | E06, E08, E11 | 8 profiles × 17 × 2 × 8 = 2,176 response and execution records |
| Observed uncertainty | Ran | E02, E06, E10 | 2,000 circular moving-block replicates, five-year blocks, report-only |
| Eligibility result | Ran/Derived | E06, E10 | 0/14 candidate/horizon rows passed all gates; no candidate eligible |
| Primary structure result | Ran/Derived | E06, E10 | Every candidate failed G1, G3, G4, and G5 at both horizons |
| Sensitivity result | Ran/Derived | E06, E10 | All except rank-one passed G2; all passed G6 and G7 |
| Downstream magnitude | Ran/Derived | E06, E11 | Paired median-across-station ratios are descriptive; no numeric WEPP bound |
| Promotion status | Static | E05, E06, E09 | No public model/profile promoted; faithful mode unchanged |
| Evidence status | Static | E05, E09 | Complete but exploratory for model selection after disclosed outcome access |
| Candidate station-days | Derived | E03, E10, E13 | 45,201,912 exact rows; 15,565,742 dewpoint caps equal 34.4%, correcting the advisory approximation |

## Operational hypothesis mapping

The preregistration states three research questions rather than formal null and
alternative hypotheses. The report therefore labels H1–H3 `retrospective
mapping` and does not call them confirmatory.

| ID | Mapping | Decision evidence | Outcome |
|---|---|---|---|
| H1 | At least one candidate passes primary Gate 1 at both horizons | E01, E02, E06, E10 | Not supported; all seven failed G1 at both horizons |
| H2 | A candidate satisfying H1 is robust across horizon/station/regime and GHCN sensitivity | E01, E02, E06, E10 | Not supported; no candidate satisfied H1, although six passed G2 |
| H3 | A candidate satisfying H1 preserves monthly, daily precipitation, descriptor, and winter guards with complete evidence | E01, E02, E06, E10, E11 | Not supported; every candidate failed G3–G5, while G6/G7 passed |

The WEPP response has no H4 pass hypothesis because the registered contract has
no downstream numeric acceptance bound. It is a required descriptive response
record and evidence-completeness component.

## Post-acceptance advisory dispositions

The advisory is prospective interpretation, not a new experiment result. Its
five findings are incorporated as follows:

| Finding | Disposition | Report consequence |
|---|---|---|
| ADV-001 — Gates 3/4 use ratios to faithful residuals | Accepted with qualification | Revision 2 says ratios do not express absolute physical error and recommends uncertainty-scaled absolute distances; registered outcomes are unchanged |
| ADV-002 — Gate 5 has no measured false-failure rate | Accepted | Revision 2 recommends a faithful-clone null candidate or paired cell test before changing the zero-excursion guard |
| ADV-003 — Gate 1/4 bootstrap availability is sparse | Accepted | Revision 2 requires eligibility-cell diagnosis and informative uncertainty surfaces before successor use |
| ADV-004 — WEPP has no numeric bound | Accepted | Revision 2 requires a prospective bound or explicit justified decision to remain descriptive |
| ADV-005 — interventions have no ceiling | Accepted with corrected derivation | Revision 2 reports the exact 34.4% dewpoint-cap rate and recommends station-day rate guards |

The advisory's statement that these candidates were gate-infeasible by
construction is retained as a mechanistic hypothesis, not a proved experiment
outcome. The idealized independent-multiplier variance identity supports a
pre-campaign feasibility screen, while A5b's renderability adjustment prevents
using it as an exact proof of every realized failure. The proposed Gate 5 null
excursion probability and spectral-extrapolation explanation were not
independently established and are not promoted to report findings.

## Interpretation boundaries

- Reject these seven version-1 overlay implementations under the frozen gates;
  do not reject interannual modeling or the referenced model families.
- Do not select a best candidate: vector AR, spectral random phase, and
  Fourier/EOF show different partial strengths but none is eligible.
- Gate 5 is a faithful-output descriptor guard, not observed storm validation.
- Gate 6 is an air-temperature/freezing proxy guard, not proof of snow or
  freeze–thaw physics.
- Gate 7 means complete evidence, not physical compatibility.
- Legacy burns provide empirical trajectory spread, not independent-sample
  confidence intervals.
- The bootstrap is report-only and does not alter deterministic gates.
- Large WEPP ratios demonstrate sensitivity within the pinned campaign, not
  universal causal multipliers or physical correctness.
- Candidate definitions and thresholds were frozen before generation, but
  limited values were inspected while successor executable contracts were
  repaired; the final selection evidence is exploratory.
- The 30-year coefficient fit is not resampled by the target-only bootstrap;
  exact-version failures do not isolate architecture from finite-record,
  source-product, rank, shrinkage, or regularization effects.
- Advisory recommendations are prospective only: no gate is rescored, no
  threshold relaxed, and no current candidate is selected for salvage.
