# A10M5R1 — Canonical CPU Export Memory Remedy

Status: `EXECUTED-COMPLETE`
Date: 2026-07-18
Evidence mode: Development-only operational diagnostic
Starting branch and push target: `main` at `d5f63e8`, push `main`

## Objective

Attribute the canonical Python 3.11/PyTorch CPU-export RSS floor observed by
all twelve A10M5 rows and identify the least complex deterministic deployment
surface that stays at or below the unchanged 2 GiB safeguard without reading
development or confirmation targets.

## Authority and boundary

A10M5 terminal `HOLD-A10-NO-VALID-NEURAL-FIT`, its R7 evidence, A10M3's model
and benchmark contracts, and canonical Lemhi v2 are normative. This package
may inspect framework/runtime behavior and run bounded synthetic or
candidate-fit-only diagnostics. It may not relax the RSS threshold, change
promotion results, open protected roles, or relabel any A10M5 row valid.

## Frozen investigation

1. Reproduce a representative 365-day state-carrying export with synthetic
   inputs and report RSS after import, load, first inference, steady inference,
   and teardown on one pinned core.
2. Separate mapped library pages, allocator arenas, thread stacks, model
   tensors, recurrent workspace, and output buffers using `/usr/bin/time -v`,
   `/proc/self/status`, and `/proc/self/smaps_rollup` where available.
3. Test only output-preserving controls first: eager versus TorchScript,
   inference mode, explicit thread pools, bounded chunks, backend enablement,
   allocator release, and a minimal non-Python loader if already supported by
   the frozen dependency closure.
4. For any apparent remedy, prove exact deterministic output identity against
   one retained/generated reference stream, export size, cold load, one-core
   RSS, and the 5x/10x benchmark contract.
5. Emit either `A10M5R1-EXPORT-REMEDY-READY` with one exact runtime recipe or
   `HOLD-A10-CPU-EXPORT-MEMORY` with attribution and the smallest material
   architecture/runtime decision required.

## Resource ceiling

At most four diagnostic one-L40 allocations of 30 minutes each plus one
five-minute exact-node recovery reserve. CPU-only diagnostics should use the
login node only for non-intensive inspection; measured inference runs belong
inside Slurm. Jobs are sequential because node03 cannot hold two canonical
isolated environments in `/tmp`.

## Gates

- prospective scripts, hypotheses, metrics, and stop rules are committed and
  pushed before allocation;
- all diagnostics use one pinned CPU core and explicit framework/BLAS thread
  counts;
- no protected-role bytes are opened and no fit-validation score is used to
  choose a runtime;
- raw and sanitized evidence, requested/actual accounting, job-local absence,
  exact remote cleanup, and toolkit close reconcile;
- a remedy must remain at or below 2 GiB and preserve exact output identity;
- repository Python, toolkit, formatting, clippy, and test gates pass.

## Exit and handoff

A remedy does not reopen or edit A10M5. It authorizes a new, independently
identified development screen retry package. Without a remedy, A10M6 remains
blocked and the operator must choose whether to change the deployment contract
or model/runtime family.

## Execution result

Terminal: `A10M5R1-EXPORT-REMEDY-READY`.

The 3.09--3.13 GiB A10M5 value was a measurement artifact, not the resident
set of the export runtime. Linux `ru_maxrss` in the exec'd child retained the
large training parent's high-water mark. A direct Lemhi control reproduced
that behavior: a child with 8,876 KiB `VmHWM` reported 530,000 KiB
`ru_maxrss` after exec from a 512 MiB parent.

Fresh shell-launched eager and TorchScript workers measured 628--635 MB by
`/usr/bin/time -v`; steady `/proc` RSS was 521--525 MB. R4 then regenerated
the exact retained N0-l32-w128-d2-lognormal candidate, reproduced all twelve
stream hashes, passed benchmark dispersion and all runtime ratios with a
3.8199 maximum, loaded cold in 1.206 seconds, and closed canonical toolkit v2
with exact remote cleanup. Its 3,321,282,560-byte `ru_maxrss` was deliberately
retained as the contaminated control.

The canonical remedy is to launch CPU export from a small supervisor after
the training process exits and measure that new process with `/proc/self/status`
`VmHWM` and external `/usr/bin/time -v`. A Python `subprocess` launched while
the high-RSS trainer remains alive is prohibited as a peak-RSS gate. No model,
dependency, threshold, or output changed. A10M5 remains immutable; A10M5R2 is
the independently identified development screen retry.
