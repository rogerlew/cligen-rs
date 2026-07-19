# A10M5O2 — Canonical Multi-L40 Qualification

Status: `SCAFFOLDED`
Date: 2026-07-19
Evidence mode: Ran
ExecPlan: [`../../exec-plans/20260719-a10-multi-l40-qualification.md`](../../exec-plans/20260719-a10-multi-l40-qualification.md)

## Objective

Qualify the exact canonical CPython 3.11/PyTorch stack for safe single-node
two- and four-L40 operation through the hardened toolkit, including collective
and DDP correctness, controlled peer failure, bounded scaling evidence,
resource accounting, and exact cleanup.

## Scope

Included are one-, two-, and four-L40 sequential roles on node03, a two-L40
controlled rank failure, immediate pre-submit occupancy snapshots, one exact-
node one-L40 recovery reserve, canonical identity gates, sanitized evidence,
guide/spec updates, and complete toolkit/Slurm/ledger reconciliation. Excluded
are cross-node work, node04 A6000s, heterogeneous devices, automatic retry,
requeue, protected scientific data, candidate training, confirmation evidence,
A10M6 authorization, or canonical-default replacement.

## Authority

The operator's 2026-07-19 instruction authorizes this package after the
published A10M5O1 prerequisite. The cumulative authority ceiling is 90
requested L40 GPU-minutes: one-GPU baseline 8, two-GPU qualification 20,
four-GPU qualification 48, two-GPU controlled failure 6, and exact-node
recovery reserve 5. Three minutes are not spendable by the frozen matrix.
Agents have authoring and execution authority for the exact package assets,
private authority/plan, registered jobs, evidence, and marked cleanup roots.
They may not answer MFA, displace work intentionally, broaden the matrix, or
operate on an unregistered path or job.

## Plan

1. Consume the published A10M5O1 implementation and freeze exact canonical
   assets, rank program, wrappers, plan, authority, and evidence rules.
2. Verify warm SSH masters and capture all-partition node03 occupancy before
   every multi-GPU submission; stop unless requested capacity is idle.
3. Run and settle one-, two-, and four-GPU correctness/scaling roles
   sequentially, stopping on any operational failure.
4. Run the expected two-rank failure, prove peer teardown, and settle its
   authenticated nonzero receipt.
5. Collect, sanitize, verify, clean, close, reconcile, classify scaling, update
   documentation, and publish the terminal record.

## Execution and dispatch

Execute in `/Users/roger/src/cligen-rs` on `rmm`, from the published A10M5O1
`main` commit and push only `main`. VPN and warm `login-ui`/`lemhi` SSH masters
are operator prerequisites. All toolkit operations use `BatchMode=yes`; an
expired master stops without interactive fallback. No role is retried.

## Gates

- exact canonical configuration ID/hash, CPython 3.11.15, NumPy 2.2.6,
  PyTorch 2.7.1+cu128, CUDA runtime, and L40 identity;
- exact requested world size, one process per unique L40, one hostname, and no
  cross-node or heterogeneous device;
- correct NCCL broadcast/barrier/all-reduce and synchronized DDP parameters;
- rank-zero checkpoint/reload and bounded three-repeat strong/weak scaling;
- controlled rank-one exit terminates peers and is authenticated as expected;
- plan GRES counts, requested/actual ledger charges, Slurm IDs, and elapsed
  accounting reconcile;
- no intentional preemption, no protected data access, exact durable and
  job-local absence, sanitized evidence, and toolkit close;
- package verifiers, toolkit tests, shell syntax, `git diff --check`,
  `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, and
  `cargo test` pass.

Coverage/CRAP is not triggered because this package changes no production
function under `crates/`.

## Exit criteria

`A10M5O2-MULTI-L40-OPS-READY` requires all operational gates. Performance is
separate: two GPUs are recommended at at least 1.6x fixed-work speedup; four
are recommended only when their incremental speedup over two is at least 1.4x.
Subthreshold scaling yields a single- or two-GPU preference without negating
operational readiness. Authentication, capacity, topology, NCCL, accounting,
evidence, or cleanup failures produce exact holds.

## Artifacts

- `artifacts/jobs/` — immutable rank program, wrappers, and asset preparation;
- `artifacts/live/` — sanitized receipts and scheduler/ledger summaries;
- `artifacts/admission/` — timestamped all-partition occupancy snapshots;
- `artifacts/scaling-summary.json` — one/two/four-GPU comparison;
- `artifacts/gate-results.md` and `execution-disposition.md` — terminal record;
- `artifacts/verify_freeze.py` and `verify_result.py` — deterministic gates.
