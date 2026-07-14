# ADR-0004: No A5b Interannual Candidate Is Promoted

Status: Accepted
Date: 2026-07-14
Deciders: Roger Lew (operator), through the dispatched A5c adjudication
Evidence: `docs/work-packages/20260714-a5c-interannual-profile-adjudication/`

## Context

ADR-0002 makes the quality-metric vector, rather than similarity to faithful
output, the authority for generation extensions. A5a fixed the corpus,
instrument, baseline, horizons, and promotion gates. A5b then evaluated seven
independently versioned interannual candidates across 17 stations at 30- and
100-year horizons, producing 1,904 candidate climates, a 2,000-replicate
observed-target bootstrap, and 2,176 complete WEPP response records.

None of the seven candidates passed all climate gates at either horizon. All
candidate/horizon rows failed the fixed monthly-contract, daily precipitation,
and storm-descriptor guards; no candidate passed the complete climate gate
vector at both horizons. The complete-evidence gate passed, but it cannot cure
a climate-gate failure. The final model-selection evidence is exploratory
because candidate metric and response access occurred while successor
executable contracts were repaired. That boundary permits a conservative
no-promotion conclusion; it does not permit selecting a near miss or relaxing
a gate after seeing results.

The post-acceptance advisory review concurred with no promotion and sharpened
the design diagnosis. The first candidate class added annual variance on top
of CLIGEN's calibrated within-year variance instead of reallocating it, making
monthly and daily contract failures structurally likely. The advisory also
identified gate-calibration work that matters prospectively but cannot rescue
these exact candidate versions.

## Decision

1. No A5b candidate, station model, or generation-profile identifier is
   promoted to a public interface.
2. The accepted runspec, station document, provenance, typed-output, and
   legacy `.par` surfaces are unchanged. Their versions remain independent;
   this adjudication creates no compatibility-version cascade.
3. `faithful_5_32_3` remains the default generation profile and `faithful`
   remains the default QC policy. This is a no-promotion decision, not a claim
   that faithful climate statistics are scientifically optimal.
4. The A5b candidate implementations and schemas remain research evidence.
   Their identifiers do not become accepted public profile values.
5. An A5b candidate cannot be rescued by post-hoc gate revision. Any renewed
   candidate requires a new prospectively registered study at both horizons.
6. Before a successor campaign, the package must establish analytic
   feasibility against the monthly variance budget, use variance reallocation
   or structure-preserving conditioning/resampling, integrate daily
   precipitation behavior, calibrate guards with a faithful-clone null, and
   register explicit downstream-response and intervention-rate criteria.

## Consequences

- A5c closes with `no_promotion`; no production code or public schema changes.
- The seven candidate families remain useful design probes, not deployable
  choices. The decision rejects their evaluated versions, not interannual
  modeling as a research direction.
- A successor A5d study is a separate work package with a new preregistration
  and evidence freeze. It may reuse lessons and tooling, but not A5b outcomes
  as confirmatory model-selection evidence.
- The complete downstream campaign remains mandatory because A5b observed
  response changes far larger than compatibility-scale perturbations.
