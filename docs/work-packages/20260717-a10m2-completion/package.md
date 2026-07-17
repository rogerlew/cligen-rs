# A10M2 Completion — Lemhi Compute Readiness

Status: `EXECUTED-COMPLETE`
Date: 2026-07-17
Evidence mode: Mixed
Starting branch and push target: clean `main` at `c5dadd0`, push `main`

## Objective

Complete the held A10M2 cluster-readiness milestone without rewriting its
immutable evidence. Apply A10M2D1's observed CUDA correction, integrate the
required A10M2D2 stage-2 storage test with A10M1's accepted v2 transfer set,
and prove offline one-GPU PyTorch, two-GPU NCCL/DDP, and synthetic Slurm
checkpoint/restart behavior on Lemhi's I-CREWS-priority L40 path.

## Scope

Included:

- noninteractive use of an operator-bootstrapped VPN/SSH control path;
- direct CUDA 12.8 with explicit `/usr/bin/g++`, followed by the unchanged
  CUDA allocation/transfer/kernel check;
- a completely hashed compute-valid Linux x86-64 Python 3.8 / PyTorch 2.4.1
  CUDA 12.4 wheelhouse, reconstructed without compute-node network access;
- one-L40 tensor, autograd, optimizer, checkpoint, and reload checks;
- A10M2D2 stage 2 using all 98 accepted A10M1 v2 objects (223,799,545
  bytes): Ceph-to-job-local many-object and archive staging, SHA-256, bounded
  read, durable copy-back, cache fallback, and exact local cleanup;
- a two-L40 NCCL all-reduce and one-step DDP check on one node;
- a Slurm `USR1` checkpoint drill and separate manual resume/control check;
- accounting, sanitization, cleanup, package review, repository gates, and
  the A10M3 handoff.

Excluded:

- candidate training, development scoring, throughput/scaling claims,
  confirmation targets, cross-node work, or deliberate preemption;
- changes to Rust production code, generator behavior, or public interfaces;
- claims that the observed compiler path is administrator-supported; and
- credentials, usernames, absolute operator paths, VPN state, SSH sockets,
  or unrestricted environment dumps in retained artifacts.

## Authority and predecessor state

- The operator's `Scaffold and execute the A10M2 completion package`
  instruction authorizes this bounded package, its remote staging, and its
  frozen Slurm matrix.
- [A10M2](../20260716-a10m2-lemhi-gpu-integration/package.md) remains
  immutable at `EXECUTED-HOLD-CUDA-ENVIRONMENT`.
- [A10M2D1](../20260716-a10m2d1-lemhi-cuda-drift-diagnostic/package.md)
  localized the drift and proved direct CUDA 12.8 plus `/usr/bin/g++`.
- [A10M2D2](../20260716-a10m2d2-rmm-lemhi-scp-characterization/package.md)
  requires stage 2 inside the next GPU-bearing continuation.
- [A10M1](../20260717-a10m1-corpus-role-freeze/package.md) authorizes only
  its accepted v2 transfer identities; failed v1 objects and confirmation
  targets remain prohibited.
- Live scheduler, driver, filesystem, and executable state is authoritative
  for execution. This package changes no faithful generator authority.

## Frozen resource envelope

| Job | Partition / GRES | CPU / memory / time | Purpose |
|---|---|---|---|
| P0 (amended) | `gpu-icrews`, `gpu:l40:1` | 2 CPU, 8 GB, 5 min | localize C1's pre-output compute precondition |
| C1 | `gpu-icrews`, `gpu:l40:1` | 4 CPU, 16 GB, 15 min | corrected CUDA, offline framework, one-GPU, and stage 2 |
| C2 | `gpu-icrews`, `gpu:l40:2` | 8 CPU, 32 GB, amended to 2 min | two-rank NCCL/DDP |
| C3a | `gpu-icrews`, `gpu:l40:1` | 2 CPU, 8 GB, amended to 2 min | Slurm signal and durable checkpoint |
| C3b | `gpu-icrews`, `gpu:l40:1` | 2 CPU, 8 GB, amended to 2 min | manual resume and control comparison |

The original base matrix requests 35 GPU-minutes. Amendment 01 added P0 after
C1-01 failed before its first output. Amendment 04 shortened the still-unrun
jobs after C2-01's pre-import entrypoint failure; all submitted and planned
attempts total 53 GPU-minutes. Any exact infrastructure retry remains allowed
only when cumulative requested use stays at or below 60 GPU-minutes. No
scientific failure is rerun. Jobs are sequential and later jobs are not
submitted after a hard failure.

## Plan

1. Freeze this package, exact scripts, inputs, pass rules, retry policy,
   environment selection, and source identities; publish them to `main` before
   the first new remote write or allocation.
2. Build and hash the wheelhouse and A10M1 bundle on `rmm`; verify all logical
   inputs against A10M1's accepted manifest before transfer.
3. Verify both SSH masters, stage only the package-owned run directory, verify
   archives after upload, and record sanitized live control-plane receipts.
