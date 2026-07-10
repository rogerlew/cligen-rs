# SPEC-QUALITY-REPORT — Machine-Readable Climate Quality Report

Status: active (rev 4 — R1 finding C-R1-003 dispositioned in Stage
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
- Collision semantics (rev 3, F3): the sidecar is **always rewritten**
  when enabled — it is derived data that must correspond to the `.cli`
  just produced; `output.overwrite` governs the `.cli` only. `cligen
  quality` writes the report to stdout and creates no files.
- The report's identity splits into two blocks (with `metrics_version`
  top-level). **`content`** (recoverable from the inputs alone,
  present in every report): tool version, `.par` SHA-256, `.cli`
  SHA-256, day count, year count and calendar span as parsed from the
  rows.
  **`provenance`** (run-emitted only; `null` from `cligen quality`
  unless supplied via explicit flags): `generation_profile`,
  `qc_filter`, `rng.burn`, mode, and the resolved runspec fields.
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
  `.cli` + `.par` yields a byte-reproducible report.

## Metric groups (`metrics_version: 1`)

All per-month groups key on calendar month over the whole run and
additionally per decade block (`by_decade`), so 30- vs 100-year
behavior is visible inside a single run. Rev 3 altitude pin (F2):
groups A and B carry full month × decade cells; group C `by_decade`
blocks are **decade-level** (correlations, contrast, and daily range
over each decade's days) — month × decade wet-day correlation cells
hold only tens of samples at a 10-year block and price nothing.

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
Keyed on `qc_filter` alone, regardless of RNG backend. When
`qc_filter: faithful`: per parameter × month retry counts, final
acceptance statistics, and **retry-cap give-up events** (the source
accepts a still-failing batch after 10,000 redos, cligen.f:4302-4332
— cap hits are reported so "rejection rate 0" is never silently
false). When `qc_filter: off`: the faithful K-S / mean / variance
verdicts evaluated diagnostically over the produced batches — the
would-have-been-rejected rate, the single number that prices what
conditioning was removed. (`fast_batch_v0` predates the knob and is
always unconditioned; its reports carry `qc_filter: null`. Rev 4,
C-R1-003: counterfactual verdicts — for `qc_filter: off` **and** for
`fast_batch_v0` — land with Q3, which implements the diagnostic
evaluation and decides the metrics-version consequence of adding the
field; as of Q1, metrics_version 1 carries no counterfactual surface
and fast-v0 reports hold the null plus counters only.) Plus:
`bk7.v7 == 0.0` recovery count,
Tdew range-check events, and per-run RNG draw totals. Diagnostic
evaluation must not mutate generation state.

## Report envelope (sketch)

```json
{
  "metrics_version": 1,
  "identity": {
    "content":    { "tool": "...", "par_sha256": "...", "cli_sha256": "...",
                    "days": 36525, "years": 100, "span": [1, 100] },
    "provenance": { "generation_profile": "...", "qc_filter": "...",
                    "burn": 0, "mode": "continuous" } },
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
- Observed mode (`iopt = 6`) reports carry
  `identity.provenance.mode: "observed"` (run-emitted); group A
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
