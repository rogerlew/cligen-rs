# A9b — Calibration-Harness Implementation

Status: `EXECUTED-COMPLETE`
Date: 2026-07-15
Evidence mode: Ran
Scaffolding and execution authorization: operator dispatched A9b on
2026-07-15 from clean `main` at
`795f76775135044f7643e44f1f08cca1136e7236`, targeting `main`

## Objective

Implement the external, optimizer-neutral A9 research harness and prove its
contracts with synthetic and adverse fixtures before any observed candidate
tuning. The package freezes artifact canonicalization, data-role isolation,
random-field identities, candidate/optimizer plugin seams, numerical
objectives, append-only evidence, and bounded replay outside production Rust.

## Scope

Included:

- a Python research tool under `research/a9_harness/` with one documented
  command surface;
- strict JSON parsing, Draft 2020-12 schema validation, canonical bytes,
  content hashes, and immutable fit-artifact handling;
- coefficient-fit, development, gate-calibration, and confirmation role
  disjointness by path, bytes, object/logical hash, and normalized key;
- append-only access records and atomic synthetic confirmation transitions;
- mock alternating-renewal and latent-regime candidate plugins whose state
  semantics remain structurally distinct;
- a deterministic mock/exhaustive optimizer, Pareto and frozen selector
  utilities, candidate-blind null calibration, and availability handling;
- exact Philox4x32-10 and length-prefixed A9 identity vectors;
- Gregorian/nested horizons, Daymet calendar mapping, event segmentation,
  daily context, monthly moments, and deterministic quadrature;
- hash-chained attempts, checkpoints, single infrastructure retry, typed
  resource exhaustion, and retention/LFS policy checks;
- all A9a fixture groups FX-001 through FX-020, including at least 200
  independent tolerance replications per recovery class; and
- source, requirement-coverage, review, and gate evidence sufficient to
  dispatch a later A9c package.

Excluded:

- observed fit, development, gate-calibration, or confirmation data access;
- production candidate implementations, accepted station-model or generation-
  profile identifiers, generator behavior, or changes under `crates/`;
- ranking the two candidate classes for climate suitability;
- altering A9a thresholds, objectives, station rosters, or family semantics;
- changes to the faithful generator or `reference/cligen532/`;
- A9c observed development, A9d confirmation, A9e Rust pilot, downstream
  WEPP/openWEPP/WEPPcloud work, and deprecated single-storm generation.

## Authority

- [A9a package](../20260715-a9a-successor-family-foundation/package.md), whose
  required terminal is `FOUNDATION-READY-A9B`.
- [A9b handoff](../20260715-a9a-successor-family-foundation/artifacts/a9b-handoff.md).
- [SPEC-A9 research foundation](../../specifications/SPEC-A9-RESEARCH-FOUNDATION.md)
  and its registered schemas.
- A9a's model-family envelope, tuning-harness contract, data/evaluation plan,
  objective registry, fixture plan, and exact authority/exposure manifests.
- ADR-0001 protects faithful behavior; ADR-0002 and ADR-0004 govern extension
  evidence and prohibit promotion from this tooling package.

The package-local predecessor manifest records exact byte hashes. Any mismatch
is `HOLD-A9B-PREDECESSOR-INTEGRITY`, not permission to reinterpret A9a.

## Plan

1. Freeze dispatch, predecessor hashes, command permissions, implementation
   units, fixture expectations, and resource ceilings.
2. Implement canonical/schema/artifact, role-firewall, RNG/calendar/event,
   model-plugin, objective, optimizer, and append-only evidence modules.
3. Implement FX-001--FX-020 and archive canonical golden, recovery, mutation,
   replay, and resource results without observed-data access.
4. Map every normative A9 MUST/MUST NOT to executable or static evidence and
   review accuracy, leakage, numerics, structural independence, resources,
   interfaces, and repository consistency.
5. Run package verification and repository gates; close only with zero open
   P1/P2 findings and one registered terminal.

## Execution & dispatch

Execution is authorized on `main` from exact clean `origin/main` commit
`795f76775135044f7643e44f1f08cca1136e7236`; the target is `main`. No branch,
pull request, commit, or push is authorized by this dispatch.

