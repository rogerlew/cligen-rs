# A10M5O2D1 — L40 Interconnect Diagnostic

Status: `SCAFFOLDED`
Date: 2026-07-19
Evidence mode: Mixed
ExecPlan: [`../../exec-plans/20260719-a10-multi-l40-qualification.md`](../../exec-plans/20260719-a10-multi-l40-qualification.md)

## Objective

Explain the A10M5O2 four-GPU throughput collapse by measuring node03's exact
GPU/PCIe/NUMA topology, peer-access matrix, every two-GPU pair, the four-GPU
collective, and a host-staging control under the canonical Python/PyTorch
environment.

## Frozen hypothesis

The slowdown is caused primarily by an unfavorable intra-node PCIe path or
peer-to-peer fallback, not an external cluster network. If true, pairwise
all-reduce bandwidth will cluster by topology class and/or disabling NCCL P2P
will resemble or worsen the slow paths. If every pair is similar and the
four-GPU default remains uniquely poor, collective selection or four-way
contention is the stronger explanation.

## Authority and scope

The operator's 2026-07-19 instruction authorizes one fresh four-L40 diagnostic
allocation after the completed A10M5O2 package. Agents have authoring and
execution authority for package-owned sources, a new private authority/ledger,
the exact job, evidence, cleanup, guide/spec updates, and `main` publication.
The ceiling is 45 requested GPU-minutes: one four-L40 ten-minute role plus an
exact-node one-L40 five-minute recovery reserve. No retry is authorized.

Excluded are cross-node tests, scientific models or data, node04, persistent
services, requeue, topology reconfiguration, NCCL tuning as a production
default, canonical designation changes, A10M6, or intentional preemption.

## Plan and gates

1. Freeze one canonical offline job and publish its exact source.
2. Require node03 to have no allocation immediately before submission.
3. Record `nvidia-smi topo -m`, P2P read/write matrices, GPU PCI identities,
   and canonical environment identities.
4. Benchmark all six GPU pairs and the four-GPU group at 1, 16, and 128 MiB,
   both with default NCCL transport and `NCCL_P2P_DISABLE=1`.
5. Authenticate positive bandwidth, collective correctness, exact ranks and
   L40s, accounting, sanitized collection, and exact cleanup.
6. Disposition the physical-path hypothesis without promoting a tuning default.

The success terminal is `A10M5O2D1-L40-INTERCONNECT-CHARACTERIZED`. Missing or
ambiguous topology, failed collectives, accounting drift, evidence failure, or
cleanup failure produces an exact hold.

## Artifacts

- `artifacts/jobs/` — immutable benchmark, merger, wrapper, and control builders;
- `artifacts/admission.txt` — immediate occupancy snapshot;
- `artifacts/live/` — sanitized topology, bandwidth, ledger, and receipt summary;
- `artifacts/analysis.md` — disposition of physical-path hypotheses;
- `artifacts/gate-results.md` and `execution-disposition.md` — terminal record;
- `artifacts/verify_freeze.py` and `verify_result.py` — deterministic gates.
