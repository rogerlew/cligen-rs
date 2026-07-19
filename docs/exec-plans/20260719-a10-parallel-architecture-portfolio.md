# A10 Parallel Architecture Portfolio

This living ExecPlan follows `.agent/PLANS.md`. It coordinates A10M5R10
without replacing its package, specification, machine contract, evidence, or
terminal disposition.

## Purpose / Big Picture

A10M5R10 will replace the recent one-architecture-at-a-time cadence with one
prospectively frozen, parallel comparison. The observable outcome is a
complete matched-seed comparison of five candidate architecture families at
P1- and P2-scale capacity, followed by a deterministic Pareto decision that
retains up to three configurations. The campaign is ready to continue only if
at least two eligible configurations survive; otherwise it closes with an
honest scientific HOLD and complete comparison evidence.

The execution optimizes wall time rather than GPU-minute minimization. After a
single control-materialization predecessor, ten independent one-L40 jobs can
run concurrently. Each job owns one family/capacity pair and executes all
three registered seeds, which keeps matched-seed evidence and failure state
together without using inefficient multi-rank synchronization.

## Progress

- [x] (2026-07-19) Audited A10M5R7 through A10M5R9 and the L40 operational
  qualification.
- [x] (2026-07-19) Froze five candidate families, two capacities, three seeds,
  common objective, physics boundary, eligibility, Pareto, and retention rule.
- [x] (2026-07-19) Scaffolded the package, research specification, machine
  contract, and this living ExecPlan.
- [ ] Publish the immutable implementation source and prospective verifier.
- [ ] Run complete core-plus-`srad` Daymet preflight before authority creation.
- [ ] Initialize the 935 GPU-minute authority and materialize all six controls.
- [ ] Dispatch, authenticate, and collect the ten concurrent family-capacity
  roles.
- [ ] Aggregate all thirty candidate seed rows, replay eligibility/Pareto
  retention, and publish the terminal.
- [ ] Reconcile accounting, exact cleanup, reserve, authority close, package
  records, review, and repository gates.

## Surprises & Discoveries

- A10M5R7's residual was mixed rather than dominated by one mechanism. Raw
  generated feedback worsened family-balanced error by 17.26%, so the
  portfolio excludes daily generated-feedback architectures.
- A10M5R8 improved its climate score 14.35% but more than doubled daily proper
  NLL and degraded location. Objective pressure alone is insufficient.
- A10M5R9's 30-parameter monthly residual improved its matched dispersion
  composite 15.15% without degrading its baseline blocks. Its failure against
  P1 came from the smaller replacement baseline, which motivates both frozen-
  backbone adapters and a capacity-matched replacement arm.
- A10M5R8 and R9 selected checkpoints at their epoch ceilings. The portfolio
  therefore freezes a longer 96-epoch maximum rather than interpreting either
  earlier ceiling as convergence.
- Four-rank NCCL on node03 uses host shared memory and is markedly slower than
  one GPU. Ten independent one-GPU jobs provide useful concurrency without
  that communication path.

## Decision Log

- Compare a portfolio now because operator time and serial scientific latency,
  not GPU minutes, are the active constraint.
- Use exact P1/P2 and their three accepted seeds so capacity and seed effects
  remain connected to reconstructable controls.
- Keep monthly and annual dispersion in the training signal and make all seven
  core climate blocks equal. Daily target pairing remains zero because the
  claim concerns stochastic climate, not reproduction of observed daily
  sequences.
- Include monthly-only, annual/monthly, shared-factor, climate-normal, and
  physics-conditioned families. This tests increasing structure through
  explicit paired differences without an unbounded model search.
- Treat observed Daymet `srad` only as a target. Latitude and day of year create
  a deterministic astronomical envelope; shared generated factors represent
  precipitation/radiation/temperature dependence without observed-weather
  input or target leakage.
- Run all three seeds within each family-capacity role. A failed role cannot be
  silently completed by another job or retried after outcome inspection.
- Retain multiple eligible Pareto configurations rather than forcing a single
  winner. Two retained configurations are required for a READY terminal.

