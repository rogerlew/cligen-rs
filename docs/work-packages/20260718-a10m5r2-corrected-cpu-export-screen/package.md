# A10M5R2 — Corrected CPU Export Development Screen Retry

Status: `SCAFFOLDED`
Date: 2026-07-18
Evidence mode: Development-only fit-validation screen
Starting branch and push target: clean `main` at `387d14c`, push `main`

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

## Plan

1. Publish and locally verify the exact trainer/worker/finalizer split,
   predecessor-identity manifest construction, twelve wrappers, aggregation,
   and terminal verifier before allocation.
2. Commit and push that prospective boundary to `main`, then create one
   toolkit-v2 authority at the frozen 365-GPU-minute ceiling.
3. Reuse the hash-pinned canonical asset cache, stage one immutable remote run,
   and execute the twelve single-attempt rows sequentially.
4. Collect only allowlisted evidence, apply the frozen promotion ordering,
   reconcile requested and actual accounting, prove job-local and durable
   cleanup, and close the toolkit authority.
5. Publish the honest terminal, roadmap/catalog transition, full gates, and
   A10M5R3 handoff.

## Gates

- the byte-identical A10M5 trainer core, grid, seed, corpus, roles, schedule,
  fit diagnostics, and predecessor streams remain frozen;
- every trainer exits before its fresh one-core worker starts;
- both worker `VmHWM` and external `/usr/bin/time -v` maximum are at or below
  2 GiB, with `VmRSS`, cold load, export bytes, and warm timing reported;
- all prior support, prefix, order, checkpoint, parameter, dispersion,
  absolute-runtime, and 5x/10x gates pass unchanged;
- all twelve rows run once, no protected role is read, and promotion uses the
  frozen five-key fit-validation ordering only;
- toolkit receipts, accounting, evidence, exact cleanup, and close reconcile;
  and
- Python/shell parse, `git diff --check`, `cargo fmt --check`,
  `cargo clippy --all-targets -- -D warnings`, and `cargo test` pass.
