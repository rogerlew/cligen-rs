# A10 Lemhi Toolkit Foundation

Status: `SCAFFOLDED`
Date: 2026-07-17
Evidence mode: Static
Starting branch and push target: clean `main` at `b25eb39`, push `main`

## Objective

Establish the smallest extensible toolkit foundation that can automate A10's
repeated Lemhi workflow mechanics without hiding authentication, scheduler,
environment, evidence, or cleanup boundaries. Freeze the normative toolkit
surface before implementation, incorporate two independent reviews, and make
the next runtime-validation dependency explicit: toolkit foundation, then a
separate CPython 3.11 smoke package, then A10M3.

## Scope

Included:

- the normative
  [Lemhi agent toolkit specification](../../specifications/SPEC-LEMHI-AGENT-TOOLKIT.md);
- a dependency-light `rmm` control plane, POSIX `sh` bootstrap/staging layer,
  and profile-declared job-runner boundary;
- versioned capability, plan, transfer, job, evidence, and cleanup records;
- separate private operational state and sanitized publication receipts;
- replaceable runtime, framework, transport, scheduler, and storage providers;
- explicit discovery, selection, staging, proof, collection, and cleanup
  states;
- fail-closed handling of MFA, login/compute drift, platform targeting,
  resource ceilings, confirmation data, and destructive paths;
- a minimum vertical-slice implementation plan and acceptance gates; and
- two independent reviews with every finding accepted, rejected, deferred, or
  superseded in a retained disposition.

Excluded:

- implementing or installing the toolkit in this scaffold;
- downloading or selecting a portable Python distribution;
- remote writes, Slurm submissions, GPU allocations, or a Python 3.11 claim;
- candidate training, A10M3 execution, or confirmation-target access;
- administrator-owned configuration, credentials, SSH aliases, control
  sockets, modules, or cluster-global installation; and
- changes to generator behavior, production interfaces, or faithful-mode
  authority.

## Authority

- The operator's instruction to scaffold the toolkit foundation, draft an
  authoritative specification, dispatch two reviewers, disposition findings,
  and order the roadmap is authority for this package.
- [A10M2 completion](../20260717-a10m2-completion/package.md),
  [A10M2D1](../20260716-a10m2d1-lemhi-cuda-drift-diagnostic/package.md),
  [A10M2D2](../20260716-a10m2d2-rmm-lemhi-scp-characterization/package.md),
  and the
  [agent compute guide](../../c3-lemhi-gpu-computing-for-agents.md) are the
  observed operational authority.
- The toolkit specification is normative for toolkit implementations. Live
  cluster observations remain authoritative over cached capabilities and
  public documentation.
- This package changes no CLIGEN scientific or generator authority.

## Plan

1. Freeze the toolkit boundary, lifecycle, records, provider contract, safety
   invariants, versioning rules, and minimum vertical slice in the
   specification.
2. Update the specification registry, work-package catalog, and roadmap with
   the mandatory toolkit-to-Python-3.11-smoke-to-A10M3 dependency.
3. Dispatch two independent subagents: architecture/extensibility review and
   HPC safety/reproducibility review.
4. Record each finding and its disposition; revise the specification where an
   accepted finding changes the normative contract.
5. Run documentation and repository gates. Leave this implementation package
   `SCAFFOLDED` until the operator dispatches execution.

## Execution and dispatch

The future implementation executor must start from the current `origin/main`
named by its kickoff prompt and push only to `main`. Execution may create
repository-local toolkit code and deterministic fixtures. It receives no
implicit authority for remote writes or allocations; any live validation must
be separately frozen and dispatched.

The two scaffold reviewers are read-only. They may inspect the package,
specification, guide, and predecessor evidence, but may not edit files or
perform remote operations.

## Gates

- the specification distinguishes discovery, selection, and proof;
- the minimum vertical slice is useful without a plugin framework or remote
  Python dependency;
- extension points are versioned, deterministic, and fail closed;
- authentication cannot fall back from warm `BatchMode=yes` control masters;
- every destructive operation is bound to an exact registered run root and
  marker;
- login and compute capability receipts cannot be conflated;
- runtime plans bind OS, architecture, libc, interpreter, framework, CUDA,
  hashes, and final install path before use;
- no provider may silently fall back or mutate a frozen plan;
- resource and confirmation firewalls are machine-checkable inputs;
- submission is single-writer, resource-reserved, token-reconciled, and
  at-most-once under ambiguous Slurm outcomes;
- the resource ledger and lock are authority-budget-wide across runs, plan
  revisions, attempts, and retries;
- repeatable per-attempt state represents sequential, parallel, retry,
  cancellation, and expected-nonzero jobs without corrupting run state;
- prospective amendments preserve completed evidence and cumulative resource
  use while changing only authorized unstarted work;
- all shell-facing values have injection-safe grammars and argument passing;
- confirmation allowlisting precedes every filesystem observation;
- exact operational paths remain private through failure-atomic cleanup while
  publication receipts remain sanitized;
- job-local cleanup survives hard termination only through a declared purge or
  authorized recovery contract;
- two independent reviews are retained and every finding is dispositioned;
- `git diff --check`, `cargo fmt --check`,
  `cargo clippy --all-targets -- -D warnings`, and `cargo test` pass.

Coverage/CRAP is not triggered by this scaffold because it changes no
production function under `crates/`.

## Exit criteria

The scaffold is ready for implementation dispatch when:

- the package, specification, registry, catalog, and roadmap agree;
- both independent reviews are complete;
- no accepted P1/P2 finding remains unresolved; and
- all static and repository gates pass.

Future package execution reaches `EXECUTED-COMPLETE` only after the minimum
vertical slice and its deterministic fixtures satisfy the specification. It
does not establish Python 3.11 support; that belongs to the separate smoke
package.

Legitimate execution holds are:

- `EXECUTED-HOLD-CONTRACT-INCOMPLETE` — an interface cannot be implemented
  without an unmade policy decision;
- `EXECUTED-HOLD-SAFETY-INVARIANT` — exact cleanup, authentication, resource,
  or confirmation boundaries cannot be enforced; or
- `EXECUTED-HOLD-PORTABILITY` — the minimum controller/runner boundary needs
  an unavailable host or remote dependency.

## Artifacts

- `artifacts/architecture-review.md` — independent extensibility review;
- `artifacts/hpc-safety-review.md` — independent HPC safety review;
- `artifacts/review-disposition.md` — authoritative finding dispositions;
- `artifacts/architecture-review-round2.md` and
  `artifacts/hpc-safety-review-round2.md` — fresh convergence reviews;
- `artifacts/review-disposition-round2.md` — round-2 dispositions and final
  convergence verification; and
- `artifacts/scaffold-gates.md` — validation receipt.
