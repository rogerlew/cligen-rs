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
| [20260709-rng-deviates-port](20260709-rng-deviates-port/package.md) | SCAFFOLDED |
