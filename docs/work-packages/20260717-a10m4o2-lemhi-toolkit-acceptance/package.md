# A10M4O2 — Lemhi Toolkit Operational Acceptance

Status: `SCAFFOLDED`
Date: 2026-07-17
Evidence mode: Mixed
Scaffold start: clean `main` at `1984380`
Execution start and push target: current published `main`, push `main`

## Objective

Accept or hold the hardened Lemhi toolkit for A10M5 by exercising the
remaining lifecycle edges on the real `rmm` → MFA-bootstrap → Lemhi path:
pre-submission abort, executable-mode rejection, revised elapsed GPU
accounting, authenticated terminal failure evidence, first-class exact-node
recovery, evidence collection, and complete cleanup/reconciliation.

## Scope

Included:

- one tiny live staged-and-aborted run with no Slurm allocation;
- one deterministic local adverse fixture proving a required executable mode
  is rejected before staging or submission;
- one successful one-L40 job of at most two requested minutes that validates
  L40 visibility and the seconds plus ceiling-rounded minutes accounting path;
- one intentionally failing one-L40 job of at most two requested minutes that
  writes an authenticated failure gate and a marked job-local recovery target;
- one exact-node one-L40 recovery allocation of at most two requested minutes,
  drawn from the prospectively reserved contingency;
- toolkit/spec/guide corrections strictly required by those acceptance tests;
- final scheduler/ledger/root reconciliation, evidence verification,
  roadmap/catalog updates, repository gates, commit, and push.

Excluded:

- A10M5 model work, development or confirmation target access, training,
  scoring, performance classification, and the frozen 5x/10x decision;
- more than 10 requested L40 GPU-minutes, more than one GPU per job, retries,
  concurrency, multi-node work, or non-L40 fallback;
- credential storage, MFA automation, cold SSH fallback, direct compute-node
  SSH, administrator changes, and destructive cleanup outside exact markers;
- canonical environment redesign or retransferring the 4.6 GB framework stack.

## Authority

- `SPEC-LEMHI-AGENT-TOOLKIT` revision-2 lifecycle and the current canonical-v2
  designation are normative.
- The operator explicitly authorizes A10M4O2 execution, repository authoring,
  remote staging under the registered Ceph roots, up to 10 requested L40
  GPU-minutes on `gpu-icrews`, exact cleanup, commit, and push to `main`.
- Agents have authoring authority for package-owned authority, plan, job,
  fixture, evidence, and toolkit files within this frozen scope. They may not
  answer MFA prompts, broaden resource or data authority, or operate on an
  unregistered path/job.

## Plan

1. Freeze the two-run authority lineage and acceptance matrix; add the missing
   first-class recovery submit/observe seam and deterministic fixtures.
2. Run Python/unit/shell/scaffold gates, commit, and push the exact source
   lineage before any live authority references it.
3. Verify both warm SSH masters, initialize the private 10-GPU-minute ledger,
   stage the abort run, prove exact abort cleanup, and derive the allocation
   run without resetting the ledger.
4. Stage and verify tiny assets; run success and controlled-failure jobs;
   settle both, then submit and settle the reserved exact-node recovery.
5. Collect allowlisted evidence, prove durable and job-local absence, close,
   reconcile Slurm jobs and the ledger, and classify toolkit acceptance.
6. Run all package/repository gates, update roadmap/catalog/guide, commit, and
   push the terminal record.

## Execution and dispatch

Execute in `/Users/roger/src/cligen-rs` on `rmm`, starting from current
`origin/main` and pushing only `main`. The operator supplies VPN and warm MFA
SSH masters. Toolkit commands use `BatchMode=yes`; expired masters stop as
`AUTH_BOOTSTRAP_REQUIRED`. Source must be committed and pushed before live
authority initialization.

The live allocation ceiling is 6 requested L40 GPU-minutes: success 2,
controlled failure 2, and reserved recovery 2. The package-level 10-minute
authority leaves four minutes unspendable by the frozen plan. No retry is
authorized. The abort run shares the authority ledger but requests no job.

## Gates

- abort creates no Slurm job and proves its exact marked Ceph root absent;
- executable-mode adverse fixture fails at `prepare` before remote mutation;
- success accounting contains exact `elapsed_seconds`, `actual_gpu_seconds`,
  and ceiling-rounded integer `actual_gpu_minutes`;
- controlled failure is `passed=false` while its registered gate receipt is
  still read and hashed;
- recovery is authority-reconciled, one-attempt, exact-node, marker/UID/device
  bound, settled, charged to its existing reserve, and proves absence;
- all authority-tagged Slurm IDs equal registered ledger IDs, queue is empty,
  and exact remote/job-local roots are absent at close;
- no protected development/confirmation data is read and no large canonical
  runtime/framework/toolchain asset is transferred;
- toolkit unit tests, shell syntax, package verifier, `git diff --check`,
  `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, and
  `cargo test` pass.

Coverage/CRAP is not triggered because this package changes no production
function under `crates/`.

## Exit criteria

`A10M4O2-LEMHI-TOOLKIT-ACCEPTED` requires every gate and supports controlled
A10M5 use. A hold records the exact failed lifecycle edge and preserves private
recovery state where cleanup is not proved. Named holds are
`HOLD-A10M4O2-AUTH-BOOTSTRAP`, `HOLD-A10M4O2-ACCOUNTING`,
`HOLD-A10M4O2-FAILURE-RECEIPT`, `HOLD-A10M4O2-RECOVERY`, and
`HOLD-A10M4O2-CLEANUP`.

## Artifacts

- `artifacts/jobs/` — tiny success and controlled-failure assets;
- `artifacts/fixture-results/` — local executable-mode rejection evidence;
- `artifacts/live/` — sanitized toolkit publications and scheduler/ledger
  summaries;
- `artifacts/execution.md`, `gate-results.md`, and `terminal.md` — populated
  during execution; and
- `artifacts/verify-acceptance.py` — closed evidence verifier.
