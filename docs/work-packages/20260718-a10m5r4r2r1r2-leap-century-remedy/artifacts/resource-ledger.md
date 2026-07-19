# Resource ledger

| Scope | Jobs | Actual GPU time | Ceiling-rounded GPU-minutes |
|---|---:|---:|---:|
| A10M5R4R2 predecessor | 1 | retained predecessor charge | 3 |
| A10M5R4R2R1 neural collection | 6 | 1,238 GPU-seconds | 24 |
| R1 and R2 local scoring remedies | 0 | 0 | 0 |
| Campaign aggregate | 7 | predecessor charge plus 1,238 seconds | 27 |

R2R1's package authority ceiling was 182 GPU-minutes, the 185-minute campaign
ceiling less R2's three-minute charge. Its six primaries could allocate at
most 174 minutes and its recovery reserve at most five, leaving three minutes
unallocatable. Actual R2R1 use was 24 rounded minutes; retry and recovery were
not invoked. R1 and R2 did not contact Slurm or allocate a GPU.
