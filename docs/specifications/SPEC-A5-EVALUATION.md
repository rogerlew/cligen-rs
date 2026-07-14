# SPEC-A5-EVALUATION — Interannual Candidate Evaluation Contract

Status: active (revision 3)
Surface: A5b candidate matrices and A5c promotion adjudication

## Purpose

This specification fixes the evidence design before A5b produces candidate
output. ADR-0002 makes observed-climate and downstream-response metrics the
extension authority. Faithful distance is compatibility information only.

## Normative executable contracts

The scalar membership, paths, sources, statistics, distance rules, gate
roles, exclusions, exact-cell completeness rule, and equal-weight
aggregation identity are frozen by these three version-1 artifacts:

| Artifact | SHA-256 |
|---|---|
| [`a5-climate-gate-metrics-v1.json`](a5-climate-gate-metrics-v1.json) | `37d2e36fe84a7fafbc2dafdea553a5702fe94677de23a6ba45ac4a4946572d95` |
| [`a5-climate-gate-metrics-v1.schema.json`](a5-climate-gate-metrics-v1.schema.json) | `f17b6a3896df1226b60a6e1f181089568cab918488d6564caa4ec12baf83be2c` |
| [`verify-a5-climate-gate-metrics-v1.py`](../work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts/verify-a5-climate-gate-metrics-v1.py) | `ae1ef7f06b4afef94910af656f2077ee2029698a42e9223f3a8099a61dac1ac0` |

A5b must reproduce all three files byte-for-byte and pass the schema and
semantic/mutation verifier before reading candidate results. It may not add,
remove, substitute, reweight, or redefine a metric cell, family, target
surface, eligibility rule, or gate role. A later contract requires a new
version and prospective amendment; it cannot rewrite version 1.

## Independent identities

Every matrix row binds, without collapsing versions:

- observed-target corpus schema/content identity;
- station-file schema and station-model identifier;
- parameter-fit schema, model family/version, fit-period and fit hash;
- generation profile and independent extension-RNG identity;
- runspec content hash, legacy burn offset, horizon, and replicate key;
- `.cli`, provenance, optional Parquet, and quality-report identities;
- quality envelope and metric-vector versions;
- for downstream rows, the WEPP response schema, executable/input-deck
  hashes, extraction adapter, and climate-disaggregation identity.

## Fixed comparison axes

- Stations: the 17 revision-1 observed-target stations, retaining regime
  labels. Cold/snow-dominated gates use the four cold stations plus New
  Meadows.
- Observed periods: fit 1980–2009; held-out evaluation 2010–2025; full
  1980–2025 is a declared sensitivity only.
- Horizons: exactly 30 and 100 complete synthetic years.
- Baselines: `faithful_5_32_3 + qc_filter: off` is the variance-priority
  scientific baseline; conditioned faithful is retained as a compatibility
  comparator.
- Candidates: the A5b rank-one monthly-SD baseline, canonical monthly
  covariance, Fourier/EOF, vector AR, HMM, spectral benchmark, and narrow
  daily precipitation-structure counterfactual. Exact versioned identifiers
  are fixed in A5b before fitting.
- Replicates: the package pre-registration supplies fixed replicate records
  containing a legacy `rng.burn` offset and, for extension profiles, an
  independent domain-separated realization seed.

`rng.burn` discards returns from fixed faithful streams and never advances
`k10`; it is not a seed and nearby offsets can share subsequences. Across-burn
intervals are labeled empirical trajectory spread. IID/bootstrap confidence
language is permitted only for independently seeded extension draws or the
observed-target resampling procedure.

## Aggregation hierarchy

No metric is flattened across stations and months. Unless a gate explicitly
says otherwise:

1. compute a scalar distance for each metric cell and replicate;
2. aggregate months/cells within variable by median;
3. aggregate variables within target family by equal-weight median;
4. aggregate families within a gate composite by equal-weight median;
5. aggregate replicates within station by median and report their 5th/95th
   empirical quantiles;
6. aggregate stations by median, also reporting every station and regime.

