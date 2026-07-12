# Independent review and disposition

Date: 2026-07-12

Three independent read-only Codex tasks audited the synthesis:
`/root/cligen_gap_map` reviewed faithful CLIGEN and repository traceability,
`/root/stochastic_wg_survey` reviewed direct stochastic generators, and
`/root/ml_extremes_survey` reviewed subdaily, extremes, and the ML boundary.
All P1/P2 findings below were accepted and corrected. No unresolved P1/P2
finding remains.

## Faithful CLIGEN and repository review

| Finding | Disposition |
|---|---|
| The package claimed completion before gate and review artifacts existed. | Added the evidence artifacts and withheld publication until the final gates were run. |
| Calling faithful spell behavior geometric ignored QC-conditioned occurrence uniforms. | Replaced it with the exact one-day-state boundary and an explicit warning that realized spells are not an ideal geometric chain. |
| “Stationary” understated deterministic seasonality and calendar effects. | Changed the baseline to “fixed-climatology, seasonally varying.” |
| Reading altitude and identities of local papers were not reproducible. | Added `source-evidence.md` and `local-reading-copies.tsv`. |
| Local reading copies and delegated reviews lacked precise acquisition/executor attribution. | Used neutral “local, Git-ignored” wording and recorded all three Codex task identities and scopes. |
| The feasibility section lacked a symbol-to-gate crosswalk. | Added exact Rust seams, identity tests, and quality groups for every ranked gap. |
| Quality groups were described as all having decadal output. | Limited the statement to decadal blocks “where defined.” |
| A typed native output might bypass legacy FORMAT quantization in the active quality report. | Kept rendered `.cli` reparsing authoritative and required a separately specified native-quality surface. |

## Direct stochastic-generator review

| Finding | Disposition |
|---|---|
| Several reusable licenses and citations were imprecise. | Corrected WeaGETS to CC BY-NC-ND 3.0; added exact licenses for GenCast, CorrDiff, spateGAN, and Hess; corrected RMAWGEN and STORM bibliographic details. |
| The open corpus omitted strong direct comparators. | Added Rglimclim, IMAGE, Bartlett–Lewis plus corrigendum, and the `pyBL` release DOI to the annotations/corpus where redistributable. |
| California scenario count hid a data-release exception. | Distinguished 30 released primary scenarios from two experimental circulation-frequency scenarios. |
| Regime-model feasibility was understated. | Recorded very high complexity and placed it after lower-dimensional interannual candidates. |
| CorrDiff wording overclaimed a reported temporal failure. | Changed the claim to temporal coherence “not established” and recorded calibration/data limits. |

## Subdaily, extremes, and ML-boundary review

| Finding | Disposition |
|---|---|
| The legacy observed seam cannot preserve complete externally supplied meteorology. | Required a new full-meteorology/subdaily bypass-or-derivation contract. |
| Daily tails, spells, and later subdaily replacement formed overlapping tracks. | Defined tails and occurrence persistence as one precipitation-structure study and subdaily generation as a conditioned/reconciled successor. |
| ML systems were described without decisive precipitation limits. | Added the GenCast scorecard exclusion and NeuralGCM P−E/tropical-extreme limits. |
| CorrDiff, spateGAN, and STORM needed stronger reproducibility and conservation caveats. | Added code/data licenses, compute/data constraints, and the distinction between patchwise mean adjustment and exact conservation. |
| AB-28 named the wrong lead author. | Corrected the citation to Y. Shmilovitz et al. |
| The recommended package sequence was not reconciled with the canonical roadmap. | Marked the sequence pending operator ratification and roadmap reconciliation rather than silently changing `docs/ROADMAP.md`. |

## Residual boundary

The curated PDF corpus prioritizes direct stochastic and implementation
comparators. Some ML/forecast papers remain DOI/link-only by design; their
exact licenses and primary links are recorded, and no in-Rust implementation
recommendation depends on archiving them.

The recommended implementation sequence is informational and pending operator
ratification. It deliberately does not change `docs/ROADMAP.md`; roadmap
reconciliation is a prerequisite to dispatching any package from the sequence.
