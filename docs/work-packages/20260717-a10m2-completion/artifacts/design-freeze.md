# Design and pass-rule freeze

Frozen prospectively on 2026-07-17 PDT before remote mutation or allocation.

## Immutable sources

- C1 CUDA source is byte-identical to A10M2's retained smoke; only the
  invocation changes to the D1-proved explicit host compiler.
- Framework tests derive from the unexecuted A10M2 J2/J3 sources and retain
  their registered numerical/device checks.
- Restart logic derives from A10M2's unexecuted J4 source and retains seed,
  recurrence, target step, atomic-write rule, and expected interruption code.
- A10M1 input is exactly `a10m1-offline-transfer-v1`: 98 accepted v2 objects,
  223,799,545 aggregate bytes. Failed v1 identities are not eligible.

## Environment

- Python: amended after P0 to
  `/opt/modules/devel/python/3.8.11/bin/python3.8`; see Amendment 02.
- CUDA toolkit: `/usr/local/cuda-12.8`.
- Host compiler: `/usr/bin/g++` via `nvcc -ccbin`.
- Framework: amended after P0 to official Linux x86-64
  `torch==2.4.1+cu124` plus its declared NVIDIA CUDA/NCCL and Triton Linux
  releases and pure-Python dependency closure. The PyTorch CUDA 12.4 index and
  authoritative PyPI release files
  are the only resolver sources; each version and SHA-256 is frozen under
  `environment/` before C1-02 staging. The original CPython 3.11 selection is
  rejected historical evidence in commit `8b7e751` and was never installed.
- Installation must use `--no-index`, the verified job-local wheelhouse, and
  `--require-hashes`; compute-node network access is prohibited.

## Classification

Every job needs a sanitized stdout/stderr pair and terminal `sacct` receipt.
C1 and C2 must be `COMPLETED/0:0`. C3a is a pass only when its durable
checkpoint validates, Slurm records the frozen nonzero interruption exit, and
the log reports classified `USR1`; C3b must be `COMPLETED/0:0`.

An exact retry changes no source, assets, resources, or pass criterion and is
permitted only for a documented infrastructure transient within the hard
one-GPU-hour cumulative ceiling. Scientific or environment failures stop the
ladder.

## Stage-2 measurements

C1 uses both the 98-object real layout and one tar bundle over identical
logical bytes. Rates are operational observations, not training throughput.
Every logical object and archive is hashed. The bounded reread is explicitly
cache-warm. A 64 MiB deterministic checkpoint-style object is copied back to
Ceph and verified. After deleting the job-local cache, the resolver must
select and hash the durable source. The job-owned local directory is removed
by a validated cleanup trap.