This hierarchy is part of the gate and cannot be selected after results are
seen.

Positive scale/dispersion targets use absolute relative distance
`abs(generated - observed) / observed`; correlations and fractions use
absolute difference. Group A Tmax/Tmin mean errors use the dimensionless
absolute difference divided by the matched, finite, strictly positive monthly
station-contract target SD. Signed temperature means and covariance are not
mixed into an unscaled observed-distance median. Undefined target/baseline
cells establish one frozen baseline-eligible cell-ID set; every candidate must
define that same exact set. Candidate-only cells are report-only and cannot
replace a missing baseline-eligible cell. Counts are completeness metadata,
never distance cells; exact minimum counts and zero-target rules are in the
version-1 manifest.

## Climate promotion gates

A candidate remains eligible only if all gates pass at both 30 and 100 years:

1. **Primary low-frequency improvement.** On the held-out Daymet target, the
   equal-weight median of the six interannual-family distances is at most 0.90
   times the `qc_filter: off` baseline. The separately equal-weighted
   low-frequency-power family must also be at most 0.90 times baseline, so it
   cannot regress while a broad composite improves. At least 11/17 station
   composite distances must be strictly smaller than baseline, and no regime
   median may exceed 1.05 times baseline.
2. **Independent-source sensitivity.** Over the exact available-GHCN station
   set, the candidate median composite distance must be at most 1.10 times the
   same-station baseline median. This is a sensitivity, not a substitute for
   the primary gate.
3. **Monthly contract preservation.** The candidate's station-median Group A
   distance for precipitation wet mean/SD/skew, wet fraction, transition
   probabilities, and Tmax/Tmin mean/SD is at most 1.10 times baseline; no
   single station exceeds 1.25 times baseline.
4. **Precipitation structure guard.** R1mm spell, amount-persistence, and
   1/3/5-day-extreme family distance is at most 1.10 times baseline. The
   positive-trace surface is compatibility information.
5. **Descriptor guard.** Until a hash-pinned subdaily target exists,
   time-to-peak and peak-ratio metrics are a no-silent-regression guard. For
   each station and frozen scalar cell, the candidate conventional median of
   raw replicate values must lie inside the inclusive faithful-baseline
   nearest-rank p05–p95 interval, or the candidate is held for descriptor
   evidence. This is not an observed-truth claim.
6. **Winter climate guard.** At the five cold/snow-domain stations, the
   held-out freezing-precipitation, winter-dependence, and air freeze/thaw
   proxy distance is at most 1.10 times baseline, with no station over 1.25.
7. **No missing evidence.** All required reports, provenance, fit artifacts,
   and downstream records validate and their content hashes match the matrix.

Passing these bounds makes a candidate eligible for A5c; it does not promote
automatically. Parameter count, fit failure, constraint interventions, and
station-level regressions remain visible to the operator.

## Observed-target uncertainty

A5b uses a deterministic circular moving-block bootstrap of complete aligned
years for primary target uncertainty: 2,000 replicates, block length five
years, resampling an entire year vector so month and variable dependence is
preserved. The pseudorandom seed is the first 64 bits of SHA-256 over
`"cligen-a5-bootstrap-v1\0" + corpus_sha256 + source_id + station_id +
period_id`, interpreted big-endian.

The named PRNG is `splitmix64-v1` with the exact state transition in the
reference implementation. Bounded starting indices use rejection sampling
against `2^64 - (2^64 mod bound)`, never modulo bias. For the 16-year held-out
period and length-five blocks, each replicate draws `ceil(16/5) = 4` starting
indices in replicate-major then block-major order, concatenates four circular
blocks, and truncates from 20 to the first 16 entire aligned-year vectors.
The 2.5% and 97.5% endpoints use the empirical inverse-CDF nearest-rank rule,
respectively one-based ranks 50 and 1950 of 2,000 values. Intervals and raw
sample sizes are mandatory and no asymptotic-normal shortcut may replace them.

The executable contract and golden vector are normative:

