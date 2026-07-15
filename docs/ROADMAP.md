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

**Operator direction 2026-07-15: continue stochastic climate-generator
development, retire the stopped A8c runtime first, and replace incremental
candidate rescue with a calibration-first successor family.** File/I/O,
openWEPP, WEPPcloud, PyO3, and other consumer-integration work remains deferred;
it is not a prerequisite for this research sequence.

The ordered active queue is:

1. **A8c1 — routed-daily runtime retirement.** Remove the unpromoted
   `a8c_routed_daily_v1` generation profile and its model-specific station,
   runtime, schema, provenance, and quality-report surfaces while preserving
   the complete A8a--A8c scientific record and faithful behavior. Compatibility
   axes are adjudicated independently: a generic seam survives only if the
   retirement audit proves it has a non-A8c contract and consumer. This package
   is [scaffolded](work-packages/20260715-a8c1-routed-daily-retirement/package.md)
   and executes first.
2. **A9a — successor-family foundation.** After A8c1 closes, specify a new
   joint precipitation/event/daily-context model family and an optimizer-
   neutral calibration harness. A9a must derive its requirements from the
   accepted A5--A8 records and SOTA review; define fit, development,
   gate-calibration, and untouched-confirmation evidence roles; cover arid,
   arid-boundary, monsoonal, other semi-arid, humid, and cold regimes without
   runtime climate classification; and separate tunable development from one-
   shot locked adjudication. It changes no production generator and selects no
   candidate. The package is
   [scaffolded](work-packages/20260715-a9a-successor-family-foundation/package.md).

The conditional successor sequence is A9b calibration-harness implementation,
A9c development-only comparison of genuinely distinct model classes, A9d
locked held-out climate confirmation, and A9e Rust runtime pilot. Those
packages remain unscaffolded and unauthorized until their predecessor returns
the registered continuation terminal. A9 does not inherit an A8c candidate,
coefficient, threshold, station classification, or confirmation claim. A
future production-promotion decision still requires separately roadmapped
downstream evidence under ADR-0004; the present sequence neither performs nor
waives openWEPP/WEPPcloud integration.

**Operator correction 2026-07-14: stop the selector/count-construction
escalation and return to the model question left open by A5c.** The A5d0-A5d1b
complete-year selector branch is closed as exploratory evidence rather than a
production prerequisite. A5d1c and the unscaffolded A5d2-A5d5 roadmap items are
cancelled, and their identifiers will not be reused. Useful evaluation and
corpus concepts may be proposed afresh only after a development candidate earns
continuation. The immutable A5d0-A5d1b records retain their evidence and
outcome-time recommendations, but this operator direction supersedes those
recommendations.

There is no active A7 item. A7b completed the prospective analytic comparison
and returned `STOP-PRECIPITATION-LINE`. Review showed that its second-order and
two-phase semi-Markov candidates are two parameterizations of the same
four-state binary process, not independent model classes. Both registered
parameterizations cleared the 184-cell corpus-breadth floor with 192/204
feasible cells, but each reached only 31/36 mandatory dry/cold/wet development
cells rather than the required 36/36. Death Valley supplied all five
development failures: its JJA season lacked the registered adjacent-wet-pair
and long-wet-state exposure, and its April and December cells exceeded the
frozen normalized-tail-error bound. No mechanism was selected.

The conditional A7c integrated pilot and A7d corpus confirmation are removed
from the queue, remain unscaffolded, and are not authorized. Relaxing A7b's
prospective gates or choosing the higher-ranked near miss would convert a stop
rule into outcome-time selection, so this roadmap does neither. Any future
precipitation proposal requires a new operator roadmap and package identifier;
it must explain how the arid-station identifiability boundary is handled
without post-generation repair, fixed-count search, or unregistered data
pooling. The accepted A7 record is retained in the
[A7a work package](work-packages/20260714-a7a-daily-precipitation-structure-baseline/package.md),
[A7a public report](reports/a7a-daily-precipitation-structure-report.md), and
[A7b work package](work-packages/20260714-a7b-analytic-precipitation-feasibility/package.md).

