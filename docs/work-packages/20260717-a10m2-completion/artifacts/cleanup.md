# Cleanup receipt

- C1-02's validated trap removed only its job-specific XFS directory and
  printed `job_local_cleanup=pass`.
- The rejected CPython 3.11 remote wheelhouse was removed after the CPython 3.8
  replacement matched its frozen hash; the rejected archive remains locally
  recoverable.
- The final evidence archive was downloaded and matched SHA-256
  `7935de3f026e1e4932667ff0dfdc750b8cbc424ab500801438f8f56633a1c439`.
- The exact remote directory `a10m2-completion-8b7e751` was then removed and
  absence verified.
- The post-cleanup user queue was empty.

The removed remote run contained approximately 2,896 MiB of assets, 4,942 MiB
of reconstructed runtime, 213 MiB of extracted inputs, 64 MiB of checkpoints,
and small results. It is recoverable from the repository, frozen local assets,
and accepted A10M1 raw cache; job-local scratch is intentionally not retained.
