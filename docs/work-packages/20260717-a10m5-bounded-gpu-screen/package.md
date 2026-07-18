# A10M5 — Bounded GPU Architecture and Pooling Screen

Status: `SCAFFOLDED`
Date: 2026-07-17
Evidence mode: Mixed
Starting branch and push target: clean `main` at `23f2e22`, push `main`

## Objective

Train every frozen A10M3 N0/N1 configuration once on the accepted A10M1 fit
surface, compare only fit-validation diagnostics, execute the normative CPU
generation benchmark, and emit at most two promotion identities per pooling
class for A10M6 without reading development or confirmation targets.

## Scope

Included:

- the exact 12-row A10M3 grid and training seed `147031`;
- `candidate_fit` gradients, candidate-fit-only normalization, complete
  eligible `fit_validation` diagnostics, and explicit missing-field masks;
- 730-day windows, 365-day overlap, 60-day warmup/loss mask, equal-regime
  sampling, frozen auxiliary losses, AdamW/bf16, early stopping, atomic rolling
  checkpoints, long unforced generation, and the frozen CPU benchmark;
- one independent one-L40 job per configuration, at most two concurrent jobs,
  toolkit v2 lifecycle evidence, bounded recovery, and exact cleanup;
- frozen ordering and at most two full-development promotions per pooling
  class.

Excluded:

- development or confirmation target bytes, A9 selector outcomes as training
  signal, three-seed finalist fitting, applicability adjudication, candidate
  sealing, public runtime changes, grid expansion, or threshold changes;
- reuse of A10M4 weights, checkpoints, exports, projected cost, or raw runtime
  ratios as candidate evidence;
- implicit Python 3.8/module fallback, direct-node SSH, ambient packages, or
  automatic retry after a failed scientific gate.

## Authority

- A10M3 terminal `A10M3-DESIGN-FROZEN`, its model/training/generation and
  selector/benchmark machine contracts, and the A10M4 handoff are normative.
- A10M1 v2 normalized and offline-transfer manifests are the only corpus
  authority. Intentional masked observations are omitted, never imputed.
- The current Lemhi operational designation is canonical v2, while immutable
  A10 model records retain the A10M3 v1 configuration identity required by
  schema revision 1. `artifacts/design-freeze.md` records both identities.
- The operator dispatch authorizes prospective source publication, one
  development-only toolkit authority, twelve bounded Slurm allocations,
  evidence retrieval, and exact cleanup.

## Frozen execution

The implementation completion in `artifacts/design-freeze.md` is frozen before
fit output. Each job requests one L40, 8 CPUs, 65,536 MiB, and 120 minutes.
Twelve attempts request 1,440 GPU-minutes (24 GPU-hours) plus one five-minute
recovery reserve, below the 9,600-minute M5 screen ceiling. Exactly two jobs
may be live concurrently. `max_attempts=1`; a remedy requires a prospective
source amendment and an explicit new attempt within the unchanged ceiling.

## Plan

1. Freeze the implementation completion, exact jobs, schemas, promotion
   arithmetic, source/corpus/runtime identities, and verification gates.
2. Commit and push the prospective source boundary before creating authority
   or submitting work.
3. Build/reuse content-addressed canonical-v2 runtime, framework, corpus,
   Rust, faithful-source, vendor, and parameter assets on `rmm`.
4. Use the warm MFA-bootstrap control path and toolkit v2 to stage and verify
   one immutable run, then submit/observe the 12 jobs in pairs.
5. Collect allowlisted evidence, validate all fit/checkpoint/runtime records,
   apply the frozen promotion ordering locally, and account every allocation.
6. Prove job-local and durable-root cleanup, close authority, reconcile the
   roadmap/catalog, run repository gates, and publish the terminal.

## Gates

- the accepted 98 objects and 223,799,545 aggregate bytes verify before parse;
- all and only the 12 frozen configurations run once with seed `147031`;
- only `candidate_fit` affects fit state; `fit_validation` is gradient-free;
- every valid fit has finite proper validation score, tail score, stability,
  complete model/checkpoint manifests, no more than 50 million parameters,
  and a reproducible final checkpoint identity;
- training observes the frozen batch/precision/optimizer/checkpoint contract,
  hard support/generation invariants, and resource ceilings;
- each valid configuration completes the six-station, two-horizon normative
  CPU benchmark with raw samples, exact 5x/10x classification, and absolute
  safeguards; at least one promotable configuration remains below 10x;
- promotion uses only the frozen five-key fit-validation ordering and returns
  at most two identities per pooling class;
- no development/confirmation target is read, no M4 fitted state is reused,
  and no role/firewall violation occurs;
- toolkit receipts, scheduler accounting, requested/actual resource ledgers,
  job-local absence, exact durable-root cleanup, and close reconcile;
- Python/shell sources parse; research tests, `git diff --check`,
  `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, and
  `cargo test` pass. Coverage/CRAP is not triggered because production Rust is
  unchanged.

## Exit criteria

`A10M5-PROMOTIONS-READY` requires every package gate and at least one bounded
promotion. Holds are `HOLD-A10-NO-VALID-NEURAL-FIT`,
`HOLD-A10-GENERATION-RUNTIME`, `HOLD-A10-RESOURCE-BOUND`, or the exact toolkit
environment/scheduler/cleanup hold. A hold retains complete screen evidence
and does not authorize development access.

## Artifacts

- `artifacts/design-freeze.md` — prospective screen implementation contract;
- `artifacts/jobs/` — exact trainer, supervisor, evidence schema, and asset
  constructor;
- `artifacts/verify-a10m5.py` — fail-closed scaffold/result verifier;
- `artifacts/toolkit/`, `execution.md`, `resource-ledger.md`,
  `screen-results.json`, `promotion-trace.json`, and `terminal.md` — live
  evidence and disposition created during execution.
