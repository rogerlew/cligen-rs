# A10 canonical multi-L40 toolkit qualification ExecPlan

This ExecPlan is a living document maintained according to `.agent/PLANS.md`.
It governs two work packages without merging their authority or evidence:
`docs/work-packages/20260719-a10m5o1-multi-l40-toolkit-hardening/` and
`docs/work-packages/20260719-a10m5o2-canonical-multi-l40-qualification/`.

## Purpose / Big Picture

After this work, an authorized agent can request two or four homogeneous L40
GPUs on one Lemhi node without letting the toolkit's declared GPU count diverge
from the Slurm GRES request or resource ledger. An operator can run an exact
canonical Python/PyTorch qualification, observe correct NCCL collectives and
distributed gradient synchronization, see bounded 1/2/4-GPU scaling evidence,
and distinguish operational readiness from whether a workload scales well.

The existing single-L40 canonical designation remains the default. The result
is an optional, package-attested capability and does not authorize A10M6,
cross-node execution, heterogeneous node03/node04 work, or scientific model
promotion.

## Progress

- [x] (2026-07-19 07:20Z) Reconciled clean `main` at `a574317`, current A10
  holds, existing toolkit semantics, and the official ExecPlan guidance.
- [x] (2026-07-19 07:30Z) Fixed the two-package boundary, single-node scope,
  sequential live matrix, and 90 requested GPU-minute authority ceiling.
- [x] (2026-07-19 08:05Z) Scaffolded both packages, the capability
  specification, package verifiers, and the repository ExecPlan convention.
- [x] (2026-07-19 08:25Z) Implemented exact typed-GRES/count/accounting
  invariants; 55 toolkit tests and all repository gates pass.
- [x] (2026-07-19 08:34Z) Published the first live-source freeze as `5f2907d`;
  authority initialization then failed closed on an invalid predecessor claim.
- [x] (2026-07-19 08:27Z) Published corrected live source `0caae8e`, initialized
  the 90-minute authority, and froze exact canonical assets and plan.
- [x] (2026-07-19 08:39Z) Executed and settled jobs `1014018`–`1014021`; all
  success gates and the bounded expected-failure gates passed.
- [x] (2026-07-19 08:47Z) Diagnosed fail-closed collection on PyTorch's raw
  `<NO_OTHER_FAILURES>` placeholder and completed corrective local successor
  A10M5O1R1 with 56 toolkit tests and all repository gates passing.
- [x] (2026-07-19 08:49Z) Reprojected 15 unchanged raw files, released recovery,
  removed the exact remote root, closed the toolkit run, and reconciled all
  four Slurm identities plus 650 actual GPU-seconds.
- [x] (2026-07-19 08:55Z) Closed all package/specification/guide/roadmap/catalog
  records; 56 toolkit tests, all package verifiers, shell syntax, and every
  repository gate pass.

## Surprises & Discoveries

- Observation: the toolkit accepts `gpus` and typed `gres` independently, but
  accounting multiplies elapsed time by `gpus` while Slurm reserves `gres`.
  Evidence: `research/a10/lemhi_toolkit/core.py` validates both fields without
  comparing them; `adapters.py` submits `job["gres"]` and accounts with
  `job["gpus"]`.
- Observation: legacy A10M2 already proved two-L40 NCCL/DDP under Python 3.8,
  so this campaign must qualify the current CPython 3.11/PyTorch 2.7.1+cu128
  configuration and toolkit semantics rather than restating hardware
  feasibility.
- Observation: `gpu-icrews` has priority tier 20 with `CANCEL` preemption over
  tier-10 `gpu-volatile`; an idle-capacity snapshot is therefore required
  immediately before multi-GPU submission to avoid intentionally displacing
  lower-priority work.
- Observation: resource-ledger genesis rejects any predecessor or scheduler
  evidence because genesis is the start of that evidence chain. The generated
  authority input incorrectly copied the package dependency terminal into
  `predecessor_evidence`, and initialization returned `AUTHORITY_INVALID`
  before creating a ledger or consuming capacity.
- Observation: PyTorch `torchrun` prints `<NO_OTHER_FAILURES>` in its expected
  failure traceback. This is diagnostic syntax, but projection revision 3
  treated every raw angle token as an attempted toolkit-token injection and
  held collection after the matrix settled.
- Observation: the adapter's collection policy label was independently
  hard-coded to projection revision 3 while the cryptographic transformation
  receipts correctly reported revision 4. Binding that label to the projector
  constant prevents future receipt drift.

## Decision Log

- Decision: use `A10M5O1` for local toolkit hardening and `A10M5O2` for live
  qualification. Rationale: code semantics must be published before a live
  authority can cite them, while the live result deserves independent evidence
  and may honestly hold without reopening implementation scope. Date/Author:
  2026-07-19, Codex under operator dispatch.
- Decision: retain the current single-L40 canonical designation and publish an
  additive multi-L40 capability attestation. Rationale: changing the default
  GRES would invalidate existing immutable semantics and silently broaden all
  A10 consumers. Date/Author: 2026-07-19, Codex.
