# Lemhi single-node multi-L40 capability

Status: proposed (revision 1; A10M5O1/A10M5O2)

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
requires exact canonical software identity, unique L40 UUIDs, one hostname,
NCCL collective correctness, synchronized DDP state, checkpoint reload,
bounded rank-failure teardown, exact GPU-second/minute accounting, authenticated
evidence, and cleanup. Scaling results are advisory and separate from
operational correctness.

Before a multi-GPU submission, the executor records `squeue -a` occupancy for
node03 and stops unless enough requested L40 capacity is idle. A four-GPU role
requires no existing node03 allocation. This is a best-effort non-preemption
admission snapshot, not an atomic scheduler reservation.

## Provenance obligations

The attestation binds source commit, package and run IDs, canonical
configuration ID and semantic hash, provider hashes, Slurm job IDs, requested
GRES, parsed count, node, GPU UUIDs, runtime versions, gate receipt hashes,
requested and actual GPU-minutes, admission snapshots, collection/cleanup
receipts, and terminal disposition. Raw private paths and user-identifying
cluster data are sanitized before publication.

## Excluded claims

Passing does not establish multi-node communication, heterogeneous execution,
universal speedup, scientific model validity, production durability, requeue,
administrator support, or a new canonical default.
