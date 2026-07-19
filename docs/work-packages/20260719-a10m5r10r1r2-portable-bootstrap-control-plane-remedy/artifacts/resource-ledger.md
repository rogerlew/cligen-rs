# Resource ledger

The authority ceiling was 935 GPU-minutes. Control job `1014054` requested 30
GPU-minutes and Slurm recorded 80 seconds on one L40, which the toolkit settled
as two actual GPU-minutes. No candidate or cleanup-recovery job was submitted.

The five-minute recovery contingency was reserved before control submission
and released after ordinary cleanup proved job-local absence. The final private
ledger has six entries, head
`64164d46a5123395390f10190a5408feb16b48538b53f45415803d6b38c797be`,
file SHA-256
`ce8bc0e99fd9a3bc75875f769b3901e1eb801b70ed3b073db5662a41e598d1cb`,
and no unsettled reservation.

Requested limits remain prospective ceilings, not consumption: 30 minutes for
the submitted control, 900 minutes for ten never-submitted candidates, and five
minutes for the released recovery reserve. Actual scheduler use was two
GPU-minutes.
