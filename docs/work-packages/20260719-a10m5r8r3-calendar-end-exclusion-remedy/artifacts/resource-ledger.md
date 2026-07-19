# Resource ledger

| Item | Requested | Actual | Disposition |
|---|---:|---:|---|
| Climate objective, job 1014025 | 60 GPU-min | 664 s / 12 charged min | settled, PASS |
| Exact-node recovery | 5 GPU-min | 0 | released after verified cleanup |

Authority ceiling: 65 GPU-minutes. One primary attempt was submitted. Recovery
was not invoked.

Corrective predecessor evidence remains separate: R1 job `1014023` used 246
GPU-seconds / five charged minutes; R2 job `1014024` used 223 GPU-seconds / four
charged minutes. The original bad-source genesis used no GPU resources.
