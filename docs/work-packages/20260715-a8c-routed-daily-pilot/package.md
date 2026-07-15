# A8c — Bounded Explicit-Routing Daily Precipitation Pilot

Status: `EXECUTED-COMPLETE`
Date: 2026-07-15
Evidence mode: Mixed
Execution authorization: operator authorized scaffolding and execution on
2026-07-15

## Objective

Implement and evaluate the one A8a-authorized integrated daily precipitation
mechanism behind an explicit, non-default generation profile while retaining
A8b's unmodified legacy daily fallback. The station document, rather than
runtime climate inference, declares the route. A8c is a development pilot: it
may recommend a separately roadmapped confirmation study but cannot promote a
public default or reopen the stopped whole-domain A7 line.

## Scope

Included:

- station-document revision 2 with an explicit `integrated_daily` or
  `legacy_daily_fallback` route and fail-closed route/model/coefficient checks;
- profile `a8c_routed_daily_v1`, selected only by the runspec and declared in
  text and structured provenance;
- the A8a second-order occurrence, log-quantile wet amount, and within-spell
  Gaussian-copula construction for eligible stations;
- exactly one occurrence uniform and one amount uniform per generated calendar
  day from two domain-separated extension streams, with state carried across
  month and year boundaries;
- A8b's `legacy_daily_only_v1` fallback with no secondary year state, extra
  fallback RNG, output inspection, repair, or silent switching;
- six frozen development stations spanning hot-arid integrated and fallback,
  monsoonal, non-monsoonal semi-arid, humid, and cold strata; and
- nested 30/100-year evaluation of engineering identity, monthly moment
  budgets, the registered A7a spell/occurrence targets, storm/winter and
  cross-variable guards, replay, and provenance.

Excluded:

- full-corpus confirmation, WEPP response, public-default change, automatic
  aridity estimation, runtime classification, coefficient fitting, station
  substitution, count optimization, rejection, clipping, monthly-total
  conditioning, post-generation repair, or an A8b year-state;
- relaxation of the A7b whole-domain stop or treatment of its isomorphic O2
  and SM2 representations as distinct mechanisms; and
- changes to faithful-mode arithmetic, source RNG streams, or legacy `.par`
  interpretation.

## Authority

- [A8a](../20260715-a8a-dry-regime-applicability/package.md) supplies the
  accepted route classes and eligible-station analytic coefficients.
- [A8b](../20260715-a8b-secondary-year-fallback/package.md) requires the
  boundary route to remain `legacy_daily_only_v1`, with no extra state or RNG.
- [A7b](../20260714-a7b-analytic-precipitation-feasibility/package.md) supplies
  the unique four-state occurrence and shared amount construction.
- [SPEC-A8C-ROUTED-DAILY](../../specifications/SPEC-A8C-ROUTED-DAILY.md) is the
  extension behavior and interface authority.
- `artifacts/pilot-contract-v1.json` is the prospective corpus, estimator,
  threshold, and terminal authority for this package.

## Plan

1. Freeze the six station identities, routes, parent inputs, profile and
   station-document semantics, RNG ownership, horizons, burns, metrics,
   thresholds, and terminal rule before the first A8c climate output.
2. Add strict station-document revision 2 intake and provenance identities;
   keep revision 1 and legacy `.par` behavior unchanged.
3. Implement the routed daily backend at the precipitation seam, with the
   fallback delegating unchanged and the integrated path using fixed daily
   draw ownership.
4. Materialize the six hash-bound pilot documents, generate nested candidate
   and faithful controls, and execute the frozen evaluation.
5. Independently verify artifacts and invariants, perform consolidated review,
   run repository plus coverage/CRAP gates, and close on one terminal.

## Execution & dispatch

Execute locally on `main` from clean commit
`046eba3c8d4508c84522c6dbd7cec4d39f094563`; push only to `main` if the
operator separately requests publication. No side branch or pull request is
authorized.

A8a/A8b artifacts are exposed parent evidence. No A8c candidate climate may be
generated until the specification, pilot contract, implementation-independent
analyzer, and pre-execution freeze bind their exact bytes. A bounded amendment
is permitted only for a defect discovered before outcome access; scientific
thresholds cannot change after candidate output exists.

## Gates

- missing, unknown, or route-inconsistent revision-2 classification fails
  closed; faithful and routed profile/station pairings are explicit;
- every eligible document reproduces its A8a route, base parameter hash,
  occurrence probabilities, amount knots, copula correlations, and monthly
  dispersion; the fallback document carries no integrated coefficients;
