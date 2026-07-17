# Scheduler receipt

All jobs ran on `node03` through `gpu-icrews` with typed L40 requests.

| Job | Name | Terminal | Elapsed / limit | CPUs / memory | Batch MaxRSS |
|---:|---|---|---|---|---:|
| 1013668 | C1-01 | `FAILED 1:0` | 1 s / 15 min | 4 / 16 GB | 4,908 KiB |
| 1013670 | P0-01 | `COMPLETED 0:0` | 0 s / 5 min | 2 / 8 GB | 2,872 KiB |
| 1013671 | C1-02 | `COMPLETED 0:0` | 76 s / 15 min | 4 / 16 GB | 72,648 KiB |
| 1013672 | C2-01 | `FAILED 126:0` | 1 s / 5 min | 8 / 32 GB | 2,892 KiB |
| 1013673 | C2-02 | `COMPLETED 0:0` | 6 s / 2 min | 8 / 32 GB | 4,848 KiB |
| 1013674 | C3a | expected `FAILED 75:0` | 29 s / 2 min | 2 / 8 GB | 2,824 KiB |
| 1013675 | C3b | `COMPLETED 0:0` | 1 s / 2 min | 2 / 8 GB | 4,868 KiB |

C1-01 and C2-01 are prospectively amended pre-test package defects. C3a's
nonzero terminal is the registered interruption success condition, supported
by its checkpoint and C3b control match. Batch MaxRSS is retained as reported
but is not interpreted as complete child-process or GPU-memory high-water
accounting; Slurm exposed neither trustworthy GPU-memory nor energy metrics.
