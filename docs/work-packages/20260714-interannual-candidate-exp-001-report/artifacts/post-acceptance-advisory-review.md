# Interannual Candidate Experiment 001 Post-Acceptance Advisory Review

Status: advisory (non-binding; does not reopen the accepted package)
Review date: 2026-07-14 (America/Los_Angeles)
Reviewer: Claude Code (single advisory lens, operator-requested)
Reviewed report SHA-256: `8f6b4b18e8e1761ab3a5ae9651f201060fc0c9ebebe801e98c4ed9909f7f83e4`
(matches the accepted report hash recorded in the [consolidated review](review.md))
SPEC-A5-EVALUATION SHA-256 at review time: `e8149a416cacc8ec57fa9a211d272993071e0c1cfc580d3b39601910e03aac88`
Evidence mode: Static

## Scope and method

This review answers three operator questions about the accepted
`interannual-candidate-exp-001` report: what was learned, whether the seven
gates are too strict, and what the sensible next steps are. It is a static
read of the accepted report, the gate and bootstrap sections of
`SPEC-A5-EVALUATION` (revisions as amended through the two 2026-07-13
amendments), the package record, and the consolidated internal review. No
table was recomputed, no evidence archive was reopened, and no candidate or
WEPP artifact was executed. All quantitative statements below either quote the
accepted report or are labeled as analytical derivations.

This artifact was created after package closure. It intentionally does not
modify `package.md`, `review.md`, the claim ledger, the report, or any
manifest; whether to register it in a catalog is an operator decision.

## Verdict

Concur with the accepted no-promotion outcome and with the report's central
structural conclusion. The gates are **not** the reason the experiment failed:
Gate 3 ratios of 1.900–3.243 and Gate 4 ratios of 1.393–2.841 against a 1.10
bound are category-scale failures, not near misses, and no defensible
recalibration would rescue any of the seven exact candidate versions. Three
gates nevertheless have calibration or scaling weaknesses that should be
repaired prospectively before a successor campaign, because in a future
experiment with a better-matched candidate class they could adjudicate
incorrectly in either direction.

## What the experiment established

1. **The candidate class was gate-infeasible by construction.** Faithful
   CLIGEN is calibrated so pooled monthly statistics match the station
   contract. A mean-one multiplicative annual overlay with nonzero variance
   necessarily inflates pooled wet-day dispersion, because it adds
   between-year variance on top of within-year variance instead of
   reallocating it. Universal Gate 3/Gate 4 failure was therefore predictable
   before generation. The report's prescription — enforce the monthly surface
   during realization — is correct and can be sharpened: the next design must
   be a variance **reallocation**, not a variance addition.
2. **The guard gates are vindicated by the downstream record.** Median WEPP
   soil-loss ratios of 4.82–16.58 show what promotion on Gate 1 alone would
   have shipped. Several candidates posted attractive Gate 1 composites
   (0.894–0.960) while inflating erosion response by roughly 5–16×; Gates 3–5
   caught exactly the failure mode that matters to WEPP users.
3. **Partial strengths are real but horizon-unstable.** Spectral random
   phase's low-frequency ratio moved from 0.811 at 30 years to 1.091 at 100
   years, consistent with 30-year DFT amplitude interpolation failing to
   extrapolate to a 128-year table. Vector AR was the only candidate holding
   low-frequency below 0.90 at 100 years (0.876) but missed the composite.
   The both-horizons requirement caught genuine model instability, not noise.
4. **The intervention diagnostics carry an unpriced physical signal.**
   15,565,742 dewpoint caps across the campaign is on the order of one fifth
   of all generated station-days (derivation: 1,904 climates at a 30/100-year
   mix of 365-day years ≈ 7×10⁷ station-days; not recomputed from evidence).
   An intervention of that magnitude is a humidity-surface distortion in its
   own right and currently has no gate.

## Gate calibration findings (advisory)