4. Run C1 through C3b sequentially, classifying every terminal state from
   logs plus `sacct` before continuing.
5. Retrieve and sanitize evidence, remove only the exact remote run directory,
   verify absence, review the claims, run repository gates, and reconcile the
   roadmap/catalog.

## Gates

- scaffold and execution commit are published before remote mutation or GPU
  allocation;
- every local A10M1 input matches the accepted v2 object hash and aggregate;
- every transferred archive matches its frozen SHA-256 before extraction;
- C1 repeats the unchanged CUDA smoke with explicit `/usr/bin/g++`, rebuilds
  the frozen framework solely from verified wheels, passes `pip check`, and
  passes the one-L40 framework check;
- stage 2 verifies all 98 objects on Ceph and job-local storage, measures both
  layouts and a bounded read/copy-back, proves verified durable fallback, and
  removes the exact job-local directory;
- C2 observes two distinct L40 devices and two NCCL ranks, gets the registered
  all-reduce result, performs one DDP update, proves identical parameters, and
  closes the process group cleanly;
- C3a receives Slurm's frozen signal, atomically publishes a verified durable
  checkpoint, and exits with the classified interruption code; C3b resumes
  that exact checkpoint and matches an uninterrupted control;
- all submissions are accounted for and cumulative requested use is at most
  one GPU-hour;
- no confirmation target is accessed and retained evidence is sanitized;
- the exact remote run is removed after retrieval and its absence is verified;
- review has no open P1/P2 finding;
- authored Python compiles, shell passes `bash -n`, `git diff --check`,
  `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, and
  `cargo test` pass. Coverage/CRAP is not triggered because production Rust
  functions are unchanged.

## Exit criteria

`EXECUTED-COMPLETE` requires terminal `A10M2-COMPUTE-READY` and every gate
above. Because A10M1 is already `A10M1-CORPUS-READY`, that terminal permits
the separately scaffolded and dispatched A10M3 milestone; it does not itself
execute A10M3.

Named holds remain `EXECUTED-HOLD-GPU-AUTHORIZATION`,
`EXECUTED-HOLD-CUDA-ENVIRONMENT`, `EXECUTED-HOLD-OFFLINE-RECONSTRUCTION`,
`EXECUTED-HOLD-COLLECTIVES`, `EXECUTED-HOLD-STORAGE-RESTART`, and
`EXECUTED-HOLD-RESOURCE-BOUND`. A hold preserves all evidence and names the
smallest corrective action.

## Artifacts

- `artifacts/design-freeze.md` — immutable execution and pass rules;
- `artifacts/environment/` — framework lock, wheel hashes, and notices;
- `artifacts/jobs/` — exact staged and submitted sources;
- `artifacts/logs/` — sanitized execution and accounting evidence;
- `artifacts/logs/execution-summary.md` — sanitized per-attempt evidence;
- `artifacts/scheduler-receipt.md` and `artifacts/resource-ledger.md` — Slurm
  accounting and the frozen one-GPU-hour ledger;
- `artifacts/transfer-receipt.md` and `artifacts/stage2-result.md` — verified
  transfer and storage-path observations;
- `artifacts/cleanup.md`, `artifacts/gates.md`, and `artifacts/review.md` —
  closure evidence; and
- `artifacts/terminal.md` and `artifacts/a10m3-handoff.md` — terminal
  disposition and bounded successor contract.

## Execution note

C1-01 (`1013668`) received one typed L40 on `node03` and failed after one
second before its first output. Amendment 01 prospectively adds P0 to identify
the compute-node precondition. P0 (`1013670`) proved the login-visible Python
3.11 path absent and compute Python 3.8.11 valid. Amendment 02 freezes the
compute-valid framework ABI before C1-02; no later base job has been submitted.
C1-02 (`1013671`) then passed in 76 seconds. Amendment 03 isolates Python and
loader paths prospectively for unsubmitted C2/C3 after a non-gating ambient
NumPy probe warning; it changes no test, framework, or resource.
C2-01 (`1013672`) saw two L40s but a stale moved-venv `torchrun` shebang failed
before import. Amendment 04 switches to interpreter-module launch and reduces
the still-unrun limits; the complete planned ledger is 53 GPU-minutes.

## Result

Terminal: `A10M2-COMPUTE-READY`

C1-02 passed the corrected CUDA smoke, hashed offline framework
reconstruction, one-L40 framework check, and 98-object stage-2 storage test.
C2-02 passed two-L40 NCCL all-reduce and DDP after the published entrypoint
correction. C3a received Slurm `USR1` and atomically published the registered
checkpoint; C3b resumed it and exactly matched the uninterrupted control.

The seven allocations consumed 53 requested and 2.0167 actual GPU-minutes.
Evidence retrieval and its SHA-256 were verified before the exact remote run
was removed; the post-cleanup queue was empty. No confirmation target was
accessed. The retained limitations and A10M3 constraints are recorded in the
[terminal](artifacts/terminal.md) and
[handoff](artifacts/a10m3-handoff.md).
