# Execution disposition

Operational terminal: `A10M5O2-MULTI-L40-OPS-READY`

Performance classification: `SINGLE-GPU-PREFERRED`

The canonical CPython 3.11/PyTorch stack is qualified for an explicitly
authorized one-node request of two or four typed L40s. Each rank received a
unique NVIDIA L40 on node03; canonical software identity, NCCL collectives,
DDP synchronization, checkpoint reload, expected peer failure, scheduler
accounting, sanitization, and exact cleanup all passed.

This does not change the canonical one-L40 default. The frozen microbenchmark
was communication-heavy and became slower as ranks increased: fixed-global
throughput was 141,193, 56,464, and 2,609 examples/s at one, two, and four
GPUs. A later workload may request multiple GPUs only under the additive
provider and must produce its own scaling rationale; availability is not a
claim of efficiency. Cross-node, heterogeneous, node04, requeue, A10M6,
scientific validity, and promotion remain excluded.
