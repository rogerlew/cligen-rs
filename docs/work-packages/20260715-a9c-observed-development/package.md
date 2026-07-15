# A9c — Observed Development Comparison

Status: `EXECUTED-HOLD-GATE-CALIBRATION`
Date: 2026-07-15
Evidence mode: Mixed
Scaffolding and execution authorization: operator dispatched A9c on
2026-07-15 from clean `main` at
`4e918ecd5d2b37eaa99ae365677f423080069480`, targeting `main`

## Objective

Implement the two actual A9 research probability laws, fit them only on the
authorized coefficient-fit evidence, calibrate candidate-blind gates, compare
them on exposed development evidence across six climate regimes, and freeze at
most one complete candidate for a separately dispatched A9d confirmation.

## Scope

Included:

- exact A9a/A9b predecessor verification and complete A9b fixture replay;
- a metadata-first freeze of Daymet fit/development and USCRN event fit/
  development roles, with synthetic-only gate calibration;
- research-only implementations of `alternating_renewal_marked_v1` and
  `latent_regime_marked_v1`, immutable fit artifacts, and structural audits;
- observed fitting, analytic/monthly reconciliation, candidate-blind null
  calibration, staged bounded evaluation, the 31-objective vector, Pareto
  trace, and frozen lexicographic selection;
- a public scientific report, consolidated review, verification, and one A9c
  terminal.

Excluded:

- access to any A9a 18-site USCRN confirmation station-year series;
- a production Rust generation profile, station schema, runtime fallback,
  automatic climate classifier, year state, output repair, or faithful-mode
  change;
- A9d confirmation, A9e runtime work, promotion, openWEPP, or WEPPcloud work.

## Authority

- [A9c handoff](../20260715-a9b-calibration-harness/artifacts/a9c-handoff.md)
  and A9b terminal `HARNESS-READY-A9C`.
- [SPEC-A9](../../specifications/SPEC-A9-RESEARCH-FOUNDATION.md), A9a's model
  family envelope, objective registry, data/evaluation plan, tuning-harness
  contract, exact exposure manifest, and locked confirmation roster.
- [ADR-0001](../../decisions/0001-source-code-authority-port.md) protects the
  faithful generator; ADR-0002 and ADR-0004 govern evaluation and promotion.

The package-local predecessor manifest will bind exact committed inputs. A
mismatch is a predecessor-integrity failure, not permission to regenerate or
reinterpret an earlier artifact.

## Plan

1. Verify the predecessor terminal/hashes and rerun all A9b fixtures.
2. Freeze roles, station metadata, logical transforms, source products,
   pooling, candidate laws, resource stages, fit/simulation identities,
   optimizer bounds, and amendment rules before station-series access.
3. Materialize only authorized fit/development inputs and append exact access,
   object-hash, logical-hash, QC, and completeness records.
4. Implement and test both real candidates, immutable fits, hierarchy,
   hard-support checks, monthly reconciliation, recovery, cross-fit, and
   non-isomorphism evidence.
5. Generate 500 paired same-model/null replicates per family and horizon and
   freeze thresholds before inspecting candidate rankings.
6. Run analytic, short-screen, full-development, and eight-burn Pareto stages;
   retain every attempt and publish all objectives and availability.
7. Apply `a9_lexicographic_pareto_v1`, freeze at most one candidate, author the
   report, perform consolidated review, run verification/repository gates, and
   close the roadmap only with the registered terminal.

## Execution & dispatch

Execution is authorized on `main` from exact clean `origin/main` commit
`4e918ecd5d2b37eaa99ae365677f423080069480`; the target is `main`. No branch,
pull request, commit, or push is authorized by this dispatch.

The metadata freeze in `artifacts/data-role-freeze-v1.json` precedes any A9c
station-series access. The existing A8a Daymet objects are exposed evidence and
may be normalized into separate 1980–2009 fit and 2010–2025 development
objects. The USCRN roster is disjoint by station from the locked confirmation
roster and has separate 2010–2017 fit and 2018–2024 development records. Gate
calibration is synthetic same-model/null only.

