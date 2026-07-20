# Execution disposition

Date: 2026-07-20
Terminal: `HOLD-A10M5R12R1-COLLECTION-CAPACITY`

The operational admission remedy passed. Control job `1016088` completed in
923 seconds and both candidates ran concurrently after serialized setup:
medium job `1016103` completed in 2,023 seconds and hierarchical job `1016104`
in 2,893 seconds. All registered job, calendar, control, physical-support,
stream-matrix, submission-admission, and job-local cleanup gates passed. The
ledger settled/charged 16 + 34 + 49 = 99 GPU-minutes. Its unused 5-minute
`toolkit-recovery` reservation remains stranded because the parent stays
unclosed: 104 GPU-minutes are committed against the 395-minute ceiling, while
R2 deliberately leaves the parent ledger bytes and head unchanged.

Toolkit collection downloaded the exact 96,491,520-byte evidence archive and
failed closed at `ARCHIVE_UNSAFE` before extraction because its 96,443,290
expanded bytes exceeded the frozen 50,000,000-byte profile ceiling. The two
intentional retained stream archives, 45,716,782 and 45,772,878 bytes, would
also independently exceed the later 10,000,000-byte per-file ceiling.

The archive is otherwise safe: SHA-256
`4c5d2ebcdbf96fa8fe75ab971a163d2a3155c4fbb7ca6fb7e852278eafbf4abf`,
exactly 51 allowlisted regular root-owned members, no link, unsafe path,
nonregular type, or set-id member. Parent state remains `MATRIX_SETTLED` at
SHA-256 `be4a20d39dc7280e091311698b6e014612753816dc661325ebe0787379d09af6`.
It was never `COLLECTED`, `CLEANED`, or `CLOSED`, and no parent terminal
receipt exists.

A10M5R12R2 is the authorized zero-allocation reconciliation. It preserves this
hold, authenticates and replays the exact archive, then performs successor-
owned marker-bound cleanup. No GPU rerun, plan amendment, profile substitution,
solar access, or confirmation access is authorized.
