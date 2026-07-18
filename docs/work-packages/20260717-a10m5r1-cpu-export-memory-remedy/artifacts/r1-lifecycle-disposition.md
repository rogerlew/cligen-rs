# A10M5R1 R1 lifecycle disposition

Slurm job 1013928 completed on node03 in 99 seconds with exit code 0 and
515,796 KiB `sacct` MaxRSS. The application produced all seven requested
fresh-process measurements and the supervisor proved job-local absence.

The package-authored gate receipt used a scientific disposition string but
omitted the nonempty boolean `gates` map required by canonical toolkit v2.
`observe` therefore failed closed with `EVIDENCE_INCOMPLETE`; R1 is not a
valid lifecycle and none of its measurements alone can close the package.
The raw evidence SHA-256 is
`7051a696d6ecde2003adaaeff905d1072256ae4277b896c9eb0dde89e6f4a8a3`.

Before exact cleanup, the evidence, supervisor receipt, and Slurm streams were
copied under `artifacts/raw-r1/`. The exact canonical remote run root was
resolved, checked to be a real directory, deleted, and verified absent. The
supervisor had already removed `/tmp/a10m5r1-memory-attribution-1013928`.

R1 requested 30 GPU-minutes and used 99 GPU-seconds. R2 is a new auditable run
that corrects the receipt and preserves the same frozen scientific boundary;
it is not a retry claim for R1.
