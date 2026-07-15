# A8b — Secondary Year-to-Year Fallback Feasibility

Status: `EXECUTED-COMPLETE`
Date: 2026-07-15
Evidence mode: Mixed
Execution authorization: operator authorized scaffolding and execution on
2026-07-15

## Objective

Determine whether the explicit A8a `legacy_daily_fallback` domain should remain
legacy-only or can support one bounded precipitation year-state mechanism that
reallocates, rather than adds, monthly variance. A8b accepts A8a's partition
and eligible-domain daily construction without reopening either. It changes no
generator, station schema, generation profile, public interface, or default and
generates no climate.

## Scope

Included:

- the five exposed A8a development and five confirmation stations classified
  `legacy_daily_fallback`, with the identities and classes fixed by A8a;
- exactly two alternatives: an explicit `legacy_daily_only_v1` null and one
  new `bounded_eof2_copula_ar1_reallocation_v1` precipitation-amount candidate;
- a pooled, fixed-rank two-EOF fit over the 1980--2009 annual monthly totals,
  with held-out 2010--2025 secondary-covariance and persistence evaluation;
- analytic preservation of the legacy monthly wet fraction, precipitation
  mean, and precipitation variance by reducing conditional wet-amount variance
  as between-year monthly-mean covariance is introduced;
- bounded wet-amount means, bounded residual-variance allocation, fixed RNG
  ownership, and explicit station/month coefficients; and
- one terminal selecting the candidate, retaining the legacy-only fallback, or
  stopping the routed pilot if the null itself is not certified.

Excluded:

- changing the A8a applicability classes, fitting integrated stations, runtime
  aridity inference, station substitution, or a monsoonal-specific branch;
- the retired A5e0 scalar-IID mechanism or any exact A5b candidate version;
- changes to occurrence, storm timing, Tmax, Tmin, radiation, or wind;
- climate generation, path selection, fixed-count optimization, rejection,
  clipping, output repair, WEPP evaluation, promotion, or implementation; and
- a second optional candidate after observing the first candidate's result.

## Authority

- [A8a](../20260715-a8a-dry-regime-applicability/package.md) supplies the
  accepted explicit partition and `CONTINUE-A8B-DRY-PARTITION` authorization.
- [ADR-0004](../../decisions/0004-a5b-interannual-no-promotion.md) prohibits
  rescue of the seven A5b versions and requires analytic monthly-budget
  feasibility before another generated campaign.
- [A5f0](../20260714-a5f0-annual-state-failure-attribution/package.md) retires
  only the exact rank-one scalar-IID mechanism and identifies cross-month
  dependence and insufficient one-component representation as the main design
  lessons.
- `artifacts/feasibility-contract-v1.json` is the package-local prospective
  authority for the corpus, alternatives, mathematics, metrics, gates, RNG
  ownership, and decision priority. It is research evidence, not a public
  coefficient or station schema.

## Plan

1. Scaffold the package, design, contract, analyzer, verifier, and freeze tool
   without computing A8b annual aggregates, coefficients, or metrics.
2. Freeze all methods and exact A8a/A5 authority identities before the first
   A8b-specific candidate fit.
3. Fit the one pooled candidate, certify every station/month budget and bound,
   evaluate held-out secondary-state covariance and persistence against the
   null, and apply the frozen terminal rule.
4. Independently reproduce coefficient and decision bytes and verify all
   algebraic, identity, class, scope, and terminal invariants.
5. Complete accuracy/consistency/public-safety review, run repository gates,
   and close the roadmap and work-package catalog.

## Execution & dispatch

Execute locally on `main` at source commit
`26f581b99b425ef9699ec85d9322ff72b0b8bdd3`. A8a is an uncommitted but
hash-pinned predecessor in the same operator-dispatched worktree; A8b records
its exact parent artifact identities and is intended to be committed with or
after that parent. Push only to `main` if separately requested. No side branch
or pull request is authorized.

A8a daily sources are already exposed parent evidence. A8b may inspect parent
class and identity artifacts while scaffolding, but its annual aggregations,
pooled EOFs, candidate coefficients, validation metrics, and terminal may not
be computed until the complete A8b contract and methods are frozen.