A9b may create and consume only synthetic fixture objects. It may read A9a
specifications and metadata records but may not acquire or inspect an observed
fit, development, calibration, or confirmation target. The metadata-only A9a
confirmation roster remains unchanged.

## Gates

- exact predecessor hashes reproduce and A9a returns `FOUNDATION-READY-A9B`;
- one command surface implements `validate`, `fit`, `evaluate`, `optimize`,
  `calibrate-gates`, `confirm`, `verify-log`, and `run-fixtures` boundaries;
- all 20 fixture groups pass without waiver and have canonical evidence;
- each recovery tolerance uses at least 200 independent 100-year synthetic
  replications and validation coverage lies in [0.90, 0.99];
- published Philox, encoding, canonicalization, moment, quadrature, objective,
  event, and calendar vectors reproduce exactly;
- the role firewall rejects path, symlink, rename, copied bytes, object hash,
  logical hash, and station-period identity in every prohibited command;
- only `confirm` can atomically consume a complete synthetic sealed freeze;
- mock class factorization/state semantics remain non-isomorphic and the
  degenerate intersection returns `MODEL-CLASS-EQUIVALENCE`;
- logs retain infeasible, failed, incomplete, dominated, and complete attempts;
- replay, retry, corruption, exhaustion, retention, and LFS rules pass;
- every normative SPEC-A9 MUST/MUST NOT maps to code plus a fixture or a static
  invariant;
- no observed target is acquired/read, and no production or vendored-reference
  path changes from dispatch;
- consolidated review has zero open P1/P2 findings;
- `git diff --check` plus untracked-file whitespace scan;
- `cargo fmt --check`;
- `cargo clippy --all-targets -- -D warnings`; and
- `cargo test`.

Coverage/CRAP is not triggered unless a production function under `crates/`
changes; such a change is outside this package's authority.

## Exit criteria

`EXECUTED-COMPLETE` returns `HARNESS-READY-A9C` only when all gates pass and
the evidence proves the harness is synthetic-only and deterministically
replayable. Legitimate holds are the handoff terminals plus
`HOLD-A9B-PREDECESSOR-INTEGRITY`; every hold names the first failed fixture or
requirement. No hold authorizes A9c or candidate substitution.

## Execution outcome

A9b returns `HARNESS-READY-A9C`. It implements a Python 3.12 research harness
outside production crates with eight commands, strict canonical/schema/hash
semantics, immutable fit artifacts, a path/hash/key role firewall, hash-
chained access and attempts, exclusive one-shot confirmation consumption,
Philox4x32-10 random fields, Gregorian/event/context interfaces, analytic and
quadrature monthly budgets, objective/null/Pareto/selection machinery,
bounded exhaustive optimization, and explicit retention/LFS rules.

All 20 registered fixture groups pass. Each class used 200 independent
calibration and 400 independent validation replications of 100 synthetic
years. Renewal scalar coverage is 0.9025--0.97 with joint coverage 0.9325;
latent scalar coverage is 0.9075--0.9875 with joint coverage 0.9575. All four
predeclared recovery fit seeds pass for both classes. Five core evidence files
replay byte-for-byte; all eight commands execute on synthetic inputs.

Consolidated review is `ACCEPT` with zero open P1/P2 findings. Python unit,
type, dependency, package, whitespace, formatting, Clippy, and full Rust test
gates pass. No observed target was acquired or read, no candidate was ranked,
and neither `crates/` nor `reference/cligen532/` changed from dispatch.

Terminal: `HARNESS-READY-A9C`. A9c remains unscaffolded and unauthorized.

## Artifacts

- `artifacts/predecessor-manifest-v1.json` — exact A9a inputs and dispatch.
- `artifacts/source-manifest-v1.json` — implementation and dependency identity.
- `artifacts/generated/` — canonical fixture/golden/recovery/mutation evidence.
- `artifacts/requirement-coverage.md` — normative contract coverage.
- `artifacts/review.md` — consolidated internal review and dispositions.
- `artifacts/gate-results.md` — executed package and repository gates.
- `artifacts/a9c-handoff.md` — context-complete next-package boundary.
