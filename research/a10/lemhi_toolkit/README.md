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
   root or reset the budget. Revision-1 examples remain historical fixtures.
4. Create a private plan from `examples/plan.example.json`. The target is
   Linux x86-64 glibc even though dependency resolution is controlled from
   macOS arm64. Every local asset path must be absolute, regular, singly linked,
   and beneath an authority allowlist root.
5. A live revision-2 authority owns its absolute mode-restricted ledger anchor;
   the CLI rejects `--state-root`. Fixture adapters may inject a temporary
   root. Private state survives exact reconciliation and cleanup.

The first live consumer is the separately dispatched CPython 3.11 smoke
package. Foundation acceptance itself uses no VPN, remote write, Slurm job, or
GPU allocation.

## Canonical A10 configuration

The current default for A10 single-L40 Python consumers is the versioned
[`lemhi-a10-py311-l40-v1`](configurations/lemhi-a10-py311-l40-v1.json)
record, governed by
[`SPEC-LEMHI-CANONICAL-CONFIGURATION`](../../../docs/specifications/SPEC-LEMHI-CANONICAL-CONFIGURATION.md).
Revision 1 is immutable status-at-issuance history. A10M4O1 publishes an
immutable revision-2 semantic candidate, but it is not current until a
separately dispatched smoke emits a passing attestation and a later
designation-index revision advances the pointer. Python 3.8 remains legacy
explicit-only.

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
observe --job-role smoke --attempt-index 0
collect
clean
close
```

`cancel` takes the same role and attempt arguments and resolves only the exact
registered job ID. `amend --input ... --reason ... --changed-field jobs`
creates a prospective revision; it cannot mutate a started role, immutable
asset, remote root, authority, confirmation classification, or resource
ledger. A failed or ambiguous submission must be reconciled from retained
private state, never retried by inventing another run or plan.

The committed profile selects an ordered SCP, Slurm, Ceph, and L40 provider
stack. Definitions are declarative JSON and content-hashed into every plan.
Adding a runtime or framework means adding a versioned provider record and an
explicit plan amendment or new plan; provider failure is not a fallback signal.

Revision-2 plans use `lemhi-v2.json`, an all-v2 provider stack including the
toolchain provider, `toolkit_recoverable` storage, `--export=NONE` environment
closure, a frozen recovery contingency, typed raw-evidence projection, integer
transfer telemetry, and append-only content-addressed manifests. Useful
operator-facing commands are:

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
