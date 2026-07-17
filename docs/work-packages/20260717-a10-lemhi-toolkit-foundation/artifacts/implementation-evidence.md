# Toolkit foundation implementation evidence

Date: 2026-07-17
Terminal: `LEMHI-TOOLKIT-FOUNDATION-READY`
Execution environment: `rmm`, macOS on an M1 Mac mini with 16 GB memory,
CPython 3.9.6
Implemented specification SHA-256:
`0dc4c768c3590156cee37fef0223d062737f37bd6d962b76f31929f5b2400008`

## Implemented surface

- `research/a10/lemhi_toolkit/core.py`: strict integer-only I-JSON/JCS records,
  stable errors, authority and path firewalls, run/attempt transitions,
  immutable plan revisions, provider composition, append-only shared resource
  ledger, evidence collection, sanitization, exact cleanup, and closeout.
- `adapters.py`: a persistent deterministic fixture backend and a live
  OpenSSH/SCP/Slurm adapter. The live adapter uses argument arrays locally,
  `BatchMode=yes`, finite timeouts, warm-master checks, fixed committed scripts,
  `.part` promotion, token reconciliation, exact job IDs, and no interactive
  authentication path.
- `remote/*.sh`: committed POSIX runners for probe, run creation, ownership
  marker installation, transfer promotion/verification, submission,
  reconciliation, observation, cancellation, allowlisted evidence packing,
  and canonical-root cleanup.
- `profiles/` and `providers/`: one content-hashed Lemhi profile and explicit
  SCP, Slurm, Ceph, and L40 revision-1 providers. They establish workflow
  mechanics only; CUDA, a framework ABI, performance, and science remain
  explicitly unestablished.
- `cli.py`, examples, and `README.md`: every normative lifecycle command plus
  private authority/plan inputs and operator sequencing.

## Acceptance disposition

The 21-test suite executes the complete lifecycle and all live adapter command
renderers with injected fakes. It proves fail-closed behavior for:

- absent or expiring warm SSH masters, stale/scope-wrong capabilities, and
  macOS-arm64/Linux-x86-64 or provider-stack mismatch;
- corrupt upload/download identities, unallowlisted or hostile archive members,
  symlink/hardlink assets, shell/path injection, and forbidden publication
  strings;
- resource-ceiling sharing across sequential and concurrent runs, accepted but
  response-lost submission, zero/multiple reconciliation, missing accounting,
  and no automatic resubmission or provider fallback;
- independent parallel, retry, cancellation, failed-gate, and expected-nonzero
  attempt lifecycles plus prospective amendment lineage; and
- missing/mutated ownership markers, canonical-root replacement, undeclared
  job-local purge, incomplete collection, and private-state removal at close.

The live command adapter was rendered and parsed only through a recording
runner. No VPN connection, SSH remote operation, SCP transfer, Slurm command,
GPU allocation, or remote deletion occurred. This is intentional: the Python
3.11 smoke package is the first live consumer and must carry its own exact
runtime hashes, job matrix, budget, stop rules, and cleanup authority.