The scientific A8 generation line remains closed: A8c completed with
`STOP-A8-ROUTED-DAILY`, A7b's whole-domain stop remains final, and no A8d
confirmation is authorized. A8c1 is retirement hygiene, not scientific
continuation or reinterpretation of that stop.

A8a completed on 2026-07-15 with `CONTINUE-A8B-DRY-PARTITION`. Its prospective
20-station confirmation found 15 `integrated_daily` and five
`legacy_daily_fallback` classifications, reproduced all eight development
dispositions, integrated all four negative controls, reached 0.850
shortened-window agreement, and passed all analytic and terminal guards.
Monsoonal and other-dry instability were both 0.1875, so A8a does not justify a
separate monsoonal campaign. The accepted record is retained in the
[A8a work package](work-packages/20260715-a8a-dry-regime-applicability/package.md).

A8b completed on 2026-07-15 with `USE-LEGACY-DAILY-FALLBACK`. Its exact pooled
two-EOF/AR(1) candidate failed before coefficients because the frozen
1980--2009 El Centro June-total scale is exactly zero; A8b did not drop or
repair the cell and opened no replacement search. The explicit null certified,
so boundary stations retain legacy daily behavior with no secondary year state
or additional RNG. The accepted record is retained in the
[A8b work package](work-packages/20260715-a8b-secondary-year-fallback/package.md).

A8c's explicit six-station routed pilot completed on 2026-07-15. All replay,
nested-horizon, fallback, provenance, and faithful-regression checks passed,
and both registered daily target families improved at both horizons. The
candidate stopped because wet-amount means missed the monthly budget broadly,
integrated time-to-peak medians collapsed to zero, and changing precipitation
occurrence propagated through CLIGEN's wet/dry-conditioned Boise dew-point and
Alamosa wind-speed paths. These are model-structure results, not a fallback or
runtime hold. The exact record is retained in the
[A8c work package](work-packages/20260715-a8c-routed-daily-pilot/package.md).

No A8d confirmation, WEPP response study, threshold relaxation, coefficient
retuning, or public-default change follows. A9 is the separately roadmapped
new family: before implementation it must jointly specify wet-amount
calibration, precipitation-conditioned downstream variables, and storm
time-to-peak semantics rather than treating them as post-generation guards.

Monsoonal climates were a mandatory stratum in A8c. Their
annual precipitation alone is not a safe routing variable: seasonal
concentration can leave dry-season occurrence states weakly identified even
when annual totals appear adequate. A8a found no excess monsoonal instability,
so a separate sequence would duplicate corpus, routing, and fallback work and
is not roadmapped.

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

A5f1 then retired the unshipped A5e0 runtime from current `main`: crates.io has
no `cligen` crate, repository releases predate A5e0, and the exact historical
implementation remains reachable at `1ca40bb`. The closed specification,
schemas, report, and work-package evidence remain in place; no accepted public
interface or faithful behavior changed.

A5e0 remains immutably retained with status
`EXECUTED-HOLD-PROSPECTIVE-BOUNDARY`: its specification, implementation, and
analyzer were not bound at the claimed prospective boundary, so A5f0 does not
retroactively ratify its climate decision. No default or public interface
changed.

The conditional A5e1 expansion is removed from the queue and remains
unscaffolded and unauthorized. A5f0 found no basis for a bounded seam ablation,
so no repair or clean-reproduction chain follows. A7a measured the published
competing explanation that daily precipitation structure contributes to the
aggregate deficit; A7b then found no registered mechanism feasible across the
complete development surface. A7 was not an A5 repair and did not inherit an
A5 candidate.

Exact per-output gates are limited to engineering invariants: faithful-mode
identity, deterministic replay and provenance, fail-closed inputs, valid
calendars and values, and the same-seed 30-year output being the prefix of its
100-year output. Climate moments, dependence, storm descriptors, and winter
behavior are ensemble evaluation targets. Exact finite-path marginal replay,
nested optimized counts, path annealing, and all-station/all-seed climate gates
are not production requirements.

A7c and A7d are closed, unscaffolded conditional concepts rather than active
roadmap items because A7b did not select a mechanism. Wet/dry-conditioned
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
