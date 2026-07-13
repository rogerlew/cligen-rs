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

**Ratified 2026-07-12: file/schema modernization precedes the first
model-structure study.** Only A4a is ready for dispatch; each later item opens
after its predecessor is accepted.

| Order | Item | Mechanism | Acceptance |
|---|---|---|---|
| 1 | **A4a — Modern fixed-monthly station schema + lossless adapter** | Specify a versioned, unit-explicit, provenance-bearing representation of the existing fixed-monthly CLIGEN 5.32.3 station model; retain legacy `.par` intake and add deterministic legacy-to-modern conversion. The package specification selects the serialization. | Bit-identical raw typed station state and unchanged `sta_parms` snapshots; all 12 faithful goldens remain byte-identical through either intake; deterministic serialization; unknown schema/model/unit variants and annual fields fail closed. Validate the adapter over the five hash-pinned Q2 station collections, with summary evidence outside the executable fixture set. |
| 2 | **A1 — Independently versioned typed output + provenance** (SPEC-PROVENANCE, SPEC-CLI-PARQUET) | Add a typed row stream and `.cli.parquet` while preserving legacy `.cli`; provenance names the independent station-schema, station-model, generation-profile, output-schema, fit, and source identities. | Output/provenance specs ratified; `.cli` identity preserved; Parquet schema and metadata deterministic; openWEPP-side consumption remains an openWEPP package. |
| 3 | **A5a — Quality metrics v3 + observed target corpus** | Extend the instrument for monthly and annual precipitation/Tmax/Tmin dispersion and dependence, fuller spell/tail behavior, storm time-to-peak and peak-ratio dependence, winter-process proxies and downstream WEPP responses, and multiple burns. | Versioned metric schema and hash-pinned observed targets; preregistered 30/100-year, multi-seed gates; climate winter proxies remain distinct from physical snowpack and soil-state metrics. |
| 4 | **A5b — Interannual candidate spike** | Fit outside the faithful generator and compare a monthly-SD/rank-one baseline, canonical monthly covariance, Fourier/EOF coefficients, vector AR, HMM, and a spectral benchmark, plus a narrow higher-order precipitation occurrence/amount-dependence counterfactual. This is an experiment, not a promoted profile. | Same corpus, seeds, horizons, fitting periods, and quality vector for every candidate; parameter counts and failure modes reported; no candidate silently changes faithful mode. |
| 5 | **A5c — Interannual profile adjudication** | Apply ADR-0002 to the candidate evidence and either promote one declared station-model/profile pair or record a hold. | Promotion requires an evidence-supported versioned model and profile with complete provenance and no material regression in preregistered climate or downstream WEPP metrics; otherwise faithful behavior remains the default and the study closes without promotion. |

A5b is the highest-value scientific work in this sequence, but A4a, A1, and
A5a are enabling dependencies rather than optional preliminaries. The first
modern station schema represents fixed monthly behavior exactly: it does not
carry optional annual SD or Fourier fields that faithful mode would ignore.
Any interannual parameterization must declare a separate station-model
identifier with required fields.

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
| A5d+ | **Subsequent model-structure studies** | Daily precipitation structure; wet/dry-conditioned radiation; full subdaily forcing and external storm benchmarks; later scenario and multisite/spatial arcs. Single-storm generation remains a deprecated companion rather than part of the first interannual study. | Each study receives its own preregistered package and ADR-0002 adjudication; no component is promoted in isolation without its required dependence and downstream-response gates. |
| A6 | **PyO3 surface** (SPEC-PYO3) | Python bindings, Arrow zero-copy hand-off | wepppy consumes without flatfiles |

**The faithful-mode port (items 1-8) is complete** (2026-07-09,
`20260709-output-cli-port`): `cligen run` on the 12 golden runspecs
reproduces the golden `.cli` files byte-identically. Faithful mode is
now ADR-0002 scaffolding: frozen, gated, carrying the ablation
platform for Q3 and the compatibility bridge — with its retirement
condition on record.
