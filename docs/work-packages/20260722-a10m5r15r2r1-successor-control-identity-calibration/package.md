# A10M5R15R2R1 — Successor Control-Identity Calibration

Status: `A10M5R15R2R1-SUCCESSOR-CONTROL-IDENTITY-READY`
Date: 2026-07-22
Evidence mode: Mixed
Starting branch and push target: current `main`, push `main`

## Objective

Capture the exact six-model control identity produced by the frozen R14
trainer on the A10M5R15R1 successor corpus, before any R15 candidate output.
A10M5R15R2 correctly failed closed because it compared the successor-corpus
checkpoint to an identity generated on the predecessor corpus.

## Scope

One 30-minute, one-L40 control-only toolkit run plus a fresh canonical
five-minute marker-bound recovery reserve. The job trains the unchanged P1/P2
control matrix for seeds 147031, 271828, and 314159; validates all static model,
calendar, corpus, optimizer, and role identities; records every dynamic
checkpoint/export/metric identity; and emits no R15 candidate stream. The
portfolio, runtime benchmark, selector, confirmation, solar, spatial, and
production roles are excluded.

## Authority

The ratified revision-2 `SPEC-A10-EXTERNAL-NORMAL-CONDITIONING` contract and
the A10M5R15R1 corpus are unchanged. This package is a candidate-blind
development calibration. It does not weaken exact reconstruction: its output
becomes a prospective pin that a separately published execution package must
reproduce checkpoint-payload and semantic identity before candidate release.

## Plan

Run `r0` was aborted before staging or allocation after the toolkit rejected
hardlinked local cache assets. Its authenticated abort receipt is retained at
`artifacts/execution-r0-abort.json`. Run `r1` replaces those aliases with
link-isolated copy-on-write clones while preserving every asset byte identity.
It was staged and then aborted with zero allocation so the review-requested
full abort authentication could be incorporated prospectively. Run `r2` bound
both authenticated aborts and was the first execution attempt. The compact zero-attempt,
zero-GPU diagnostic is `artifacts/pre-submission-diagnostics.json`.

Run `r2` was manually canceled during a live progress audit after 519 seconds.
That cancellation was premature: its first model completed by 445 seconds,
its second family began by 475 seconds, and the same six-model loop previously
completed on node03 in 893 seconds. The original 30-minute limit therefore
remains empirically sufficient. The canceled run has no scientific result.
It also exposed that the live adapter incorrectly required a scientific gate
from a scheduler-canceled job. This package corrects that closure path:
canceled jobs settle from terminal scheduler accounting without a nonexistent
gate and remain scientifically failed.

Because cancellation can prevent the gate finalizer from publishing its
recovery target, the retained setup and collection receipts bind a narrow
post-collection recovery registration. The recovery target must be derived
exactly from the frozen job script, and exact-node recovery now treats an
already-absent target as authenticated success while retaining full marker,
UID, device, canonical-path, and immediate-revalidation checks before any
deletion of a present target.

Run `r2` is closed as canceled/no-science. Its externally authenticated
cleanup registration is `31bec9a326c1cfe7b177f9c5fcd76c557c23b551202e94f2a051651c3a3ba439`,
its cleanup receipt is
`465575ced925b3ef47796f7552fd0227b6cc70787a5d8655bd8a9470a889b147`,
and its terminal receipt is
`d8eacd70925416ac6b628c6b023eb9f062ea2f56f7c8af70ef7298338b6d037c`.
The unused recovery reserve was released. Fresh execution is run
`a10m5r15r2r1-successor-control-identity-calibration-r3` under a new
35-minute authority; no r2 root, authority, or staged asset is reused.

The operator-authorized outer campaign ceiling is 597 L40-minutes; it is not
an additional reserve. Before release of r2's unused recovery reserve, the
bounded maximum is 573 = 8 prior R2 execution + 9 canceled calibration + 1
out-of-band corrective cleanup + 5 outstanding r2 recovery + 35 fresh
calibration + 515 later study execution. After authenticated cleanup releases
the 5-minute r2 reserve, the bounded maximum is 568. Fresh r3 calibration remains
30 science minutes plus one 5-minute recovery contingency.

Run r3 completed in 20 billed L40-minutes. Its cleanup authenticated remote
and job-local absence and released the unused five-minute recovery reserve.
The realized campaign total is now 38 minutes, so the remaining 515-minute
study yields a bounded campaign maximum of 553 under the 597-minute outer cap.

1. Authenticate the closed A10M5R15R2 failure, R1 corpus/calendar identities,
   R2 assets, source commit, and sealed-role state.
2. Overlay a control-calibration producer that retains the frozen trainer and
   verifies immutable control fields while recording corpus-dependent fields.
3. Publish a control-only semantic plan with a 35 L40-minute ceiling, one
   attempt, exact composed admission, and no candidate role.
4. Run doctor, probe, plan, prepare, stage, verify, admission, control, observe,
   collect, cleanup, and close under fresh authority.
5. Authenticate all six identities and scaffold the exact-reconstruction
   execution successor. Any incomplete, nondeterministic, or malformed row
   closes this package on hold without candidate output.

## Data calendar and missingness preflight

The exact R2 `daymet_official_365_v1` preflight is inherited: 10,958 normalized
calendar rows, 10,950 core/physics observations, 1,200 candidate-fit and 240
fit-validation points, and the 1980-01-01 through 1988-01-01 exclusive fixture
with 2,922 calendar and 2,920 observed rows. Eligibility requires at least 28
mask-present rows in every point/year/month cell. The staged preflight must
remain byte-bound to corpus SHA-256
`7b41e497d215c85ae734dea438424f23ae01cff59a3b3ba55ec32442578553f2`.

## Execution & dispatch

Execute from `/Users/roger/src/cligen-rs`, current published `main`, push
`main`. Fresh package-private assets, state, authority, run, admission, and
remote roots are mandatory. No R2 root or authority is reused.

## Gates

- exact R2 terminal/failure and R1 evidence identities;
- exact staged manifest and corpus/calendar preflight;
- six unique P1/P2 × three-seed control rows;
- immutable field agreement for capacity, family, hidden size, parameter
  count, row ID, and seed;
- authenticated dynamic checkpoint, export, record, cursor, and validation
  identities for every row;
- no candidate or protected role and at most 35 L40-minutes;
- `cargo fmt --check`;
- `cargo clippy --all-targets -- -D warnings`;
- `cargo test`.

## Exit criteria

Success is `A10M5R15R2R1-SUCCESSOR-CONTROL-IDENTITY-READY` with six complete
authenticated rows and closed accounting. Failure is
`EXECUTED-HOLD-SUCCESSOR-CONTROL-CALIBRATION-<REASON>`. No result from this
package is candidate evidence.

## Artifacts

- `artifacts/control-calibration-contract.json` — frozen calibration boundary;
- `artifacts/jobs/` — asset, authority, admission, and control producers;
- `artifacts/successor-control-identity.json` and
  `artifacts/successor-control-summary.json` — six authenticated identities;
- `artifacts/execution-r3-*.json` — job, collection, cleanup, terminal, and
  recovery-release accounting.
