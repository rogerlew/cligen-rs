# SPEC-QUALITY-REPORT — Machine-Readable Climate Quality Report

Status: active (rev 8 — A5a advances only `metrics_version = 3`, adding
complete-period monthly/annual dispersion and dependence, R1mm
precipitation structure, corrected event-descriptor semantics, and explicit
winter air-temperature proxies; the report envelope remains version 2. Rev 7 — A1 adds independent `quality_report_schema_version =
2`, generic station content identity, and shared SPEC-PROVENANCE without
changing `metrics_version = 2`; rev 6 — A4a permits run-emitted targets from a modern
fixed-monthly station document without a metrics-version change. Rev 5 — Q3 implements the `qc_filter: off`
counterfactual: **metrics_version 2** adds `process.counterfactual`
(would-have-been K-S/mean/variance verdicts over the produced
batches, evaluated against a parallel diagnostic copy of the QC
state — generation state untouched). Ruling on the record:
`fast_batch_v0` reports keep `counterfactual: null` — the faithful
verdicts are defined over the source's rolling-predecessor batch
stream, which the v0 producer does not have; a batch-line
counterfactual surface, if ever needed, belongs to the v1 promotion
work. Rev 4 — R1 finding C-R1-003 dispositioned in Stage
R2: counterfactual QC verdicts, including `fast_batch_v0`'s, begin
with Q3, which owns their metrics-version consequence; metrics_version
1 carries none. Rev 3 — ratified by the implementing package
`20260710-q1-quality-report`; rev 3 records the contract defects
implementation exposed, as package findings F1-F3: the post-hoc
equality null set extends to every run-only surface, group C
`by_decade` is decade-level, sidecar/stdout emission semantics
pinned. Rev 2 = R1 review dispositions: identity content/provenance
split, group P keyed on qc_filter with retry-cap give-up reporting,
estimator pins)
Surface: the `<output>.quality.json` sidecar emitted with every
generated `.cli`, the `cligen quality <file.cli> --par <file.par>`
standalone subcommand, and the metric definitions both share.

## Purpose

ADR-0002 makes quality metrics the correctness authority for all
non-faithful generation. This spec defines the instrument: every run
self-reports a versioned metric vector; adjudicating profiles,
horizons, or the legacy binary means comparing reports. The report
never gates a run — bounds and decision rules belong to
pre-registered campaign packages, not to the emitter.

## Producers / consumers

Producers: `cligen run` (all profiles, all modes, on by default) and
`cligen quality` (post-hoc, over any WEPP-format `.cli` including
legacy-Fortran output). Consumers: adjudication packages, wepppy /
WEPPcloud pipelines, and dashboards. A1 Parquet embeds the same run identity,
not the quality vector: provenance says what made an artifact; quality says
what the paired text climate statistically is.

## Input surface — deliberately the text `.cli`

Metrics are computed from the parsed daily rows of the `.cli` text
surface, not from in-process f32 state, because:

1. the text surface is the consumer contract — its FORMAT quantization
   is what WEPP/WEPS actually receive; and
2. it makes the instrument universal: the same code path measures
   cligen-rs output and a legacy-Fortran `.cli` byte stream.

One exception: **process metrics** (§Metric groups, group P) are
observable only during generation and appear only in run-emitted
reports; `cligen quality` reports them as `null`.

## Emission

- Default: writing `<name>.cli` also writes `<name>.cli.quality.json`.
- Opt-out: runspec `output.quality: false`.
- Collision semantics (rev 7): `output.overwrite` governs both declared
  climate destinations (`.cli` and optional Parquet). Derived provenance and
  quality companions are atomically rewritten when enabled. `cligen quality`
  writes the report to stdout and creates no files.
