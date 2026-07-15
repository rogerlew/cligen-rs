# cligen-rs Roadmap

Status: living — forward-only queue. Completed items move to the
[work-package record](work-packages/README.md).

Ordering principles: **fixtures before port, faithful before native,
port before augmentation** (the port arc, complete) — and now, under
[ADR-0002](decisions/0002-quality-metrics-authority.md):
**instrument before adjudication, adjudication before promotion.**
No generation-behavior change is recommended before the quality
instrument has measured it at both the 30- and 100-year horizons.

The station-file schema version, station-model identifier, generation
profile, and typed-output schema version are independent compatibility
axes. A revision of one does not imply a revision of another.

## Active queue

**Operator correction 2026-07-14: stop the selector/count-construction
escalation and return to the model question left open by A5c.** The A5d0-A5d1b
complete-year selector branch is closed as exploratory evidence rather than a
production prerequisite. A5d1c and the unscaffolded A5d2-A5d5 roadmap items are
cancelled, and their identifiers will not be reused. Useful evaluation and
corpus concepts may be proposed afresh only after a development candidate earns
continuation. The immutable A5d0-A5d1b records retain their evidence and
outcome-time recommendations, but this operator direction supersedes those
recommendations.

The active queue is the ordered A5f1/A7 sequence below. Roadmapping fixes the
dependency order and scope boundaries; it does not authorize a downstream
package after a failed or held predecessor. Every item remains unscaffolded
until separately dispatched, and each scientific contract must be frozen
before its candidate output is generated or inspected.

1. **A5f1 — retired A5e0 runtime cleanup.** Audit the release/API exposure of
   the experimental `pub mod a5e0`, example runner, generator hook, and
   A5e0-only support code. If the surface has not shipped, remove it from the
   current crate; if it has shipped, use an explicit semver-safe deprecation
   disposition rather than silently breaking consumers. Preserve the closed
   specification, schemas, reports, work-package artifacts, source commit,
   and Git history as the reproducibility record. Retain a generic RNG or
   diagnostic primitive only when it has an independently documented use.
   This package generates no climate and adds no replacement mechanism. It
   exits `A5E0-RUNTIME-RETIRED` with faithful parity and public-surface checks
   passing.
2. **A7a — daily precipitation-structure baseline.** Freeze a measurement-only
   contract on the existing 17-station Daymet/GHCN corpus before producing the
   new derived analysis. Quantify seasonal wet/dry spell distributions,
   higher-order occurrence residuals, wet-day amount lag-one dependence,
   wet-day upper tails, 1/3/5-day maxima, and the propagation of daily
   clustering into monthly and annual dispersion. Compare faithful and
   `qc_filter: off` at both 30- and 100-year horizons, reusing hash-identical
   retained output where available. This package adds no candidate model and
   no public quality schema. It exits either
   `DAILY-PRECIPITATION-GAP-MEASURED` or
   `NO-DAILY-STRUCTURE-PRIORITY`; only the former permits A7b.
3. **A7b — analytic precipitation-model feasibility.** Conditional on A7a's
   measured-gap decision, compare one small declared set of integrated daily
   mechanisms: second-order or semi-Markov occurrence and an
   occurrence-conditioned wet-day amount model with limited persistence and a
   tail-aware marginal. Before any generator output, prove or numerically
   certify stationary monthly wet fraction, wet-day amount mean/variance,
   monthly-total moment budgets, valid probabilities/support, fit
   identifiability, and deterministic RNG ownership. Reject mechanisms that
   add variance on top of the monthly contract or require path selection,
   count optimization, or post-generation repair. The package selects exactly
   one bounded A7c mechanism or exits `STOP-PRECIPITATION-LINE`; it does not
   implement a tournament of near misses.
4. **A7c — bounded integrated precipitation pilot.** Conditional on A7b,
   register one generation profile and evaluation contract before code or
   output, then integrate only the selected occurrence/amount mechanism at the
   daily precipitation seam. Run the dry, cold, and wet exposed development
   stations with fixed replicate membership at both horizons. Require monthly
   wet fraction and moment preservation, improved spell/tail/multi-day targets,
   unchanged faithful mode, storm/winter/cross-variable guards, deterministic
   replay/provenance, and explicit intervention-rate ceilings. No annual
   latent state, selector, optimized year library, public promotion, or WEPP
   confirmation is in scope. Only a complete three-station climate pass may
   return `CONTINUE-A7D`; every other scientific outcome closes the tested
   mechanism.
