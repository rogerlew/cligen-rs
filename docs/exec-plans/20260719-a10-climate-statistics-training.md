# A10 climate-statistics training ExecPlan

This ExecPlan is a living document maintained according to `.agent/PLANS.md`.
It governs
`docs/work-packages/20260719-a10m5r8-climate-statistics-objective/` without
merging that package's authority or evidence into earlier A10 records.

## Purpose / Big Picture

After this work, the accepted P1 architecture will have undergone a controlled
training-objective experiment. The control is the exactly reconstructed
A10M5R3 P1 seed-147031 model. The treatment has the same architecture, amount
family, corpus roles, seed, and generation closure, but learns primarily from
realized multi-year stochastic climate statistics for precipitation, maximum
temperature, and minimum temperature. The experiment answers whether the
failed free-running climate behavior is principally an objective mismatch
before a new architecture is introduced.

Solar radiation is deliberately not fitted here. If the core objective is
supported, the next prospective package adds radiation normalized by its
latitude/day-of-year astronomical envelope and tests its dependence on wetness
and temperature.

## Progress

- [x] (2026-07-19) Reconciled the A10 roadmap, package catalog, prior mixed
  architecture hold, clean `main`, canonical Lemhi assets, and live SSH path.
- [x] (2026-07-19) Froze the bounded same-architecture control/treatment design
  and the core-variable boundary requested by the operator.
- [x] (2026-07-19) Publish the package, research specification, executable contract, source,
  and local verification on `main`.
- [x] (2026-07-19) Published scaffold source at `56a7d42`; detected and
  preserved a pre-spend private authority genesis with a nonexistent manually
  expanded SHA; scaffolded unchanged corrective A10M5R8R1.
- [x] (2026-07-19) Initialize the package-scoped resource authority and execute one bounded
  single-L40 attempt through the canonical toolkit lifecycle.
- [x] (2026-07-19) R1 job `1014023` reconstructed the control exactly and
  passed the synthetic dispersion test, then exposed accepted leap-day
  missingness as incompatible with the all-day-complete window predicate;
  collected failure evidence and closed exact cleanup after 246 GPU-seconds.
- [x] (2026-07-19) R2 job `1014024` reached masked calendar attachment and
  exposed an inclusive target-end label slice; collected and closed exact
  failure evidence after 223 GPU-seconds.
- [x] (2026-07-19) R3 job `1014025` completed in 664 GPU-seconds with exact
  control identity and all operational gates; the treatment improved the
  climate score 14.35% but failed the 15% and four nondegradation guards.
- [x] (2026-07-19) Authenticate and score the full fit-validation comparison, reconcile
  resources and cleanup, and close package/campaign records.

## Surprises & Discoveries

- The inherited auxiliary term named `monthly_expected_precipitation` averages
  an entire 730-day batch window rather than calendar months.
- The inherited term named `annual_aggregate_dispersion` compares the
  difference between two precipitation totals rather than estimating
  interannual dispersion.
- The accepted checkpoint selector uses only fit-validation daily proper NLL,
  so the existing training loop never selects directly for free-running
  climate behavior.
- Latitude is constant within a site. It can define a physical radiation
  baseline in a future package, but its general relationship is identifiable
  only across the multi-site corpus.
- The first private authority genesis recorded a manually inferred full SHA
  that did not match `git rev-parse HEAD`. Detection preceded every remote and
  resource lifecycle step; its zero-reservation ledger is preserved rather
  than reset.
- Accepted Daymet points have 10,950 observed rows on a 10,958-day 1980–2009
  Gregorian axis. The eight leap-day rows are explicitly unobserved, so exact
  multi-year climate windows must carry the accepted mask rather than require
  every calendar row or synthesize data.
- Calendar target-end is exclusive. Including its first post-window day yields
  2,923 labels against the correct 2,922-day eight-year target and must fail.

## Decision Log

- Decision: repair the objective before changing architecture. Rationale: the
  diagnostic found mixed structural evidence while the current loss and
  checkpoint score do not represent the desired stochastic climate target.
  Date/Author: 2026-07-19, operator and Codex.
- Decision: restrict the treatment to precipitation, Tmax, and Tmin while
  defining statistic blocks that can later accept solar radiation. Rationale:
  this is the smallest coupled climate core and preserves causal attribution.
  Date/Author: 2026-07-19, operator and Codex.
- Decision: use exact eight-calendar-year windows and differentiable sampled
  ensembles. Rationale: calendar-month and interannual dispersions cannot be
  inferred from the inherited two-half surrogate or from expected heads alone.
  Date/Author: 2026-07-19, Codex.
- Decision: retain a low-weight open-loop daily proper NLL as a support guard,
  but prohibit paired-day error from the climate score and checkpoint selector.
  Rationale: stochastic realizations should match climate distributions rather
  than a particular observed trajectory. Date/Author: 2026-07-19, operator and
  Codex.

## Outcomes & Retrospective

The campaign reached an honest scientific result after two fail-closed
calendar corrections. A10M5R8R3 completed the full experiment with every
corpus, role, support, identity, and operational gate passing. The treatment
improved family-balanced stochastic climate behavior by 14.35%, led by a
64.88% improvement in within-month dispersion and 18.57% in annual dispersion.
It nevertheless degraded annual/monthly location and more than doubled core
daily proper NLL, so it did not advance under the frozen 15%/10% gates.