| Artifact | SHA-256 |
|---|---|
| [`observed-bootstrap-v1.py`](../work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts/observed-bootstrap-v1.py) | `d154773bb8bd5265e8423360b69fc6acb0cec8cc64280cdee5c1ac705df8d649` |
| [`observed-bootstrap-v1-golden.json`](../work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts/observed-bootstrap-v1-golden.json) | `d38a730371a847e78fb9563821ea7efffa24f364787f902f555634a32f8c2ec2` |

Application is limited to baseline-eligible held-out raw Daymet target cells in
Gates 1, 4, and 6. It does not apply to GHCN Gate 2, station-contract Gate 3,
descriptor Gate 5, or evidence Gate 7. For each station, sampled source years
remain in draw order and are relabeled positions 0–15; estimators never sort or
group by the duplicated/nonmonotone original year labels. Month/day and daily
order are preserved. Spells, rolling windows, and lag estimators cross every
boundary inside the linear concatenated sequence, including block seams and a
source-year circular wrap, but the final sampled day/year is not joined back
to the first. Daymet's no-leap 365-day calendar is retained.

For each target bootstrap index, every fixed scalar target is recomputed from
the entire resampled aligned-year vectors. That target is crossed with all
eight fixed generated reports for the faithful-off baseline or the candidate
and horizon being assessed. Distances then follow scalar cell → variable →
family → gate → eight generated replicates within station → station/regime/
corpus aggregation. Baseline, each candidate, and each horizon are computed
separately against the same station target stream. Station streams are seeded
independently; index `b` is aligned across stations only for regime/corpus
aggregation. If a resample makes a fixed eligible target cell undefined, it is
not dropped or replaced: every dependent aggregate is unavailable for that
`b`. Each reported scalar-cell, station-variable, station-family,
station-gate, regime-gate, and corpus-gate interval carries `n_available`, and
nearest-rank endpoints use only those available bootstrap aggregates (zero
available means null endpoints).

These intervals are report-only. They never change deterministic promotion
pass/fail; the unresampled target and fixed gate rules remain the sole
adjudication surface.

A5b must reproduce both files byte-for-byte and pass all positive, mutation,
duplicate-key, and non-finite-token self-tests. It cannot select a different
PRNG, endian interpretation, bounded-integer mapping, draw order, block unit,
truncation, replicate count, or percentile estimator.

## 2026-07-13 prospective pre-candidate amendment

Revision 1 fixed decision bounds but did not enumerate scalar membership or
make the bootstrap pseudorandom stream executable. Revision 2 prospectively
adopts the five hash-pinned artifacts above before any A5b candidate output.
It also makes the 0.90 low-frequency-family bound explicit in addition to the
six-family composite bound, preventing the named primary outcome from being
diluted by hundreds of other cells, and makes Group A temperature-location
distance dimensionless using its matched monthly target SD.

This amendment does not retroactively adjudicate the stale development
baseline. The complete 544-run A5a baseline and its analysis must be
regenerated under revision 2; no earlier report, summary, cell set, bootstrap
draw, or pass claim may be reused. No A5b candidate output may be read until
the replacement baseline and all five artifact identities validate.

## 2026-07-13 A5b experimental-lineage amendment

Revision 2 requires a separately identified candidate station model and
generation profile while the accepted quality envelope and provenance v1
vocabularies are intentionally closed to the A1 public surfaces. Before any
candidate output, A5b prospectively resolves that incompatibility as follows:

- A5b remains an external model-structure spike under
  `SPEC-A5B-CANDIDATES` revision 1. It consumes exact pre-format rows from a
  `faithful_5_32_3 + qc_filter: off` run and cannot alter or advance faithful
  generator state.
- Candidate quality is computed through the public post-hoc quality surface.
  Reports remain exactly `quality_report_schema_version = 2` and
  `metrics_version = 3`, with `identity.provenance: null`, `process: null`,
  and the base `fixed_monthly_5_32_3` parameter identity used for the fixed
  monthly-contract targets.