- The report's identity splits into two blocks (with independent
  `quality_report_schema_version` and `metrics_version`
  top-level). **`content`** (recoverable from the inputs alone,
  present in every report): tool version, station model,
  syntax-independent station parameter-set SHA-256, declared legacy-source
  SHA-256, `.cli` SHA-256, day count, year count and calendar span as parsed
  from the rows. **`provenance`** (trusted run-emission only; always `null`
  from public post-hoc `cligen quality`/library computation): the full revision-1
  SPEC-PROVENANCE object for the paired text artifact.
  A bare `.cli` cannot authoritatively recover these — the header
  command echo is a verbatim, arbitrary field (SPEC-RUNSPEC §Header
  echo) and is never parsed as authority.
- Determinism: all accumulation in f64; sample statistics use the
  n−1 convention; **skew** is the adjusted Fisher–Pearson estimator
  g1·√(n(n−1))/(n−2) (n ≥ 3, else `null`); Spearman uses
  average-rank ties; **top-N event ordering** breaks ties by earlier
  date, then lower row index; decades are fixed 10-year blocks from
  the first simulated year (a trailing partial decade is reported
  with its `n_years`); JSON keys are emitted in schema order. A given
  `.cli` + fixed-monthly station state and its declared source identity
  yields a byte-reproducible report.

## Metric groups (`metrics_version: 3`)