This separates the next model question cleanly: the aggregate stochastic loss
is informative, but the absolute-weather P1 representation cannot allocate
location and residual variability independently. A climate-normal-conditioned
residual family is therefore warranted. Solar radiation remains downstream of
a passing core architecture.

## Context and Orientation

`docs/work-packages/20260718-a10m5r3-candidate-family-capacity-knee/artifacts/jobs/screen_core_v2.py`
contains the accepted P1 architecture and inherited training objective.
`docs/work-packages/20260718-a10m5r7r2-authorized-architecture-execution/`
contains the latest structural diagnostic. The new package owns only research
scripts and evidence; it does not modify production generator code or faithful
CLIGEN.

The A10M1 corpus supplies 1,200 `candidate_fit` and 240 `fit_validation`
Daymet points across six regimes. Only `candidate_fit` may contribute
gradients or normalization. The treatment checkpoint is selected on a frozen,
value-blind subset of four fit-validation points per regime and is finally
evaluated on all 240 fit-validation points. Development-selection and
confirmation roles remain sealed.

## Plan of Work

Milestone one publishes the research contract and executable source. The
contract fixes P1/lognormal/seed-147031, exact calendar windows, statistic
blocks, transforms, scales, weights, stochastic member counts, fit-validation
checkpoint surface, final comparison, and terminal rules. A CPU synthetic test
must show that changing ensemble dispersion changes monthly and annual
dispersion losses without introducing paired-day trajectory error.

Milestone two freezes immutable Lemhi assets and a new resource authority. One
single-L40 job reconstructs the accepted control exactly, trains one treatment,
evaluates both arms with identical member fields, publishes the complete score
surface, and owns supervised job-local cleanup. The primary attempt is capped
at 60 GPU-minutes and exact-node recovery at five, for a 65 GPU-minute ceiling.
There is no scientific retry or second seed under this authority.

Milestone three authenticates evidence, replays the deterministic decision,
reconciles accounting, releases or uses recovery only for exact cleanup,
removes the durable run root, and closes the toolkit lifecycle. The package
then records either core-objective readiness or an honest hold and updates the
roadmap, catalog, specification registry, gates, and this plan.

## Concrete Steps

All local commands run from `/Users/roger/src/cligen-rs` on `main`:

    python3 docs/work-packages/20260719-a10m5r8-climate-statistics-objective/artifacts/verify_freeze.py
    git diff --check
    cargo fmt --check
    cargo clippy --all-targets -- -D warnings
    cargo test

Before live execution, commit and push the exact source. Prepare immutable
assets from `/Users/roger/.cache/cligen-rs/a10-python311-smoke/assets`, create
the private authority and plan with the package-owned builders, and execute the
canonical `lemhi-v2` toolkit sequence: doctor, probe, plan, prepare, stage,
verify, submit, terminal observation, collect, clean, and close.

## Validation and Acceptance

The treatment is supported only if all operational and support gates pass, its
full fit-validation family-balanced climate score improves by at least 15%
over the reconstructed control, no registered statistic block degrades by more
than 10%, and its daily proper-NLL guard degrades by no more than 10%. The
decision is computed mechanically from complete finite evidence. A failed
scientific gate is an informative hold, not a retry signal.

## Idempotence and Recovery

Local generation and verification are additive and repeatable. Authority
genesis occurs once. An ambiguous submit is reconciled from its registered
token and is never repeated under a new identity. Rolling treatment
checkpoints remain inside the supervised job-local root; only final evidence
and declared model records enter the durable result. Recovery is reserved only
for an authenticated marked job-local cleanup failure on the exact node.

## Artifacts and Notes

The package will contain the contract, scripts, freeze verifier, gate log,
toolkit/resource records, score summaries, review, and terminal disposition.
Complete sanitized evidence remains in the private toolkit publication tree
when too large for the repository; committed summaries bind its byte count and
SHA-256.

## Interfaces and Dependencies

The new research-only interface is
`docs/specifications/SPEC-A10-CLIMATE-STATISTICS-TRAINING.md`. Runtime
dependencies remain the canonical CPython 3.11.15, NumPy 2.2.6, PyTorch
2.7.1+cu128, A10M1 corpus, A10M3/M5R3 P1 model surface, and toolkit revision 2.
No public generation profile, crate interface, protected corpus role, or
faithful behavior changes.

Revision note (2026-07-19): initial self-contained plan created after campaign,
objective, corpus, runtime, and cluster reconnaissance.

Revision note (2026-07-19): recorded the pre-spend source-identity hold and the
unchanged A10M5R8R1 corrective authority path.

Revision note (2026-07-19): recorded R1's authenticated calendar-missingness
failure and the exact-mask R2 correction without changing the estimand.

Revision note (2026-07-19): recorded R2's end-boundary failure and the tested
exclusive-end R3 correction.

Revision note (2026-07-19): recorded R3 completion, the objective hold, exact
cleanup, and the residual-architecture successor interpretation.
