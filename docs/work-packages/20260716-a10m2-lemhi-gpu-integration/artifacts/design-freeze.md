# A10M2 design and pass-rule freeze

Frozen before the first remote write or Slurm submission on 2026-07-16 PDT.

## Job rules

- Every job uses `gpu-icrews` and a typed `gpu:l40` request.
- Jobs execute sequentially. A later job is not submitted after a hard failure.
- The scripts under `jobs/` are the exact submission sources. Any functional
  edit after J1 begins invalidates the affected result and requires a package
  amendment; it is not an exact retry.
- A job is classified only after both its sanitized log and terminal `sacct`
  receipt exist.

## Pass rules

- J1: one visible/allocated CUDA device; L40 identity; CUDA 12.8 compiler and
  driver receipts; successful allocation, host-to-device transfer, kernel,
  synchronization, device-to-host transfer, exact element check, and durable
  versus local copy comparison.
- J2: Python 3.11 and the post-J1 pinned PyTorch stack reconstruct solely from
  the hashed wheelhouse; `pip check` passes; exactly one L40 is visible;
  tensor, autograd, optimizer, checkpoint, and reload checks pass.
- J3: two distinct L40 devices; two NCCL ranks; registered all-reduce result;
  one DDP update; identical final parameters; clean shutdown.
- J4a: Slurm delivers the frozen pre-timeout `USR1` to the batch shell, which
  forwards it to the synthetic state machine; an atomic durable checkpoint is
  written and the expected nonzero interruption exit is classified.
- J4b: the exact checkpoint resumes and reaches the target state and rolling
  trace digest identical to an uninterrupted control.

No test accesses A10 corpus or confirmation series, trains a candidate,
deliberately preempts a job, or makes a throughput/scaling claim.

## Amendment

[Amendment 01](amendment-01-compute-module-registry.md) prospectively replaces
Lmod lookup with the same modulefiles' canonical installation paths after the
first J1 attempt established that the login and compute registries differ.
It changes no selected version, test, or resource request and caps the amended
matrix at 50 requested GPU-minutes with no retry remaining.
