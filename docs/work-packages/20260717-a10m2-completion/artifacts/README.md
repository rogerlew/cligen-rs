# A10M2 completion artifact registry

- `design-freeze.md` and `dispatch.md` freeze authority and execution rules.
- `environment/` records the exact offline framework selection and hashes.
- `jobs/` contains every exact source staged or submitted.
- `logs/` receives sanitized job and accounting evidence.
- `attempt-ledger.md`, `resource-ledger.md`, `stage2-result.md`,
  `cleanup.md`, `gates.md`, `review.md`, `terminal.md`, and
  `a10m3-handoff.md` are execution outputs.

Large wheel, corpus, runtime, and raw scheduler artifacts are temporary and
must not be committed. Their retained identities are SHA-256 manifests.
