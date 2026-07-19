# Work Packages

The execution record. One directory per unit of work:
`YYYYMMDD-<slug>/` containing `package.md` (scope, plan, gates, exit
criteria) and `artifacts/` (evidence produced during execution). The
convention is inherited from openWEPP, deliberately slimmed (ADR-0001):
single review pass, no dual-verification apparatus, no line-count
governance.

Rules that are not slimmed:

- **Honest terminal states.** A package ends `EXECUTED-COMPLETE` or
  `EXECUTED-HOLD-<reason>` with the exact blocker and the first follow-on
  action named. No silent abandonment.
- **Evidence discipline.** Claims labeled Ran vs Static; commands that
  produced evidence are recorded; reference-binary evidence carries build
  provenance (ADR-0001 §4).
- **Completed work leaves the roadmap** and lives here.

Start from [templates/package.md](templates/package.md).

## Catalog

| Package | Status |
|---|---|
| [20260709-repo-scaffold](20260709-repo-scaffold/package.md) | EXECUTED-COMPLETE |
| [20260709-golden-fixture-harness](20260709-golden-fixture-harness/package.md) | EXECUTED-COMPLETE |
| [20260709-decomposition-ratification](20260709-decomposition-ratification/package.md) | EXECUTED-COMPLETE |
| [20260709-rng-deviates-port](20260709-rng-deviates-port/package.md) | EXECUTED-COMPLETE |
| [20260709-par-monthlies-port](20260709-par-monthlies-port/package.md) | SCAFFOLDED |
| [20260710-q1-quality-report](20260710-q1-quality-report/package.md) | EXECUTED-COMPLETE |
| [20260710-q2-station-db](20260710-q2-station-db/package.md) | EXECUTED-COMPLETE |
| [20260710-q3-qc-filter-dissection](20260710-q3-qc-filter-dissection/package.md) | EXECUTED-COMPLETE |
| [20260710-q4-fast-batch-adjudication](20260710-q4-fast-batch-adjudication/package.md) | EXECUTED-COMPLETE |
| [20260710-changelog-history-doc](20260710-changelog-history-doc/package.md) | EXECUTED-COMPLETE |
| [20260712-faithful-generation-spec](20260712-faithful-generation-spec/package.md) | EXECUTED-COMPLETE |
| [20260712-sota-climate-generator-review](20260712-sota-climate-generator-review/package.md) | EXECUTED-COMPLETE |
| [20260712-a4a-modern-station-schema](20260712-a4a-modern-station-schema/package.md) | EXECUTED-COMPLETE |
| [20260712-a1-typed-output-provenance](20260712-a1-typed-output-provenance/package.md) | EXECUTED-COMPLETE |
| [20260712-a5a-quality-v3-observed-corpus](20260712-a5a-quality-v3-observed-corpus/package.md) | EXECUTED-COMPLETE |
| [20260713-a5b-coefficient-source-assessment](20260713-a5b-coefficient-source-assessment/package.md) | EXECUTED-COMPLETE |
| [20260713-a5b-interannual-candidate-spike](20260713-a5b-interannual-candidate-spike/package.md) | EXECUTED-COMPLETE |
| [20260714-interannual-candidate-exp-001-report](20260714-interannual-candidate-exp-001-report/package.md) | EXECUTED-COMPLETE |
| [20260714-a5c-interannual-profile-adjudication](20260714-a5c-interannual-profile-adjudication/package.md) | EXECUTED-COMPLETE |
| [20260714-a5d0-successor-feasibility-calibration](20260714-a5d0-successor-feasibility-calibration/package.md) | EXECUTED-HOLD-CONTRACT-INCOMPLETE |
| [20260714-a5d1-selector-feasibility](20260714-a5d1-selector-feasibility/package.md) | EXECUTED-HOLD-PATH-INFEASIBILITY |
| [20260714-a5d1b-finite-path-realization](20260714-a5d1b-finite-path-realization/package.md) | EXECUTED-HOLD-COUNT-SEARCH-BOUNDED |
| [20260714-a5e0-direct-annual-state-pilot](20260714-a5e0-direct-annual-state-pilot/package.md) | EXECUTED-HOLD-PROSPECTIVE-BOUNDARY |
| [20260714-a5f0-annual-state-failure-attribution](20260714-a5f0-annual-state-failure-attribution/package.md) | EXECUTED-COMPLETE |
| [20260714-a5f1-retired-a5e0-runtime-cleanup](20260714-a5f1-retired-a5e0-runtime-cleanup/package.md) | EXECUTED-COMPLETE |
| [20260714-a7a-daily-precipitation-structure-baseline](20260714-a7a-daily-precipitation-structure-baseline/package.md) | EXECUTED-COMPLETE |
| [20260714-a7b-analytic-precipitation-feasibility](20260714-a7b-analytic-precipitation-feasibility/package.md) | EXECUTED-COMPLETE |
| [20260715-a8a-dry-regime-applicability](20260715-a8a-dry-regime-applicability/package.md) | EXECUTED-COMPLETE |
| [20260715-a8b-secondary-year-fallback](20260715-a8b-secondary-year-fallback/package.md) | EXECUTED-COMPLETE |
| [20260715-a8c-routed-daily-pilot](20260715-a8c-routed-daily-pilot/package.md) | EXECUTED-COMPLETE |
| [20260715-a8c1-routed-daily-retirement](20260715-a8c1-routed-daily-retirement/package.md) | EXECUTED-COMPLETE |
| [20260715-a9a-successor-family-foundation](20260715-a9a-successor-family-foundation/package.md) | EXECUTED-COMPLETE |
| [20260715-a9b-calibration-harness](20260715-a9b-calibration-harness/package.md) | EXECUTED-COMPLETE |
| [20260715-a9c-observed-development](20260715-a9c-observed-development/package.md) | EXECUTED-HOLD-GATE-CALIBRATION |
| [20260715-a9c2-grouped-hot-arid-reentry](20260715-a9c2-grouped-hot-arid-reentry/package.md) | EXECUTED-HOLD-HOT-ARID-ROSTER |
| [20260715-a9c3-two-site-grouped-observed-comparison](20260715-a9c3-two-site-grouped-observed-comparison/package.md) | EXECUTED-HOLD-NO-SELECTABLE-CANDIDATE |
| [20260715-a9c4-context-support-completeness](20260715-a9c4-context-support-completeness/package.md) | EXECUTED-HOLD-COMPLETENESS-SURFACE |
| [20260715-a9d-successor-development-confirmation](20260715-a9d-successor-development-confirmation/package.md) | EXECUTED-HOLD-NO-SELECTABLE-CANDIDATE |
| [20260716-a10m0-dispatch-predecessor-freeze](20260716-a10m0-dispatch-predecessor-freeze/package.md) | EXECUTED-COMPLETE |
| [20260716-a10m2-lemhi-gpu-integration](20260716-a10m2-lemhi-gpu-integration/package.md) | EXECUTED-HOLD-CUDA-ENVIRONMENT |
| [20260716-a10m2d1-lemhi-cuda-drift-diagnostic](20260716-a10m2d1-lemhi-cuda-drift-diagnostic/package.md) | EXECUTED-COMPLETE |
| [20260716-a10m2d2-rmm-lemhi-scp-characterization](20260716-a10m2d2-rmm-lemhi-scp-characterization/package.md) | EXECUTED-COMPLETE |
| [20260717-a10m1-corpus-role-freeze](20260717-a10m1-corpus-role-freeze/package.md) | EXECUTED-COMPLETE |
| [20260717-a10m2-completion](20260717-a10m2-completion/package.md) | EXECUTED-COMPLETE |
| [20260717-a10-lemhi-toolkit-foundation](20260717-a10-lemhi-toolkit-foundation/package.md) | EXECUTED-COMPLETE |
| [20260717-a10-lemhi-python311-smoke](20260717-a10-lemhi-python311-smoke/package.md) | EXECUTED-COMPLETE |
| [20260717-a10-lemhi-canonical-configuration](20260717-a10-lemhi-canonical-configuration/package.md) | EXECUTED-COMPLETE |
| [20260717-a10m3-model-training-generation-selector-freeze](20260717-a10m3-model-training-generation-selector-freeze/package.md) | EXECUTED-COMPLETE |
| [20260717-a10m4-one-l40-qualification](20260717-a10m4-one-l40-qualification/package.md) | EXECUTED-COMPLETE |
| [20260717-a10m4o1-lemhi-operational-hardening](20260717-a10m4o1-lemhi-operational-hardening/package.md) | EXECUTED-COMPLETE |
| [20260717-a10-lemhi-canonical-v2-smoke](20260717-a10-lemhi-canonical-v2-smoke/package.md) | EXECUTED-HOLD |
| [20260717-a10-lemhi-canonical-v2-environment-closure-smoke](20260717-a10-lemhi-canonical-v2-environment-closure-smoke/package.md) | EXECUTED-HOLD |
| [20260717-a10-lemhi-canonical-v2-exact-asset-smoke](20260717-a10-lemhi-canonical-v2-exact-asset-smoke/package.md) | EXECUTED-COMPLETE |
| [20260717-a10-lemhi-canonical-v2-designation](20260717-a10-lemhi-canonical-v2-designation/package.md) | EXECUTED-COMPLETE |
| [20260717-a10m4o2-lemhi-toolkit-acceptance](20260717-a10m4o2-lemhi-toolkit-acceptance/package.md) | EXECUTED-COMPLETE |
| [20260717-a10m5-bounded-gpu-screen](20260717-a10m5-bounded-gpu-screen/package.md) | EXECUTED-HOLD-NO-VALID-NEURAL-FIT |
| [20260717-a10m5r1-cpu-export-memory-remedy](20260717-a10m5r1-cpu-export-memory-remedy/package.md) | EXECUTED-COMPLETE |
| [20260718-a10m5r2-corrected-cpu-export-screen](20260718-a10m5r2-corrected-cpu-export-screen/package.md) | EXECUTED-COMPLETE |
| [20260718-a10m5r3-candidate-family-capacity-knee](20260718-a10m5r3-candidate-family-capacity-knee/package.md) | EXECUTED-HOLD-A10-RESOURCE-BOUND |
| [20260718-a10m5r3r1-evidence-reconciliation](20260718-a10m5r3r1-evidence-reconciliation/package.md) | EXECUTED-COMPLETE |
| [20260718-a10m5r4-realized-temporal-adjudication](20260718-a10m5r4-realized-temporal-adjudication/package.md) | EXECUTED-HOLD-A10-REVISED-STOCHASTIC-PRISM-COMPARATOR |
| [20260718-a10m5r4r1-stochastic-prism-comparator](20260718-a10m5r4r1-stochastic-prism-comparator/package.md) | EXECUTED-COMPLETE |
| [20260718-a10m5r4r2-realized-temporal-adjudication](20260718-a10m5r4r2-realized-temporal-adjudication/package.md) | SCAFFOLDED |