| ID | Finding | Recommendation |
|---|---|---|
| ADV-001 | Gates 3 and 4 bound the ratio to a near-zero denominator. Faithful's distance to the monthly-contract targets is its own calibration residual, so a 1.10× ratio bound is effectively an absolute near-zero perturbation budget, and the observed 2–3× ratios overstate physical severity. A candidate could sit within observational uncertainty of the monthly targets and still fail at 2×. | In the successor evaluation revision, re-express Gates 3 and 4 as absolute distances scaled by observation uncertainty (the existing Daymet block-bootstrap machinery is the natural yardstick), retaining preservation as a hard requirement while fixing the scaling. |
| ADV-002 | Gate 5 tolerates zero excursions across 408 cells. With eight replicates, the nearest-rank p05–p95 faithful envelope is the min–max of eight values, and every one of 408 candidate medians must fall inside it. Under a paired-replicate design the realized noise is suppressed (several candidates failed only 1–2 cells; Vector AR failed the 30-year row on a single cell), but no false-failure rate was ever measured, and an analytical independence bound puts the per-cell null excursion probability near 2.6% — the pairing assumption is doing unquantified work. | Register either a small excursion allowance or a per-cell paired test, and add a **faithful-clone null candidate** (faithful trajectories under an independent extension seed) to the next matrix to measure every gate's empirical false-failure rate directly. |
| ADV-003 | Gate 1's uncertainty surface is nearly empty. Corpus bootstrap availability was 221/2,000 for Gate 1 (8/2,000 for Gate 4), so the primary composite is defined in about 11% of resamples of a 16-year held-out target. The deterministic gate remains valid as registered, but the interval machinery cannot currently speak to the primary decision, and the fragility indicates sensitivity to individual target cells. | Diagnose which eligibility cells drive unavailability and repair cell definitions (or aggregation fallbacks) in the successor revision so the registered uncertainty surface is informative where it matters most. |
| ADV-004 | No numeric downstream acceptance bound exists. The report states twice that WEPP ratios are descriptive because none was registered; the most decision-relevant surface in the project was therefore unadjudicated. | Register a numeric WEPP response bound (or an explicit, justified decision not to gate on response) before any successor candidate output. |
| ADV-005 | Constraint interventions are diagnostics only. Precipitation-bound clips, temperature-order repairs, and dewpoint caps have no ceiling, yet at exp-001 scale they constitute a material rewrite of the generated humidity surface. | Add a bounded intervention-rate guard (per station-day rates, not campaign totals) to the successor gate set. |

The Gate 1 joint bound itself (composite and low-frequency both ≤0.90, 11/17
stations, worst regime ≤1.05, both horizons) is judged appropriately strict:
a 10% joint improvement is a reasonable effect size to demand before adding
216–666 runtime coefficients per station, and the near misses recorded in the
report were accompanied by instability the gate was right to reject.

## Recommended next steps, in order

1. **Feasibility analysis before any new campaign.** Derive the variance
   budget analytically: given the (rescaled) Gate 3 bound, how much
   interannual variance can an overlay add? Exp-001 spent 1,904 climates and
   2,176 WEPP runs to learn what a one-page derivation would have predicted.
   Make "candidate class is not gate-infeasible by construction" a
   preregistration checklist item.
2. **Build the successor class on conditioning or resampling, not
   multiplication.** Two precedented shapes: (a) state-conditioned year/block
   resampling in the style of Steinschneider & Brown (report R07) — a
   persistent latent state selecting among generated years adds low-frequency
   power while preserving daily and storm structure exactly by construction,
   so Gates 3–5 pass structurally and the contest happens at Gate 1 where it
   belongs; (b) Wilks/Chen-style conditioning of occurrence–amount parameters
   on the annual state with analytic moment compensation holding pooled
   monthly moments on contract. Option (a) is the lower-risk first move.
3. **Freeze a SPEC-A5-EVALUATION revision 4 prospectively** incorporating
   ADV-001 through ADV-005, including the faithful-clone null candidate. The
   exploratory access boundary already requires the successor to be newly
   frozen; that is the natural moment.
4. **Retain the full downstream campaign** (the report already recommends
   this) — observed WEPP sensitivity is the strongest argument the project
   has for why the guard gates exist.
5. **Consider hierarchical or regional pooling for coefficient fitting.**
   Thirty annual vectors for 36 features per station is the quiet weakness
   under every candidate; shrinkage made the fits executable, not
   well-estimated. Pooling across stations or regimes helps any successor
   architecture.

A caution stated plainly: the temptation to salvage Vector AR or spectral
random phase by post-hoc gate relaxation should be resisted. The exploratory
access boundary makes any such rescue unregistered model selection. The
candidates did their job as probes; the answer is a new candidate class under
newly frozen rules, not a lower bar.

## Boundaries of this review

- Static only. No published number was independently recomputed; accuracy is
  inherited from the accepted consolidated review's recomputation record.
- The station-day and Gate 5 null-probability figures above are analytical
  derivations by the reviewer, labeled as such, not evidence recomputations.
- The full `SPEC-A5B-CANDIDATES` revision 1 mathematics, the claim ledger,
  and the canonical analysis archives were not re-read.
- Nothing here reopens the accepted package, alters its verdict, or amends
  any frozen specification; every recommendation is prospective input to a
  successor work package.
