# Lemhi single-node multi-L40 capability

Status: authoritative (revision 2; A10M5O1/A10M5O2/A10M5O2D1)

## Surface

This specification defines an optional single-node, homogeneous multi-L40
capability for the Lemhi agent toolkit. It reuses the exact current canonical
runtime and framework assets without replacing the single-L40 default. This
additive capability does not change the default.

## Producers and consumers

A10M5O1 produces fail-closed toolkit semantics for typed GRES and accounting.
A10M5O2 produces the live capability attestation. Later explicitly authorized
work packages may consume the attested counts. Ordinary canonical consumers
continue to request one typed L40.

## Authority basis

`SPEC-LEMHI-AGENT-TOOLKIT` revision 2 governs lifecycle, authority, evidence,
ledger, and cleanup. `SPEC-LEMHI-CANONICAL-CONFIGURATION` revision 2 governs
the exact runtime assets and immutable designation boundary. The operator's
2026-07-19 dispatch authorizes the bounded qualification but not A10M6 or
scientific promotion.

## Semantics

A multi-L40 job is one Slurm allocation on node03, requested through
`gpu-icrews` with typed GRES `gpu:l40:N`, where `N` is two or four. The plan's
positive integer `gpus` must equal the parsed GRES count. One is retained as
the canonical baseline. Counts above four, generic GPU requests, other models,
multiple nodes, node04, and mixed devices fail before remote mutation.

One PyTorch process binds to each Slurm-visible GPU. A passing capability
requires exact canonical software identity, unique Slurm-visible L40 bindings,
one hostname, NCCL collective correctness, synchronized DDP state, checkpoint reload,
bounded rank-failure teardown, exact GPU-second/minute accounting, authenticated
evidence, and cleanup. Scaling results are advisory and separate from
operational correctness.

The revision-1 attestation is `A10M5O2-MULTI-L40-OPS-READY`, plan
`f6b9f4f6bd4ca4f92dd314365e2467a4dc27cf094b3b35b5f6962317770f4a86`,
from jobs `1014018`–`1014021`. Counts one, two, and four passed. The measured
microbenchmark classification is `SINGLE-GPU-PREFERRED`; multi-GPU consumers
must justify workload-specific scaling and may not infer speedup from this
operational attestation.

The revision-2 transport characterization is
`A10M5O2D1-L40-INTERCONNECT-CHARACTERIZED`, plan
`fb21c78ee7e5611f16187f3c28d53e48fdcac4d56155535ac4f116467e039413`,
from job `1014026`. All six two-L40 groups had complete driver and PyTorch peer
access and used NCCL `P2P/CUMEM`. At 128 MiB, pairs 0–1 and 2–3 reached
20.117 and 20.067 GB/s bus bandwidth; other pairs reached 14.488–14.619 GB/s.
The four-L40 group instead selected `SHM/direct/direct` with
`intraNodeP2pSupport 0` and reached 1.148 GB/s, effectively matching the
explicit P2P-disabled control at 1.155 GB/s.

Consequently, a hardware P2P matrix is necessary but insufficient evidence
for a multi-rank performance claim. The consumer must verify NCCL's actual
channel transport at the intended rank count. Two-GPU execution remains
optional and workload-qualified. Four-GPU operational correctness remains
attested, but four-GPU performance use is held until a later bounded package
proves a supported direct-transport remedy. No undocumented NCCL override may
become a provider or toolkit default on the strength of diagnostic evidence.

Before a multi-GPU submission, the executor records `squeue -a` occupancy for
node03 and stops unless enough requested L40 capacity is idle. A four-GPU role
requires no existing node03 allocation. This is a best-effort non-preemption
admission snapshot, not an atomic scheduler reservation.

## Provenance obligations

The attestation binds source commit, package and run IDs, canonical
configuration ID and semantic hash, provider hashes, Slurm job IDs, requested
GRES, parsed count, node, per-rank visible-device bindings, runtime versions,
gate receipt hashes, requested and actual GPU-minutes, admission snapshots, collection/cleanup
receipts, and terminal disposition. Raw private paths and user-identifying
cluster data are sanitized before publication.

## Excluded claims

Passing does not establish multi-node communication, heterogeneous execution,
universal speedup, the administrative cause of NCCL's four-rank P2P decision,
scientific model validity, production durability, requeue, administrator
support, or a new canonical default.
