# Lemhi workflow toolkit

This is the dependency-free `rmm` control plane specified by
[`SPEC-LEMHI-AGENT-TOOLKIT`](../../../docs/specifications/SPEC-LEMHI-AGENT-TOOLKIT.md).
It runs with the macOS system Python 3.9.6 observed during foundation execution;
the remote scripts require only POSIX `sh` and profile-declared cluster tools.
It does not store credentials, start SSH masters, answer Duo, accept host keys,
or silently select a replacement provider.

Agents have authoring authority for toolkit-owned authority files, plans, job
scripts, and evidence rules when a dispatched work package grants the matching
operation, resource, confirmation, and cleanup scope. That authority does not
extend to SSH configuration, credentials, administrator-owned cluster state,
unplanned allocations, or protected confirmation data.

## Before a live run

1. Follow the VPN, bootstrap, and keepalive procedure in
   [`docs/c3-lemhi-gpu-computing-for-agents.md`](../../../docs/c3-lemhi-gpu-computing-for-agents.md).
2. Confirm both masters yourself with `ssh -O check login-ui` and
   `ssh -O check lemhi`. Toolkit remote operations repeat these checks using
   `BatchMode=yes`; failure is `AUTH_BOOTSTRAP_REQUIRED` and never an
   interactive fallback.
3. For a hardened dispatch, copy `examples/authority-v2.example.json` outside
   the repository and run the exclusive `initialize-authority` operation once.
   Later source corrections use `derive-run`; they never choose another ledger
   root or reset the budget. A new authority or resource-budget ID is not a
   successor run and must not be used to work around a failed lineage, even if
   cumulative actual usage would remain below the original minute ceiling.
   Revision-1 examples remain historical fixtures.
4. Create a private plan from `examples/plan.example.json`. The target is
   Linux x86-64 glibc even though dependency resolution is controlled from
   macOS arm64. Every local asset path must be absolute, regular, singly linked,
   and beneath an authority allowlist root. Invoked assets declare
   `executable: true`; preparation and remote verification both enforce it.
5. A live revision-2 authority owns its absolute mode-restricted ledger anchor;
   the CLI rejects `--state-root`. Fixture adapters may inject a temporary
   root. Private state survives exact reconciliation and cleanup.

The first live consumer is the separately dispatched CPython 3.11 smoke
package. Foundation acceptance itself uses no VPN, remote write, Slurm job, or
GPU allocation.

## Canonical A10 configuration

The current default for A10 single-L40 Python consumers resolves through
[`lemhi-canonical-designation-index-v1`](configurations/lemhi-canonical-designation-index-v1.json)
to the smoke-attested v2 configuration, governed by
[`SPEC-LEMHI-CANONICAL-CONFIGURATION`](../../../docs/specifications/SPEC-LEMHI-CANONICAL-CONFIGURATION.md).
Revision 1 is immutable status-at-issuance history. Configuration semantics,
smoke attestation, and current designation remain separate immutable records.
Python 3.8 remains legacy explicit-only.

## Command sequence

Run commands from the repository root. The common prefix is intentionally
explicit so a task log records every authority input:

```sh
python3 -m research.a10.lemhi_toolkit \
  --state-root /private/absolute/state/root \
  --authority /private/absolute/authority.json \
  --profile research/a10/lemhi_toolkit/profiles/lemhi-v1.json \
  --provider-root "$PWD" \
  --run-id a10-python311-smoke \
  doctor
```

Repeat that prefix with these lifecycle commands, in order:

```text
probe
plan --input /private/absolute/plan.json
prepare
stage
verify
submit --job-role smoke --attempt-index 0
# Monitor with squeue until the job leaves the queue and sacct is settled.
observe --job-role smoke --attempt-index 0
# If an exhausted failed upstream role makes every zero-attempt role moot:
# stop-matrix --trigger-job-role smoke --reason-code upstream-role-exhausted
# Only when observe authenticates unresolved job-local cleanup:
recover --job-role smoke --attempt-index 0
observe-recovery
collect
clean
close
```

Use `abort` only before submission when a prepared or staged run must stop. It
retains private controller receipts, validates and removes the exact staged
root when one exists, and publishes a pre-submission abort receipt.

`cancel` takes the same role and attempt arguments and resolves only the exact
registered job ID. `amend --input ... --reason ... --changed-field jobs`
creates a prospective revision; it cannot mutate a started role, immutable
asset, remote root, authority, confirmation classification, or resource
ledger. A failed or ambiguous submission must be reconciled from retained
private state, never retried by inventing another run or plan.

`recover` is not a generic retry or cleanup command. It consumes the single
prospectively reserved contingency only after the original attempt and all
steps have settled, submits to the exact authenticated original node, and
revalidates the UID, filesystem device, canonical target, and marker twice.
`observe-recovery` must authenticate the recovery gate receipt and accounting
before `collect` or `clean`; ambiguity retains both private state and the
reserve as `CLEANUP_INCOMPLETE`.

`observe` is intentionally one-shot and terminal-only. It does not wait for a
running job; an early call returns `JOB_TERMINAL_MISMATCH` without changing the
registered attempt. Use `squeue` as the live monitor, wait for terminal `sacct`
accounting, and then call `observe` once.