5. **A7d — conditional corpus confirmation and residual adjudication.** Only
   after `CONTINUE-A7D`, freeze a new confirmation package before accessing
   confirmation output. Expand the one unchanged A7c mechanism to the full
   17-station corpus, GHCN sensitivity, both horizons, a faithful-clone null
   for guard calibration, and the complete WEPP campaign with prospectively
   declared response and intervention-rate bounds. Adjudicate the candidate
   and then measure the low-frequency deficit remaining after daily
   precipitation structure is corrected. Promotion, closure, and residual-
   gap findings remain separate decisions. A residual may justify proposing a
   new interannual design study, but it cannot resurrect A5 candidates or
   automatically authorize code. Any such future study must use integrated
   moment reallocation, more than one empirically justified factor if needed,
   hierarchical/regional pooling, and a new package identifier; none is
   roadmapped yet.

A5f0 supplied the pivot into this queue. Its derived-only attribution returned
`RETIRE-SCALAR-IID-MECHANISM` for the exact
`a5e0_direct_annual_state_v1` mechanism and
`a5e0_direct_monthly_loading_fit_v1` recipe. Cross-month dependence supplied
70.6% and 67.9% of positive H1-family degradation at 30 and 100 years, one
component represented only 11.9–16.5% of fit-period annual-feature variance,
and all 96 active loadings responded with the expected sign (global median
realized/expected slope ratio 0.994). No one parameter seam met the frozen
five-of-six localization rule. The disposition is descriptive on the exposed
three-station development surface; it is not causal proof and does not reject
annual-state models generally.

A5e0 remains immutably retained with status
`EXECUTED-HOLD-PROSPECTIVE-BOUNDARY`: its specification, implementation, and
analyzer were not bound at the claimed prospective boundary, so A5f0 does not
retroactively ratify its climate decision. No default or public interface
changed.

The conditional A5e1 expansion is removed from the queue and remains
unscaffolded and unauthorized. A5f0 found no basis for a bounded seam ablation,
so no repair or clean-reproduction chain follows. A7 tests the published
competing explanation that daily precipitation structure contributes to the
aggregate deficit. It is not an A5 repair and does not inherit an A5 candidate.

Exact per-output gates are limited to engineering invariants: faithful-mode
identity, deterministic replay and provenance, fail-closed inputs, valid
calendars and values, and the same-seed 30-year output being the prefix of its
100-year output. Climate moments, dependence, storm descriptors, and winter
behavior are ensemble evaluation targets. Exact finite-path marginal replay,
nested optimized counts, path annealing, and all-station/all-seed climate gates
are not production requirements.

A7d is a conditional roadmap item, not a scaffolded or authorized confirmation
package; it exists only if A7c returns `CONTINUE-A7D`. Wet/dry-conditioned
radiation, full subdaily forcing, external storm benchmarking, and
multisite/spatial generation remain later studies.
Single-storm generation remains deprecated.

The closed selector exploration remains in the work-package catalog:
[A5d0](work-packages/20260714-a5d0-successor-feasibility-calibration/package.md),
[A5d1](work-packages/20260714-a5d1-selector-feasibility/package.md), and
[A5d1b](work-packages/20260714-a5d1b-finite-path-realization/package.md), and
[A5e0](work-packages/20260714-a5e0-direct-annual-state-pilot/package.md), with
the derived disposition in
[A5f0](work-packages/20260714-a5f0-annual-state-failure-attribution/package.md).
The selector branch's stationary-weight result and finite-path failures remain
useful evidence, but its count-search holds do not govern the A5e0
evidence-boundary disposition or A5f0's mechanism-specific retirement.

The A5a–A5c sequence is complete. **A5c executed** (2026-07-14,
[`20260714-a5c-interannual-profile-adjudication`](work-packages/20260714-a5c-interannual-profile-adjudication/package.md))
and accepted [ADR-0004](decisions/0004-a5b-interannual-no-promotion.md): none
of the seven independently versioned A5b candidates passed all climate gates
at both horizons, so no public station model or generation profile was
promoted. The evidence is exploratory for model selection and may support the
conservative rejection only. `faithful_5_32_3` remains the default; station
schema, station model, generation profile, provenance, and output versions
remain independent and unchanged. Any successor considered for promotion
requires a new prospective study with analytic feasibility, monthly variance
reallocation, integrated daily precipitation structure, prospectively
calibrated guards, and complete downstream evidence.

The preceding quality arc (ADR-0002, Q1-Q4) is complete. Both closing
adjudications were ratified by the operator on 2026-07-10 on the R1-amended
record: **ADR-0003 Accepted** (`qc_filter` user-facing, default `faithful`,
`off` a considered opt-in for 100-year variance-priority runs) and **the
fast-batch line retired** (SPEC-FAST-BATCH-V1 → RETIRED; reopening condition
pinned).

The closed arc:

- **Q3 executed** (2026-07-10,
  [`20260710-q3-qc-filter-dissection`](work-packages/20260710-q3-qc-filter-dissection/package.md)):
  `qc_filter: faithful | off` implemented (SPEC-RUNSPEC rev 5;
  metrics_version 2 counterfactuals); the ratified 102-run dissection
  quantified the frontier — ~52% of unconditioned batches fail the
  QC verdicts in every regime (faithful's actual discard cost is far
  larger where it retries), the convergence buy is real with an
  estimator-sensitive horizon profile (R1-corrected), the
  interannual-variability cost is material at both horizons and
  farther from observed climate on 15/17 stations (single-burn Daymet;
  detrended 14/17, GHCN 6/8), and conditioning is the dominant
  generation cost (1.70× median / 8.8× corpus total).
  **ADR-0003 Accepted** (operator, 2026-07-10, on the R1-amended
  draft: user-facing, default `faithful`, `off` a considered opt-in
  for 100-yr variance-priority runs).
- **Q4 executed** (2026-07-10,
  [`20260710-q4-fast-batch-adjudication`](work-packages/20260710-q4-fast-batch-adjudication/package.md)):
  same-instrument comparison against the qc_off re-baseline: quality
  legs pass (the batch line is equivalent, not better); the
  performance leg was not evaluable as pre-registered (R1 finding 2;
  observed end-to-end gain 1.32× on this host). **Retirement
  ratified** (operator, 2026-07-10) as a portfolio decision with a
  pinned reopening condition.

Dependencies are real, not ceremonial: Q1 (complete) is the
instrument every later item reports through; Q2 (complete) supplies
the regime corpus (and the packaging substrate) Q3/Q4 adjudicate
over; Q3's qc_off re-baseline is the denominator of Q4's performance
case.

**Q2 (station databases + deployability) is complete** (2026-07-10,
[`20260710-q2-station-db`](work-packages/20260710-q2-station-db/package.md)):
the five production collections (us-legacy, us-2015, ghcn-intl, au,
chile) ship as hash-pinned GitHub-release payloads outside the crate
(SPEC-STATION-DB rev 1); `cligen stations sync` is the only
network-touching operation; `nearest` reproduces an independent
oracle across all collections; a fresh install → sync → run
round-trip reproduces the goldens byte-identically through the
cache; `cargo publish --dry-run` is clean at 163.5 KiB. The repo went
public same-day: tokenless `sync` verified for all five collections
(`CLIGEN_SYNC_TOKEN` remains supported but is no longer required).
Addendum: au payload revised to 2026.07.1 — longitudes corrected to
east-positive at the source (pars + catalog, jimf-cligen532
`ddfa671d`), operator-directed
([addendum](work-packages/20260710-q2-station-db/artifacts/au-longitude-correction.md)).

**Q1 (quality-report instrument) is complete** (2026-07-10,
[`20260710-q1-quality-report`](work-packages/20260710-q1-quality-report/package.md)):
every `cligen run` emits a `*.cli.quality.json` sidecar (groups A-D +
group P process metrics, per-decade blocks, byte-deterministic;
SPEC-QUALITY-REPORT active rev 4 with published JSON Schema), and
`cligen quality <file.cli> --par <file.par>` measures any WEPP-format
`.cli` post hoc — legacy-Fortran output included. Faithful golden
byte identity was untouched throughout.

## Other deferred augmentations

These remain outside the active A7 precipitation sequence and may reorder on
operator direction. Each lands behind a versioned profile or specification.

| # | Item | Mechanism | Acceptance |
|---|---|---|---|
| A2 | **Native f64 mode** | Uniform-f64 engine; measured faithful↔native divergence characterization; the idiomatic destination architecture (faithful modules graduate to executable spec) | Divergence documented per variable; profile `native-f64-v1`; quality report ≥ faithful on groups A/B |
| A3 | **Observed parquet input + single-pass substitution + leap-year imputation** (SPEC-OBSERVED-INPUT) | f64 parquet observed series; variable replacement in one pass; leap-day handling | Spec + fixtures; kills the flatfile→wepppyo3→flatfile round-trip |
| A4b | **Station mutation and localization utilities** | Provenance-stamped PRISM localization, future-climate deltas, and mean/CV scaling against the modern station schema; no mutation operation selects generation behavior. | Every mutation is explicit and deterministic, carries complete lineage into output provenance, and produces a schema-valid declared station model. |
| A6 | **PyO3 surface** (SPEC-PYO3) | Python bindings, Arrow zero-copy hand-off | wepppy consumes without flatfiles |

**The faithful-mode port (items 1-8) is complete** (2026-07-09,
`20260709-output-cli-port`): `cligen run` on the 12 golden runspecs
reproduces the golden `.cli` files byte-identically. Faithful mode is
now ADR-0002 scaffolding: frozen, gated, carrying the ablation
platform for Q3 and the compatibility bridge — with its retirement
condition on record.
