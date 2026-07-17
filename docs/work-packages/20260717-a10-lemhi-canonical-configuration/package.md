# A10 Lemhi Canonical Configuration

Status: `EXECUTED-COMPLETE`
Date: 2026-07-17
Evidence mode: Ran (retained smoke evidence plus repository identity checks)
Execution branch and push target: `main`

## Objective

Promote the accepted CPython 3.11 one-L40 smoke stack into the current
versioned canonical configuration for A10 Lemhi GPU agents, require later A10
consumers to bind its identifier and semantic hash, and retain the Python 3.8
A10M2 stack only as an explicit legacy fallback.

## Scope

Included:

- authoritative configuration semantics and consumer/invalidation policy;
- one machine-readable record pinning the proven provider, runtime, framework,
  scheduler, storage, isolation, evidence, and cleanup identities;
- a regression test that recomputes the semantic identity and hashes every
  repository-resident dependency;
- operator-guide and toolkit documentation; and
- the A10M3 roadmap handoff.

Excluded:

- new downloads, transfers, remote writes, Slurm jobs, GPU allocations, or
  confirmation access;
- performance, training, multi-GPU, requeue, durability, scientific, or
  administrator-support claims; and
- mutation of the accepted smoke evidence or A10M2 historical record.

## Authority

- The operator explicitly directed that the passing configuration be locked in
  as the current canonical configuration.
- The accepted evidence authority is the
  [CPython 3.11 smoke package](../20260717-a10-lemhi-python311-smoke/package.md),
  terminal `A10-LEMHI-PY311-SMOKE-READY`.
- The toolkit lifecycle remains governed by
  [SPEC-LEMHI-AGENT-TOOLKIT](../../specifications/SPEC-LEMHI-AGENT-TOOLKIT.md).

## Plan

1. Define the canonical-configuration record identity, consumer obligations,
   legacy fallback, invalidation, replacement, and claim boundaries.
2. Materialize `lemhi-a10-py311-l40-v1` with exact profile, provider, artifact,
   lock, manifest, evidence, scheduler, storage, and isolation identities.
3. Add a deterministic identity/linkage test and update the guide, toolkit,
   specification registry, smoke handoff, catalog, and roadmap.
4. Run package and repository gates, record the terminal, commit, and push
   `main`.

## Gates

- the semantic SHA-256 recomputes from canonical JSON with only its identity
  field omitted;
- all repository-resident pinned files exist as regular nonsymlink files and
  match their recorded hashes and byte counts where recorded;
- the accepted 19-gate receipt is pinned exactly;
- A10M3 is required to bind both configuration ID and semantic hash;
- Python 3.8 is legacy explicit-only and automatic fallback is prohibited;
- invalidation requires a new versioned candidate and fresh bounded smoke;
- `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`,
  `cargo test`, toolkit unit tests, JSON parsing, and `git diff --check` pass.

Coverage/CRAP is not triggered because this package changes no production
function under `crates/`.

## Exit criteria

`EXECUTED-COMPLETE` requires terminal
`A10-LEMHI-CANONICAL-CONFIGURATION-LOCKED`, exact agreement among the record,
specification, guide, roadmap, and regression test, and all gates passing. A
hash or evidence mismatch is `EXECUTED-HOLD-IDENTITY-DRIFT`; an unmade consumer
or invalidation policy decision is `EXECUTED-HOLD-POLICY-INCOMPLETE`.

## Artifacts

- `artifacts/validation.md` — final identity and repository gate receipt.

## Execution result

Terminal: `A10-LEMHI-CANONICAL-CONFIGURATION-LOCKED`

Configuration `lemhi-a10-py311-l40-v1`, semantic SHA-256
`0b1115a6801259c62d9550c877a3c49a897319348ba1c2027be0d9c4f77c1179`,
is now the current canonical A10 Lemhi single-L40 Python stack. The record,
specification, guide, toolkit documentation, smoke lineage, A10M3 handoff, and
machine identity test agree. Python 3.8 remains legacy explicit-only.
