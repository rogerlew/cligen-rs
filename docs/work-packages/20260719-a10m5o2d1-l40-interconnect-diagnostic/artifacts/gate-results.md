# A10M5O2D1 gate results

| Gate | Result |
|---|---|
| Immediate node03 no-allocation admission | PASS |
| Exact four homogeneous L40s | PASS |
| Canonical CUDA/PyTorch identity | PASS |
| Topology and P2P read/write matrices captured | PASS |
| All six default and P2P-disabled pairs complete | PASS |
| Default and P2P-disabled four-rank groups complete | PASS |
| All collectives correct | PASS |
| Positive finite bandwidth | PASS |
| Slurm terminal/accounting authenticated | PASS |
| Sanitized evidence collected | PASS |
| Remote and job-local cleanup | PASS |
| Recovery reserve released | PASS |

Slurm job `1014026` completed with exit code 0. It used 656 actual GPU-seconds
(11 per-job-rounded GPU-minutes) against 40 requested GPU-minutes. All 13
machine gates passed. The unused five-GPU-minute recovery reservation was
released, the ledger closed at
`957bb49642e6d71e59752da673aa476f8af08588f8716194226ea77f6242f9a7`,
and an independent SSH check confirmed the exact remote run root absent.