- A strict, separately versioned `a5b_run_record_v1` binds the candidate
  station-model/profile, coefficient payload, fit/source lineage, independent
  extension seed and PRNG, base typed-run/runspec identity, candidate CLI,
  post-hoc report, runtime, and diagnostics. Gate 7 requires this record and
  its cross-hash verifier; it does not require candidate claims to fit inside
  public provenance v1.
- The candidate command echo declares its A5b profile and extension seed.
  Candidate Parquet is prohibited because typed-output revision 1 does not
  contain the A5b profile vocabulary.
- Public station-document, runspec, generation-profile, provenance, and typed-
  output versions are unchanged. A5c must create independently versioned
  public surfaces for a promoted model, if any.
- In a candidate WEPP response record, the inherited
  `climate.provenance_sha256` field binds the strict A5b run-record bytes.
  Faithful baseline records continue to bind provenance v1. The response
  remains explicit about this experimental-lineage meaning.

This amendment changes lineage representation only. It does not change the
17-station corpus, fit/held-out periods, seven candidate families, horizons,
replicate records, metric vector, baseline-eligible cell set, aggregation,
decision bounds, uncertainty procedure, or downstream response obligation.
No post-hoc report is represented as trusted run provenance.

## Downstream WEPP response record

Physical response is a separate campaign record validated by
`a5-wepp-response-v1.schema.json`; it is never embedded in a climate quality
report. Each record binds the climate and quality hashes to a pinned WEPP
executable, run/man/sol/slp inputs, output parser, and extraction definitions.

The structural schema, execution protocol, and semantic validator identities
are normative:

| Artifact | SHA-256 |
|---|---|
| [`a5-wepp-response-v1.schema.json`](a5-wepp-response-v1.schema.json) | `7d006023684f2079ce09e5ab1af21e1154a417eb4295ebf1a02c40d7f7a2e70d` |
| [`wepp-response-protocol.md`](../work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts/wepp-response-protocol.md) | `9cd770d18c04dfde877c91e03304697b107d117bf2e52cc94f1f83e3d99c5800` |
| [`verify-wepp-response-schema.py`](../work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts/verify-wepp-response-schema.py) | `05e7a085f146e264c3b34e3f7c04f498f0f4d3dd0c9b0cd17a0f8176221b683b` |

A5b analyzers and every response record must bind these exact identities and
pass the schema and semantic validator under the pinned protocol. Schema
validity alone is insufficient: the semantic
validator enforces cross-field horizon/year counts, complete family/summary
membership, units/source coherence, summary ordering, and its own self-hash.
A different validator or changed bytes require a new response-contract
version; they cannot be substituted during analysis.

At the five cold/snow-domain sites the response vector must include, where
the pinned WEPP output surface supports them:

- annual maximum snow water equivalent or the exact WEPP snow-state analogue;
- annual snowmelt and rain-on-snow runoff under declared extraction rules;
- winter runoff and annual/winter soil loss;
- annual runoff and peak runoff as general response guards.

For every available response family the record carries four scalar summaries
over complete simulation years: mean, sample SD, nearest-rank p95, and maximum.
Each summary names its units, year count, output-file hash, selector/record
meaning, aggregation, and missing-value rule. General sites must carry annual
runoff, annual peak runoff, and annual soil loss; `cold_snow` sites must also
carry every cold-domain family above. A family unsupported by the pinned
output surface appears once as `status: unavailable` with a reason and source
audit, never as a zero or an omitted field.

Unavailable physical fields are explicit with a reason and source-output
audit. A hybrid observed P/T forcing that regenerates other meteorology is
labeled `hybrid_observed_pt`, never `observed_truth`.

A5a pins the record format and protocol. A5b executes it only after exact
candidate climates, a reviewed WEPP binary/input deck, and extraction adapter
are pinned. No sibling repository's mutable working tree is an authority.

## Winter terminology rule

Quality-report climate fields must include `air_temperature_proxy` in their
names/descriptions. WEPP response fields must identify the physical state or
flux and extraction source. A climate proxy may not be relabeled as rain/snow
partition, snowpack, frost depth, rain-on-snow runoff, or soil freeze/thaw.
