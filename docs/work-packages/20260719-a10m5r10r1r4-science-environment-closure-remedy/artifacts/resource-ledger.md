# Resource ledger

The fresh authority ceiling was 935 GPU-minutes: 30 for one control job, 900
for ten single-attempt candidate jobs, and five for exact-node recovery. The
control and all ten candidates were reserved, submitted once, observed, and
settled. Slurm accounting charged 396 actual GPU-minutes:

| Role | Job | Elapsed seconds | Actual GPU-minutes |
| --- | ---: | ---: | ---: |
| control materialization | 1014057 | 893 | 15 |
| monthly residual K1 | 1014058 | 2,224 | 38 |
| monthly residual K2 | 1014059 | 2,259 | 38 |
| annual/monthly residual K1 | 1014060 | 2,042 | 35 |
| annual/monthly residual K2 | 1014061 | 2,575 | 43 |
| hierarchical joint factor K1 | 1014062 | 2,253 | 38 |
| hierarchical joint factor K2 | 1014063 | 1,848 | 31 |
| climate-normal state space K1 | 1014064 | 2,477 | 42 |
| climate-normal state space K2 | 1014065 | 3,014 | 51 |
| physics-conditioned K1 | 1014073 | 1,848 | 31 |
| physics-conditioned K2 | 1014074 | 2,003 | 34 |

No job was retried and no recovery allocation ran. The five-minute reserve was
released after ordinary cleanup. The final ledger has 36 entries, head
`f8a2ee09cfa80ac4f61016fece23caf90fcff33c20db886a8e3b29d5dda2b934`,
file SHA-256
`40671f97d6df313bbbcabcf6209087604a99305f38399420ae6d1741b549e759`,
and no unsettled reservation.
