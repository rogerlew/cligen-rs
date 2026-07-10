# SPEC-QUALITY-REPORT — Machine-Readable Climate Quality Report

Status: draft rev 1 (contract under ADR-0002; implementation package
to ratify)
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
WEPPcloud pipelines, dashboards, the future `.cli.parquet` metadata
block (SPEC-PROVENANCE pairing: provenance = what made the file;
quality = what the file statistically is).

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
- The report embeds run identity: `metrics_version`, tool version,
  `.par` SHA-256, `.cli` SHA-256, `generation_profile`, `qc_filter`,
  `rng.burn`, mode, years simulated, day count, and (run-emitted only)
  the resolved runspec fields.
- Determinism: all accumulation in f64; sample statistics use the
  n−1 convention; Spearman uses average-rank ties; decades are
  fixed 10-year blocks from the first simulated year (a trailing
  partial decade is reported with its `n_years`); JSON keys are
  emitted in schema order. A given `.cli` + `.par` yields a
  byte-reproducible report.

## Metric groups (`metrics_version: 1`)

All per-month groups key on calendar month over the whole run and
additionally per decade block (`by_decade`), so 30- vs 100-year
behavior is visible inside a single run.

**A — par_convergence** (authority: the `.par` contract)
Per parameter × month: generated vs `.par` target, absolute and
relative error, for: precipitation wet-day mean / SD / skew; wet-day
fraction, `P(W|W)`, `P(W|D)`; tmax / tmin mean and SD; radiation
mean; dew-point mean; wind speed mean. Targets are the parsed `.par`
values (post the source's own seed corrections where the generator
applies them — the target is what the generator was *asked* to
reproduce).

**B — interannual** (authority: observed climate, external)
SD and CV across years of: annual precipitation total, annual wet-day
count, annual maximum daily precipitation, annual mean tmax / tmin;
per-calendar-month interannual SD of monthly precipitation totals.
All with `by_decade` blocks — the cumulative-QC prediction (early
decades underdispersed) is read directly from this group. The report
carries no observed-data comparison itself; adjudication packages
join reports against observed series.

**C — covariation** (authority: observed climate, external)
Wet-day Pearson and Spearman correlations, per month and whole-run:
amount×duration, amount×peak-intensity, duration×radiation;
radiation wet/dry contrast (mean radiation on wet days ÷ dry days,
per month); tmax−tmin daily-range mean (sanity surface). Note on
record: the current model generates radiation independent of
wetness, so faithful output is expected to show contrast ≈ 1 and
correlation ≈ 0 — group C prices a structural absence (layer 3) and
motivates tier-2 augmentation profiles; it does not discriminate
among current RNG/QC configurations.

**D — tails**
Per year: maximum daily precipitation, storm count, maximum
peak-intensity, longest wet and dry spell (days). Whole-run: the top
five daily events (depth, duration, ip, date).

**P — process** (run-emitted only; `null` from `cligen quality`)
QC filter outcomes when active: per parameter × month retry counts
and final acceptance statistics. QC **counterfactuals** when
inactive (`qc_filter: off` or batch backends): the faithful K-S /
mean / variance verdicts evaluated diagnostically over the produced
batches — the would-have-been-rejected rate, the single number that
prices what conditioning was removed. Plus: `bk7.v7 == 0.0` recovery
count, Tdew range-check events, and per-run RNG draw totals.
Diagnostic evaluation must not mutate generation state.

## Report envelope (sketch)

```json
{
  "metrics_version": 1,
  "identity": { "tool": "...", "par_sha256": "...", "cli_sha256": "...",
                "generation_profile": "...", "qc_filter": "...",
                "burn": 0, "mode": "continuous", "years": 100, "days": 36525 },
  "par_convergence": { "precip_wet_mean": { "jan": { "target": ..., "generated": ...,
      "abs_err": ..., "rel_err": ... }, "...": "...",
      "by_decade": [ ... ] }, "...": "..." },
  "interannual":   { "...": "..." },
  "covariation":   { "...": "..." },
  "tails":         { "...": "..." },
  "process":       { "...": "..." }
}
```

The implementation package publishes the full JSON Schema
(`docs/specifications/quality-report.schema.json`) with this
structure; unknown fields are never emitted.

## Modes

- Continuous / observed / storm modes all emit reports; single-storm
  reports carry group D plus identity only (one day supports no
  distributional metric).
- Observed mode (`iopt = 6`) reports are labeled `mode: observed`;
  group A errors there measure the observed series against the
  station `.par` (a data-vs-parameter consistency surface, not
  generator quality) and are flagged `observed_passthrough: true`.

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
  for the same file minus group P (byte-identical after `process`
  nulling).
- Run over a legacy-Fortran `.cli` (fixture cross-references)
  produces a well-formed report — the legacy-measurability check.
- Determinism: repeated runs produce byte-identical reports.
