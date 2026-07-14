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
| [20260714-a5d1-selector-feasibility](20260714-a5d1-selector-feasibility/package.md) | SCAFFOLDED |
