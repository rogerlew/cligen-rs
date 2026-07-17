# A10M2 — Lemhi GPU Integration and Restartability Readiness

Status: `SCAFFOLDED`
Date: 2026-07-16
Evidence mode: Mixed
Scaffolding authorization: operator direction on 2026-07-16 from clean
`main` at `9c6570bf00d0ff4be8e4a2f569b8f00cf19c159c`, targeting `main`

## Objective

Establish that the A10 research workflow can reach Lemhi through the
supervised MFA bootstrap, submit bounded jobs through the I-CREWS-priority GPU
partition, execute compatible CUDA and pinned offline PyTorch workloads on one
and two L40 GPUs, use durable and node-local storage correctly, and survive a
synthetic Slurm interruption/restart. Produce an auditable environment and
resource receipt that A10M3/A10M4 can rely on without claiming that the A10
model itself has been implemented or qualified.

## Scope

Included:

- reproduce the SSH/VPN, Slurm association, group, partition, priority,
  preemption, node, module, driver, filesystem, and accounting inventory;
- verify access through `gpu-icrews` with typed `gpu:l40` requests without
  deliberately displacing another job;
- compile and run a deterministic CUDA allocation/transfer/kernel/result
  smoke test with no framework dependency;
- select a driver-compatible Python 3.11/PyTorch/CUDA stack only after the
  live driver receipt exists, stage its complete Linux x86-64 wheelhouse or
  approved image, and reconstruct it without compute-node network access;
- run a one-GPU PyTorch tensor/autograd/optimizer/checkpoint smoke;
- run a two-GPU NCCL collective and minimal DDP smoke on one node;
- discover and measure Ceph/project durability and `$SLURM_TMPDIR` or the
  actual node-local alternative, without assuming the public guide's paths;
- run a synthetic signal/checkpoint/manual-resume drill that proves Slurm,
  storage, and environment behavior; and
- retain exact scripts, hashes, job/accounting receipts, sanitized logs,
  resource use, review, gates, cleanup, and the A10M3 handoff.

Excluded:

- A10 corpus acquisition or production training shards;
- A10 architecture choice, candidate training, development scoring, or
  confirmation access;
- M4's authoritative A10 model/optimizer/scheduler/scaler/RNG/sampler/data-
  cursor interruption-equivalence test;
- cross-node training, four-GPU scaling, performance tuning, or throughput
  claims beyond smoke diagnostics;
- deliberate preemption of a `gpu-volatile` job;
- production Rust functions, generation profiles, or public interfaces; and
- credentials, SSH keys/sockets, VPN material, usernames, absolute operator
  paths, or unrestricted environment dumps in committed artifacts.

## Authority