- faithful profile golden byte identity remains unchanged;
- all routed-fallback climate rows equal their faithful controls and differ in
  artifact bytes only through required profile/provenance declarations;
- integrated replay is byte deterministic; its 30-year output is the exact
  climate-row prefix of the same 100-year run;
- integrated paths consume exactly two extension draws per emitted calendar
  day and fallback paths consume none;
- every frozen monthly-moment, daily-target, storm/winter, cross-variable, and
  provenance guard in `pilot-contract-v1.json` is evaluated without repair;
- review has zero open P1/P2 findings;
- `cargo fmt --check`;
- `cargo clippy --all-targets -- -D warnings`;
- `cargo test`;
- `cargo llvm-cov --workspace --lcov --output-path target/lcov.info`; and
- `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**'
  --fail-above`.

## Exit criteria

`EXECUTED-COMPLETE` requires reproducible artifacts, accepted review, passing
engineering gates, and exactly one terminal:

- `RECOMMEND-A8D-CONFIRMATION` means every frozen pilot guard passes and only a
  separately roadmapped confirmation study is recommended; or
- `STOP-A8-ROUTED-DAILY` means the implementation is valid but at least one
  frozen scientific guard fails, so no confirmation or promotion follows.

An input/freeze defect holds `EXECUTED-HOLD-PARENT-EVIDENCE`; a runtime,
calculation, or review defect holds `EXECUTED-HOLD-IMPLEMENTATION-DEFECT`.

## Execution result

The package closed on `STOP-A8-ROUTED-DAILY`. The frozen 96-process matrix
completed, replayed exactly, preserved every 30-year climate-row prefix, and
kept the explicit fallback row-identical to its faithful control. The target
daily families passed: median relative improvements were 0.207–0.251 for spell
structure and 0.469–0.476 for higher-order occurrence, with five of six
stations nonworse at each horizon.

The candidate nevertheless failed three gate groups. Wet-amount means passed
only 47/72 30-year and 36/72 100-year station-month cells; Bakersfield July
had no precipitation at either horizon, leaving three monthly statistics
unavailable. The time-to-peak median collapsed to zero for all five integrated
stations while faithful medians remained positive. The exact cross-variable
guard also failed because CLIGEN conditions selected downstream variables on
wet/dry state: changed occurrence altered Boise dew point and Alamosa wind
speed even though their algorithms and random batches were not replaced.
Winter bounds and the cold-wet `1.01` normalized-peak rule passed.

The first analysis invocation exposed no outcome and wrote no result artifact;
it found that three infeasible A8a fallback cells omitted a cached variance
budget. Amendment 001 reconstructed the identical legacy Markov variance from
the retained parent inputs, rebound the analyzer before outcome access, and
changed no gate or candidate byte. Final independent replay passed 160 checks,
including the LFS archive and post-stop closure identities.

No A8d confirmation, promotion, public-default change, threshold relaxation,
or outcome-time repair follows from this package. The explicit profile remains
an experimental, non-default development surface and is not recommended for
production climate generation.

## Artifacts

- `artifacts/pilot-contract-v1.json` — prospective station, execution,
  estimator, gate, and terminal contract.
- `artifacts/pre-execution-freeze-v1.json` — exact specification, code,
  analyzer, parent, and input identities before candidate generation.
- `artifacts/post-generation-pre-outcome-amendment-001.md` and
  `artifacts/pre-analysis-freeze-v2.json` — bounded missing-cache correction
  and rebound before any result artifact existed.
- `artifacts/stations/` and `artifacts/runspecs/` — six strict revision-2
  station documents and deterministic execution inputs.
- `artifacts/execute-a8c.py` and `artifacts/analyze-a8c.py` — canonical campaign
  and analysis tools.
- `artifacts/execution-evidence-v1.json` — 24 station/burn cells with stream,
  replay, prefix, fallback, cross-variable, runspec, and provenance hashes.
- `artifacts/a8c-retained-streams-v1.tar.gz` and
  `artifacts/retained-streams-manifest-v1.json` — deterministic Git LFS archive
  of all 96 hashed climate/provenance files; `archive-a8c-evidence.py
  --restore` reconstructs the verifier input under `target/`.
- `artifacts/a8c-analysis-v1.json`, `artifacts/a8c-decision-v1.json`, and
  `artifacts/findings.md` — generated result.
- `artifacts/verify-a8c.py`, `artifacts/review.md`, and
  `artifacts/gate-results.md` — independent checks and closure evidence.
- `artifacts/closure-manifest-v1.json` — immutable post-decision identities for
  the status-only closure edits and retained evidence transport.
