# A5 Interannual Candidate Pre-Registration

Status: **FIXED BEFORE A5a BASELINE OR A5b CANDIDATE OUTPUT**
Date: 2026-07-12
Authority: ADR-0002, SPEC-A5-EVALUATION revision 2

## Questions

1. Can an explicit low-frequency climate state reduce the held-out observed
   deficit in monthly/annual precipitation and Tmax/Tmin dispersion and
   dependence relative to `faithful_5_32_3 + qc_filter: off`?
2. Is any improvement robust to horizon, station/regime, realization, target
   source, and detrending choice?
3. Does it preserve the monthly station contract, precipitation structure,
   storm descriptors, winter climate proxies, and downstream WEPP responses?

## Frozen corpus and periods

- Corpus: `observed_target_corpus_schema_version = 1`, 17 stations and the
  exact content SHA-256 recorded by A5a's corpus manifest.
- Primary target: Daymet V4 R1, held-out 2010–2025.
- Fitting: 1980–2009 only.
- Sensitivities: Daymet full 1980–2025, raw vs OLS-detrended; the independently
  archived GHCN snapshot where each metric has enough complete observations.
- Daymet and GHCN are never pooled.
- Horizons: 30 and 100 complete synthetic years.
- Begin year: 1; mode: continuous; interpolation: none.

## Replicate records

The eight records below are fixed. The extension seed is the first 64 bits,
big-endian, of `SHA-256("cligen-a5-replicate-v1\\0" + decimal_index)`.

| replicate | legacy `rng.burn` | extension realization seed |
|---:|---:|---|
| 0 | 0 | `0x0c8862ed55f21e2e` |
| 1 | 17 | `0x0c268832683959b1` |
| 2 | 101 | `0x1a237b2016b95a3f` |
| 3 | 503 | `0x91328e5fa9a0e916` |
| 4 | 1009 | `0x0ee45605e7d362c3` |
| 5 | 5003 | `0xc59c065475f321a3` |
| 6 | 10007 | `0x9d9ef1d097f866ab` |
| 7 | 50021 | `0x50984769b3e59a89` |

`rng.burn` advances the fixed faithful `k1`–`k9` streams and does not advance
`k10`. These rows are trajectory offsets, not independent seeds. Faithful
baseline ranges are called **empirical across-burn spread**, never confidence
intervals. A5b extension profiles must consume the independent seed through a
domain-separated RNG without perturbing faithful streams.

## Matrices

A5a instrument/baseline validation:

`17 stations × 2 horizons × 8 burn offsets × 2 QC policies = 544 runs`, both
policies on `faithful_5_32_3`. The conditioned leg is compatibility/context;
`qc_filter: off` is the scientific denominator.

A5b candidate matrix:

`17 stations × 2 horizons × 8 replicate records × every candidate`, using the
same fit artifact, quality metrics, and output settings for every candidate.
The required candidates are:

1. rank-one monthly-SD baseline;
2. canonical full monthly covariance;
3. Fourier/EOF coefficient model;
4. vector AR model;
5. Gaussian-mixture HMM;
6. spectral random-phase benchmark;
7. narrow higher-order precipitation occurrence/amount-dependence
   counterfactual.

Exact model/profile identifiers, parameter counts, fit seeds, constraints,
and failure rules must be frozen in the A5b package before it reads candidate
results.

## Metric vector

The sole climate vector is `quality_report_schema_version = 2`,
`metrics_version = 3`. Required families:

- Group A monthly station-contract metrics;
- Group B annual/monthly precipitation and temperature dispersion;
- Group B cross-month/cross-variable anomaly dependence, lag one, and
  period-≥4-year low-frequency power fraction;
- Group C daily covariation and winter air-temperature proxies;
- Group D trace-positive and R1mm spells, wet amount persistence,
  1/3/5-day maxima, and event descriptor distributions/dependence;
- the separately versioned downstream-WEPP response record.

Generated files with any missing report, invalid schema, mismatched hash, or
fewer usable target cells than the baseline fail evidence completeness.

## Estimator and aggregation pins

- Generated report estimators are those in SPEC-QUALITY-REPORT revision 8.
- Target uncertainty uses the deterministic five-year circular block
  bootstrap in SPEC-A5-EVALUATION (2,000 replicates).
- Candidate replicate summaries use median plus empirical 5th/95th quantiles.
- The aggregation hierarchy is cell → variable → family → replicate →
  station → corpus, all equal-weight medians. No pooled month/station median.
- Positive metrics use absolute relative distance; correlations/fractions use
  absolute difference.
- Primary adjudication uses held-out raw Daymet. Full-period, detrended, and
  GHCN columns are named sensitivities and cannot replace a failed primary.

## Fixed decision bounds

All seven climate gates and their exact 0.90/1.05/1.10/1.25 and 11/17 bounds
are normative in SPEC-A5-EVALUATION revision 1. A5b must reproduce them
verbatim in its analyzer. No candidate wins by parameter-count or runtime
advantage; those are reported separately.

## Downstream protocol boundary

A5a does not run an unpinned sibling WEPP executable. Before A5b response
runs, its package must bind exact WEPP executable, run/man/sol/slp inputs,
climate substitution, output parser, extraction fields, and response schema.
Hybrid observed P/T forcing is labeled hybrid and is not observation truth.

## Amendments

After the first A5a baseline output exists, any change to this document is an
explicit dated amendment. It cannot replace the original preregistration and
cannot retroactively define a pass.

### 2026-07-12 — median definition and baseline regeneration

