# A10M5R3R1 — Evidence and Authority Reconciliation

Status: `EXECUTED-COMPLETE`
Date: 2026-07-18
Evidence mode: Development-only, zero-allocation collection recovery and audit
Starting branch and push target: `main`, push `main`

## Objective

Adjudicate whether the exact successful A10M5R3 `r4` matrix remains valid
scientific evidence after the parent package exceeded its frozen primary-job
count through two failed correction lineages, without rerunning a job,
relaxing a gate, or erasing the parent hold.

## Boundary

This package may read the authenticated A10M5R3 `RAW_COLLECTED` receipt, its
retained private quarantine, and published toolkit receipts. It authorizes one
deterministic local re-projection with the already specified remote-root value
and the projection-v3-valid token `<REMOTE_RUN_ROOT>`, followed by one
marker-bound invocation of the committed `clean.sh` against the exact parent
remote run root. It authorizes no Slurm submission, GPU/CPU allocation, model
refit, new role access, selector change, threshold change, raw evidence edit,
or other remote mutation. The A10M5R3 package, raw hashes, gates, and failed
lineage receipts are immutable inputs.

The audit separates two questions:

1. resource governance: every settled job in every A10M5R3 lineage counts,
   so fresh revision-0 authorities cannot make the original 18-job ceiling
   pass; and
2. scientific admissibility: the independent `r4` lineage may be accepted
   only if it contains exactly the frozen 18 distinct roles, one attempt each,
   the pushed corrected source, the unchanged corpus/roles/selectors, all hard
   gates, complete accounting, and exact cleanup/close.

## Plan

1. Preserve the original package's `HOLD-A10-RESOURCE-BOUND` and reconcile all
   failed and successful lineage receipts.
2. Re-project every raw file through the committed projection-v3 function,
   verify its parent hash against `RAW_COLLECTED`, publish per-file projection
   receipts, and preserve the parent's `SANITIZATION_FAILED` terminal.
3. Invoke committed marker-bound cleanup once with the exact parent plan and
   prove the durable root absent; the parent toolkit run cannot be relabeled
   closed.
4. Replay the family, capacity, and pair selectors solely from recovered `r4`
   evidence and verify its exact 18-role, single-attempt matrix.
5. Prove that failed lineages supplied no row to the accepted selections, no
   protected role opened, and the accepted pair remains under the 10x runtime
   boundary across all three seeds.
6. Publish a zero-allocation disposition and the bounded A10M5R4 handoff; add
   the authority-continuation trap to canonical agent guidance.

## Gates

- A10M5R3 remains an honest resource-bound hold; this package does not amend
  its ceiling or retroactively bless fresh authority IDs;
- all lineage receipts and cumulative actual/rounded GPU use reconcile;
- accepted `r4` has exactly 18 registered roles, attempt zero once each, all
  passed, and source commit `47963a9`;
- every recovered file matches its authenticated raw parent hash, uses the
  unchanged projection-v3 implementation, passes the original forbidden-value
  scan, and records the corrected token only as an operational projection;
- collected rows replay the committed family and capacity selectors exactly;
- the retained two capacities each pass all hard gates, seed NLL stability,
  and the 10x runtime fail boundary across all three seeds;
- development-selection and confirmation remain unopened;
- job-local cleanup and marker-bound durable cleanup pass; the original
  `SANITIZATION_FAILED` and inability to toolkit-close remain explicit;
- no allocation and no remote mutation other than exact durable cleanup occurs
  in this package; and
- Python/JSON parse, `git diff --check`, `cargo fmt --check`,
  `cargo clippy --all-targets -- -D warnings`, and `cargo test` pass.

## Exit

`A10M5R3R1-CAPACITY-PAIR-READY` accepts the `r4` family and neighboring
capacity pair only as inputs to A10M5R4 temporal adjudication. It makes no
final architecture, spatial, confirmation, or promotion claim. Any scientific
row mismatch yields `HOLD-A10-NO-CAPACITY-PAIR`; incomplete cleanup or receipt
reconciliation yields the exact toolkit terminal.

## Terminal result

`A10M5R3R1-CAPACITY-PAIR-READY`

The audit preserved A10M5R3's `HOLD-A10-RESOURCE-BOUND` and independently
accepted only the corrected `r4` evidence. All 239 raw files matched the
authenticated `RAW_COLLECTED` receipt and re-projected through unchanged
projection v3 with the grammar-correct token. The committed marker-bound
cleaner removed the exact durable root and an independent probe confirmed it
absent. The parent toolkit run remains explicitly unclosed.

The frozen selectors replayed exactly: `lognormal_wet_v2` won the family
screen; P1 (87,295 parameters) is the knee and P2 (276,927 parameters) its
larger neighbor. Both are stable across seeds 147031, 271828, and 314159 and
remain below the 10x runtime failure boundary. This result authorizes A10M5R4
realized temporal-dispersion adjudication only.
