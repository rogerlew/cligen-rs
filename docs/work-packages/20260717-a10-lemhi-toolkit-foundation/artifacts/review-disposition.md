# Review disposition

Disposition date: 2026-07-17
Specification disposition: authoritative revision 1 design, ready for
implementation dispatch after repository gates

Every independent-review finding is dispositioned below. “Merged” means the
finding independently identified the same defect and shares one normative
correction; it does not mean the finding was ignored.

| Finding | Disposition | Normative result |
|---|---|---|
| AR-01 | ACCEPTED | Sections 5, 6.5, 10, 12, and 15 now define locked, reserved, token-reconciled at-most-once submission and `SUBMISSION_OUTCOME_UNKNOWN`. |
| AR-02 | ACCEPTED | Sections 5 and 6.1 define transition events and pre-/post-plan identity binding; §6.3 defines semantic `plan_id`. |
| AR-03 | ACCEPTED | Section 6 adopts RFC 8785/JCS and §15 requires cross-serializer golden fixtures. |
| AR-04 | ACCEPTED | Section 14 now requires executable paths for every lifecycle operation against injected fakes. |
| AR-05 | ACCEPTED | Sections 6.3 and 7 require one ordered provider stack with checked `requires`/`provides`. |
| AR-06 | ACCEPTED | Section 7 limits revision 1 to declarative providers and toolkit-owned typed operations; executable plugins require a later major API. |
| AR-07 | ACCEPTED | Sections 3 and 4 separate POSIX bootstrap/staging from declared and probed job interpreters. |
| AR-08 | ACCEPTED | Section 4 uses content-hashed logical endpoints with the observed aliases only as revision-1 defaults. |
| AR-09 | ACCEPTED | Section 6.3 narrows per-asset license provenance to external redistributable assets. |
| AR-10 | ACCEPTED / DEFERRED SURFACE | Section 14 implements only SCP in the minimum slice; rsync remains a later provider, not a foundation claim. |
| HS-01 | ACCEPTED / MERGED AR-01 | Submission locking, reservation, token recovery, concurrency fixtures, and exact job reconciliation are normative. |
| HS-02 | ACCEPTED | Section 11 moves default-deny confirmation allowlisting before all filesystem observation and §15 adds direct/link/glob/archive fixtures. |
| HS-03 | ACCEPTED | Sections 3, 6, and 6.6 separate private operational records from sanitized publication receipts and prohibit sanitized-only cleanup. |
| HS-04 | ACCEPTED | Section 5 makes discovery nonallocating and compute validation post-plan/post-submission. |
| HS-05 | ACCEPTED | Section 11 requires exclusive atomic marker creation, run locks, bounded validation/deletion, and authorized abort handling. |
| HS-06 | ACCEPTED | Section 9 defines raw-evidence quarantine, archive rejection, separate sanitization, and private raw/published hash binding. |
| HS-07 | ACCEPTED | Section 10 defines requested and actual GPU-minutes, no-requeue default, restart counting, settled accounting, and exact-job closure. |
| HS-08 | ACCEPTED | Section 4 requires master checks immediately before every operation, post-transfer recheck, batch mode, and finite total timeouts. |
| HS-09 | ACCEPTED | Section 8 adds hostile-archive, manifest, loader/libc/CPU, and native-build gates. |
| HS-10 | ACCEPTED | Section 16 now freezes the exact Python 3.11 contract, positive tests, cleanup, and excluded claims. |
| HS-11 | ACCEPTED / MERGED AR-03 | RFC 8785/JCS and cross-serializer fixtures are normative. |
| HS-12 | ACCEPTED | Sections 6.6 and 10 reconcile exact registered jobs rather than require an empty user queue. |

No accepted P1/P2 finding remains unresolved. No finding was rejected or
silently deferred. AR-10 narrows the first implementation surface and records
rsync as an explicit later extension rather than pretending it is tested.

## Post-revision verification

- The architecture reviewer re-read the revised specification and confirmed
  AR-01 through AR-10 are accurately dispositioned, the minimum slice remains
  lightweight, and no accepted architecture P1/P2 remains.
- The HPC safety reviewer re-read the revised specification and confirmed
  HS-01 through HS-12 are accurately dispositioned, including the exact
  Python 3.11 contract in §16, and no accepted safety P1/P2 remains.
