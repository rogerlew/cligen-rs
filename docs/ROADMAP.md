# cligen-rs Roadmap

Status: living — forward-only queue. Completed items move to the
[work-package record](work-packages/README.md).

Ordering principles: **fixtures before port, faithful before native,
port before augmentation** (the port arc, complete) — and now, under
[ADR-0002](decisions/0002-quality-metrics-authority.md):
**instrument before adjudication, adjudication before promotion.**
No generation-behavior change is recommended before the quality
instrument has measured it at both the 30- and 100-year horizons.

## Active queue — the quality arc (ADR-0002)

The queue is **empty pending two operator ratifications** (the arc's
execution is complete):

- **Q3 executed** (2026-07-10,
  [`20260710-q3-qc-filter-dissection`](work-packages/20260710-q3-qc-filter-dissection/package.md)):
  `qc_filter: faithful | off` implemented (SPEC-RUNSPEC rev 5;
  metrics_version 2 counterfactuals); the ratified 102-run dissection
  quantified the frontier — conditioning discards ~52% of batches in
  every regime, buys material convergence only at 30 yr (B1 1.25 vs
  1.12 at 100 yr), costs material interannual variability at both
  horizons and is farther from observed climate on 15/17 stations,
  and is the dominant generation cost (1.70× median / 8.8× corpus
  total). **Awaiting: ADR-0003 ratification** (Proposed: user-facing,
  default `faithful`, `off` recommended for 100-yr native runs).
- **Q4 executed** (2026-07-10,
  [`20260710-q4-fast-batch-adjudication`](work-packages/20260710-q4-fast-batch-adjudication/package.md)):
  same-instrument comparison against the qc_off re-baseline; the
  pre-pinned promotion gate **fails on performance** (1.32×
  generation-only vs the required 1.5×; quality legs pass — the
  batch line is equivalent, not better). **Awaiting: operator
  retirement decision** (recommendation: retire; v0 stays a closed
  spike).

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

## Deferred augmentation queue

May reorder on demand; each lands behind a versioned profile or spec.

| # | Item | Mechanism | Acceptance |
|---|---|---|---|
| A1 | **Provenance + `.cli.parquet`** (SPEC-PROVENANCE, SPEC-CLI-PARQUET) | Generation-profile block; parquet writer with provenance columns; embeds the Q1 quality report as metadata | Spec ratified; openWEPP-side consumption is openWEPP's package |
| A2 | **Native f64 mode** | Uniform-f64 engine; measured faithful↔native divergence characterization; the idiomatic destination architecture (faithful modules graduate to executable spec) | Divergence documented per variable; profile `native-f64-v1`; quality report ≥ faithful on groups A/B |
| A3 | **Observed parquet input + single-pass substitution + leap-year imputation** (SPEC-OBSERVED-INPUT) | f64 parquet observed series; variable replacement in one pass; leap-day handling | Spec + fixtures; kills the flatfile→wepppyo3→flatfile round-trip |
| A4 | **Par mutation utilities** (residual of the pulled-forward Q2) | Provenance-stamped mutation ops (PRISM localization, future-climate deltas, mean/CV scaling) over the Q2 typed DB | Mutated pars carry lineage; lineage flows into output provenance |
| A5 | **Model-structure augmentations** (was: storm-model extensions) | Modified duration/intensity derivation; NOAA design-storm curves; radiation–wetness coupling and interannual-variance mechanisms (the group-B/C structural gaps the instrument prices) | Each behind its own versioned generation profile; promotion by quality report against observed climate |
| A6 | **PyO3 surface** (SPEC-PYO3) | Python bindings, Arrow zero-copy hand-off | wepppy consumes without flatfiles |

**The faithful-mode port (items 1-8) is complete** (2026-07-09,
`20260709-output-cli-port`): `cligen run` on the 12 golden runspecs
reproduces the golden `.cli` files byte-identically. Faithful mode is
now ADR-0002 scaffolding: frozen, gated, carrying the ablation
platform for Q3 and the compatibility bridge — with its retirement
condition on record.
