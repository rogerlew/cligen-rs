# Resource ledger

The authority ceiling was 935 GPU-minutes. Only control job `1014053` was
submitted. Slurm recorded one elapsed second on one L40, which rounds to one
actual GPU-minute under the toolkit accounting rule. No candidate or recovery
job ran.

The controller ledger retains 35 requested GPU-minutes because observation
could not authenticate a gate: 30 for control in `submitted` state and five for
the unused recovery contingency in `reserved` state. These are unsettled
controller reservations, not 35 minutes of scheduler use. Manual Slurm
accounting proves one actual GPU-minute for control and zero for recovery.

The private ledger stopped at submitted entry head
`18f26425ad728c7b3a7d7fb3ce5c5e51bd3295a5c36add786f322ae8369eb49c`
because the missing failure gate prevented toolkit observation. The retained
ledger file has SHA-256
`6a928eaf38315f065e60042978a6cff557eb579799b8cfd5941736ff0535dc73`.
The unsettled controller reservation is disclosed rather than rewritten; the
scheduler authority contains exactly job `1014053` and the durable root is
absent.
