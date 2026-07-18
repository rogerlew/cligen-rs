# A10M5 execution record

Execution used the warm MFA-bootstrap SSH path from `rmm`, canonical Lemhi v2,
`gpu-icrews`, one typed L40, 8 CPUs, 65,536 MiB, and a 120-minute limit per
screen job. After concurrent R2 jobs proved that two isolated environments
exhaust node03 `/tmp`, every later allocation ran sequentially.

| Lineage | Source | Slurm jobs | Actual GPU seconds | Result |
|---|---|---|---:|---|
| R1 | `b49bfc1` | none | 0 | Staged, then aborted before submission when wrapper supervision was found incomplete. |
| R2 | `b396b72` | 1013870--1013871 | 332 | Two concurrent environments exhausted node03 `/tmp` before training; exact job-local cleanup passed. |
| R3 | `3e36f4c` | 1013872 | 570 | First complete fit; failed because RSS included training state and one timing row exceeded dispersion. |
| R4 | `470f7db` | 1013873 | 567 | Fresh export process still invoked with autograd; all gates except 2 GiB RSS passed. |
| R5 | `737e7e5` | 1013874 | 593 | True inference mode still used a full-sequence GRU workspace; RSS and one timing row failed. |
| R6 | `ff3a44e` | 1013875 | 552 | Bounded 365-day state-carrying export passed all gates except RSS. |
| R7 | `abeddf9` | 1013876--1013927 | 6,557 | Complete 12-row frozen screen; all rows failed RSS, one also failed dispersion. |

R7 reached `MATRIX_SETTLED`, collected 87 allowlisted files in a 1,495,040-byte
archive, authenticated raw and sanitized hashes, proved every job-local root
absent, removed the exact durable root, and closed as
`LEMHI-TOOLKIT-RUN-CLOSED`. The successful cleanup receipt reports
`remote_absent: true` and `job_local_cleanup: verified_absent`.

Collection exposed three toolkit issues and produced source fixes with tests:
finite scientific JSON projection, restartable quarantine handling, and
non-reserved diagnostic redaction. The immutable R7 collection receipt retains
the adapter's stale projection-2 policy label; amendment 010 records that
metadata discrepancy and future receipts now report projection 3.

No development or confirmation target series was read. Failed fit artifacts
are development-only evidence and cannot be promoted or reused as A10M6
candidates.