## Authoring traps from live acceptance

- Asset staging preserves each declared relative path; it does not synthesize
  missing parent directories inside an authored wrapper. Before submission,
  create every nested output parent used by shell redirection, including
  `slurm/` for `%o`/`%e` paths and any receipt subdirectory. A failure here is
  a pre-submission staging defect, not a Slurm or GPU failure.
- Do not run staged selectors, resolvers, or finalizers with Lemhi's ambient
  system `python`. It may be older than the authored language contract (the
  A10M5R3 resolver used annotations unsupported by that interpreter). Create
  and verify the canonical CPython 3.11 environment first, then invoke all
  package Python through that exact executable. The toolkit control plane may
  continue to use `rmm`'s supported system Python.
- Every job gate receipt needs a nonempty boolean `gates` object even when the
  scientific result has a different disposition vocabulary. Keep operational
  gates and scientific gates in separate fields.
- Revision-2 evidence allowlists are maximum permitted surfaces. Collection
  authenticates the exact sorted present/absent partition and archives only
  present regular single-link files. Every submitted attempt still requires
  its gate receipt and both Slurm streams; an invoked recovery likewise
  requires its gate receipt and both fixed streams. Never invent success-shaped
  data for a stopped role or an unused recovery reserve.
- Prospectively register typed evidence replacements for exact durable and
  job-local paths that can appear in tracebacks. Collection quarantines raw
  evidence and fails closed on an unregistered forbidden value.
- Projection replacement tokens use reserved angle-bracket syntax such as
  `<REMOTE_RUN_ROOT>`. Producer-side placeholders should use square brackets.
  Projection revision 4 escapes third-party raw angle tokens to
  `[[RAW_RESERVED_TOKEN:NAME]]` and counts them before typed replacements, so
  raw logs cannot masquerade as toolkit-authored redactions. Revision-2
  planning and amendment reject an invalid replacement token before staging.
- Run amendment is available while `VERIFIED` or `MATRIX_ACTIVE`, not after
  `MATRIX_SETTLED`. Inspect failure traces and amend projection rules before
  observing the final outstanding role when a correction is necessary.
- `/usr/bin/time -v` includes the full command line in its first output line.
  A plan that collects it must register durable/job-local path replacements,
  or the producer must use non-reserved pre-redaction such as
  `[REMOTE_RUN_ROOT]`, before the matrix settles.
- A successful job-local cleanup does not make `ru_maxrss` a valid child
  deployment metric. A worker forked by a high-RSS parent can retain the
  parent's maximum across exec. Launch memory-gated workers from a small
  supervisor after training exits and record `/proc/self/status` `VmHWM` plus
  external `/usr/bin/time -v`.

The committed profile selects an ordered SCP, Slurm, Ceph, and L40 provider
stack. Definitions are declarative JSON and content-hashed into every plan.
Adding a runtime or framework means adding a versioned provider record and an
explicit plan amendment or new plan; provider failure is not a fallback signal.

Every job and recovery record uses one authenticated GPU count. The toolkit
parses typed GRES such as `gpu:l40:2`, requires its resource/model to match the
selected accelerator provider, requires its count to equal `gpus`, and rejects
counts above that provider's maximum. The default `accelerator-l40-v2`
provider therefore remains one GPU. Explicitly authorized single-node counts
two and four use the additive `accelerator-l40-multigpu-v1` provider and do not
alter the canonical single-L40 designation.

Revision-2 plans use `lemhi-v2.json`, an all-v2 provider stack including the
toolchain provider, `toolkit_recoverable` storage, `--export=NONE` environment
closure, a frozen recovery contingency, typed raw-evidence projection, integer
transfer telemetry, and append-only content-addressed manifests. Useful
operator-facing commands are:

Packages that intentionally retain large binary streams use the separately
versioned `lemhi-v2-large-evidence.json` profile. It changes only evidence
collection ceilings and does not alter the designated canonical profile.

Evidence projection revision 4 accepts finite scientific JSON numbers while
continuing to reject duplicate keys, NaN/Infinity, forbidden values, and
invalid UTF-8. Raw reserved-looking tokens are escaped and counted before
authorized replacements. A failed collection quarantine is retained
under a numbered private identity; retry always downloads and extracts into a
fresh quarantine.

```text
initialize-authority --output /private/authority.json
derive-run --input /private/derivation.json --output /private/revision.json
```

The first is authorized exactly once for a new dispatch. The second preserves
authority, budget, class, ceiling, branch, and push target and accepts only a
published source lineage. Neither command authenticates, submits, or allocates.

## Foundation verification

```sh
python3 -m unittest discover -s research/a10/lemhi_toolkit/tests -v
for script in research/a10/lemhi_toolkit/remote/*.sh; do sh -n "$script" || exit; done
```

The fixtures exercise the full lifecycle, live command rendering through a
recording adapter, shared-budget concurrency, response-loss reconciliation,
retries, cancellation, expected nonzero exits, hostile paths and archives,
evidence sanitization, canonical records, and exact-marker cleanup.
