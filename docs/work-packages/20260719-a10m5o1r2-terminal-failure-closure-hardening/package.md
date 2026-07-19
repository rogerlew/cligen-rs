# A10M5O1R2 — Terminal Failure Closure Hardening

Status: `EXECUTED-COMPLETE`
Date: 2026-07-19
Evidence mode: Local injected fixtures and shell fixtures; no allocation
Starting branch and push target: current `main`, push `main`

## Objective

Revise the Lemhi toolkit so a run with an exhausted failed upstream role can
honestly settle never-submitted dependent roles, collect the evidence that
actually exists, prove cleanup, and close without submitting doomed work or
fabricating missing job/admission records.

## Trigger evidence

A10M5R10R1 control job `1014042` failed before runtime extraction. The toolkit
had no post-submission abort or dependent-role settlement operation, so ten
known-doomed roles had to be submitted only to exhaust the frozen matrix.
Afterward, `pack_evidence.sh` treated the evidence allowlist as a mandatory
file manifest and failed because rejected roles correctly lacked PASS-only
admission receipts. The exact root required owner-bound manual cleanup.

## Frozen change

- Add one v2-only `stop-matrix` command. It requires an exact exhausted failed
  trigger role, every existing attempt settled, whole-authority
  scheduler/ledger reconciliation, the fixed `upstream-role-exhausted` reason,
  and an atomic self-authenticating matrix-stop receipt.
- Settle all remaining zero-attempt roles together as
  `NOT_EXECUTED_UPSTREAM_FAILURE`. They are not attempts, do not consume
  resources, do not become job receipts, and cannot be selectively skipped or
  silently restored within the run.
- Treat `evidence_allowlist` as the maximum permitted set. Remote collection
  includes only present regular nonsymlink members, requires at least one
  member, and retains all existing archive/extraction allowlist checks.
- During v2 cleanup, require job-local cleanup evidence for submitted roles
  and skip only the authenticated never-submitted stopped roles. Exact durable-root
  marker validation and deletion remain unchanged.
- Require every submitted attempt and any invoked recovery to contribute its
  authenticated gate receipt and Slurm streams to sparse collection. Bind
  recovery gates into `RAW_COLLECTED` and reject missing or changed receipts.
- Globally reject duplicate Slurm-stream ownership and any planned or recovery
  gate path that aliases a planned or recovery stream. The frozen recovery
  contingency is immutable across amendments.
- Add an optional stopped-role count to the terminal receipt. Historical
  receipts and state remain immutable.

## Gates

- Positive fixture: failed exhausted trigger plus stopped dependents reaches
  `MATRIX_SETTLED`, collects, cleans, and closes without a dependent ledger or
  scheduler entry.
- Adverse fixtures reject stop before trigger exhaustion, any unsettled or
  retry-eligible attempt, duplicate stop, unknown triggers/reasons, and
  scheduler/ledger divergence.
- Shell fixtures prove missing allowlisted members are omitted, present
  regular members are archived, an empty present set fails, and a present
  symlink is rejected.
- Existing toolkit acceptance and hardening suites pass unchanged.
- `git diff --check`, `cargo fmt --check`,
  `cargo clippy --all-targets -- -D warnings`, and `cargo test` pass.

Coverage/CRAP is not triggered because no production function under `crates/`
changes.

## Exit criteria

`A10M5O1R2-TERMINAL-FAILURE-CLOSURE-READY` requires passing positive and
adverse fixtures, an independent review with no unresolved finding, updated
authoritative toolkit specification, and complete disposition/gate artifacts.
Otherwise the package records an exact HOLD and the prior manual closure
remains the only valid A10M5R10R1 terminal evidence.

## Artifacts

- `artifacts/gate-results.md` — exact validation commands and results;
- `artifacts/review.md` — independent and executor review;
- `artifacts/execution-disposition.md` — terminal and successor impact.

## Disposition

Reached `A10M5O1R2-TERMINAL-FAILURE-CLOSURE-READY`. The final independent
review approved the atomic whole-matrix stop, sparse evidence contract,
recovery evidence closure, global evidence-path ownership, idempotent receipt
republication, and cleanup behavior with no unresolved finding. All 79 toolkit
tests, shell syntax, repository checks, and Rust gates pass. No allocation was
opened and the historical A10M5R10R1 evidence was not rewritten.