## Gates

- A8a terminal and all ten fallback identities reproduce exactly, with five
  development and five confirmation stations and no reclassification;
- the alternative set contains exactly the explicit null and one new bounded
  pooled two-mode candidate, with no retired identifier or scalar-IID state;
- a candidate reaching coefficient construction must pass all 120
  station/month wet-fraction, monthly-mean, monthly-variance, and coefficient
  bounds; a failure at an earlier frozen fit requirement is recorded as
  candidate infeasibility and selects the null without coefficients;
- candidate selection requires every frozen fit, breadth, covariance-skill,
  annual-covariance, persistence, and coefficient-bound guard; otherwise the
  certified null wins without repair or a replacement candidate;
- coefficient, analysis, decision, and findings artifacts reproduce byte for
  byte and independent algebraic checks pass;
- review has zero open P1/P2 findings;
- `cargo fmt --check`;
- `cargo clippy --all-targets -- -D warnings`; and
- `cargo test`.

Coverage and CRAP gates are not applicable because A8b changes no production
function under `crates/`.

## Exit criteria

`EXECUTED-COMPLETE` requires a valid parent/null, frozen and reproducible
candidate evidence, accepted review, passing gates, and exactly one terminal:

- `SELECT-BOUNDED-EOF2-AR1-REALLOCATION` selects the one candidate for an A8c
  development pilot only;
- `USE-LEGACY-DAILY-FALLBACK` retains the explicit null and sends that route to
  A8c without an interannual mechanism; or
- `STOP-A8-ROUTED-PILOT` closes A8 if the parent partition or legacy-only null
  cannot be certified.

An input/freeze defect holds `EXECUTED-HOLD-PARENT-EVIDENCE`; a calculation or
review defect holds `EXECUTED-HOLD-ANALYSIS-DEFECT`. Candidate scientific
failure is not a hold: it returns the registered legacy-only terminal.

## Execution result

A8b returned `USE-LEGACY-DAILY-FALLBACK` and selected
`legacy_daily_only_v1`. The A8a parent, all ten fallback identities, and the
explicit null certified successfully. The optional
`bounded_eof2_copula_ar1_reallocation_v1` mechanism failed at its first frozen
fit requirement: El Centro (`ca042713`) has 30 identical June precipitation
totals of 0.0 mm in the 1980--2009 Daymet training period, so its required
station-month sample standard deviation is zero and the registered
standardization is undefined.

The first invocation stopped before an EOF, coefficient, monthly budget,
validation metric, or decision artifact existed. Amendment 001 and successor
freeze v2 preserve that boundary and change only the reporting path: the
already fail-closed exception becomes structured candidate infeasibility and
the prospectively registered null terminal. No month was omitted, imputed,
pooled, or repaired. The coefficient sentinel contains zero station
coefficients and explicitly has no use authorization.

Independent verification confirmed the zero-scale source evidence and
reproduced all output bytes. Consolidated review accepted the result with zero
open P1/P2 findings, and all repository gates passed. A8c may proceed with the
A8a eligible-domain daily construction and an explicit legacy-only fallback;
it must not implement an A8b secondary year-state, coefficients, or RNG.

## Artifacts

- `artifacts/design.md` — frozen mechanism mathematics and interpretation.
- `artifacts/feasibility-contract-v1.json` — exact inputs, periods,
  alternatives, thresholds, RNG ownership, and terminal priority.
- `artifacts/pre-analysis-freeze-v1.json` — prospective method and input
  identities.
- `artifacts/pre-analysis-amendment-001.json` and
  `artifacts/pre-analysis-freeze-v2.json` — bounded fail-closed reporting
  amendment and successor freeze.
- `artifacts/analyze-a8b.py` and `artifacts/verify-a8b.py` — canonical and
  independent analysis tools.
- `artifacts/a8b-coefficients-v1.json`, `artifacts/a8b-analysis-v1.json`,
  `artifacts/a8b-decision-v1.json`, and `artifacts/findings.md` — result.
- `artifacts/review.md` and `artifacts/gate-results.md` — closure evidence.
