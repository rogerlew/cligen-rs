# A11 exploratory strategy lab ExecPlan

## Purpose / Big Picture

Build a research environment where A11 can try several transparent non-neural
weather-generator strategies without pretending each iteration is a locked
confirmation study. A useful outcome is a published, tested strategy registry
that supports iterative development while keeping each executed strategy
reproducible and every result explicitly exploratory.

## Progress

- [x] 2026-08-25: accepted the operator's exploratory posture and separated
  strategy-level immutability from program-level flexibility.
- [x] 2026-08-25: wrote revision-1 exploratory specification, package, strict
  manifest/schema, two initial strategies, and shared daily primitives.
- [x] 2026-08-25: passed 18 synthetic tests, including 48-field/30-year
  execution for both registered annual strategies.
- [x] 2026-08-25: independent review closed with no P0/P1 findings; repository
  and package gates passed.
- [x] 2026-08-25: committed and pushed exact implementation source
  `b842430cb665a1219e01061312357688e04e6c62` to `origin/main`.
- [ ] Open a separately identified observed-data execution from that published
  source only when dispatched.

## Surprises & Discoveries

The failed one-shot A11 attempt showed that a large monolithic science contract
was counterproductive for early research: missing choices became invisible
rather than flexible. The successor therefore permits adaptive strategy
addition but makes output-bearing strategy entries immutable.

## Decision Log

- Decision: exploratory results may inform later strategies. Rationale:
  iteration is the purpose of this stage; pretending otherwise would obscure
  the actual research process. Date/Author: 2026-08-25, operator/Codex.
- Decision: exploratory outputs cannot authorize confirmation or production.
  Rationale: flexibility and confirmatory inference require different evidence
  regimes. Date/Author: 2026-08-25, Codex.
- Decision: begin with a latent Gaussian scalar-AR(1) and fixed-length circular block
  bootstrap. Rationale: they provide a compact parametric and a minimally
  parametric comparison while sharing the same forcing and daily primitives.
  Date/Author: 2026-08-25, Codex.

## Outcomes & Retrospective

The laboratory closed `EXECUTED-COMPLETE`. Revision 1 registers a latent
Gaussian scalar-AR(1) and a fixed-length circular block bootstrap, a strict
domain-separated RNG surface, population-law covariance reconciliation, and a
composed support-valid daily core. Independent review found no unresolved P0
or P1 issue; 18 synthetic tests and all repository gates passed. Exact source
`b842430cb665a1219e01061312357688e04e6c62` was published before any observed
execution. No observed data, confirmation targets, candidate outputs, public
profiles, or production code were consumed or changed.

## Context and Orientation

The owning package is
`docs/work-packages/20260825-a11e-exploratory-strategy-lab/package.md`.
`docs/specifications/SPEC-A11-EXPLORATORY-STRATEGY-LAB.md` defines the research
surface. Package-local Python under `artifacts/` is intentional: the lab has no
public runtime authority. The prior A11 attempt and review are historical
inputs only.

## Plan of Work

Milestone 1 defines a strict additive manifest and lifecycle. Acceptance is a
manifest that rejects unknown fields, duplicate IDs, invalid RNG domains, and
capability ambiguity.

Milestone 2 implements within-site variation normalization, covariance
reconciliation, the two annual laws, and conditional daily primitives.
Acceptance is exact synthetic replay, explicit persistence, PSD receipts,
feasible wet counts without repair, and exact conditional invariants.

Milestone 3 reviews, gates, and publishes the source before any observed-data
execution. Acceptance is zero unresolved P0/P1 findings, all repository gates
passing, and `origin/main` containing the exact files.

## Concrete Steps

Run from `/Users/roger/src/cligen-rs` on `main`:

```sh
/Users/roger/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  -m unittest -v \
  docs/work-packages/20260825-a11e-exploratory-strategy-lab/artifacts/test_strategy_lab.py
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
git diff --check
```

Observed-data execution is deliberately absent. A later execution must name
the published source commit, complete the per-object Daymet preflight, and use
a fresh strategy/attempt ledger.

## Validation and Acceptance

The synthetic tests cover strict manifests, RNG separation/replay, removal of
between-site climatology, constant-field failure, tied ranks, feasible and
infeasible covariance reconciliation, annual persistence, block replay, wet
support, exact occurrence/count/amount constraints, and temperature/range
conditioning. No strategy may claim storm/context or WEPP capability until
those surfaces and tests exist.

## Idempotence and Recovery

Tests consume only synthetic in-memory arrays and are repeatable. A failure
does not create scientific output. Once an observed-data strategy executes,
its manifest entry is immutable; corrections use a new attempt only for
operational defects or a new strategy ID for scientific changes.

## Artifacts and Notes

Commit the spec, manifest/schema, implementation, tests, review, and gate
receipt. Do not commit observed streams or working-tree execution evidence.

## Interfaces and Dependencies

The lab uses Python 3.12.13 and NumPy 2.3.5 from the bundled workspace runtime.
It modifies no Rust crate, faithful path, public runspec, or profile. Later
observed execution may consume the existing Daymet/PRISM assets only after its
own calendar, role, and source-identity preflight.
