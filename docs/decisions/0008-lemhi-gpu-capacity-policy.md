# ADR-0008: Prefer one- and two-L40 Lemhi execution topologies

Status: Accepted
Date: 2026-07-22
Deciders: Roger Lew (operator)
Evidence: `A10M5O2D1-L40-INTERCONNECT-CHARACTERIZED` and live node03
occupancy observed during A10M5R15R2R4 admission monitoring.

## Context

The Lemhi toolkit attests one-, two-, and four-L40 correctness, but that
attestation is not a throughput claim. Two-rank L40 groups use NCCL P2P and
measured 14.5--20.1 GB/s at 128 MiB. At four ranks NCCL selected host shared
memory and measured about 1.15 GB/s, matching the P2P-disabled control.

Large allocations also contend with ordinary node03 users. Requiring three or
four idle L40s can delay otherwise-ready work without a demonstrated reduction
in elapsed time.

## Decision

1. One and two typed L40s are the canonical Lemhi execution capacities. One
   L40 remains the baseline; two L40s are the normal concurrent capacity when
   independent roles or a measured workload support it.
2. Three- and four-L40 requests are exceptional. The toolkit admits them only
   when their frozen job record supplies a measured one/two-L40 baseline, a
   strictly lower projected elapsed time, and a separately frozen evidence
   asset supporting that comparison.
3. Recovery remains restricted to canonical capacity. Four-L40 operational
   correctness remains attested, but its existing transport result does not
   satisfy the exceptional-use evidence requirement.
4. This rule is prospective. It does not rewrite completed package records or
   alter the frozen two-L40 topology of A10M5R15R2R4.

## Consequences

- The multi-L40 provider declares one/two as canonical and three/four as
  exceptional, and the toolkit validates that distinction before remote
  mutation.
- A fresh occupancy snapshot remains necessary for every multi-GPU admission.
- Existing two-L40 R2R4 admission still needs two fresh idle L40s; it cannot be
  silently converted to one GPU.