## Outcomes & Retrospective

The package is scaffolded and has not consumed compute or opened an authority.
This section must be updated after execution with per-family/capacity results,
retained identities, resource use, operational reconciliation, and a direct
comparison with the intended reduction in scientific wall time.

## Context and Orientation

The authoritative package is
`docs/work-packages/20260719-a10m5r10-parallel-architecture-portfolio/package.md`.
The research interface is
`docs/specifications/SPEC-A10-ARCHITECTURE-PORTFOLIO.md`, and its exact machine
freeze is `artifacts/portfolio-contract.json` below the package. Execution
sources will live in the package's `artifacts/jobs/` directory. Prospective and
result verifiers will be `artifacts/verify_freeze.py` and
`artifacts/verify_result.py`.

P1/P2 accepted identities are recorded in
`docs/work-packages/20260718-a10m5r4r2-realized-temporal-adjudication/artifacts/temporal-contract.json`.
The common climate score is defined by
`docs/specifications/SPEC-A10-CLIMATE-STATISTICS-TRAINING.md`. Calendar and
missingness behavior comes from `docs/specifications/SPEC-A10-CORPUS.md` and
`docs/specifications/a10-daymet-calendar-profile-v1.json`.

In this plan, a family-capacity role is one Slurm job that runs all three seeds
for one architecture at K1 or K2. A matched-control ratio divides a candidate's
error by the exact same-capacity, same-seed control error; lower is better. A
Pareto configuration is one for which no eligible peer is effectively no worse
on every registered decision axis and at least 2% better on one.

## Plan of Work

### Milestone 1: prospective implementation and preflight

Implement the shared architecture, objective, scoring, selector, and dispatch
code under the package's `artifacts/jobs/`. Add a prospective verifier that
constructs every architecture/capacity, checks state centering and output
support, proves role enumeration and decision fixtures, and rejects observed
weather inputs. Run a complete standard-library calendar preflight over all
1,440 candidate-fit and fit-validation Daymet objects, including the extra
`srad` mask. Acceptance is a hash-bound receipt showing the exact revision-2
counts before any authority or ledger exists.

### Milestone 2: controls and parallel portfolio

Publish and push the exact source commit, prepare immutable assets, and
initialize one authority with a 935 GPU-minute ceiling. The 30-minute
predecessor reconstructs P1 and P2 for all three seeds and publishes immutable
control/checkpoint/random-field records. Acceptance is six exact checkpoint
identities and no protected-role access.

Submit the ten family-capacity roles together after the predecessor succeeds.
Each role requests one typed L40 for 90 minutes, verifies its assets and
calendar locally, executes its three seeds, scores all 240 validation points,
publishes complete learning curves and metrics, and removes job-local state.
Acceptance is ten authenticated terminal receipts and thirty complete candidate
rows; partial rows remain failures rather than being imputed.

### Milestone 3: decision and closure

Collect all sanitized evidence and run the CPU aggregator over the immutable
rows. It computes matched-control ratios, three-seed summaries, eligibility,
Pareto dominance, deterministic retention, and the typed terminal. Acceptance
is an independently replayable decision retaining zero through three exact
configuration identities.

Perform owner-marker-validated cleanup for every exact durable and remote root,
using the five-minute reserve only if ordinary cleanup cannot be authenticated.
Close the authority and reconcile requested versus actual resources. Update
the package, this plan, catalog/roadmap as separately authorized, disposition,
review, gate results, and hashes. Acceptance is closed accounting, absent exact
roots, passing result verifier, and passing repository gates.

## Concrete Steps

Run from `/Users/roger/src/cligen-rs`. Before authority creation:

    python3 docs/work-packages/20260719-a10m5r10-parallel-architecture-portfolio/artifacts/verify_freeze.py
    python3 docs/work-packages/20260719-a10m5r10-parallel-architecture-portfolio/artifacts/verify_corpus_calendar.py --corpus-tar <private-corpus.tar>

