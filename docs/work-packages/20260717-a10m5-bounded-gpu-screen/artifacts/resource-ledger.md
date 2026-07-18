# A10M5 resource ledger

The frozen package ceiling was 9,600 one-L40 GPU-minutes. Submitted attempts
requested 2,160 GPU-minutes (22.5% of the ceiling) and consumed 9,171 elapsed
GPU-seconds (152.85 minutes). Per-job ceiling-rounded accounting totals 161
GPU-minutes. No recovery GPU allocation ran.

| Lineage | Jobs submitted | Requested GPU-min | Actual GPU-s | Rounded GPU-min |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 0 | 0 |
| R2 | 2 | 240 | 332 | 6 |
| R3 | 1 | 120 | 570 | 10 |
| R4 | 1 | 120 | 567 | 10 |
| R5 | 1 | 120 | 593 | 10 |
| R6 | 1 | 120 | 552 | 10 |
| R7 | 12 | 1,440 | 6,557 | 115 |
| **Total** | **18** | **2,160** | **9,171** | **161** |

R7's five-minute exact-node recovery reserve was released unused at close.
Staging repeatedly transferred roughly 4.83 GB but consumed no GPU allocation.
The need to restage immutable assets across corrective lineages remains a
documented cross-run-cache limitation, not GPU-budget consumption.
