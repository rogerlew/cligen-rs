# Execution evidence and disposition

Executed from `rmm` on 2026-07-17 through the warm MFA-authenticated
`login-ui` and `lemhi` SSH control masters. All jobs used `gpu-icrews`,
`gpu:l40:1`, 4 CPUs, 16 GiB, and a 20-minute limit on `node03`. No job used
network access or confirmation data.

## Run history

| Run | Source | Slurm | State | Elapsed | Disposition |
|---|---|---:|---|---:|---|
| 1 | `1135a98` | 1013742 | FAILED (1) | 93 s | Invalid `_sqlite3.__file__` harness assumption; exact root recovered and absent |
| 2 | `7845a69` | 1013746 | FAILED (1) | 92 s | Incorrect NumPy expected arithmetic; failure evidence collected, exact cleanup and close passed |
| 3 | `bd063b0` | 1013747 | COMPLETED (0) | 100 s | All 19 authenticated gates passed; collection, cleanup, and close passed |

The three independently frozen intents reserved 60 requested GPU-minutes.
Slurm recorded 285 aggregate GPU-seconds (4.75 GPU-minutes) of actual elapsed
allocation. Toolkit accounting exposed the actual value as unavailable in the
job receipts, so the 4.75 figure is reported separately from direct `sacct`
`ElapsedRaw` evidence and is not substituted into toolkit records.

## Accepted result

Run 3's exact gate receipt SHA-256 is
`4a8347a5468a6ef26cee27767bed4d97b7bdfd2c1a86af1dfc7309cea8c5afcc`.
The live adapter authenticated that receipt from the registered regular,
nonsymlink `evidence.json`; all 19 values were boolean true:

- exact CPython 3.11.15 and cp311 ABI;
- `ssl`, `sqlite3`, `ctypes`, `venv`, subprocess, and spawned
  multiprocessing;
- isolated Python/loader inheritance and compiled NumPy linkage without a
  missing `ldd` dependency;
- NumPy 2.2.6 arithmetic and zero-copy NumPy/PyTorch interop;
- PyTorch 2.7.1+cu128, CUDA 12.8 availability, exactly one visible L40,
  device tensor operation, autograd update, and checkpoint/reload;
- offline `--require-hashes` installation and `pip check`; and
- verified job-local cleanup.

The evidence archive was 10,240 bytes and downloaded with SHA-256
`758154efe5568abfea17fe0068906e1f11097df246070727a25e8f090e9460a2`.
Sanitization published the 740-byte gate receipt, empty stderr, and the single
line `A10-PY311-SMOKE-PASS`. The toolkit then removed the exact marked remote
run, verified absence, and closed with `LEMHI-TOOLKIT-RUN-CLOSED`.

## Toolkit findings resolved during live use

Live execution added regression-covered corrections for:

- stable `linux-x86_64-glibc` login receipts with explicit glibc/architecture;
- authentication of scheduler success against an exact allowlisted gate
  receipt rather than controller placeholder gates;
- human-readable license-provenance records;
- settlement of an exhausted failed role so failure collection and exact
  cleanup remain reachable; and
- atomic detailed failure evidence from the smoke job.

Run 1 predated the exhausted-failure correction and therefore required the
registered marker recovery path after its private logs were retained. Runs 2
and 3 exercised the corrected normal failure and success lifecycles.

## Boundaries

This establishes a bounded portable CPython/NumPy/PyTorch one-L40 capability,
not performance, training readiness, multi-GPU behavior, requeue behavior,
production durability, or any A10M3 scientific claim. Confirmation access was
false throughout.

Terminal: `A10-LEMHI-PY311-SMOKE-READY`
