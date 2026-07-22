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
| [20260718-a10m5r4r2-realized-temporal-adjudication](20260718-a10m5r4r2-realized-temporal-adjudication/package.md) | EXECUTED-HOLD-MODEL-RECONSTRUCTION-IDENTITY |
| [20260718-a10m5r4r2r1-reconstruction-identity-remedy](20260718-a10m5r4r2r1-reconstruction-identity-remedy/package.md) | EXECUTED-HOLD-EVALUATION-YEAR-AXIS |
| [20260718-a10m5r4r2r1r1-evaluation-year-axis-remedy](20260718-a10m5r4r2r1r1-evaluation-year-axis-remedy/package.md) | EXECUTED-HOLD-LEAP-CENTURY |
| [20260718-a10m5r4r2r1r2-leap-century-remedy](20260718-a10m5r4r2r1r2-leap-century-remedy/package.md) | EXECUTED-HOLD-NO-TEMPORALLY-ELIGIBLE-CAPACITY |
| [20260718-a10m5r7-structural-architecture-identification](20260718-a10m5r7-structural-architecture-identification/package.md) | EXECUTED-HOLD-OBSERVATION-SHARD-PATH |
| [20260718-a10m5r7r1-observation-shard-path-remedy](20260718-a10m5r7r1-observation-shard-path-remedy/package.md) | EXECUTED-HOLD-RESOURCE-AUTHORITY-EXHAUSTED |
| [20260718-a10m5r7r2-authorized-architecture-execution](20260718-a10m5r7r2-authorized-architecture-execution/package.md) | EXECUTED-HOLD-ARCHITECTURE-HYPOTHESIS-MIXED |
| [20260719-a10m5r8-climate-statistics-objective](20260719-a10m5r8-climate-statistics-objective/package.md) | EXECUTED-HOLD-AUTHORITY-SOURCE-IDENTITY |
| [20260719-a10m5r8r1-authority-source-identity-remedy](20260719-a10m5r8r1-authority-source-identity-remedy/package.md) | EXECUTED-HOLD-CALENDAR-MISSINGNESS |
| [20260719-a10m5r8r2-calendar-missingness-remedy](20260719-a10m5r8r2-calendar-missingness-remedy/package.md) | EXECUTED-HOLD-CALENDAR-END-EXCLUSION |
| [20260719-a10m5r8r3-calendar-end-exclusion-remedy](20260719-a10m5r8r3-calendar-end-exclusion-remedy/package.md) | EXECUTED-HOLD-CORE-OBJECTIVE-NOT-SUPPORTED |
| [20260719-a10-calendar-contract-hardening](20260719-a10-calendar-contract-hardening/package.md) | EXECUTED-COMPLETE |
| [20260719-a10m5r9-climate-normal-residual-architecture](20260719-a10m5r9-climate-normal-residual-architecture/package.md) | EXECUTED-HOLD-RESIDUAL-ARCHITECTURE-NOT-SUPPORTED |
| [20260719-a10m5r10-parallel-architecture-portfolio](20260719-a10m5r10-parallel-architecture-portfolio/package.md) | EXECUTED-HOLD-JOB-LOCAL-CAPACITY |
| [20260719-a10m5r10r1-candidate-job-local-capacity-remedy](20260719-a10m5r10r1-candidate-job-local-capacity-remedy/package.md) | EXECUTED-HOLD-PYTHON311-CONTROL-PLANE |
| [20260719-a10m5r10r1r1-python311-control-plane-remedy](20260719-a10m5r10r1r1-python311-control-plane-remedy/package.md) | EXECUTED-HOLD-COMPUTE-PYTHON311-ABSENT |
| [20260719-a10m5r10r1r2-portable-bootstrap-control-plane-remedy](20260719-a10m5r10r1r2-portable-bootstrap-control-plane-remedy/package.md) | EXECUTED-HOLD-CORPUS-ROOT-NESTING |
| [20260719-a10m5r10r1r3-corpus-extraction-root-remedy](20260719-a10m5r10r1r3-corpus-extraction-root-remedy/package.md) | EXECUTED-HOLD-CUBLAS-ENVIRONMENT-SCOPE |
| [20260719-a10m5r10r1r4-science-environment-closure-remedy](20260719-a10m5r10r1r4-science-environment-closure-remedy/package.md) | EXECUTED-COMPLETE |
| [20260719-a10m5r11-retained-adapter-temporal-generalization](20260719-a10m5r11-retained-adapter-temporal-generalization/package.md) | EXECUTED-HOLD-ADMISSION-ROLE-MATRIX |
| [20260719-a10m5r11r1-admission-role-matrix-remedy](20260719-a10m5r11r1-admission-role-matrix-remedy/package.md) | EXECUTED-HOLD-SCORER-COMPARATOR-BURNS |
| [20260719-a10m5r11r2-comparator-burn-contract-remedy](20260719-a10m5r11r2-comparator-burn-contract-remedy/package.md) | EXECUTED-HOLD-NO-TEMPORALLY-ELIGIBLE-CANDIDATE |
| [20260719-a10m5r12-continuous-latent-temporal-process](20260719-a10m5r12-continuous-latent-temporal-process/package.md) | EXECUTED-HOLD-ADMISSION-MATERIALIZATION |
| [20260719-a10m5r12r1-admission-materialization-remedy](20260719-a10m5r12r1-admission-materialization-remedy/package.md) | EXECUTED-HOLD-COLLECTION-CAPACITY |
| [20260720-a10m5r12r2-collection-ceiling-reconciliation](20260720-a10m5r12r2-collection-ceiling-reconciliation/package.md) | EXECUTED-HOLD-NO-TEMPORALLY-ELIGIBLE-CANDIDATE |
| [20260720-a10m5r13-selector-aligned-continuous-hierarchy](20260720-a10m5r13-selector-aligned-continuous-hierarchy/package.md) | EXECUTED-ABORTED-BEFORE-SUBMISSION |
| [20260720-a10m5r13r1-admission-controller-materialization-remedy](20260720-a10m5r13r1-admission-controller-materialization-remedy/package.md) | EXECUTED-HOLD-NO-TEMPORALLY-ELIGIBLE-CANDIDATE |
| [20260720-a10m5r13r2-semantic-plan-replay-authentication-remedy](20260720-a10m5r13r2-semantic-plan-replay-authentication-remedy/package.md) | EXECUTED-HOLD-NO-TEMPORALLY-ELIGIBLE-CANDIDATE |
| [20260720-a10m5r14-continuous-distribution-head-factorial](20260720-a10m5r14-continuous-distribution-head-factorial/package.md) | EXECUTED-ABORTED-BEFORE-SUBMISSION |
| [20260720-a10m5r14r1-admission-role-matrix-remedy](20260720-a10m5r14r1-admission-role-matrix-remedy/package.md) | EXECUTED-HOLD-OPERATIONAL-PREREQUISITES |
| [20260720-a10m5r14r2-shared-environment-four-l40-portfolio](20260720-a10m5r14r2-shared-environment-four-l40-portfolio/package.md) | EXECUTED-ABORTED-BEFORE-SUBMISSION |
| [20260720-a10m5r14r2r1-inherited-admission-checker-identity-remedy](20260720-a10m5r14r2r1-inherited-admission-checker-identity-remedy/package.md) | EXECUTED-HOLD-FOUR-IDLE-L40-UNAVAILABLE |
| [20260720-a10m5r14r2r2-two-l40-two-wave-portfolio](20260720-a10m5r14r2r2-two-l40-two-wave-portfolio/package.md) | EXECUTED-HOLD-NO-TEMPORALLY-ELIGIBLE-CANDIDATE |
| [20260721-a10m5r15-external-normal-conditioning](20260721-a10m5r15-external-normal-conditioning/package.md) | HOLD-A10M5R15-ENGINEERING-INCOMPLETE |
| [20260721-a10m5r15r1-prism-eligible-cohort](20260721-a10m5r15r1-prism-eligible-cohort/package.md) | A10M5R15R1-COHORT-READY |
| [20260721-a10m5r15r2-external-normal-conditioning-execution](20260721-a10m5r15r2-external-normal-conditioning-execution/package.md) | EXECUTED-HOLD-SUCCESSOR-CONTROL-IDENTITY |
| [20260722-a10m5r15r2r1-successor-control-identity-calibration](20260722-a10m5r15r2r1-successor-control-identity-calibration/package.md) | A10M5R15R2R1-SUCCESSOR-CONTROL-IDENTITY-READY |
| [20260722-a10m5r15r2r2-successor-control-execution](20260722-a10m5r15r2r2-successor-control-execution/package.md) | EXECUTION-READY |
| [20260718-prism-mode-bundle-pedigree](20260718-prism-mode-bundle-pedigree/package.md) | EXECUTED-COMPLETE |
| [20260718-prism-residual-attribution](20260718-prism-residual-attribution/package.md) | SCAFFOLDED |
| [20260719-a10m5o1-multi-l40-toolkit-hardening](20260719-a10m5o1-multi-l40-toolkit-hardening/package.md) | EXECUTED-COMPLETE |
| [20260719-a10m5o1r1-evidence-token-projection-hardening](20260719-a10m5o1r1-evidence-token-projection-hardening/package.md) | EXECUTED-COMPLETE |
| [20260719-a10m5o1r2-terminal-failure-closure-hardening](20260719-a10m5o1r2-terminal-failure-closure-hardening/package.md) | EXECUTED-COMPLETE |
| [20260720-a10m5o1r3-composed-admission-identity-hardening](20260720-a10m5o1r3-composed-admission-identity-hardening/package.md) | EXECUTED-COMPLETE |
| [20260719-a10m5o2-canonical-multi-l40-qualification](20260719-a10m5o2-canonical-multi-l40-qualification/package.md) | EXECUTED-COMPLETE |
| [20260719-a10m5o2d1-l40-interconnect-diagnostic](20260719-a10m5o2d1-l40-interconnect-diagnostic/package.md) | EXECUTED-COMPLETE |