- [A10 study plan M2](../../planning/a10-study-plan.md#M2--cluster-and-restartability-readiness)
  defines the scientific and operational boundary.
- [A10 review and operator amendment](../../planning/a10-study-plan-review.md#post-review-operator-amendments)
  records the accepted design and milestone-package topology change.
- Live Slurm/module/driver/filesystem state is authoritative for execution;
  the public [C3+3 GPU guide](https://docs.c3plus3.org/docs/workshops/Cluster/GPU_Nodes.html)
  is secondary where it conflicts with a timestamped live receipt.
- The package changes no faithful or production generator behavior.

## Frozen resource envelope

| Job | Partition and GRES | CPU / memory / time | Purpose |
|---|---|---|---|
| J1 | `gpu-icrews`, `gpu:l40:1` | 2 CPU, 8 GB, 10 min | CUDA compiler/driver/kernel and storage smoke |
| J2 | `gpu-icrews`, `gpu:l40:1` | 4 CPU, 16 GB, 10 min | offline PyTorch reconstruction and one-GPU smoke |
| J3 | `gpu-icrews`, `gpu:l40:2` | 8 CPU, 32 GB, 5 min | NCCL collective and minimal DDP smoke |
| J4a | `gpu-icrews`, `gpu:l40:1` | 2 CPU, 8 GB, 5 min | synthetic Slurm signal and durable checkpoint |
| J4b | `gpu-icrews`, `gpu:l40:1` | 2 CPU, 8 GB, 5 min | manual resume and control comparison |

The base matrix requests at most 40 GPU-minutes. At most one exact rerun of a
job invalidated by a documented infrastructure transient adds no more than 10
GPU-minutes, so the frozen maximum is 50 GPU-minutes (0.833 GPU-hour) under a
hard 1-GPU-hour ceiling. A rerun does not change code, environment, resources,
or pass criteria. Any other retry or resource increase requires a recorded
package amendment before submission.

## Plan

1. Freeze the execution dispatch, source commit, live-authority commands,
   artifact schema, job matrix, pass/fail rules, cleanup rules, and resource
   ceiling. Verify the `login-ui` and `lemhi` control masters; fail closed for
   human bootstrap if either is absent.
2. Reproduce the sanitized control-plane preflight. Record Slurm 25.05.6,
   account/group eligibility, `gpu-icrews` versus `gpu-volatile` priority and
   preemption settings, typed L40 availability, module tree, storage, and an
   empty/known starting job inventory.
3. Commit the CUDA source and J1 Slurm script before submission. Use
   `module purge`, `/opt/modules/modulefiles`, and the live CUDA module. Require
   the CUDA runtime to see exactly the allocated device count; compile and run
   allocation, transfer, kernel, synchronization, result, and durable-output
   checks.
4. Select the pinned framework stack from J1's driver/runtime receipt. Build a
   complete offline wheelhouse or verified image outside the compute job,
   record hashes and licenses, reconstruct from only those assets, and execute
   J2's seeded tensor/autograd/optimizer/checkpoint/reload smoke.
5. Execute J3 with two typed L40 GPUs on one node. Verify distinct rank/device
   binding, NCCL initialization, a known all-reduce result, one minimal DDP
   update, clean process-group shutdown, and bounded resources.
6. Execute J4a/J4b with a synthetic state machine. J4a writes an atomic durable
   checkpoint, receives the frozen Slurm signal, and terminates with a
   classified receipt. J4b manually resumes from the exact checkpoint and
   compares resumed state/trace with the uninterrupted control. Observe
   requeue support but do not depend on it unless verified.
7. Retrieve logs through the configured `lemhi` transport, record `sacct` and
   `scontrol` receipts, hash every retained artifact, remove nonretained
   environment/scratch objects, independently review the claims, run gates,
   and emit the A10M2 terminal and A10M3 handoff.

## Execution & dispatch

The operator authorized this scaffold on clean `main` at
`9c6570bf00d0ff4be8e4a2f569b8f00cf19c159c`; `main` is the only push target.
Scaffolding does not itself submit Slurm jobs, install a remote environment, or
deliver a signal. Execution requires a kickoff naming the then-current
`origin/main` commit, referencing an accepted A10M0 predecessor terminal, and
confirming that the five-job resource envelope is authorized. A10M1 may execute
in parallel and is not required for A10M2 closure.

MFA remains human-supervised. The executor uses only pre-existing SSH masters
and noninteractive commands with `BatchMode=yes`; it never receives or stores
password or Duo material. The repository keep-alive may preserve a bootstrapped
session but cannot create one.

## Gates

- exact execution dispatch, source identity, job scripts, environment assets,
  pass/fail rules, and resource ceiling are frozen before J1;
- the account remains in `icrews`, `gpu-icrews` remains group-authorized and
  higher-tier than `gpu-volatile`, and no test intentionally triggers
  preemption;
- all five `sbatch --parsable` submissions are accepted and each job reaches a
  terminal accounting state with a complete classified receipt;
- J1 runs on an L40 allocation, sees exactly one CUDA device, and passes the
  compiler/driver, allocation, transfer, kernel, synchronization, numerical,
  and durable-output checks;
- J2 reconstructs without network access, reports the pinned Python/PyTorch/
  CUDA/cuDNN identities, uses the GPU, produces finite expected diagnostics,
  and reloads its checkpoint successfully;
- J3 sees exactly two distinct allocated L40 devices and passes the registered
  NCCL all-reduce and DDP update;
- J4a's durable checkpoint verifies, the signal path is classified, and J4b's
  resumed synthetic state/trace matches the uninterrupted control under the
  frozen rule;
- actual durable, local, scratch, wall-time, memory, GPU-memory, and cleanup
  behavior is measured rather than inferred;
- total requested GPU use does not exceed 1 GPU-hour and the attempt inventory
  accounts for every submission and rerun;
- committed logs are sanitized and contain no credentials, usernames,
  absolute operator paths, tokens, unrestricted environment dumps, or
  confirmation data;
- package review has zero open P1/P2 findings;
- authored shell passes `sh -n` and applicable static checks;
- `git diff --check`, `cargo fmt --check`,
  `cargo clippy --all-targets -- -D warnings`, and `cargo test` pass on an
  identified environment; and
- coverage/CRAP is not triggered unless execution changes a production
  function under `crates/`.

## Exit criteria

`EXECUTED-COMPLETE` requires terminal `A10M2-COMPUTE-READY`: every in-scope
gate passes, the environment can be reconstructed offline, one- and two-GPU
smokes pass, synthetic restart behavior is proven, cleanup is recorded, and a
bounded A10M3 handoff is complete. This terminal does not authorize A10M3
until A10M1's required corpus/role evidence is also accepted.

Legitimate holds are:

- `EXECUTED-HOLD-GPU-AUTHORIZATION` — the live account cannot schedule the
  frozen `gpu-icrews`/L40 request;
- `EXECUTED-HOLD-CUDA-ENVIRONMENT` — the driver/toolkit/kernel path cannot pass;
- `EXECUTED-HOLD-OFFLINE-RECONSTRUCTION` — the pinned framework stack cannot
  be reconstructed without compute-node network access;
- `EXECUTED-HOLD-COLLECTIVES` — the frozen two-GPU NCCL/DDP smoke cannot pass;
- `EXECUTED-HOLD-STORAGE-RESTART` — durable storage, signal, checkpoint, or
  resume behavior cannot satisfy the frozen rule; or
- `EXECUTED-HOLD-RESOURCE-BOUND` — the test cannot complete within the 1
  GPU-hour package ceiling.

A hold preserves its evidence and names the smallest corrective decision. It
does not automatically authorize a suffixed rescue package.

## Artifacts

- `artifacts/preflight.md` — sanitized read-only evidence available at
  scaffolding time.
- `artifacts/README.md` — planned artifact registry and naming contract.
- `kickoff-prompt.md` — execution dispatch template with branch/push rules.
- Planned execution evidence: dispatch/design freeze, live inventory,
  environment lock and asset manifest, CUDA/PyTorch/NCCL/signal sources and
  Slurm scripts, raw sanitized logs, `sacct`/`scontrol` receipts, attempt and
  resource ledgers, checkpoint hashes, cleanup receipt, independent review,
  gate results, terminal, and A10M3 handoff.
