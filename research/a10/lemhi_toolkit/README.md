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
3. Copy `examples/authority.example.json` outside the repository, replace its
   values with the dispatched package identity and exact source commit, and
   allowlist only the individual local roots needed by that package.
4. Create a private plan from `examples/plan.example.json`. The target is
   Linux x86-64 glibc even though dependency resolution is controlled from
   macOS arm64. Every local asset path must be absolute, regular, singly linked,
   and beneath an authority allowlist root.
5. Put `--state-root` outside the repository in a mode-restricted location.
   Private state must survive through exact reconciliation and cleanup. `close`
   removes it after sanitized publication receipts are durable.

The first live consumer is the separately dispatched CPython 3.11 smoke
package. Foundation acceptance itself uses no VPN, remote write, Slurm job, or
GPU allocation.

## Canonical A10 configuration

The current default for A10 single-L40 Python consumers is the versioned
[`lemhi-a10-py311-l40-v1`](configurations/lemhi-a10-py311-l40-v1.json)
record, governed by
[`SPEC-LEMHI-CANONICAL-CONFIGURATION`](../../../docs/specifications/SPEC-LEMHI-CANONICAL-CONFIGURATION.md).
Consumers bind both its ID and semantic SHA-256. Provider, artifact,
scheduler, storage, or isolation drift fails closed and requires a new
versioned record plus a fresh smoke; Python 3.8 is legacy explicit-only.

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

## Foundation verification

```sh
python3 -m unittest discover -s research/a10/lemhi_toolkit/tests -v
for script in research/a10/lemhi_toolkit/remote/*.sh; do sh -n "$script" || exit; done
```

The fixtures exercise the full lifecycle, live command rendering through a
recording adapter, shared-budget concurrency, response-loss reconciliation,
retries, cancellation, expected nonzero exits, hostile paths and archives,
evidence sanitization, canonical records, and exact-marker cleanup.
