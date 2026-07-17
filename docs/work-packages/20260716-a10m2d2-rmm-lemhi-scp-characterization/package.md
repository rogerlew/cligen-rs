# A10M2D2 — rmm-to-Lemhi SCP Transfer Characterization

Status: `EXECUTED-COMPLETE`
Date: 2026-07-16
Evidence mode: Mixed
Scaffolding authorization: operator direction on 2026-07-16 from clean
`main` at `7e76c1a5689750252f38162b057bab7742e0d935`, targeting `main`
Execution authorization: operator direction on 2026-07-16 from published
`main` at `5d8abbe61df810d4a11dc4ab92fa686214be25a1`, targeting `main`
Terminal: `A10M2D2-SCP-EXPECTATIONS-FROZEN`

## Objective

Characterize the warm, MFA-bootstrapped SCP path from the `rmm` macOS control
host through the University of Idaho VPN and `login-ui` jump host to Lemhi's
durable Ceph home storage. Establish integrity, latency, sustained throughput,
small-file overhead, archive benefit, and SSH compression behavior so A10 can
translate artifact sizes into realistic operator-supervised transfer times.

This package is stage 1 only. It consumes no Slurm or GPU resource. The
Ceph-to-compute-local stage is a separate future M2 readiness gate that must
share the next authorized GPU-bearing integration allocation.

## Scope

Included:

- verify `rmm`, VPN-reachable warm SSH masters, agent-safe `BatchMode=yes`
  transport, OpenSSH identity, Ceph capacity, and an empty unique remote run;
- generate disposable synthetic random and compressible fixtures without
  loading a large fixture into memory;
- measure ten zero-payload warm SSH commands;
- measure bidirectional 16 MiB, 256 MiB, and 1 GiB single-file SCP;
- compare 1,024 64-KiB files transferred recursively with the same content in
  one tar archive;
- compare default SCP with `scp -C` for 64-MiB incompressible and compressible
  fixtures;
- deliberately interrupt one rate-limited SCP upload, characterize its partial
  remote-file semantics, and remove or resume only that exact partial;
- inventory local/remote rsync and Globus CLI visibility; when compatible
  rsync is present on both ends, test `--partial --append-verify` recovery of
  the interrupted object inside the same byte ceiling;
- record sanitized live capacity/quota visibility and identify which retention
  claims remain administrator-dependent;
- verify every uploaded and downloaded object with SHA-256;
- report exact bytes, elapsed seconds, effective MiB/s, repeat variability,
  projected 1/10/50/100-GiB durations, observed limitations, and an operational
  recommendation;
- retain sanitized dispatch, timing, integrity, capacity, cleanup, review,
  and terminal evidence; and
- remove all local fixtures and the exact remote run after verified evidence
  retrieval.

Excluded:

- Slurm, GPU allocation, direct compute-node SSH, Ceph-to-node-local staging,
  checkpoint copy-back, or training I/O;
- scientific data, A10 shards, LFS objects, private data, or credentials as
  transfer fixtures;
- concurrent transfers, denial/load testing, cold-MFA timing, cipher tuning,
  legacy SCP protocol forcing, or network configuration changes;
- performance claims beyond the observed `rmm`/VPN/time window;
- framework/environment selection, package installation, production Rust
  changes, or confirmation-series access; and
- usernames, absolute user paths, key material, control sockets, passwords,
  Duo material, or unrestricted environments in committed evidence.

## Authority

- [Lemhi GPU computing for agents](../../c3-lemhi-gpu-computing-for-agents.md)
  defines the human bootstrap, agent transport, sanitization, and cleanup
  boundary.
- [A10M2 live inventory](../20260716-a10m2-lemhi-gpu-integration/artifacts/inventory-live.md)
  establishes the reachable Ceph-backed Lemhi home and warm transport.
- [A10M2D1 cleanup](../20260716-a10m2d1-lemhi-cuda-drift-diagnostic/artifacts/cleanup.md)
  establishes exact remote-run cleanup practice.
