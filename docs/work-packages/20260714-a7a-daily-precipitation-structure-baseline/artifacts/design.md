# A7a Design and Interpretation Boundary

Status: frozen before new A7a-derived output
Date: 2026-07-14

## Question

Does the existing fixed-monthly CLIGEN model exhibit a material, repeatable
daily precipitation-structure gap against the exposed 17-station Daymet
corpus, with enough GHCN sensitivity support to justify a separate analytic
model-feasibility package?

## Access boundary

The A5a corpus, baseline quality reports, and earlier broad quality summaries
were already visible. Before this freeze, no A7a seasonal aggregation,
second-order occurrence residual, trajectory-null family distance, gap
ranking, propagation diagnostic, or A7a terminal decision had been produced.
The exact A7a derivation is prospective relative to those new outcomes, but
the parent data are not an independently sealed confirmation set.

## Measurement posture

The primary surface is Daymet V4 R1 over the fixed 1980–2025 no-leap window at
all 17 stations. The eight screened GHCN-Daily series are sensitivity evidence,
not a substitute primary target. A generated R1mm wet day is a rendered daily
precipitation value greater than or equal to 1.0 mm.

The eight burn offsets are deterministic trajectory offsets, not IID samples.
A7a uses their bounded leave-one-trajectory-out spread as a stringent internal
null, not as a confidence interval. A model/observed family distance is called
material only when it exceeds every corresponding leave-one-out trajectory
distance at that station, horizon, and QC arm.

## Daily families

- Seasonal spells use DJF/MAM/JJA/SON and attribute a whole contiguous wet or
  dry spell to its starting season. Missing observed days break continuity.
- Higher-order occurrence residuals compare each seasonal
  `P(W_t | W_{t-2}, W_{t-1})` with the corresponding first-order
  `P(W_t | W_{t-1})`; the residual is descriptive, not a fitted model.
- Wet-amount dependence uses Pearson and tied-rank Spearman correlation only
  for adjacent-calendar-day pairs where both days are R1mm wet.
- Upper tails use seasonal wet-day p95 and p99 amounts.
- Multi-day extremes use p50/p90/p95 across complete-year maxima of 1-, 3-,
  and 5-day contiguous totals, with windows attributed to their end year.
- Monthly and annual dispersion use sample SD of complete-period precipitation
  totals and are diagnostics, not terminal-decision families.

## Distance and decision restraint

Positive quantities use absolute natural-log ratios; signed correlations and
occurrence residuals use absolute differences. A family distance is the median
over components available in the observation and all eight trajectories. The
null ceiling is the maximum of eight leave-one-trajectory-out family
distances. No p-value or population confidence interval is inferred.

Analysis amendment 003 clarifies the frozen minimum-component rule after
component-availability access: a cell below its family minimum is unavailable,
has no distance or severity, and is conservatively non-material. No component
is imputed and no family minimum is lowered. H1–H4 are therefore amended rather
than confirmatory.

The binary decision requires one core family to cross all three frozen breadth
guards at both horizons: at least 12/17 material Daymet misses under
`qc_filter: off`, at least 10/17 faithful corroborations, and at least 5/8
material GHCN misses under `qc_filter: off`. This rule identifies a priority
for feasibility work; it does not establish a causal mechanism or guarantee
that a particular augmentation will improve monthly or annual behavior.

Propagation is reported only as cross-station co-localization and Spearman
association between daily-family distance and monthly/annual dispersion
distance. It must not be described as causal transmission.