The executor must record the exact source commit and use package-scoped private
controller and ledger roots. Prepare and verify assets using
`research/a10/lemhi_toolkit`, then execute the registered
`control-materialization` role. Only an authenticated passing predecessor may
release all ten one-L40 role submissions. Submit them without DDP/NCCL and
observe each role exactly once. Concrete toolkit commands, run IDs, authority
hashes, Slurm job IDs, and collection commands must be appended here when the
implementation fixes those identifiers.

After collection, run the package result verifier and repository gates:

    python3 docs/work-packages/20260719-a10m5r10-parallel-architecture-portfolio/artifacts/verify_result.py
    git diff --check
    cargo fmt --check
    cargo clippy --all-targets -- -D warnings
    cargo test

If production functions under `crates/` are changed, additionally run the
workspace coverage and CRAP gates required by `AGENTS.md`.

## Validation and Acceptance

Prospective acceptance requires exact agreement between package, specification,
contract, implementation role table, seeds, capacity shapes, objective weights,
members, epochs, calendar counts, resource ceiling, and terminal fixtures. The
preflight must demonstrate 10,958/10,950 full-period core and physics counts,
2,922/2,920 representative-window counts, observed February 29, absent
leap-year December 31, exclusive target-end behavior, at least 28 observations
per year-month, and all 1,440 role-eligible objects.

Execution acceptance requires six exact controls; ten single-attempt
family-capacity roles; thirty complete candidate rows; candidate-fit-only
normalization and gradients; gradient-free fit-validation; sealed protected
roles; finite supported sixteen-member generation; all-240 scores; parameter,
epoch, and resource compliance; and deterministic selector replay.

Operational acceptance requires authenticated terminal accounting at or below
935 GPU-minutes, sanitized evidence collection, job-local and durable exact
cleanup, reserve settlement, authority close, and repository gates. Scientific
READY is separate: at least two eligible Pareto configurations must be
retained.

## Idempotence and Recovery

Prospective verifiers, the calendar scan, aggregation, result verification,
and repository gates are repeatable and read-only with respect to frozen
evidence. Asset preparation may be repeated only before authority creation and
must reproduce hashes.

Once an authority exists, never reset, copy, or replace its ledger. A role is
single-attempt; after ambiguous scheduler state, authenticate terminal state
and use only the toolkit's exact role/run recovery path. The five-minute
reserve authorizes cleanup, not training or a scientific retry. Do not resubmit
a failed role under another ID, combine partial seeds, or change thresholds.
If cleanup cannot be proved after the one bounded recovery, preserve evidence
and close with an exact cleanup hold.

## Artifacts and Notes

- `artifacts/portfolio-contract.json` is the prospective machine freeze.
- `artifacts/calendar-preflight.json` will bind full corpus mask evidence.
- `artifacts/control-materialization.json` will bind all six controls.
- `artifacts/portfolio-summary.json` will contain all seed and aggregate rows.
- `artifacts/portfolio-decision.json` will contain eligibility, Pareto, and
  retained identities.
- `artifacts/execution-disposition.md` will explain the scientific terminal.
- `artifacts/resource-ledger.md` and `toolkit-records.md` will reconcile live
  operations without publishing private paths or credentials.
- `artifacts/review.md`, `gate-results.md`, and `verify_result.py` will close
  the evidence and repository state.

## Interfaces and Dependencies

The experiment depends on Python 3.11, NumPy, PyTorch, the private immutable A10
corpus, accepted P1/P2 reconstruction sources, the Daymet revision-2 calendar
profile, Slurm, one typed L40 per role, and
`research/a10/lemhi_toolkit`. The physics arm requires the existing Daymet
`srad` field but no external acquisition. The package changes no Rust runtime,
faithful generator, public CLI, or production model interface.

The downstream research interface is a list of zero through three exact
retained architecture/capacity identities and their complete comparison
evidence. Any later temporal, spatial, confirmation, public-profile, or
production work requires separate authority.

## Revision note

2026-07-19: created the prospective parallel portfolio plan with five families,
two matched capacities, three seeds, ten concurrent one-L40 roles, and a frozen
multi-candidate Pareto decision.