- Decision: limit execution to one node and counts 1, 2, and 4 on node03.
  Rationale: node03 is the only homogeneous four-L40 node; node04 contains RTX
  A6000 devices and cross-node work would add networking and heterogeneous
  behavior. Date/Author: 2026-07-19, Codex.
- Decision: cap authority at 90 requested GPU-minutes. Rationale: four
  sequential roles reserve 82 minutes and exact-node recovery reserves five;
  the remaining three minutes cannot be spent by the frozen plan. Date/Author:
  2026-07-19, Codex.
- Decision: keep `A10M5O1-MULTI-L40-TOOLKIT-READY` in the package/ExecPlan
  dependency record, but generate empty genesis evidence arrays. Rationale:
  package provenance and an append-only resource ledger are distinct chains;
  only the latter is constrained by ledger genesis. Date/Author: 2026-07-19,
  Codex.
- Decision: repair projection locally instead of mutating raw evidence,
  widening the frozen plan, or resubmitting a job. Raw reserved-looking tokens
  are escaped and counted before authorized replacements, retaining their
  meaning while preventing token spoofing. Rationale: all scheduler/gate
  evidence is already terminal and authentic; the defect is solely in the
  publication layer. Date/Author: 2026-07-19, Codex.

## Outcomes & Retrospective

A10M5O1 reached `A10M5O1-MULTI-L40-TOOLKIT-READY`. A previously possible
four-device reservation charged as one now fails during plan validation. The
default provider remains one-device-only and a new additive provider owns the
bounded one/two/four-device contract. Live A10M5O2 reached
`A10M5O2-MULTI-L40-OPS-READY`. Jobs `1014018`–`1014021` passed
one/two/four-L40 correctness and controlled-failure gates, used 650 actual
GPU-seconds (14 per-job-rounded GPU-minutes), released the unused five-minute
recovery reserve, and closed with durable/job-local absence.
A10M5O1R1 also reached `A10M5O1R1-EVIDENCE-PROJECTION-READY` without another
allocation. It preserves raw third-party placeholders as explicit escaped text
and lets only registered rules introduce toolkit projection tokens. The
performance classification is `SINGLE-GPU-PREFERRED`: fixed-global two/one
speedup was 0.3999x and incremental four/two speedup was 0.0462x, well below
the advisory 1.6x and 1.4x thresholds.

## Context and Orientation

`research/a10/lemhi_toolkit/` is the dependency-free macOS control plane. Its
`core.py` validates plans and owns the append-only resource ledger;
`adapters.py` renders Slurm submissions and derives actual GPU-minutes from
Slurm elapsed seconds. `remote/submit_v2.sh` sends the typed GRES request to
Slurm. `docs/specifications/SPEC-LEMHI-AGENT-TOOLKIT.md` is the authoritative
lifecycle contract, while
`docs/specifications/SPEC-LEMHI-CANONICAL-CONFIGURATION.md` keeps the current
single-L40 runtime designation immutable.

The live control host is `rmm`, an Apple M1 Mac mini running macOS. Lemhi is
reachable only through the University of Idaho VPN and warm MFA-authenticated
SSH masters named `login-ui` and `lemhi`. Compute nodes have no internet. The
canonical runtime, wheelhouse, requirements lock, and job assets must be staged
from hash-verified local files. A GRES is Slurm's typed accelerator request;
`gpu:l40:4` means four L40 GPUs on one node. NCCL is NVIDIA's collective
communication library used by PyTorch distributed jobs.

## Plan of Work

Milestone one creates the two package records and hardens the toolkit. Add one
typed-GRES parser in `research/a10/lemhi_toolkit/core.py`; use it for primary
and recovery jobs; require resource `gpu`, model `l40`, count equality with the
integer `gpus` field, and a provider-declared maximum of four. Extend unit and
fixture tests to prove mismatches fail before remote mutation and 2/4-GPU
charges use the declared count. Amend the toolkit specification and README.
The observable result is a previously accepted mismatch failing with
`PLAN_DRIFT` while valid multi-GPU fixture plans pass and account correctly.

Milestone two freezes and publishes live assets. Add a small canonical
PyTorch program and Slurm wrappers beneath the A10M5O2 package. The success
program records rank/world size, hostname, unique visible-device bindings,
exact runtime versions, NCCL all-reduce results, one deterministic DDP update, checkpoint
reload, CUDA-event timings, throughput, and per-rank memory. It runs warmup and
three measurements for fixed-global-work and fixed-per-GPU-work cases. A
separate role deliberately exits rank one and proves bounded peer teardown.
All roles use `torchrun --standalone`, typed GRES, no requeue, and one node.

Milestone three executes the live matrix sequentially: one-GPU baseline for
eight minutes, two-GPU qualification for ten, four-GPU qualification for
twelve, and two-GPU controlled failure for three. Immediately before each
multi-GPU submit, capture `squeue -a` and refuse submission unless sufficient
node03 L40 capacity is idle; the four-GPU role requires node03 to have no other
allocation. Observe and authenticate each terminal before continuing. The
single recovery reserve is one L40 for five minutes on the exact original node
and is invoked only for unresolved toolkit-owned job-local cleanup.

