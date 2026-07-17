# A10M2D2 terminal

Disposition: `A10M2D2-SCP-EXPECTATIONS-FROZEN`

The package is `EXECUTED-COMPLETE`. All integrity, stability, hard traffic,
resource, and cleanup gates passed. Two P3 capture/estimate defects are
preserved in `review.md`; neither breached the safety envelope or weakens the
transfer conclusions. There are zero open P1/P2 findings.

The observed warm path supports routine hash-verified SCP of single files or
archives up to approximately 10 GiB. Many-file inputs must be bundled. Do not
enable SSH compression by default for A10 artifacts. For approximately 50 GiB
or larger, or whenever restarting would be operationally expensive, prefer the
observed verified rsync resume path or investigate an administrator-supported
managed transfer service.

Stage 2 is supported and remains required inside the next authorized
GPU-bearing A10M2 continuation allocation. This terminal does not authorize a
standalone GPU I/O job, framework testing, training, or A10M3.
