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

**Operator-ordered 2026-07-14: resolve the A5d0 holds as independent work
packages before any confirmation candidate exists.** A5d1 is scaffolded as
the next package. A5d2 and A5d3 may begin from the A5d0 evidence independently;
before A5d4, the corpus power result must be revalidated against A5d2's frozen
metric/composite identity. A5d4 depends on successful closure of all three.

| Order | Work package | Dependency and mechanism | Acceptance |
|---|---|---|---|
| 1 | **[A5d1 — Selector feasibility](work-packages/20260714-a5d1-selector-feasibility/package.md)** (`SCAFFOLDED`) | Regenerate hash-bound `faithful_5_32_3 + qc_filter: off` year libraries for the 17 exposed development stations; freeze and solve the complete constrained-weight problem; compare predeclared bounded repeat-safe/calendar-safe path algorithms. | One globally fixed research algorithm, contract, tolerance set, and deterministic fitting/selection rule is structurally feasible at all 17 stations; station-specific fitted weights/coefficients are permitted outputs of that common rule. Selected physical rows remain bitwise unchanged, the frozen monthly/daily and annual-vector rules pass, and one bounded 100-year path supplies the exact selected-index and physical-row prefix for 30 years. Otherwise close on a named hold. |
| 2 | **A5d2 — Successor evaluation calibration** (planned package `YYYYMMDD-a5d2-evaluation-calibration`) | Create a separately versioned `SPEC-A5D-EVALUATION`; implement observation-scaled preservation guards, faithful-clone null calibration, bootstrap-availability rules, and a numeric WEPP reference/criterion. Revision 3 remains immutable. | Every climate and downstream rule is numeric, executable at both horizons, uncertainty-available under its frozen floor, and supported by a defensible null-independence/audit design before candidate confirmation output. |
| 3 | **A5d3 — Confirmation corpus qualification and seal** (planned package `YYYYMMDD-a5d3-confirmation-corpus`) | Run calibration-only spatial/composite power analysis; select stations from metadata only; acquire, qualify, hash, and seal an untouched primary corpus and new long-record sensitivity set. The 28-station design remains only a planning floor. | Fit, development, null-calibration, confirmation, and sensitivity roles are disjoint; the actual powered count is justified against the frozen A5d2 metric identity; target construction is reproducible and sealed with zero value exposure. |
| 4 | **A5d4 — Candidate freeze review** (planned package `YYYYMMDD-a5d4-candidate-freeze-review`) | Bind the immutable A5d1 selector, A5d2 evaluation, and A5d3 corpus records; pin exactly one experimental candidate, exact executable, coefficient schema/bundle and fitting identity, comparison/null identities, replicate counts, seeds, complete climate/WEPP matrix, verifier, and synthetic conformance evidence. | A later campaign can execute without discretionary post-exposure choices. A5d4 does not run or score confirmation output and changes no public default or profile enum. |

The downstream confirmation run is a separately dispatched
`YYYYMMDD-a5d5-candidate-confirmation-campaign`. It is named here as an
evidence-freeze barrier, not scaffolded or authorized. Wet/dry-conditioned
radiation, full subdaily forcing, external storm benchmarking, and
multisite/spatial generation remain later studies. Single-storm generation
remains deprecated.

**A5d0 held** (2026-07-14,
[`20260714-a5d0-successor-feasibility-calibration`](work-packages/20260714-a5d0-successor-feasibility-calibration/package.md)):
a constructive fixture proves complete-year selection can reallocate variance
in some libraries, but no bounded repeat-safe, calendar-safe, common-prefix
selector is specified or demonstrated on faithful development libraries. The
package closes `HOLD-CONTRACT-INCOMPLETE`; evaluation calibration and an
untouched confirmation corpus are separately held. No A5d candidate output or
public surface was created. The first follow-on is a development-only
constrained-weight and repeat-safe path solver package; confirmation remains
forbidden.

The A5a–A5c sequence is complete. **A5c executed** (2026-07-14,
[`20260714-a5c-interannual-profile-adjudication`](work-packages/20260714-a5c-interannual-profile-adjudication/package.md))
and accepted [ADR-0004](decisions/0004-a5b-interannual-no-promotion.md): none
of the seven independently versioned A5b candidates passed all climate gates
at both horizons, so no public station model or generation profile was
promoted. The evidence is exploratory for model selection and may support the
conservative rejection only. `faithful_5_32_3` remains the default; station
schema, station model, generation profile, provenance, and output versions
remain independent and unchanged. Any successor requires a new prospective
study, with analytic feasibility, monthly variance reallocation, integrated
daily precipitation structure, prospectively calibrated guards, and complete
downstream evidence.

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

These remain outside the ratified five-package sequence and may reorder on
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