- [A10 data staging](../../planning/a10-study-plan.md#86-data-staging)
  requires verified durable transfer before node-local staging.

## Frozen transfer envelope

- Conservatively accounted logical payload across all registered transfer
  cells must not exceed 5 GiB (`5,368,709,120` bytes), counting each upload,
  download, intentional partial source, and conditional rsync source.
- Expected SCP baseline payload is about 4.35 GiB and the full conditional
  matrix is about 4.85 GiB; archive headers remain inside the hard ceiling.
- Peak remote retained fixture data must remain below 2 GiB.
- Each individual command has a 30-minute timeout; the whole supervised run
  should stop after two hours rather than silently expand.
- There is no automatic matrix rerun. A transport failure closes or amends the
  package from retained evidence; it does not double network use implicitly.
- No Slurm allocation, GPU-minute, external dataset, or paid service is
  authorized.

## Plan

1. Freeze the source commit, matrix, exact byte accounting, integrity rules,
   timeout, sanitization, and cleanup targets before remote write.
2. Require the operator's active UI VPN and supervised `login-ui`/`lemhi`
   control masters. Verify both with `ssh -O check`, then prove one bounded
   `BatchMode=yes` command. Stop for human bootstrap if either master is absent.
3. Confirm clean `main`, record safe `rmm`/OpenSSH facts, verify remote
   `sha256sum` and Ceph capacity, and create one commit-derived relative remote
   run directory only if it does not already exist.
4. Generate the disposable fixture family in a validated `mktemp` directory;
   freeze local sizes and hashes.
5. Execute the frozen latency, single-file, small-file/archive, and compression
   matrix sequentially. Record a status for every command and verify hashes
   immediately after every upload/download.
6. Enforce the 5-GiB logical-byte ceiling, retrieve all compact results,
   compute summary statistics and transfer-time projections, and distinguish
   payload throughput from protocol/storage/caching effects.
7. Remove the exact remote run and validated local temporary directory; prove
   remote absence. Review, run repository gates, update the stage-2 handoff,
   reconcile roadmap/catalog state, and close with one terminal.

## Execution & dispatch

Scaffolded on `main` at
`7e76c1a5689750252f38162b057bab7742e0d935` and dispatched from published
`main` at `5d8abbe61df810d4a11dc4ab92fa686214be25a1`; push target is `main`.
The operator supplied only VPN connectivity and interactive MFA bootstrap.
Agents did not receive or automate password/Duo material.

The frozen one-pass driver completed on 2026-07-16 with 5,206,187,008 logical
bytes, 27 passing registered integrity verdicts, one expected timeout, verified
rsync recovery, zero Slurm/GPU use, and exact local/remote cleanup. Results and
limitations are in `artifacts/execution/summary.md` and the terminal record.

## Gates

- local source is clean published `main` and both SSH masters are live before
  remote write;
- `BatchMode=yes` succeeds and no command can fall back to credential prompts;
- fixture sizes and hashes are frozen before transfer;
- all frozen matrix cells run once and have explicit timing/status evidence,
  or a conditional alternative's unavailability is proven;
- logical transferred payload is at most 5 GiB and peak remote retained data
  is below 2 GiB;
- every completed upload and download verifies by SHA-256, with zero
  unexplained mismatch; the intentional partial is identified by bounded size
  and expected noncompletion rather than misclassified as corruption;
- results report MiB/s and exact elapsed time, not SCP progress-bar estimates;
- projections use observed 1-GiB direction-specific rates and are labeled as
  linear planning estimates, not guarantees;
- small-file and archive results use identical logical content;
- compression conclusions separate compressible from incompressible content;
- no Slurm/GPU resource is used and no cold authentication is attempted;
- exact local/remote cleanup passes, with no fixture retained;
- committed evidence passes the sensitive-data scan and review has zero open
  P1/P2 findings;
- `bash -n`, Python bytecode compilation, `git diff --check`,
  `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, and
  `cargo test` pass; and
- coverage/CRAP is not triggered because no production function changes.

## Exit criteria

`EXECUTED-COMPLETE` requires terminal `A10M2D2-SCP-EXPECTATIONS-FROZEN`: all
integrity gates pass, the matrix yields usable direction-specific rates and
small-file guidance, cleanup passes, and the report states reasonable
operator-supervised SCP size/time expectations plus the threshold for testing
an alternative transport.

Legitimate holds are:

- `EXECUTED-HOLD-SSH-BOOTSTRAP` — operator bootstrap cannot provide a stable
  warm noninteractive path;
- `EXECUTED-HOLD-TRANSFER-INTEGRITY` — any payload hash mismatch remains
  unexplained;
- `EXECUTED-HOLD-TRANSFER-STABILITY` — the frozen matrix cannot complete
  within its per-command/two-hour bounds;
- `EXECUTED-HOLD-CAPACITY` — safe local or remote temporary capacity is below
  the frozen envelope; or
- `EXECUTED-HOLD-CLEANUP` — the exact fixture/run cleanup cannot be proven.

## Artifacts

- `artifacts/design-freeze.md` — transfer, safety, and resource freeze.
- `artifacts/test-matrix.md` — exact stage-1 matrix and byte budget.
- `artifacts/analysis-contract.md` — statistics, projections, and decisions.
- `artifacts/additional-investigations.md` — included and deferred follow-up.
- `artifacts/stage2-roadmap-handoff.md` — future shared-allocation M2 gate.
- `artifacts/jobs/measure_command.py` — monotonic command timer.
- `artifacts/jobs/run_stage1.sh` — bounded `rmm` orchestrator.
- `artifacts/execution/` — sanitized raw evidence, analysis, review, gates, and
  terminal disposition.
- `artifacts/README.md` — execution artifact registry.
- `kickoff-prompt.md` — bounded execution dispatch template.
