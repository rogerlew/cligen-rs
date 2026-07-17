# A10M4 — One-L40 Implementation Qualification

Status: `SCAFFOLDED`
Date: 2026-07-17
Evidence mode: Mixed
Starting branch and push target: clean `main` at `44ff4bb`, push `main`

## Objective

Qualify the smallest frozen A10M3 N0 neural state-space configuration on real
A10M1 fit data under the canonical Lemhi Python 3.11/L40 environment. Prove
role-safe loading and normalization, one finite training update, exact fresh-
process checkpoint/resume, stateless nested generation, portable CPU export,
paired faithful-Rust benchmark mechanics, telemetry, and exact cleanup without
creating or scoring a development candidate.

## Scope

Included:

- all 98 accepted A10M1 v2 transfer objects, verified before use;
- `candidate_fit` gradient input and separately observed `fit_validation`
  exclusion, using the accepted normalization statistics;
- frozen configuration `N0-l32-w128-d2-lognormal`, one L40, and two optimizer
  steps solely for restart equivalence;
- atomic checkpoint publication with model, optimizer, scheduler, scaler, RNG,
  sampler, and corpus cursor state;
- Random123 Philox 4x32-10 counter generation, one-year smoke, nested 30/100-
  year streams, order independence, support/calendar checks, and CPU export;
- offline release faithful-Rust construction from the exact source commit and
  vendored Cargo dependencies, followed by the frozen six-station benchmark as
  a qualification diagnostic;
- toolkit lifecycle receipts, resource accounting, sanitization, retrieval,
  and exact remote-root cleanup.

Excluded:

- architecture search, full epochs, hyperparameter promotion, climate scores,
  selector decisions, development target-series reads, confirmation access,
  multi-GPU work, public profiles, or faithful generator changes;
- network access on the compute node, automatic Python 3.8 fallback, cluster
  module/compiler inheritance, or performance claims from this qualification.

## Authority

- A10M3 terminal `A10M3-DESIGN-FROZEN`, its machine contracts, and its A10M4
  handoff are normative.
- Canonical runtime ID `lemhi-a10-py311-l40-v1` and semantic SHA-256
  `0b1115a6801259c62d9550c877a3c49a897319348ba1c2027be0d9c4f77c1179`
  are mandatory; Python 3.8 is legacy explicit-only.
- A10M1's accepted v2 normalized and offline-transfer manifests are the only
  corpus authority. Failed v1 Daymet identities are prohibited.
- The operator's dispatch authorizes one prospective toolkit run, remote
  staging, the bounded Slurm intent, evidence retrieval, and exact cleanup.

## Frozen execution

See `artifacts/design-freeze.md`. One attempt requests `gpu-icrews`,
`gpu:l40:1`, 8 CPUs, 65,536 MiB, and 120 minutes: 120 requested GPU-minutes
(2 GPU-hours), below M4's 40-hour ceiling. No retry is automatic. A harness-
only defect may receive a prospective amendment before another allocation,
provided the cumulative ledger remains at or below 40 GPU-hours.

## Plan

1. Author and locally validate the package, exact job, asset builder, schemas,
   and pass rules; commit and push the prospective source boundary.
2. Build content-addressed runtime, framework, corpus, Cargo/vendor, selected-
   parameter, and exact-source assets on `rmm`.
3. Run the toolkit doctor/probe/plan/prepare/stage/verify lifecycle against the
   warm MFA control path and submit exactly one bounded job.
4. Monitor to a settled scheduler/accounting state; collect only allowlisted
   evidence and logs, validate every gate, and account requested/actual use.
5. Clean the exact remote run, verify absence, close private toolkit state,
   reconcile roadmap/catalog, run repository gates, and publish the terminal.

## Gates

- all 98 objects and 223,799,545 aggregate bytes match the accepted transfer
  manifest before parsing;
- the loader observes both roles, sends only `candidate_fit` through the
  optimizer, keeps `fit_validation` diagnostic-only, and binds accepted
  candidate-fit-only normalization;
- the exact N0 architecture has latent 32, width 128, depth 2, lognormal tail,
  and no more than 50 million parameters;
- GPU loss and gradients are finite, parameters update, and exactly one L40 is
  visible;
- a fresh process restores the atomic checkpoint and its next loss and every
  parameter match the uninterrupted control exactly;
- Philox counter vectors pass, generation is order-independent, 30 years is
  the exact prefix of 100 years, Gregorian rows and physical supports pass,
  and no repair is applied;
- the CPU export reloads with the GPU hidden; the six-station, two-horizon,
  two-warmup, nine-alternating-sample benchmark completes against release
  faithful Rust with one physical core and retains raw timings;
- all M3 absolute resource/export safeguards are evaluated as qualification
  diagnostics, not candidate selection or runtime classification;
- structured evidence authenticates every gate, resource use remains within
  the ledger, no protected target is accessed, and exact remote cleanup passes;
- Python and shell sources parse; toolkit tests, `git diff --check`,
  `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, and
  `cargo test` pass. Coverage/CRAP is not triggered because production Rust is
  unchanged.

## Exit criteria

`A10M4-QUALIFICATION-READY` requires every gate. Holds are
`HOLD-A10M4-LOADER`, `HOLD-A10M4-TRAINING`, `HOLD-A10M4-RESTART`,
`HOLD-A10M4-GENERATION`, `HOLD-A10M4-CPU-EXPORT`,
`HOLD-A10M4-RESOURCE`, or the exact toolkit environment/scheduler/cleanup
hold. A hold preserves evidence and does not authorize scored output.

## Artifacts

- `artifacts/design-freeze.md` — exact prospective execution contract;
- `artifacts/environment/build-assets.py` — private asset constructor;
- `artifacts/jobs/qualify.py`, `qualify.sh`, and `evidence.schema.json` — exact
  compute implementation and fail-closed receipt;
- `artifacts/toolkit/`, `execution.md`, `resource-ledger.md`, `review.md`,
  `gate-results.md`, `terminal.md`, and `a10m5-handoff.md` — populated only
  after execution.
