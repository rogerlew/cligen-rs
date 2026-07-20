# A10M5R12R2 — Collection Ceiling Reconciliation

Status: `SCAFFOLDED`
Date: 2026-07-20
Evidence mode: Development-only, zero-allocation collection recovery
Starting branch and push target: current `main`, push `main`

## Objective

Recover and adjudicate the exact successful A10M5R12R1 continuous-process
evidence after controller collection failed closed solely because its two
retained stream archives exceeded the frozen generic evidence-volume ceilings.

## Boundary

This successor may read the parent private state, plan, ledger, quarantined
archive, published job receipts, and exact remote archive/owner marker. It may
validate and project that evidence under successor-only ceilings of 51 files,
50,000,000 bytes per file, and 100,000,000 expanded bytes; replay the frozen
temporal selector; and, only after successful recovery and replay, invoke the
committed marker-bound cleaner against the exact parent remote root.

It authorizes no Slurm submission, GPU or CPU allocation, model fit, stream
regeneration, plan amendment, parent-state edit, threshold change, candidate
change, solar access, or confirmation access. A10M5R12R1 remains
`MATRIX_SETTLED`, toolkit-unclosed, and terminally
`HOLD-A10M5R12R1-COLLECTION-CAPACITY`; R2 owns the recovery and scientific
disposition.

## Frozen parent facts

- source commit: `87d38996e1f46ddb47b80c16c9625c16beaede9b`;
- plan: `39a7f91c1da86964210027a10487aae150de82c9f377a634b7917d9485d1d8a7`;
- profile: `d124cebc18e1035ec81991d5fc8f5b59736729ad32c57c1900ec770149656ba6`;
- private state SHA-256:
  `be4a20d39dc7280e091311698b6e014612753816dc661325ebe0787379d09af6`;
- archive: 96,491,520 bytes, SHA-256
  `4c5d2ebcdbf96fa8fe75ab971a163d2a3155c4fbb7ca6fb7e852278eafbf4abf`;
- 51 exact allowlisted regular root-owned members, 96,443,290 expanded
  bytes, largest member 45,772,878 bytes;
- jobs `1016088`, `1016103`, and `1016104` passed every registered gate and
  charged 16, 34, and 49 GPU-minutes respectively; and
- owner marker SHA-256
  `28b9254445a3f9350b6f87b922bb0ab4e9c8018801d3025e74826392aa55d017`.

## Plan

1. Freeze the parent operational hold and the exact archive/state/plan/profile,
   authority, ledger, marker, job-receipt, and gate identities.
2. Verify the local and remote archives match; reject unsafe paths, nonregular
   members, links, non-root ownership, set-id bits, unexpected members, or
   successor ceiling violations.
3. Authenticate all parent attempts and create a successor-owned
   `RAW_COLLECTED`-equivalent record without inserting anything into parent
   state.
4. Project all 51 members through unchanged projection v5. `.npz` and `.pt`
   remain exact bytes and still receive the forbidden-byte scan.
5. Replay the unchanged source/receipt-bound selector twice from recovered
   evidence and require byte identity.
6. After recovery and replay pass, invoke source-87d3899 `clean.sh` against the
   exact parent marker and independently prove the durable root absent.
7. Publish the parent hold, R2 science disposition, cleanup receipt, resource
   reconciliation, and prospective toolkit hardening.

## Gates

- exact parent state/plan/profile/source/archive/marker and three job receipts;
- 51/51 allowlist equality and exact archive statistics;
- all submission, setup, calendar, science, support, and job-local cleanup
  gates true;
- exactly 99 charged GPU-minutes and no R2 allocation;
- exact-byte binary projection and authenticated raw-parent manifests;
- byte-identical temporal replay using the frozen A10M5R12 selector;
- parent private-state hash unchanged before and after cleanup;
- committed marker-bound cleanup and independent `REMOTE_ABSENT` proof;
- solar and confirmation sealed;
- `cargo fmt --check`;
- `cargo clippy --all-targets -- -D warnings`; and
- `cargo test`.

Coverage/CRAP does not apply because no production function under `crates/`
changes.

## Exit

Recovered evidence receives the exact inherited A10M5R12 temporal terminal.
An eligible candidate still requires random-origin rolling-window sensitivity
before promotion because calendar bins remain the frozen loss estimand. Any
identity, projection, replay, cleanup, or state-continuity failure holds R2
without remote cleanup. The parent toolkit run is never relabeled closed.