All per-month groups key on calendar month over the whole run and
additionally per decade block (`by_decade`), so 30- vs 100-year
behavior is visible inside a single run. Rev 3 altitude pin (F2):
groups A and B carry full month × decade cells; group C `by_decade`
blocks are **decade-level** (correlations, contrast, and daily range
over each decade's days) — month × decade wet-day correlation cells
hold only tens of samples at a 10-year block and price nothing.

**A — par_convergence** (authority: the fixed-monthly station contract)
Per parameter × month: generated vs station target, absolute and
relative error, for: precipitation wet-day mean / SD / skew; wet-day
fraction, `P(W|W)`, `P(W|D)`; tmax / tmin mean and SD; radiation
mean; dew-point mean; wind speed mean. Targets are the shared typed values
from parsed `.par` or a validated A4a station document (post the source's own
seed corrections where the generator applies them — the target is what the
generator was *asked* to reproduce).

**B — interannual** (authority: observed climate, external)
Only complete Gregorian months/years enter dispersion or dependence; an
EOF-truncated observed tail remains visible in identity/tails but cannot bias
an annual statistic. Annual cells contain precipitation total, trace-positive
and R1mm wet-day counts, maximum daily precipitation, and annual mean
Tmax/Tmin. Per-calendar-month cells contain precipitation-total mean/SD/CV,
trace-positive and R1mm wet-day-count and wet-day-mean-amount dispersion, and
monthly-mean Tmax/Tmin mean/SD (temperature CV is deliberately absent).

Dependence contains:

- 12×12 pairwise-complete covariance and Pearson-correlation matrices for
  monthly precipitation-total, Tmax-mean, and Tmin-mean anomalies, ordered
  January through December on both axes;
- per-month Pearson/Spearman precipitation–Tmax, precipitation–Tmin, and
  Tmax–Tmin anomaly correlations;
- annual lag-one Pearson/Spearman correlations and a low-frequency power
  fraction for annual precipitation total and annual mean Tmax/Tmin.

The low-frequency fraction is the two-sided demeaned periodogram power in
nonzero Fourier bins whose periods are at least four years divided by total
nonzero power. For n observations, positive bins `k = 1..floor(n/2)` use
period `n/k`; non-Nyquist bins receive weight two and an even-n Nyquist bin
weight one. The implementation uses pinned `libm` sine/cosine. Zero-variance,
fewer-than-four-year, and non-finite cases are `null`.

Annual and monthly dispersion retain `by_decade` blocks. Dependence is
whole-run because ten-year month matrices are too weak to be a decision
surface. The report carries no observed-data comparison itself;
SPEC-OBSERVED-TARGET-CORPUS supplies the external join.

**C — covariation** (authority: observed climate, external)
Wet-day Pearson and Spearman correlations, per month and whole-run:
amount×duration, amount×peak-intensity-ratio, duration×radiation;
radiation wet/dry contrast (mean radiation on wet days ÷ dry days,
per month); tmax−tmin daily-range mean (sanity surface). Group C also carries
`winter_air_temperature_proxies`:

- whole-run and monthly precipitation fraction on days whose mean air
  temperature `(Tmax + Tmin)/2` is `<= 0 °C`, including numerator,
  denominator, and day count;
- Pearson/Spearman dependence between R1mm precipitation and mean air
  temperature on December/January/February days;
- per-year and complete-year dispersion of transitions between consecutive
  daily mean-air states `<= 0 °C` and `> 0 °C`, with a transition across a
  year boundary attributed to the second day.

These are explicitly air-temperature/precipitation proxies. They are not a
physical rain/snow partition, snowpack, snowmelt, rain-on-snow runoff, frost
depth, or soil freeze/thaw state. Those responses use the separate
SPEC-A5-EVALUATION record. Note on
record: the current model generates radiation independent of
wetness, so faithful output is expected to show contrast ≈ 1 and
correlation ≈ 0 — group C prices a structural absence (layer 3) and
motivates tier-2 augmentation profiles; it does not discriminate
among current RNG/QC configurations.

**D — tails, precipitation structure, and event descriptors**
The historical v2 spellings `storm_count` and `peak_intensity` were
misleading: a positive-rain row is one wet event day and `.cli ip` is the
dimensionless peak/mean intensity ratio `xmav`. Metrics v3 uses
`wet_event_day_count` and `peak_intensity_ratio` throughout.

Per year, Group D reports completeness, maximum 1/3/5-day precipitation,
wet-event-day count, maximum peak-intensity ratio, and longest wet/dry spell
clipped to that year. Rolling 3/5-day sums are evaluated over the contiguous
stream and assigned to the year of the final day. Whole-run top events include
depth, duration, time-to-peak fraction, peak-intensity ratio, date, and row
index. Ranking uses every positive-precipitation row. The three descriptor
fields preserve their raw finite `.cli` values even when they fail the
descriptor-validity predicate below; descriptor filtering never changes
top-event identity.

Two precipitation-structure surfaces are emitted: `trace_positive`
(`precipitation > 0`) and `r1mm` (`precipitation >= 1.0 mm`). Each contains:

- wet/dry spell-length distributions over the whole contiguous row stream,
  so spells cross month/year boundaries, plus distributions by spell start
  month;
- wet-day amount distribution and adjacent-calendar-day wet-amount
  Pearson/Spearman correlation;
- distributions across complete years of annual maximum 1/3/5-day totals.

A scalar distribution is `{n, mean, sd, p50, p90, p95, p99, max}`. Quantiles
use the empirical inverse CDF/nearest-rank rule: for `0 < p <= 1`, sorted
index `ceil(p*n)-1`; empty distributions are all `null`.

Event-descriptor metrics use positive-precipitation rows with duration > 0,
time-to-peak in `[0,1]`, and peak-intensity ratio >= 0. They report included
and excluded counts; depth, duration, time-to-peak, and ratio distributions;
and all six pairwise Pearson/Spearman relationships among those four fields.
Daily Daymet/GHCN observations do not provide descriptor targets, so these
remain a no-silent-regression surface until a versioned high-resolution
target corpus exists.

**P — process** (run-emitted only; `null` from `cligen quality`)
Keyed on `qc_filter` alone, regardless of RNG backend. When
`qc_filter: faithful`: per parameter × month retry counts, final
acceptance statistics, and **retry-cap give-up events** (the source
accepts a still-failing batch after 10,000 redos, cligen.f:4302-4332
— cap hits are reported so "rejection rate 0" is never silently
false). When `qc_filter: off`: the faithful K-S / mean / variance
verdicts evaluated diagnostically over the produced batches — the
would-have-been-rejected rate, the single number that prices what
conditioning was removed. (`fast_batch_v0` predates the knob and is
always unconditioned; its reports carry `qc_filter: null` and — rev 5
ruling — `counterfactual: null`: the faithful verdicts are defined
over the source's rolling-predecessor batch stream, which the v0
producer does not have. Historical: rev 4 had deferred a possible
fast-v0 counterfactual surface to Q3; Q3 ruled it undefined instead.)
Plus: `bk7.v7 == 0.0` recovery count,
Tdew range-check events, and per-run RNG draw totals. Diagnostic
evaluation must not mutate generation state.

## Report envelope (sketch)

```json
{
  "quality_report_schema_version": 2,
  "metrics_version": 3,
  "identity": {
    "content":    { "tool": "...", "station_model": "fixed_monthly_5_32_3",
                    "station_parameter_set_sha256": "...",
                    "station_source_sha256": "...", "cli_sha256": "...",
                    "days": 36524, "years": 100, "span": [1, 100] },
    "provenance": { "provenance_schema_version": 1, "...": "..." } },
  "par_convergence": { "precip_wet_mean": { "jan": { "target": ..., "generated": ...,
      "abs_err": ..., "rel_err": ... }, "...": "...",
      "by_decade": [ ... ] }, "...": "..." },
  "interannual":   { "annual": "...", "monthly": "...", "dependence": "..." },
  "covariation":   { "...": "...", "winter_air_temperature_proxies": "..." },
  "tails":         { "per_year": "...", "precipitation_structure": "...",
                     "storm_descriptors": "..." },
  "process":       { "...": "..." }
}
```

For the explicit A8c development profile, `station_model` may instead be
`a8c_integrated_daily_v1` and `station_parameter_set_sha256` identifies the
complete revision-2 routed parameter payload. This expands an independently
versioned model-identity vocabulary; it does not change quality schema 2 or
metrics version 3. Existing profiles retain `fixed_monthly_5_32_3` and their
existing bytes.

The implementation package publishes the full combination JSON Schema
(`docs/specifications/quality-report-s2-m3.schema.json`) with this structure;
unknown fields are rejected. `quality-report-v2.schema.json` remains the
immutable envelope-2/metrics-2 resource.
The pre-A1 envelope remains immutable at `quality-report-v1.schema.json`;
`quality-report.schema.json` is only a latest-version convenience alias.

## Modes

- Continuous / observed / storm modes all emit reports. A one-day storm has
  group D plus identity and, on trusted run emission, group P; post-hoc storm
  reports have group P null. One day supports no A/B/C distributional metric.
- Observed mode (`iopt = 6`) reports carry
  `identity.provenance.generation.mode: "observed"` (run-emitted); group A
  additionally carries a top-level boolean field
  `par_convergence.observed_passthrough` (true when mode is known to
  be observed, `null` post-hoc): the errors there measure the
  observed series against the station `.par` — a data-vs-parameter
  consistency surface, not generator quality.

## Non-goals

- No pass/fail, no thresholds, no gating — bounds live in campaign
  pre-registrations (SPEC-FAST-BATCH-V1 §Quality assessment pattern).
- Not a replacement for faithful-mode byte-identity gates.
- No embedded observed-data comparison, no network access.
- Not the extensibility surface for arbitrary user metrics; new
  metrics require a `metrics_version` bump.

## Acceptance (for the implementing package)

- Report emission does not perturb faithful golden byte identity
  (sidecar only; the `.cli` byte stream is untouched).
- `cligen quality` over a golden `.cli` equals the run-emitted report
  for the same file after nulling **every** run-only surface: group
  P, `identity.provenance`, and
  `par_convergence.observed_passthrough` (rev 3, F1 — the rev 2
  two-surface null set was not satisfiable: `observed_passthrough` is
  true/false when the mode is known and null post-hoc, so byte
  equality failed for every mode).
- Run over a legacy-Fortran `.cli` (fixture cross-references)
  produces a well-formed report — the legacy-measurability check.
- Determinism: repeated runs produce byte-identical reports.
- Changing report-envelope or metric-vector versions is independent: A1
  changes only `quality_report_schema_version`; A5a retains ownership of
  `metrics_version: 3`.
