# A11E9 — Thermal Mean-Regression Attribution

Status: `EXECUTED-COMPLETE — CENTERING_REMEDY_SUPPORTED`

Date: 2026-09-10

Evidence mode: prospective observed-target development diagnostic;
confirmation sealed

Starting branch and push target: current `origin/main`, push `main`

## Objective

Determine whether A11E8's monthly-temperature mean regression is caused by
finite-cohort latent-state drift or integer-tenths rendering, and whether a
zero-mean thermal overlay preserves the demonstrated annual-dispersion gain.

## Scope

Included: the exact A11E8 20-station/32-burn grid, four frozen thermal
counterfactuals, calendar preflight, complete scoring, deterministic balancing,
cryptographic provenance, compact-input replay, review, gates, and closure.

Excluded: precipitation state, additional factors, selector changes,
confirmation, public Rust/CLI integration, promotion, and defaults.

## Authority

- [SPEC-A11-THERMAL-MEAN-REGRESSION-ATTRIBUTION](../../specifications/SPEC-A11-THERMAL-MEAN-REGRESSION-ATTRIBUTION.md)
- A11E8 rejected component evidence and frozen loading/state semantics
- operator authorization to scaffold and execute A11E9

## Plan

1. Freeze the specification, manifest, executor, and synthetic tests.
2. Publish exact source to `origin/main`, then execute one 640-stream grid.
3. Replay arm construction and scoring from the authenticated compact bundle.
4. Review, run gates, and reconcile the package, catalogs, and roadmap.

## Data calendar and missingness preflight

Repeat the A11E8/SPEC-A10-CORPUS preflight before generation. Require 20
development objects, 5,844 axis rows and 5,840 observed rows per object, four
named masked dates, mask-based eligibility, and confirmation=false.

## Gates

- deterministic centering and balancing vectors;
- exact A11E8 input identities and complete 640-record grid;
- finite metrics, exact rendered invariants, and frozen decision arithmetic;
- byte-identical replay of preflight, evidence, and decision;
- SHA-256 input/output chain and review without unresolved P0/P1;
- `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, `cargo test`;
- `git diff --check` and changed-document link validation.

Coverage/CRAP is not triggered unless a production function under `crates/`
changes.

## Exit criteria

Close with one frozen scientific disposition or an exact integrity HOLD. No
outcome promotes a model or authorizes confirmation or production.

## Artifacts

- `artifacts/execution-manifest-v1.json` — frozen experiment.
- `artifacts/execute.py` and `test_execute.py` — prospective implementation.
- `artifacts/review.md` — pending review surface.

## Outcome

Execution and replay completed from published commit
`a25f12723ae264b94749a0a69a1ad04cb0dd6858`. The 640-stream grid and all four
diagnostic arms were complete; confirmation remained sealed.

The raw arm reproduced A11E8 (`1.09564` monthly-mean error ratio). Centering
alone reduced that ratio to `1.00049`; exact zero-sum balancing reduced it to
`1.00000`. The balanced rendered arm passed every frozen gate, retained annual
dispersion error at `0.16053` of faithful, and improved 639/640 pairs. The
unquantized arm also passed, so finite-sample latent-state mean drift—not
tenths quantization—caused the regression. Disposition:
`CENTERING_REMEDY_SUPPORTED`.

This authorizes only a new prospective centered-thermal validation package;
it does not revive A11E8, promote the selector, or authorize confirmation or
production.
