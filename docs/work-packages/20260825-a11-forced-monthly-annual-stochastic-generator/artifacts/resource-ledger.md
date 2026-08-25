# A11 resource ledger

Status: reconciled at `HOLD-A11-CONTRACT-NONCONFORMANCE`

## Authorized ceiling

- CPU: 28,800 seconds aggregate
- GPU: zero
- evidence/output: 2,147,483,648 bytes
- operational candidate attempts: two

## Realized

- Attempt 0001: 88.1 wall seconds, zero GPU, failed before evidence
  publication.
- Attempt 0002: 108.08889629199984 measured process seconds, zero GPU,
  1,137,915 final diagnostic-evidence bytes.
- A later comparator-recovery diagnostic was stopped when independent review
  established P0 architecture nonconformance. It produced no canonical
  evidence and was not a candidate attempt.
- Hash-verifying repository sync restored the registered `us-2015` station and
  PRISM 2026.07 caches. They are shared immutable caches and were retained.

The two authorized candidate attempts are consumed. No third candidate or
authentication replay ran. CPU, storage, and GPU ceilings were not exceeded.

## Cleanup

- Raw candidate daily arrays existed only in process memory and were released.
- Comparator scratch roots totaling approximately 2.1 MiB were moved from
  `target/` to the user's Trash; this is recoverable until Trash is emptied.
- Compact invalid diagnostics, audit, decisions, and hashes remain in the work
  package.
