# Resource ledger

| Attempt | GPUs x limit | Conservative requested GPU-min | Actual elapsed | Actual GPU-min |
|---|---:|---:|---:|---:|
| J1-01 / 1013515 | 1 x 10 min | 10 | 0 s | 0.0000 |
| J1-02 / 1013516 | 1 x 10 min | 10 | 1 s | 0.0167 |
| **Submitted total** | | **20** | **1 s** | **0.0167** |

The amended full-ladder ceiling was 50 requested GPU-minutes (0.833
GPU-hour). Thirty GPU-minutes remained unsubmitted when the ladder stopped.
The hard one-GPU-hour ceiling was respected. Both attempts allocated 2 CPUs
and 8 GB; terminal `MaxRSS` for the amended batch step was 2860 KiB. Slurm did
not report energy or GPU-memory high-water metrics for these failed steps.
