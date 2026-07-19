# Resource ledger

The authority ceiling was 935 GPU-minutes. Control job `1014056` requested 30
GPU-minutes and Slurm recorded 251 seconds on one L40, settled by the toolkit as
five actual GPU-minutes. No candidate or recovery job was submitted.

The five-minute recovery contingency was reserved before control and released
after ordinary cleanup proved job-local absence. The final ledger has six
entries, head
`02b22045c5ec6cb350d7d5b49fd9ddbbd2da98d6a1bfa7c4b221de3d75773d93`,
file SHA-256
`c1f61a55ead5c423edb8aa7c593fe8716548011f18afe9d74ce7b0cb8ac64961`,
and no unsettled reservation.

Requested limits remain prospective ceilings: 30 minutes for submitted
control, 900 minutes for ten never-submitted candidates, and five minutes for
the released reserve. Actual scheduler use was five GPU-minutes.
