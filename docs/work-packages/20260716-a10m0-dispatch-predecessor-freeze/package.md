# A10M0 — Dispatch and Predecessor Freeze

Status: `EXECUTED-COMPLETE`
Date: 2026-07-16
Evidence mode: Mixed
Terminal: `A10M0-PREDECESSORS-FROZEN`

## Objective

Freeze the accepted A7--A9 authority chain, confirmation firewall, A10
milestone topology, resource ceilings, and execution rules before any A10
remote write or compute submission. Establish the bounded dispatch authority
for A10M2 without reopening predecessor scientific dispositions.

## Scope

Included immutable hashes and status checks for the A10 plan, governing ADRs,
A7/A8/A9 packages, and the A9d report; a replay of A9d's development verifier;
the A10 design, access, and risk freeze; and the A10M1/A10M2 handoff.

Excluded confirmation-series access, new candidate selection, model training,
Slurm submission, remote environment installation, production-code changes,
and reinterpretation of an accepted predecessor terminal.

## Authority

- The files in `artifacts/predecessor-manifest.sha256` are the frozen local
  predecessor authorities at source commit
  `f831d54c2f5c37eb69b27acaa99a3a228a32f7c7`.
- [A10 study plan](../../planning/a10-study-plan.md) and its
  [review](../../planning/a10-study-plan-review.md) define the campaign.
- Accepted predecessor package terminals remain authoritative; a `HOLD` is
  preserved as evidence and is not rewritten as a pass.
- The operator's 2026-07-16 direction authorizes A10M2's frozen five-job,
  one-GPU-hour maximum envelope.

## Plan

1. Identify the exact `origin/main` source and hash the authority set.
2. Hydrate Git LFS evidence and replay the terminal A9d development verifier.
3. Freeze scope, confirmation isolation, access rules, risks, and resource
   ceilings for milestone execution.
4. Review the record, run repository gates, publish to `main`, and hand A10M2
   an immutable accepted predecessor terminal.

## Execution & dispatch

Executed on host `rmm` from `main`, with `origin/main` equal to
`f831d54c2f5c37eb69b27acaa99a3a228a32f7c7` before this package. Push target is
`main`. A10M2 may perform its ordinary remote writes and frozen job submissions
only after this package commit is present on `origin/main`.

## Gates

- all authority hashes are recorded and predecessor statuses agree with their
  package records;
- the A9d verifier passes against hydrated LFS evidence and retains
  `HOLD-A9D-NO-SELECTABLE-CANDIDATE`;
- confirmation target series remain unread;
- the A10M2 resource envelope remains at or below one GPU-hour;
- review has zero open P1/P2 findings;
- `git diff --check`, `cargo fmt --check`,
  `cargo clippy --all-targets -- -D warnings`, and `cargo test` pass; and
- no production function is changed, so coverage/CRAP is not triggered.

## Exit criteria

`EXECUTED-COMPLETE` requires terminal `A10M0-PREDECESSORS-FROZEN`, an immutable
authority manifest, successful predecessor replay, a preserved confirmation
firewall, accepted review, passing gates, and a bounded A10M2 dispatch.

## Result

All exit criteria passed. The A9d development record replayed as 18 fits, 24
staged evaluations, 92 retained and 19 report-only cells per horizon, with the
unchanged no-selectable-candidate terminal. A10M2 is authorized to execute its
frozen five-job matrix after this package is published to `origin/main`.

## Artifacts

- `artifacts/predecessor-manifest.sha256` — immutable authority identities.
- `artifacts/verification.md` — status, LFS, replay, and firewall evidence.
- `artifacts/design-freeze.md` — campaign and resource boundaries.
- `artifacts/risk-access-register.md` — operational and scientific controls.
- `artifacts/execution-dispatch.md` — exact branch and successor authority.
- `artifacts/gate-results.md` and `artifacts/review.md` — closure evidence.
- `artifacts/a10m1-a10m2-handoff.md` — bounded milestone handoff.
