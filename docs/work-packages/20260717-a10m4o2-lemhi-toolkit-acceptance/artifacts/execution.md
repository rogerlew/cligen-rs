# A10M4O2 execution

Source commit `c46a88d` was pushed to `origin/main` before live authority
creation. Both warm masters passed `BatchMode` checks. One private authority
with a 10-GPU-minute ceiling and one hash-chained ledger controlled two run
lineages.

The first lineage staged and byte/mode-verified 2,110 bytes, then invoked the
toolkit `abort` command before submission. It reached
`LEMHI-TOOLKIT-RUN-ABORTED-BEFORE-SUBMISSION`; the exact marked Ceph root was
removed and no authority-tagged Slurm job belongs to this lineage.

The live lineage staged 2,947 bytes—two package job scripts and the toolkit
recovery script. It did not transfer the canonical Python, framework, or Rust
archives and did not read A10 development or confirmation data.

- Job `1013867` completed on `node03` in 5 seconds. It saw exactly the
  registered NVIDIA L40 and passed all success/cleanup gates. The revised
  accounting path emitted 5 elapsed seconds, 5 GPU-seconds, and 1
  ceiling-rounded GPU-minute.
- Job `1013868` intentionally exited 7 on `node03` in 2 seconds. The toolkit
  still read and hashed its registered failure receipt, classified the attempt
  `passed=false`, and retained the exact marker/UID/device/target needed for
  recovery.
- `recover --job-role failure --attempt-index 0` reconciled the complete
  authority against Slurm, proved the source allocation and steps settled,
  and submitted reserved job `1013869` to exact node `node03`. It completed in
  1 second, revalidated the marker/UID/device/target, removed that target, and
  emitted `JOB_LOCAL_ABSENT`; `observe-recovery` authenticated all four gates.

The plan requested exactly 6 GPU-minutes and the ledger recorded 8 actual
GPU-seconds and 3 per-job ceiling-rounded GPU-minutes. The four remaining
authority minutes were never reachable from the frozen plan. Collection
promoted a 10,240-byte archive, both Ceph run roots are absent, the queue has
no authority-tagged job, all three scheduler IDs equal the ledger IDs, and the
live lineage closed as `LEMHI-TOOLKIT-RUN-CLOSED`.
