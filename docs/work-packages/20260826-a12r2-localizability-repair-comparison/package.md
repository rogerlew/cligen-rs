# A12R2 — Localizability and Repair Corpus Comparison

Status: `EXECUTED-HOLD-REPAIR-INELIGIBLE`

Date: 2026-08-26

Evidence mode: observed fit-validation; confirmation sealed

Starting branch and push target: current `origin/main`, push `main`

## Objective

Execute the prospective 240-site, 2,400-candidate comparison of raw selected
donors with explicit repair against full-localizability-filtered selector arms,
then make an evidence-bound exploratory recommendation.

## Authority

- [SPEC-A12R2-LOCALIZABILITY-REPAIR-COMPARISON](../../specifications/SPEC-A12R2-LOCALIZABILITY-REPAIR-COMPARISON.md)
- [SPEC-A12R1-LOCALIZABILITY-AWARE-SELECTION](../../specifications/SPEC-A12R1-LOCALIZABILITY-AWARE-SELECTION.md)
- [SPEC-A12-STATION-SELECTION-EVALUATION](../../specifications/SPEC-A12-STATION-SELECTION-EVALUATION.md)

## Plan and gates

1. Authenticate and calendar-preflight the frozen fit-validation inputs.
2. Evaluate ordinary feasibility for all ten candidates at all 240 sites.
3. Score the six frozen strategy-selector arms and execute the production
   repair profile for current-selector parity at every site.
4. Replay evidence and decision byte-identically.
5. Obtain independent GO, run package and repository gates, and reconcile the
   roadmap, specification registry, catalog, and ExecPlan.

No production code changes are planned, so the coverage/CRAP production gate
is not triggered.

## Calendar and missingness preflight

Before feasibility or scoring, authenticate all A10 manifests and Daymet
shards; pin the inclusive 10,958-row axis, 10,950 observed rows, eight masked
leap-year December 31 dates, month masks, transition-chain gap behavior, 240
fit-validation roles, and six equal regime counts. Confirmation objects are
prohibited.

## Execution and dispatch

Execute from the published prospective source commit on `main` with the exact
locked release binary and registered external station archive. The living
[ExecPlan](../../exec-plans/20260826-a12r2-localizability-repair-comparison.md)
contains resumable commands. Independent prospective and closure reviews are
mandatory.

## Required gates

- evaluator synthetic tests and strict manifest validation;
- exactly 240 sites and 2,400 feasibility cells;
- byte-identical evidence and decision replay;
- `cargo fmt --check`;
- `cargo clippy --all-targets -- -D warnings`;
- `cargo test`.

## Artifacts

The package publishes the frozen manifest/schema/evaluator/tests, build
receipt, calendar preflight, complete feasibility evidence, quality evidence
or named failure receipt, decision when scoring is authorized, preserved
first/replay receipts, independent review, and test log.

## Exit

Complete on authenticated feasibility, six-arm evidence, a frozen disposition,
byte-identical replay, all required gates, and independent GO. Stop honestly on
the named feasibility or repair gates without scientific policy inference.

## Prospective amendment boundary

The authenticated parity diagnostic required after first-source evaluator
failure also unsealed a feasibility fact: current raw winners fail the explicit
repair at four sites (indices 56, 57, 63, and 64), all in June. A12R2 is
therefore expected to close on `HOLD-REPAIR-INELIGIBLE`, not reach six-arm
quality scoring. Execution remains necessary to publish the complete 2,400-cell
ordinary-localizability census, all raw-policy repair failures, production
failure parity, and the formal named receipt. The package will not weaken its
prospective gate after observing this result.

## Disposition

`EXECUTED-HOLD-REPAIR-INELIGIBLE` at exact source commit
`866d0401ab757708d80a58ad9dda5683f6e000bc`. The evaluator authenticated all
240 fit-validation sites and all 2,400 nearest-ten candidate cells before
scoring. Of those cells, 2,362 complete ordinary localization; every site has
between 3 and 10 eligible donors. Filtering changes 4 closest winners and 5
winners in each heuristic selector.

The raw repair arms have 11 policy-site failures across four desert sites,
all in June: 3 closest, 4 current, and 4 elevation-reference. Three sites have
zero PRISM June precipitation with all-dry raw donors, outside the positive-
target repair contract. The fourth has positive PRISM precipitation but a
one-sided absorbing source state (`PWW=0.25`, `PWD=0`), also outside the
both-zero repair contract. No quality metric or policy disposition was emitted.
Confirmation access remained false.

First and independent replay calendar preflights are byte-identical at
`e7a042c7e5aed05b15a17a431bc19e7e117cc5f31bae7f56a2cbb16f49b10a36`;
feasibility evidence is byte-identical at
`9523b1a27d09affd755fde1c701ae6b26f7d31be883e054c78b99aee5a84d508`.

Artifacts:

- [calendar preflight](artifacts/calendar-preflight-v1.json)
- [complete feasibility evidence](artifacts/feasibility-evidence-v1.json)
- [failure receipt](artifacts/execution-failure-receipt-v1.json)
- [HOLD replay receipt](artifacts/hold-replay-receipt-v1.json)
- [build receipt](artifacts/build-receipt-v1.json)
- [independent review](artifacts/review.md)
- [test results](artifacts/test-results.md)

## Successor boundary

Do not broaden repair inside this closed package. The least-complex successor
is a new prospective localizability-only quality evaluation of closest,
current rank-sum, and elevation-reference arms on all 240 sites. It can answer
the original selector question without inventing zero-target rainfall or a new
one-sided absorbing-chain repair. A separately frozen repair-generalization
study remains optional.
