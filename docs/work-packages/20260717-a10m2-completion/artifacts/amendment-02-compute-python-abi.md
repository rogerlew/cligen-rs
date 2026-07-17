# Amendment 02 — compute-valid Python ABI

Date: 2026-07-17 PDT
Applied after P0 and before C1-02

## Evidence

P0 (`1013670`) completed on `node03` and proved:

- the login-visible Python 3.11.11 executable is absent;
- `/opt/modules/devel/python/3.8.11/bin/python3.8` is present;
- direct CUDA 12.8 and `/usr/bin/g++` remain executable;
- the job-local root is writable with no C1 candidate collision; and
- the allocation exposes one NVIDIA L40 with driver 610.43.02.

This localizes C1-01 to the frozen Python precondition. It is documentation
and installation drift, not a CUDA, GPU, storage, or framework runtime result.

## Prospective correction

- Select the compute-observed Python 3.8.11 ABI.
- Select the official CPython 3.8 Linux x86-64
  `torch==2.4.1+cu124` wheel and its exact declared dependency closure.
- Retain direct CUDA 12.8 plus `/usr/bin/g++` for the standalone CUDA smoke.
  The framework's packaged CUDA 12.4 runtime is a separate, driver-compatible
  stack whose usability must be measured by C1-02.
- Add postponed annotation evaluation to Python sources that used modern
  built-in generic syntax, and remove `zip(strict=...)`, so the unchanged
  test logic is valid under Python 3.8.
- Replace the remote CPython 3.11 wheelhouse only after the CPython 3.8 tar is
  independently hash-verified. The rejected asset is derived and recoverable
  from the local frozen archive and git identity; it is removed from the
  package-owned remote run to avoid quota waste.

The one-GPU, two-GPU, stage-2, and restart pass rules do not change. Revised
conservative requested use remains 55 GPU-minutes, below the hard one-hour
ceiling. This is a functional environment correction, not an exact retry.
