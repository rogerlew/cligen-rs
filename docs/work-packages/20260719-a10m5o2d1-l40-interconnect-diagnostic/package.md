# A10M5O2D1 — L40 Interconnect Diagnostic

Status: `EXECUTED-COMPLETE`
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

## Result

Job `1014026` completed on node03 with four L40s and all 13 frozen gates
passing. Every hardware/driver peer-read and peer-write relation was `OK`, and
PyTorch reported peer access for every pair. Default two-rank NCCL used
`P2P/CUMEM`: the favored pairs 0–1 and 2–3 reached 20.117 and 20.067 GB/s at
128 MiB, while the other four pairs reached 14.488–14.619 GB/s. Their
P2P-disabled controls fell to 1.025–5.383 GB/s.

The four-rank default did not use those peer paths. NCCL reported
`intraNodeP2pSupport 0` and selected `SHM/direct/direct` for every ring edge.
It reached 1.148 GB/s bus bandwidth, effectively indistinguishable (0.6%
apart) from the explicit P2P-disabled control at 1.155 GB/s. NCCL
initialized the host's InfiniBand devices, but the actual same-node collective
channels were shared-memory paths; the collapse is not evidence of external
network traffic.

The frozen hypothesis is therefore refined: topology creates two pairwise
bandwidth classes, but the four-GPU cliff is caused by NCCL declining
intra-node P2P for the full four-rank group and falling back to host shared
memory. The exact administrative cause of that NCCL decision is not proved.
The package reaches `A10M5O2D1-L40-INTERCONNECT-CHARACTERIZED`. Continue to
prefer one GPU by default, use two only after workload-specific scaling, and
do not recommend four-GPU jobs until a separately authorized successor proves
a supported transport remedy.

## Artifacts

- `artifacts/jobs/` — immutable benchmark, merger, wrapper, and control builders;
- `artifacts/admission.txt` — immediate occupancy snapshot;
- `artifacts/live/` — sanitized topology, bandwidth, ledger, and receipt summary;
- `artifacts/analysis.md` — disposition of physical-path hypotheses;
- `artifacts/gate-results.md` and `execution-disposition.md` — terminal record;
- `artifacts/verify_freeze.py` and `verify_result.py` — deterministic gates.