## Gates

- exact A9a/A9b hashes reproduce and A9b returns `HARNESS-READY-A9C`;
- the metadata-first role freeze predates all station-series access;
- role/path/object/logical/station-period firewalls pass and no confirmation
  target is acquired or read;
- both actual candidate laws pass support, factorization, recovery, cross-fit,
  non-isomorphism, and degenerate-intersection tests;
- all fit artifacts pass exposure, identifiability, hierarchy, and monthly
  analytic/quadrature reconciliation checks;
- 500 paired candidate-blind null replicates per objective family and horizon
  freeze thresholds before candidate ranking;
- the complete staged campaign respects the exact A9 resource ceilings;
- all 31 objectives publish availability and station/stratum/horizon results;
- the frozen selector is reproduced byte-for-byte and selects no more than one
  A9d candidate;
- the scientific report and consolidated review pass their acceptance gates
  with zero open P1/P2 findings;
- `git diff --check` plus untracked whitespace scan;
- `cargo fmt --check`;
- `cargo clippy --all-targets -- -D warnings`; and
- `cargo test`.

Coverage/CRAP is not triggered unless production functions under `crates/`
change; such a change is outside this package.

## Exit criteria

Success is exactly `CANDIDATE-FROZEN-READY-A9D` with one complete sealed A9d
freeze. Legitimate holds are the seven named A9c holds in the predecessor
handoff. A hold retains all negative evidence and authorizes neither A9d nor a
replacement search.

## Execution outcome

A9c returns `HOLD-A9C-GATE-CALIBRATION`. It verified and replayed A9b,
froze the data/campaign boundaries before series access, materialized 40
Daymet and 24 USCRN normalized role objects from 180 hash-ledgered USCRN
station-years, and calibrated 7,000 candidate-blind null identities. Five
official-schema fit artifacts completed before the upstream availability stop.

The hot-arid development stations supplied 136 and 97 valid events. The
objective registry therefore yields 0/2 available hot-arid stations for
mandatory time-to-peak and peak-ratio objectives (150 events required) and
joint dependence (200 required), producing three failed mandatory cells.
Global borrowing remains valid only for duration under its distinct rule.

No development score, 31-objective candidate vector, Pareto frontier,
lexicographic selection, A9d freeze, or confirmation station-year series was
accessed. The incomplete downstream phases are intentionally not presented as
passed gates. The accepted public report and consolidated review describe the
availability hold without making a candidate-quality claim. No production
crate, generation profile, station schema, or vendored Fortran source changed.

The first follow-on action, if separately authorized, is a new metadata-only
re-entry design that prospectively demonstrates two event-development sites
per mandatory stratum can meet the 150/200-event support floors. It may not
amend A9c outcomes or use the locked confirmation series.

Terminal: `HOLD-A9C-GATE-CALIBRATION`. A9d and A9e remain unauthorized.

## Artifacts

- `artifacts/data-role-freeze-v1.json` — pre-access station/period/source and
  logical-role freeze.
- `artifacts/observed-source-manifest-v1.json` and
  `observed-access-log-v1.ndjson` — exact observed identities and access log.
- `artifacts/null-thresholds-v1.json` — completed candidate-blind numeric
  calibration.
- `artifacts/gate-calibration-availability-v1.json` — canonical three-cell
  availability failure and terminal.
- `artifacts/fit-attempt-inventory-v1.json` — five valid pre-hold fits and the
  explicit zero-development-score boundary.
- `artifacts/gate-results.md` — scientific, reproduction, and repository gate
  outcomes at the registered hold.
- `artifacts/review.md` — accepted consolidated review with zero open P1/P2.
- `artifacts/reentry-requirements.md` — recommendation-only future design
  boundary.
- `artifacts/large/` — LFS-managed normalized observed and retained campaign
  evidence at or above the package retention threshold.
