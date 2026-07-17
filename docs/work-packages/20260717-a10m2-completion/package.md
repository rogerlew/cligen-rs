# A10M2 Completion — Lemhi Compute Readiness

Status: `SCAFFOLDED`
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
- a completely hashed Linux x86-64 Python 3.11 / PyTorch 2.7.1 CUDA 12.8
  wheelhouse, reconstructed without compute-node network access;
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
| C2 | `gpu-icrews`, `gpu:l40:2` | 8 CPU, 32 GB, 5 min | two-rank NCCL/DDP |
| C3a | `gpu-icrews`, `gpu:l40:1` | 2 CPU, 8 GB, 5 min | Slurm signal and durable checkpoint |
| C3b | `gpu-icrews`, `gpu:l40:1` | 2 CPU, 8 GB, 5 min | manual resume and control comparison |

The original base matrix requests 35 GPU-minutes. Amendment 01 adds P0 after
C1-01 failed before its first output. C1-01, P0, a corrected C1, and the
remaining base jobs total at most 55 GPU-minutes. At most one exact retry after a
documented infrastructure transient is allowed, and only when cumulative
requested use remains at or below 60 GPU-minutes. No scientific failure is
rerun. Jobs are sequential and later jobs are not submitted after a hard
failure.

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
- terminal, review, ledgers, cleanup, gates, and A10M3 handoff are produced
  during execution.

## Execution note

C1-01 (`1013668`) received one typed L40 on `node03` and failed after one
second before its first output. Amendment 01 prospectively adds P0 to identify
the compute-node precondition; no later base job has been submitted.