The first A5a baseline execution on 2026-07-12 used the lower of the two
center order statistics when summarizing eight burn offsets. That output is a
stale development baseline: it is not admissible evidence for A5a or A5b and
cannot define, or be used to claim, a pass.

For every median in the A5a baseline analysis and A5b candidate analysis,
**median** now means the conventional sample median: the center order
statistic for odd sample size and the arithmetic mean of the two center order
statistics for even sample size. The empirical p05 and p95 estimators remain
nearest-rank order statistics. This clarification does not alter the frozen
matrix, metrics, aggregation hierarchy, or decision bounds.

The complete 544-run A5a baseline matrix must be regenerated after this
amendment with the amended runner and evidence contract. No report, summary,
or analysis row from the stale development baseline may be reused.

### 2026-07-13 — executable metric cells and observed bootstrap

The original registration fixed broad families and bounds but did not
enumerate every scalar cell or specify a pseudorandom stream for the observed-
target bootstrap. This prospective pre-candidate amendment adopts the
following normative artifacts before any A5b candidate output exists:

| Artifact | SHA-256 |
|---|---|
| `docs/specifications/a5-climate-gate-metrics-v1.json` | `37d2e36fe84a7fafbc2dafdea553a5702fe94677de23a6ba45ac4a4946572d95` |
| `docs/specifications/a5-climate-gate-metrics-v1.schema.json` | `f17b6a3896df1226b60a6e1f181089568cab918488d6564caa4ec12baf83be2c` |
| `artifacts/verify-a5-climate-gate-metrics-v1.py` | `ae1ef7f06b4afef94910af656f2077ee2029698a42e9223f3a8099a61dac1ac0` |
| `artifacts/observed-bootstrap-v1.py` | `d154773bb8bd5265e8423360b69fc6acb0cec8cc64280cdee5c1ac705df8d649` |
| `artifacts/observed-bootstrap-v1-golden.json` | `d38a730371a847e78fb9563821ea7efffa24f364787f902f555634a32f8c2ec2` |

A5b must reproduce all five files byte-for-byte and pass the Draft 2020-12,
semantic, mutation, duplicate-key, non-finite-token, and bootstrap golden
checks before reading candidate results. A5b cannot redefine membership,
paths, sources, raw/detrended projections, statistics, distance or
normalization rules, families, gate roles, common-cell eligibility, count
sufficiency, exclusions, or equal-weight aggregation.

The manifest prospectively resolves the underspecified cells as follows:

- Gate 1 uses an equal-weight composite of six interannual families and keeps
  the registered 0.90/11-of-17/1.05 bounds. In addition, the
  `interannual_low_frequency` family itself must be at most 0.90 times the
  baseline. This anti-dilution subguard ensures the named primary outcome
  cannot regress while hundreds of other cells improve.
- Gate 2 is the exact Gate 1 membership retargeted to the available held-out
  raw GHCN surface; candidate median distance must be at most 1.10 times the
  same-station baseline median.
- Gate 3 requires candidate station-parameter identity and every embedded
  target scalar to equal the matched `qc_filter: off` baseline/base contract.
  Tmax/Tmin monthly mean distance is dimensionless:
  `abs(generated_mean - target_mean) / target_sd`, using the matched finite,
  strictly positive monthly station-contract target SD.
- The baseline-eligible scalar cell-ID set is fixed from target, baseline,
  and minimum-count eligibility. Candidate output must define every identical
  cell ID. Candidate-only cells are report-only; denominator switching is
  forbidden. Counts and other metadata are never distance cells.
- Gate 5 uses, for each station and scalar descriptor cell, the inclusive
  faithful-baseline nearest-rank p05–p95 interval around the candidate's
  conventional replicate median.

The bootstrap reference fixes seed extraction as SHA-256 digest bytes 0–7
interpreted unsigned big-endian; the exact `splitmix64-v1` transition; unbiased
rejection-sampled bounded indices; replicate-major then block-major draw
order; four circular length-five blocks for `n = 16`; concatenation then
truncation to the first 16 entire aligned-year vectors; exactly 2,000
replicates; and nearest-rank p2.5/p97.5 (one-based ranks 50 and 1950). No other
PRNG, block unit, draw order, or percentile estimator is admissible.

Uncertainty application is exact and report-only. It covers only the
baseline-eligible held-out raw Daymet memberships in Gates 1, 4, and 6, not
GHCN Gate 2, station-contract Gate 3, descriptor Gate 5, or Gate 7. Sampled
years remain in draw order and are relabeled bootstrap positions 0–15 before
metrics are recomputed; original source-year labels are never sorted or used
for grouping. Daily/spell/rolling/lag estimators cross boundaries within the
linear concatenated sequence, including block seams and source-year circular
wraps, but never join the final sampled position back to the first.

For each station/bootstrap index, recompute every fixed observed scalar target
and cross it with all eight fixed generated reports. Apply the registered
cell → variable → family → gate → generated-replicate → station → regime/
corpus hierarchy inside that bootstrap index. Do this separately for the
faithful-off baseline, every candidate, and each horizon against the same
station target stream. Station streams are independently seeded; the same
index is aligned across stations only for regime/corpus aggregation. An
undefined resampled fixed cell makes its dependent aggregate unavailable for
that index without dropping, replacing, or reweighting the cell. Report
`n_available` and nearest-rank p2.5/p97.5 at scalar-cell, station-variable,
station-family, station-gate, regime-gate, and corpus-gate levels; zero
available means null endpoints. These intervals cannot alter deterministic
promotion pass/fail.

This amendment cannot retroactively define a pass. The complete 544-run A5a
baseline and analysis must be regenerated after it; no earlier report,
summary, scalar membership, bootstrap draw, or analysis row may be reused.
