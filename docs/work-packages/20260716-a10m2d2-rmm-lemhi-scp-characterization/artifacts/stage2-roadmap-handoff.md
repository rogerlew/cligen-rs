# Stage-2 roadmap handoff

Stage 2 is a required future M2 readiness gate, not part of A10M2D2 execution.
It must be integrated into the next authorized GPU-bearing A10M2 continuation
instead of consuming an L40 solely for an I/O benchmark.

Inside that allocation, before framework or training claims, the package must:

1. identify the actual durable Ceph source and resolved
   `${SLURM_TMPDIR:-${TMPDIR:-/tmp}}` destination plus filesystem types and
   available capacity;
2. copy a prospectively bounded immutable object set from Ceph to job-local
   storage, time it, and verify every SHA-256;
3. compare a representative many-shard layout with an archived/bundled form if
   A10M1 has frozen real shard sizes by then;
4. measure a bounded local read and durable checkpoint-style copy-back without
   treating page cache as training throughput;
5. publish the durable result before cleanup, verify it, then remove only the
   job-owned local directory and leave a cleanup receipt;
6. prove that missing local cache falls back to verified durable objects; and
7. translate measured staging/copy-back time into checkpoint/preemption
   guidance.

It must also consume the stage-1 alternative-transport and interruption
findings: use a resumable transport for large durable staging only if the
measured SCP expectations and administrator-supported options justify it.

The future package freezes its bytes and time from A10M2D2 results and, where
available, the A10M1 transfer manifest. No stage-2 resource or execution is
authorized by this handoff.
