# A10M5R2 — Corrected CPU Export Development Screen Retry

Status: `SCAFFOLDED`
Date: 2026-07-18
Evidence mode: Development-only fit-validation screen
Starting branch and push target: `main` at A10M5R1 completion, push `main`

## Objective

Retry the frozen A10M5 development screen under a new package identity with
the A10M5R1 clean-process CPU memory recipe, producing zero or more valid N0
and N1 promotions without changing any scientific or deployment threshold.

## Authority and boundary

A10M3's model/generation/benchmark contract, A10M5's twelve-configuration
grid and seed 147031, A10M5R1's terminal and process-accounting remedy, and
canonical Lemhi v2 are normative. A10M5R2 may read candidate-fit and
fit-validation roles only. Development-selection and confirmation roles
remain sealed. A10M5 evidence is immutable and may be used only as an exact
identity predecessor.

## Frozen correction

For each configuration, training must finish and the immutable CPU export
must be persisted before the high-RSS trainer exits. A small shell supervisor
then directly launches the CPU export worker. The worker records its own
`/proc/self/status` `VmHWM` and `VmRSS`; external `/usr/bin/time -v` provides
an independent maximum. `ru_maxrss` from a child forked by the live trainer is
prohibited as gate evidence.

All prior model, generation, checkpoint, 250 MiB export, 2 GiB RSS, 15-second
cold-load, 10/30-second warm, benchmark dispersion, and 5x/10x ratio gates
remain unchanged. Candidate streams must reproduce their A10M5 predecessor
identities exactly or fail closed.

## Execution shape

- twelve seed-147031 jobs, sequential on node03;
- one typed L40, eight CPUs, 64 GiB, and at most 30 minutes per row;
- one five-minute exact-node recovery reserve;
- one immutable staged closure reused across rows;
- no retry or resource expansion without a prospective package amendment.

## Exit

Emit `A10M5R2-PROMOTIONS-READY` only when every lifecycle/package gate passes
and at least one N0 and one N1 row are valid. Otherwise emit
`HOLD-A10-NO-VALID-NEURAL-FIT` with the exact surviving gate failures. A10M6
is not authorized by scaffolding.
