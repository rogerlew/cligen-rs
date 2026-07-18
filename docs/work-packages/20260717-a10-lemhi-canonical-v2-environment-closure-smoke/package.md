# A10 Lemhi canonical v2 environment-closure smoke

Status: `SCAFFOLDED`
Date: 2026-07-17
Evidence mode: Live
Starting branch and push target: current `origin/main`, push `main`

## Objective

Run the unchanged canonical-v2 candidate at semantic SHA-256
`5addee9c5db3592ee247eab2b5266ed5567fd9aaf24ed78dcb321ecbb001e22d`
on one Lemhi L40 after correcting the environment-entry protocol exposed by
the predecessor hold. Validate the hardened toolkit mechanics that bind
executable intent, preserve a gate receipt on failure, and cleanly abort a
staged run before submission.

## Predecessor evidence and hypotheses

The predecessor package stopped before Python import because one or more of
`PYTHONPATH`, `PYTHONHOME`, and `LD_LIBRARY_PATH` was present despite Slurm
`--export=NONE`. The candidate itself was not tested. This successor freezes:

1. Lemhi's site launch path may export one or more prohibited variables after
   Slurm applies `--export=NONE`.
2. Presence at entry is operational evidence, not candidate failure. Recording
   typed presence flags, clearing the variables, reconstructing the allowlisted
   environment, and asserting closure before import is sufficient.
3. Executable intent belongs in the asset contract rather than an operator
   side check.
4. A catchable failure must still produce the exact registered gate receipt so
   observation can classify the failed gate instead of losing evidence.

No ambient value, unrestricted environment, private path, endpoint, or
identity may enter publication.

## Scope and authority

The operator's instruction to run a successor authorizes VPN/warm-master use,
exact staging, one primary `gpu-icrews` allocation, conditional exact-node
recovery, evidence collection, and exact cleanup. It authorizes repository
documentation and toolkit changes needed to close the demonstrated protocol
gaps. It does not authorize A10M5, administrator changes, direct compute-node
SSH, confirmation-target access, or mutation of the candidate or canonical v1.

Agents have authoring authority for this package's repository artifacts and
ordinary reversible toolkit corrections within these boundaries.

## Frozen resources

- primary: one `gpu:l40:1`, 4 CPUs, 16,384 MiB, 15-minute limit;
- recovery: at most one exact-node `gpu:l40:1`, 2 CPUs, 1,024 MiB, 5-minute
  limit, only for authenticated `CLEANUP_INCOMPLETE`;
- cumulative requested ceiling: 20 L40-GPU-minutes;
- one concurrent allocation, one primary attempt, no retry or requeue; and
- unchanged seven-provider v2 candidate stack.

## Plan

1. Harden and fixture-test executable verification, terminal failure receipts,
   and exact pre-submission abort.
2. Publish the complete source authority before constructing the private live
   authority and content-addressed source archive.
3. Verify candidate/provider/assets locally, stage, and verify hashes, byte
   counts, and all required executable modes remotely.
4. Run one primary job from `--export=NONE`; record entry presence flags, clear
   prohibited variables, assert reconstructed closure, then execute the full
   Python/CUDA/Rust/supervisor smoke.
5. Observe the authenticated gate receipt, collect only the evidence allowlist,
   prove durable and job-local absence, settle scheduler/ledger records, and
   close the toolkit run.
6. On pass, emit an immutable smoke attestation binding the candidate hash. On
   any failed or unavailable gate, record a hold and emit no attestation.

## Gates

- `python3 -m unittest discover -s research/a10/lemhi_toolkit/tests -v`
- all remote shell scripts pass `sh -n`
- `cargo fmt --check`
- `cargo clippy --all-targets -- -D warnings`
- `cargo test`
- candidate/profile/provider and exact live-input identity verification
- toolkit remote verify, observe, collect, clean, and close receipts
- scheduler queue/accounting reconciliation and 20-minute ledger ceiling

## Exit criteria

`A10-LEMHI-CANONICAL-V2-SMOKE-READY` requires every registered gate, exact
cleanup, settled accounting, and an immutable
`lemhi-canonical-smoke-attestation-1`. The attestation does not designate the
candidate current; designation remains a separate local revision.

Any failed gate, missing gate receipt, ambiguous allocation, cleanup
uncertainty, identity drift, or ceiling issue yields a specific hold and no
attestation or designation.

## Artifacts

- `artifacts/jobs/` — exact compute scripts;
- `artifacts/evidence/` — sanitized live receipts and accounting summaries;
- `artifacts/execution.md` — command/evidence narrative;
- `artifacts/gate-results.md` — final gate matrix; and
- `artifacts/terminal.md` — terminal disposition.