Milestone four collects and sanitizes evidence, proves durable and job-local
roots absent, reconciles all authority-tagged Slurm IDs and the ledger, computes
1/2/4 speedups, and issues separate operational and performance dispositions.
It then updates the guide, specs, roadmap, catalog, packages, and this plan.

## Concrete Steps

All local commands run from `/Users/roger/src/cligen-rs` on branch `main`.
The implementation sequence is:

    python3 -m unittest discover -s research/a10/lemhi_toolkit/tests -v
    for script in research/a10/lemhi_toolkit/remote/*.sh; do sh -n "$script" || exit; done
    python3 docs/work-packages/20260719-a10m5o1-multi-l40-toolkit-hardening/artifacts/verify.py
    python3 docs/work-packages/20260719-a10m5o2-canonical-multi-l40-qualification/artifacts/verify_freeze.py
    git diff --check
    cargo fmt --check
    cargo clippy --all-targets -- -D warnings
    cargo test

Before live work, commit and push the exact source, then confirm:

    ssh -O check login-ui
    ssh -O check lemhi
    ssh lemhi 'sinfo -a -N -p gpu-icrews,gpu-volatile -o "%N|%P|%t|%G"'
    ssh lemhi 'squeue -a -w node03 -o "%i|%u|%P|%T|%b"'

Private authority, plan, ledger, and raw collection paths live beneath
`/Users/roger/.cache/cligen-rs/a10m5o2-multi-l40/` with mode 0700 and are never
committed. Lifecycle commands use `python3 -m research.a10.lemhi_toolkit` with
the exact authority, `lemhi-v2.json`, repository provider root, and run ID.
The precise generated commands and sanitized receipts are added to the A10M5O2
execution artifact as they run.

## Validation and Acceptance

A10M5O1 completes when every mismatch fixture fails before remote mutation,
valid one/two/four-GPU plans pass, requested and elapsed charges use the same
count, and toolkit plus repository gates pass.

A10M5O2 operational readiness requires exact canonical hashes and versions;
exactly the requested unique L40 devices; one process per GPU; successful NCCL
broadcast, barrier, and all-reduce; synchronized DDP parameters; rank-zero
checkpoint reload; bounded controlled peer failure; correct GPU-second/minute
settlement; authenticated evidence; and exact cleanup. Scaling is classified
separately: recommend two GPUs only if median fixed-work speedup is at least
1.6x, and recommend four only if its incremental speedup over two is at least
1.4x. Failing these performance thresholds yields `SINGLE-GPU-PREFERRED` or
`TWO-GPU-PREFERRED`, not an operational hold.

## Idempotence and Recovery

Local generation and verification overwrite only package-owned generated
files and are repeatable. The live authority and ledger are initialized once.
After any ambiguous submission, reconcile the authority token and registered
job ID before retry; no automatic retry is authorized. Never reset or replace
the 90-minute budget. Invoke recovery only when authenticated primary evidence
identifies an unresolved marked job-local target. Cleanup validates exact
markers and paths; it never infers a target.

## Artifacts and Notes

A10M5O1 contains its design freeze, local gate transcript, tests, and terminal
disposition. A10M5O2 contains immutable job sources, an asset manifest,
admission snapshots, sanitized toolkit receipts, rank evidence, scaling
summary, ledger summary, cleanup proof, and terminal disposition. Raw toolkit
state and canonical archives stay in the private cache.

The ExecPlan format follows OpenAI's published guidance that plans be
self-contained living documents with mandatory progress, discoveries,
decisions, and retrospective sections.

## Interfaces and Dependencies

No new third-party control-host dependency is introduced. The live program uses
the already-pinned CPython 3.11.15, NumPy 2.2.6, PyTorch 2.7.1+cu128, CUDA 12.8
runtime contract, and NCCL bundled by that framework. The toolkit exposes a
single typed-GRES parser whose result supplies the validated resource, model,
and positive count. Job and recovery validation require that count to equal
their `gpus` field. The optional multi-L40 capability record binds counts two
and four to one homogeneous node03 allocation; it does not change the default
canonical designation.

Revision note (2026-07-19): initial self-contained plan created after repository,
toolkit, cluster-policy, and current A10 campaign reconnaissance.

Revision note (2026-07-19): recorded completion of local toolkit hardening and
the exact live role/resource freeze after all local and repository gates passed.

Revision note (2026-07-19): recorded the fail-closed genesis discovery and
corrected the authority-input generator before any live mutation.

Revision note (2026-07-19): recorded successful live matrix settlement and the
bounded projection-repair successor triggered by a PyTorch diagnostic token.

Revision note (2026-07-19): recorded authenticated collection, ledger release,
exact cleanup, operational readiness, and single-GPU performance preference.

Revision note (2026-07-19): execution complete; all milestones, artifacts,
acceptance gates, and retrospective outcomes are closed.
