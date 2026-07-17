# Review

Disposition: accept `A10M2-COMPUTE-READY`

No open P1/P2 finding remains. The two failed base attempts occurred before
their registered scientific gates and were prospectively corrected under
published amendments. C1-02, C2-02, C3a, and C3b then passed unchanged result
criteria. All 53 requested GPU-minutes and 2.0167 actual GPU-minutes are
accounted, confirmation remained untouched, evidence was verified before the
exact remote cleanup, and no production code changed.

## Retained P3 traps and limitations

1. Compute Python drift: login Python 3.11.11 is absent on `node03`; the proved
   stack uses compute Python 3.8.11 and PyTorch 2.4.1/CUDA 12.4. Do not infer
   that a login-visible module exists on compute.
2. Compiler support: direct CUDA 12.8 plus `/usr/bin/g++` is observed working,
   not administrator-certified.
3. Relocated venv console scripts retain absolute shebangs. Create future
   venvs at their final path or use `python -m ...`.
4. PyTorch's NumPy probe warns under the cluster Python even with inherited
   paths isolated. NumPy was outside this lock and unused by the tests. Any
   NumPy-dependent A10 loader must add and test an exact compatible wheel.
5. Stage-2 timings are cache-warm because integrity verification preceded the
   timed copy. They support access/integrity, not cold-start or throughput
   claims. A10M4 must instrument real loader/checkpoint behavior.
6. Shared Ceph availability is not an account quota. The temporary run reached
   about 8 GiB before cleanup without establishing a quota ceiling.
7. Scheduler MaxRSS did not expose complete child/GPU memory or energy
   high-water metrics; no such resource claim is made.
8. Python 3.8 is end-of-life. A10M3 must either freeze the proved stack for the
   bounded study or prospectively validate a portable/newer runtime; it may
   not silently swap environments.

These are handoff constraints, not failures of the frozen M2 capability tests.
