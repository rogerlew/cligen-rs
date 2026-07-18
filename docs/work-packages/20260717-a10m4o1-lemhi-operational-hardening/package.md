# A10M4O1 — Lemhi Operational Hardening

Status: `SCAFFOLDED`
Date: 2026-07-17
Evidence mode: Mixed
Starting branch and push target: clean `main` at `d9f3a6c`, push `main`

## Objective

Convert the operational friction and failure evidence from A10M4 into durable
agent guidance and generic Lemhi-toolkit safeguards before A10M5 creates
scored development candidates. Reduce manual plan editing, make failure
collection and job-local cleanup reliable, validate complete build/runtime
closures, and stop treating empirically unproved storage or environment
behavior as canonical.

## Scope

Included:

- update the Lemhi agent compute guide, toolkit README, and authoritative
  toolkit specification with the accepted A10M4 lessons and recovery rules;
- add an explicit compute-safe toolchain provider contract that validates the
  complete Rust/compiler/build closure and extracted layout;
- add toolkit-owned process-supervisor semantics for job-local admission,
  ownership, signal forwarding, all-catchable-exit cleanup, durable cleanup
  status, reserved recovery capacity, and exact recovery after an uncatchable
  exit;
- replace the unproved `scheduler_purged` job-local assumption for new work
  with a versioned `toolkit_recoverable` storage contract;
- add deterministic required-job-environment validation, including
  `CUBLAS_WORKSPACE_CONFIG=:4096:8` where deterministic CUDA work requires it;
- split authenticated raw collection from publication, then apply typed,
  boundary-aware deterministic projection while still rejecting unknown
  forbidden material;
- add safe authority revision/run derivation against one persistent
  hash-chained ledger anchor with an exclusive genesis, published head
  checkpoints, and pre-spend scheduler reconciliation, plus integer transfer
  telemetry and immutable per-run revision manifests;
- preserve the application-owned lessons for masked rows, checkpoint cursors,
  CPU-first deserialization, and format-aware completeness tests in package
  authoring guidance rather than overgeneralizing them into toolkit core;
- split immutable configuration semantics, smoke attestation, and canonical
  designation; create a versioned successor candidate and scaffold its bounded
  smoke successor after the toolkit/provider changes; and
- deterministic positive/adverse fixture coverage, review disposition,
  roadmap/catalog reconciliation, and repository gates.

Excluded:

- A10M5 training or scoring, development/confirmation target access, model or
  selector changes, and reinterpretation of A10M4 timing ratios;
- changing the frozen 5x/10x runtime thresholds; that is a separate prospective
  scientific-contract decision;
- automatic MFA, interactive SSH fallback, direct SSH to compute nodes,
  administrator-owned module changes, or unbounded recovery allocations;
- cross-run or cross-authority cluster caching, quota claims, physical secure
  erasure, arbitrary provider-supplied code, or a general dependency solver;
- mutating canonical configuration `lemhi-a10-py311-l40-v1` in place; and
- live GPU allocation during this hardening package.

## Authority

- A10M4 terminal `A10M4-QUALIFICATION-READY`, its eleven run records, ten
  prospective amendments, sanitized evidence, and exact cleanup record are the
  empirical authority.
- `SPEC-LEMHI-AGENT-TOOLKIT` remains normative until this package prospectively
  amends it before implementation.
- `SPEC-LEMHI-CANONICAL-CONFIGURATION` requires a new configuration version and
  bounded smoke when provider, storage, or deterministic execution semantics
  change. Historical `v1` evidence remains immutable.
- The operator authorizes repository authoring, local fixtures, dual-agent
  review, disposition, and push to `main`. No remote write or allocation is
  authorized by scaffolding this package.

## Plan

1. Freeze the lesson/remedy register, ownership boundary, exact v2
   records/providers/commands, ledger genesis/checkpoint/reconciliation model,
   and canonical successor sequence before code.
2. Amend the toolkit specification and agent guide, then implement the minimum
   generic safeguards in toolkit core, remote scripts, providers, examples,
   and README.
3. Add deterministic fixtures for pre-receipt failure, insufficient job-local
   space, catchable and uncatchable exits, recovery accounting, exact-token
   sanitization, toolchain/layout closure, stable authority derivation,
   deterministic environment, and transfer telemetry/matrix reuse.
4. Publish a new canonical-configuration candidate without rewriting `v1` and
   scaffold a separate bounded Lemhi smoke package as the only route to making
   the candidate current.
5. Run package and repository gates, audit prohibited data/side effects,
   reconcile roadmap/catalog, and publish the terminal and successor handoff.

## Execution and dispatch

Execute from current `origin/main` in `/Users/roger/src/cligen-rs` and push
only to `main`. Specification and fixture changes precede implementation.
Execution is local on `rmm`; injected adapters and temporary directories stand
in for SSH, Slurm, and remote storage. A later canonical smoke package receives
its own explicit remote/resource dispatch.

The two scaffold reviews are independent and advisory. The primary agent owns
their written disposition and may revise this package before execution. Review
does not authorize implementation, remote mutation, or allocation.

## Gates

- every A10M4 stumble has one owned disposition: toolkit implementation,
  documentation/application guidance, canonical successor, or explicit defer;
- spec/record/CLI/provider changes are versioned and fail closed; historical
  receipts and canonical `v1` remain readable and immutable;
- fixture tests prove reserved recovery capacity, settled exact recovery
  targets, cleanup on every catchable exit, fail-closed hard-kill behavior,
  race-safe capacity admission, safe raw collection/projection, complete
  toolchain closure, anchored and reconciliation-checked authority lineage,
  and integer stage telemetry;
- no test initiates MFA, SSH, Slurm, remote write, GPU allocation, development
  target read, or confirmation access;
- Python and shell sources parse; all package JSON parses; toolkit tests,
  A10M3 contract tests, `git diff --check`, `cargo fmt --check`,
  `cargo clippy --all-targets -- -D warnings`, and `cargo test` pass.

Coverage/CRAP is not triggered unless execution changes a production function
under `crates/`.

## Exit criteria

`A10M4O1-TOOLKIT-HARDENED` requires every gate, accepted review disposition,
an immutable canonical-successor semantic contract, and a separately
scaffolded smoke handoff. It does not create a smoke attestation, advance the
canonical designation, or authorize A10M5.

Holds are `HOLD-A10M4O1-SPEC-BOUNDARY`,
`HOLD-A10M4O1-RECOVERY-UNSAFE`, `HOLD-A10M4O1-SANITIZATION-UNSAFE`,
`HOLD-A10M4O1-CANONICAL-TRANSITION`, or the exact failed compatibility/gate
condition. A hold preserves findings and does not fall back to the old storage
claim for new commitments.

## Artifacts

- `artifacts/lessons-register.md` — stumble, cause, owner, and remedy map;
- `artifacts/design-freeze.md` — proposed toolkit/documentation contract;
- `artifacts/architecture-review-brief.md` and
  `hpc-safety-review-brief.md` — independent review instructions;
- `artifacts/architecture-review.md`, `hpc-safety-review.md`, and
  `review-disposition.md` — populated during scaffold review;
- `artifacts/scaffold-gates.md` — scaffold validation; and
- execution evidence, terminal, and canonical-smoke handoff — populated only
  when the package is later executed.
