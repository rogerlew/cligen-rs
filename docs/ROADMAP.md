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

The queue now contains one bounded, production-shaped pilot and one
conditional development expansion. It starts from A5c and
[ADR-0004](decisions/0004-a5b-interannual-no-promotion.md), not from the A5d1b
integer-count hold.

| Order | Work package | Dependency and mechanism | Acceptance |
|---|---|---|---|
| 1 | **A5e0 — Direct annual-latent-state pilot** (planned package `YYYYMMDD-a5e0-direct-annual-state-pilot`) | Freeze one intentionally rank-one mechanism before outcomes: draw one independent scalar annual state and apply it through separate fixed monthly loadings at the precipitation-occurrence, precipitation-amount, Tmax-mean, and Tmin-mean generator seams before daily draws. Store loadings directly as monthly values in a versioned development-only coefficient bundle; defer Fourier/EOF compression, serial persistence, and public station-schema changes. Use a dedicated extension RNG, establish and compensate the monthly variance budget, and generate fresh daily climate rather than select library years. Evaluate independent paired 30-/100-year replicates at three predeclared exposed development stations representing wet, dry, and cold regimes. | Unchanged faithful-profile output remains byte-identical, and the experimental path passes deterministic replay/provenance, fail-closed input, calendar/value validity, and same-seed 30-year-prefix gates. At both horizons, a prospectively frozen ensemble-level rule must show a useful interannual signal without material monthly/daily degradation or catastrophic degradation in any represented regime; otherwise close this mechanism. No default change, user-facing promotion, or confirmation data. |
| 2 | **A5e1 — Conditional development expansion** (planned package `YYYYMMDD-a5e1-annual-state-development-expansion`) | Authorized only by an A5e0 continuation decision. Retain the frozen mechanism, fitting procedure, generator seams, and evaluation semantics; fit the other exposed development stations prospectively; expand evaluation to all 17 stations; and add a bounded downstream WEPP screen without confirmation exposure. | Population- and regime-level evidence either warrants separately roadmapping a candidate freeze and confirmation campaign or closes the line. Success is not conditioned on every station, seed, or finite realization passing every climate metric. |

Exact per-output gates are limited to engineering invariants: faithful-mode
identity, deterministic replay and provenance, fail-closed inputs, valid
calendars and values, and the same-seed 30-year output being the prefix of its
100-year output. Climate moments, dependence, storm descriptors, and winter
behavior are ensemble evaluation targets. Exact finite-path marginal replay,
nested optimized counts, path annealing, and all-station/all-seed climate gates
are not production requirements.

No confirmation package is planned, scaffolded, or authorized until A5e1
succeeds. Wet/dry-conditioned radiation, full subdaily forcing, external storm
benchmarking, and multisite/spatial generation remain later studies.
Single-storm generation remains deprecated.

The closed selector exploration remains in the work-package catalog:
[A5d0](work-packages/20260714-a5d0-successor-feasibility-calibration/package.md),
[A5d1](work-packages/20260714-a5d1-selector-feasibility/package.md), and
[A5d1b](work-packages/20260714-a5d1b-finite-path-realization/package.md). Its
stationary-weight result and finite-path failures remain useful evidence, but
its count-search holds do not block A5e0.

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

These remain outside the active interannual sequence and may reorder on
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
