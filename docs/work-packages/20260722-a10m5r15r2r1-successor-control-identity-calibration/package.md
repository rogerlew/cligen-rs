# A10M5R15R2R1 — Successor Control-Identity Calibration

Status: `SCAFFOLDED`
Date: 2026-07-22
Evidence mode: Mixed
Starting branch and push target: current `main`, push `main`

## Objective

Capture the exact six-model control identity produced by the frozen R14
trainer on the A10M5R15R1 successor corpus, before any R15 candidate output.
A10M5R15R2 correctly failed closed because it compared the successor-corpus
checkpoint to an identity generated on the predecessor corpus.

## Scope

One 30-minute, one-L40 control-only toolkit run plus the existing five-minute
marker-bound recovery reserve. The job trains the unchanged P1/P2 control
matrix for seeds 147031, 271828, and 314159; validates all static model,
calendar, corpus, optimizer, and role identities; records every dynamic
checkpoint/export/metric identity; and emits no R15 candidate stream. The
portfolio, runtime benchmark, selector, confirmation, solar, spatial, and
production roles are excluded.

## Authority

The ratified revision-2 `SPEC-A10-EXTERNAL-NORMAL-CONDITIONING` contract and
the A10M5R15R1 corpus are unchanged. This package is a candidate-blind
development calibration. It does not weaken exact reconstruction: its output
becomes a prospective pin that a separately published execution package must
reconstruct byte-for-byte before candidate release.

## Plan

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
- collected control identity, receipts, and terminal accounting after run.
