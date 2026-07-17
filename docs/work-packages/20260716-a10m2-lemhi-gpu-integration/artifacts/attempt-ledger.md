# Attempt ledger

| Attempt | Frozen request | Placement | Terminal | Evidence and action |
|---|---|---|---|---|
| J1-01 / 1013515 | `gpu-icrews`, `gpu:l40:1`, 2 CPU, 8 GB, 10 min | node03 | FAILED, `1:0`, 0 s | Compute Lmod did not know `cuda/12.8`; Amendment 01 published before retry |
| J1-02 / 1013516 | same | node03 | FAILED, `1:0`, 1 s | One L40 visible; CUDA 12.8 `nvcc` host `gcc` died by SIGILL; terminal hold |
| J2 | frozen but unsubmitted | — | NOT SUBMITTED | Fail-closed ladder stopped after J1 hard failure |
| J3 | frozen but unsubmitted | — | NOT SUBMITTED | Same |
| J4a | frozen but unsubmitted | — | NOT SUBMITTED | Same |
| J4b | frozen but unsubmitted | — | NOT SUBMITTED | Same |

There were two Slurm submissions and no cancellation, preemption, requeue, or
additional retry. The second attempt consumed the only amended retry
allowance.
