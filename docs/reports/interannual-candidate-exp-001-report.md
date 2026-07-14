# Interannual climate-state candidates for CLIGEN: experiment 001

Report ID: `interannual-candidate-exp-001`
Status: `ACCEPTED`
Date: 2026-07-14
Revision: 2
Authors: cligen-rs project contributors
Evidence mode: Mixed
Experiment record: [A5b work package](../work-packages/20260713-a5b-interannual-candidate-spike/package.md)
Evidence snapshot: [report manifest](interannual-candidate-exp-001-report.manifest.json)
Review record: [consolidated internal review](../work-packages/20260714-interannual-candidate-exp-001-report/artifacts/review.md)

## Abstract

CLIGEN represents climate through fixed monthly station parameters and daily
stochastic generation, a structure that does not explicitly model
interannual climate state. We evaluated seven versioned annual-state overlays:
rank-one monthly standard deviations, full monthly covariance, Fourier/EOF,
vector autoregression, a two-state Gaussian hidden Markov model, spectral
random phase, and a Fourier/EOF precipitation counterfactual. Models were fit
to 1980–2009 Daymet V4 R1 gridded estimates at 17 stations and scored against
held-out 2010–2025 Daymet estimates, a separately archived GHCN point-record
sensitivity, fixed climate guards, and a pinned WEPP response campaign. The
experiment produced 1,904 candidate climates, 2,000 observed-target bootstrap
replicates, and 2,176 WEPP response/execution records. None of 14 candidate-
horizon rows passed the seven-gate contract: all candidates failed the joint
primary Gate 1, monthly-contract preservation, daily precipitation structure,
and the storm-descriptor guard at both 30 and 100 years. All passed the winter-
proxy and evidence-completeness gates. Median station-level WEPP ratios were
large but descriptive because no downstream numeric acceptance bound was
registered. Candidate values were inspected while successor analysis
contracts were repaired, making the model-selection evidence exploratory. The
experiment therefore supports no promotion of these exact versions under the
frozen gates; it does not reject interannual modeling generally. A new
prospective test should reallocate rather than simply add variance, enforce the
monthly surface while jointly generating daily precipitation structure, and
repair identified gate-calibration weaknesses. [E05] [E06] [E07] [E08] [E13]

## Introduction

Classical single-site weather generators commonly combine a daily
precipitation occurrence process, conditional amount generation, and
temperature/radiation relationships [R01]. Their compact parameterization is
useful, but daily models can underrepresent aggregated precipitation variance;
that deficit can arise from occurrence and amount structure as well as from a
missing low-frequency state [R02] [R03]. Consequently, improved monthly
variance alone is not sufficient evidence that an annual-state mechanism is
scientifically adequate.

CLIGEN is a stochastic generator used with the Water Erosion Prediction
Project (WEPP). Its historical design, trajectory-conditioning behavior, and
storm-generation corrections have been documented across several CLIGEN
versions [R04] [R05] [R09]. Published evaluations show why precipitation
amount, duration, peak, and other storm descriptors matter to downstream
runoff and erosion, but those studies are context rather than exact authority
for the vendored CLIGEN 5.32.3 implementation [R10] [R11] [R12]. In this
repository the Fortran source remains the faithful-mode authority; A5b is an
explicit research extension layered on exact faithful-off trajectories. [E03]

Low-frequency generator precedents include spectral correction, hierarchical
annual conditioning, and autoregressive annual states [R06] [R07] [R08]. A5b
did not reproduce those published generators. It implemented seven
project-defined, version-1 contrasts behind research-only identities so their
effects could be evaluated without changing faithful CLIGEN. The study asked
whether explicit annual state improves held-out interannual behavior, whether
any improvement is robust, whether it preserves monthly, daily, storm, and
winter climate surfaces, and what downstream WEPP responses it produces.
Downstream preservation could not be adjudicated because no numeric response
bound was registered. [E01] [E02]

## Hypotheses

The preregistration stated research questions, not formal null and alternative
hypotheses. H1–H3 are therefore operational hypotheses mapped retrospectively
from those questions and the frozen gates; they summarize the registered
decision logic but are not presented as confirmatory hypotheses.

| ID | Provenance | Scope and comparison | Decision rule | Outcome | Result |
|---|---|---|---|---|---|
| H1 | retrospective mapping | At least one candidate improves held-out Daymet interannual behavior relative to faithful-off at 30 and 100 years | Same candidate passes Gate 1 at both horizons | Not supported | [Climate gates](#climate-gates) |
| H2 | retrospective mapping | The H1 improvement is robust across stations, regimes, horizons, and the GHCN sensitivity | H1 candidate also satisfies registered station/regime conditions and Gate 2 | Not supported; no candidate met H1, although six passed Gate 2 | [Climate gates](#climate-gates) |
| H3 | retrospective mapping | An H1 candidate preserves monthly climate, daily precipitation, faithful storm descriptors, and winter proxies with complete evidence | H1 candidate passes Gates 3–7 at both horizons | Not supported; every candidate failed Gates 3–5 | [Climate gates](#climate-gates) |

No quantitative WEPP pass hypothesis was registered. Gate 7 requires a
complete downstream record, while response ratios remain descriptive. [E01]
[E02]

## Methods

### Authority, data, and periods

Candidate mathematics and overlay behavior were fixed by
`SPEC-A5B-CANDIDATES` revision 1; evaluation was fixed by
`SPEC-A5-EVALUATION` revision 3. Faithful inputs were generated by the accepted
Rust port under `faithful_5_32_3 + qc_filter: off`. The A5b executable consumed
typed faithful rows and used independently domain-separated extension random
streams; it did not read or advance faithful generator state. [E02] [E03]

Daymet V4 R1 was selected as the coefficient source because it covered the
complete 1980–2009 fit period and all 17 project stations, including Alaska,
and because the exact source objects were already archived and hash-bound.
Daymet is a 1-km gridded estimate constructed primarily from GHCN-Daily inputs,
not point-observation truth [R13] [R14]. The primary evaluation used held-out
2010–2025 Daymet estimates. Eight archived GHCN station records provided a
separately scored point-record sensitivity, but not a statistically independent
observing system [R15]. The project mapped Daymet ordinal days through its
frozen `noleap_365` transform; this is a project normalization, not the
official Daymet civil-calendar interpretation. PRISM and gridMET informed the
source assessment but were not used for coefficient fitting or scoring. [E04]

### Candidate construction

Each fit year was represented by 36 centered features: 12
`log1p` monthly precipitation totals, 12 monthly mean maximum temperatures,
and 12 monthly mean minimum temperatures. The primary fit was not detrended;
sample covariances used denominator 29. Fourier candidates projected each
variable onto a constant and the first three real seasonal harmonics, then
used a deterministically ordered, shrunk EOF representation retaining 90% of
positive variance within a rank bound of 3–10. [E03]

| Candidate | Version-1 structural contrast | Runtime parameters per station |
|---|---|---:|
| Rank-one monthly SD | One annual normal per variable multiplied by 12 fitted monthly SDs | 36 |
| Full monthly covariance | Shrunk 36 × 36 covariance and deterministic Cholesky | 666 |
| Fourier/EOF | Independent annual EOF scores mapped to 36 monthly features | 216–360 |
| Vector AR | Ridge VAR(1) in EOF-score space with spectral-radius cap and warm-up | 273–515 |
| Gaussian HMM | Two-state, diagonal-emission HMM in EOF-score space | 242–402 |
| Spectral random phase | Interpolated 30-year DFT amplitudes with random phases | 306–510 |
| Precipitation counterfactual | Fourier/EOF state plus second-order wet occurrence and lag-one wet-amount dependence | 276–420 |

Every candidate generated a 128-year annual-state table. The 30- and 100-year
runs consumed common prefixes. Temperature anomalies were centered over the
table; monthly precipitation multipliers were projected to `[0.05, 20]` with
an exact mean of one. The overlay scaled monthly precipitation, added maximum-
and minimum-temperature anomalies, adjusted dew point, repaired temperature
ordering, and left solar radiation and wind unchanged. The counterfactual
preserved each faithful month's wet-event tuple multiset and wet-day count
while relocating events; it did not synthesize new storm descriptors. [E03]

### Experimental matrix and access boundary

The matrix crossed seven candidates, 17 stations, two horizons (30 and 100
years), and eight registered replicate records, yielding
`7 × 17 × 2 × 8 = 1,904` candidate climates. The replicate records include
legacy burn offsets and independent extension seeds. Legacy burns can share
subsequences and therefore describe empirical trajectory spread rather than
independent-sample confidence. A 544-run A5a baseline matrix and 272 shared
faithful bases were retained. [E01] [E05] [E08]

Candidate definitions and decision thresholds were frozen before candidate
generation. During execution, valid climate-analysis and WEPP-format cases
exposed successor-contract defects. Limited candidate response and metric
values were inspected while those executable contracts were repaired; the
earlier versions and amendments were retained. Thus the completed analysis is
exploratory for model selection even though no candidate, threshold, matrix,
or scientific gate was changed. [E05] [E09]

### Study identity

The following checked block is duplicated in the report manifest so that the
mechanical gate can reject contradictory report and manifest dimensions.

| Fact | Registered value |
|---|---|
| Stations | 17 |
| Candidates | 7 |
| Horizons years | 30, 100 |
| Replicate records per cell | 8 |
| Candidate horizon rows | 14 |
| Candidate climates | 1,904 |
| Observed bootstrap replicates | 2,000 |
| WEPP response records | 2,176 |
| WEPP execution records | 2,176 |
| Eligible candidate horizon rows | 0 |
| Promoted candidates | 0 |
| Evidence classification | exploratory for model selection |

### Downstream response

The pinned WEPP campaign crossed faithful-off plus seven candidates with the
same 17 stations, two horizons, and eight replicate records, producing
`8 × 17 × 2 × 8 = 2,176` response and execution records. General response
families were annual runoff, peak runoff, and soil loss. Five cold/snow-domain
sites carried additional available snow-state, snowmelt, rain-on-snow, winter
runoff, and winter soil-loss records under declared extraction rules. [E02]
[E11]

## Analysis

### Climate decision rules

Metric aggregation was fixed as scalar cell → variable → family → replicate →
station → regime/corpus, using equal-weight medians rather than flattening
months or stations. Ratios below are candidate observed-distance divided by
matched faithful-off observed-distance; smaller is better. Undefined baseline
cells established a frozen eligibility set that candidates could not replace.
[E02]

A candidate had to pass all seven gates at both horizons to remain eligible:

1. Gate 1 required held-out Daymet composite and low-frequency ratios ≤0.90,
   at least 11 of 17 stations improved, and worst-regime ratio ≤1.05.
2. Gate 2 required the available-GHCN same-station composite ratio ≤1.10.
3. Gate 3 required monthly-contract corpus ratio ≤1.10 and no station >1.25.
4. Gate 4 required daily precipitation-structure corpus ratio ≤1.10; the
   positive-trace surface was compatibility information.
5. Gate 5 required every candidate storm-descriptor median to remain within
   the matched faithful p05–p95 envelope. This is a no-regression guard, not
   observed storm truth.
6. Gate 6 required the five-station winter air-temperature/freezing-proxy
   ratio ≤1.10 and no station >1.25.
7. Gate 7 required complete, hash-valid climate, fit, lineage, and downstream
   evidence. It did not override a scientific gate failure.

Passing every bound would only make a candidate eligible for later
adjudication; it would not itself promote a profile. [E02]

### Uncertainty and diagnostics

Observed-target uncertainty used 2,000 deterministic circular moving-block
bootstrap replicates of aligned years with five-year blocks. Intervals were
report-only and could not change deterministic gates. Corpus availability was
221/2,000 for Gate 1, 8/2,000 for Gate 4, and 2,000/2,000 for Gate 6 in every
candidate/horizon row, so the sparse Gate 1 and Gate 4 interval surfaces are
not treated as confirmation of the deterministic decision. Interval endpoints
were nearest-rank p2.5 and p97.5 over available aggregates only. The procedure
resampled held-out targets, not coefficient fitting. [E02] [E07] [E10]

Fit status, parameter counts, run time, multiplier-bound clips, temperature-
order repairs, and dewpoint caps were reported as intervention diagnostics,
not gate metrics. Six full-period/detrended Daymet and GHCN sensitivity
projections were also report-only. [E06]

### Mechanistic interpretation of the annual overlay

The universal Gate 3 and Gate 4 failures are consistent with variance addition
rather than variance reallocation. In an idealized overlay where a daily amount
`X` is independent of a nondegenerate annual multiplier `F` and `E[F] = 1`,
`Var(FX) = Var(X) + Var(F)E[X²]`; the multiplier necessarily increases pooled
variance. A5b's effective-factor adjustment and other runtime constraints mean
this identity is a mechanistic explanation, not a proof that every registered
gate had to fail. It nevertheless supplies a feasibility screen for successor
candidates: their pooled monthly moment budget should be derived before an
expensive campaign, and low-frequency variance should be reallocated through
conditioning or resampling rather than added after generation. This
interpretation was added after acceptance and does not alter a frozen result.
[E03] [E13]

### WEPP summaries

For each candidate, horizon, station, and replicate, downstream analysis paired
the candidate response with faithful-off. The reported table is the median
across stations of paired candidate/faithful-off ratios for the annual-mean
response statistic. Baseline-zero ratios are null rather than zero or infinity.
Revision 1 registered no downstream numeric pass bound, so these summaries do
not determine eligibility except through Gate 7 evidence completeness. [E06]
[E11]

## Results

### Climate gates

All 119 station-candidate fits completed and all 1,904 candidate climates were
sealed. No candidate passed Gate 1, Gate 3, Gate 4, or Gate 5 at either
horizon. Rank-one also failed Gate 2; the other six candidates passed it. All
candidates passed Gate 6 and, after the WEPP campaign was attached, Gate 7.
Accordingly, H1, H2, and H3 were not supported, 0/14 candidate-horizon rows
were eligible, and no model was promoted. [E06] [E08] [E10]

| Candidate | Years | G1 | G2 | G3 | G4 | G5 | G6 | G7 | Eligible |
|---|---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Rank-one monthly SD | 30 | F | F | F | F | F | P | P | No |
| Rank-one monthly SD | 100 | F | F | F | F | F | P | P | No |
| Full monthly covariance | 30 | F | P | F | F | F | P | P | No |
| Full monthly covariance | 100 | F | P | F | F | F | P | P | No |
| Fourier/EOF | 30 | F | P | F | F | F | P | P | No |
| Fourier/EOF | 100 | F | P | F | F | F | P | P | No |
| Vector AR | 30 | F | P | F | F | F | P | P | No |
| Vector AR | 100 | F | P | F | F | F | P | P | No |
| Gaussian HMM | 30 | F | P | F | F | F | P | P | No |
| Gaussian HMM | 100 | F | P | F | F | F | P | P | No |
| Spectral random phase | 30 | F | P | F | F | F | P | P | No |
| Spectral random phase | 100 | F | P | F | F | F | P | P | No |
| Precipitation counterfactual | 30 | F | P | F | F | F | P | P | No |
| Precipitation counterfactual | 100 | F | P | F | F | F | P | P | No |

The gate magnitudes show partial improvements but no dominant candidate.
Spectral random phase was the only row with a Gate 1 composite below 0.90
(0.894 at 100 years), but its low-frequency ratio was 1.091. Vector AR was the
only 100-year row with low-frequency ratio below 0.90 (0.876) while meeting the
station/regime conditions, but its composite was 0.925. Fourier/EOF had only
two descriptor failures at each horizon, but missed the primary low-frequency,
monthly-contract, and precipitation-structure bounds. [E06] [E10]

| Candidate | Years | G1 composite | G1 low-frequency | Improved stations | Worst regime | G3 | G4 | G5 failed/408 | G6 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Rank-one monthly SD | 30 | 1.395 | 1.177 | 0 | 1.580 | 2.790 | 1.924 | 10 | 0.978 |
| Rank-one monthly SD | 100 | 1.429 | 1.127 | 0 | 1.578 | 2.712 | 2.193 | 19 | 1.044 |
| Full monthly covariance | 30 | 0.944 | 1.198 | 9 | 1.018 | 2.750 | 2.443 | 10 | 0.928 |
| Full monthly covariance | 100 | 0.934 | 1.160 | 13 | 0.992 | 2.592 | 2.841 | 20 | 0.894 |
| Fourier/EOF | 30 | 0.918 | 1.173 | 11 | 1.046 | 2.064 | 1.428 | 2 | 1.032 |
| Fourier/EOF | 100 | 0.939 | 1.158 | 12 | 1.018 | 2.014 | 1.544 | 2 | 1.015 |
| Vector AR | 30 | 0.960 | 0.915 | 9 | 1.044 | 2.074 | 1.549 | 1 | 1.005 |
| Vector AR | 100 | 0.925 | 0.876 | 11 | 1.026 | 2.101 | 1.662 | 8 | 1.000 |
| Gaussian HMM | 30 | 0.955 | 0.922 | 12 | 0.981 | 2.110 | 1.487 | 2 | 0.945 |
| Gaussian HMM | 100 | 0.946 | 1.154 | 11 | 1.024 | 1.946 | 1.695 | 6 | 0.940 |
| Spectral random phase | 30 | 0.930 | 0.811 | 11 | 1.012 | 1.918 | 1.393 | 2 | 0.984 |
| Spectral random phase | 100 | 0.894 | 1.091 | 12 | 0.966 | 1.900 | 1.602 | 12 | 0.996 |
| Precipitation counterfactual | 30 | 0.933 | 1.210 | 11 | 1.009 | 2.570 | 1.849 | 5 | 1.016 |
| Precipitation counterfactual | 100 | 0.907 | 1.134 | 12 | 0.976 | 3.243 | 2.021 | 10 | 0.968 |

The universal Gate 3 ratios (1.900–3.243) and Gate 4 ratios (1.393–2.841)
were the clearest structural failure. The tested annual overlays improved
some interannual components but did not preserve the fixed monthly surface or
daily precipitation structure. The precipitation counterfactual did not solve
this: its Gate 3 ratios were 2.570 and 3.243 and Gate 4 ratios were 1.849 and
2.021. [E06]

### Execution diagnostics

All fits reported `ok`, with no fit warnings or execution failures; the HMM
fitter recorded two deterministic state-relabeling interventions. Across all
candidate climates the canonical analysis recorded 24,486 precipitation-bound
clips, 59,033 temperature-order repairs, and 15,565,742 dewpoint caps. These
counts document the overlay's realized constraints and are not independent
quality measures. The candidate matrix contains 45,201,912 exact station-days:
10,957 days per 30-year run and 36,524 per 100-year run across
`7 × 17 × 8` candidate/station/replicate combinations. Dewpoint was therefore
capped on 34.4% of candidate station-days. This corrects the advisory's rough
“one fifth” estimate and shows why successor gates should use per-station-day
intervention rates rather than campaign totals. Rank-one and full covariance
required substantially more precipitation clips and temperature repairs than
the other candidates. [E03] [E06] [E10] [E13]

### Downstream WEPP response

All 2,176 response and 2,176 execution records validated with zero campaign
failures. The fixed-width audit retained four `EffInt` overflows, 13,473 `Sm`
overflows, 152 source-anchored `PeakRO` recoveries, and seven same-day duplicate
rows under the frozen parser contract. Gate 7 therefore passed for every row;
this completed the evidence record but did not cure climate-gate failures.
[E08] [E11]

| Candidate | Years | Annual runoff | Annual peak runoff | Annual soil loss |
|---|---:|---:|---:|---:|
| Rank-one monthly SD | 30 | 6.74 | 2.82 | 9.12 |
| Rank-one monthly SD | 100 | 9.98 | 2.75 | 13.34 |
| Full monthly covariance | 30 | 9.58 | 4.66 | 9.20 |
| Full monthly covariance | 100 | 12.06 | 5.72 | 16.58 |
| Fourier/EOF | 30 | 5.28 | 2.69 | 6.80 |
| Fourier/EOF | 100 | 6.17 | 3.10 | 7.91 |
| Vector AR | 30 | 3.94 | 2.89 | 4.93 |
| Vector AR | 100 | 5.15 | 2.99 | 5.96 |
| Gaussian HMM | 30 | 3.71 | 2.68 | 4.82 |
| Gaussian HMM | 100 | 4.38 | 2.59 | 5.51 |
| Spectral random phase | 30 | 5.42 | 2.71 | 6.78 |
| Spectral random phase | 100 | 5.54 | 3.07 | 6.32 |
| Precipitation counterfactual | 30 | 5.10 | 2.95 | 6.62 |
| Precipitation counterfactual | 100 | 5.89 | 2.78 | 7.32 |

Values are median-across-station paired ratios to faithful-off for the annual-
mean response statistic, not ratios of corpus totals. They show large response
differences within the pinned campaign but have no registered pass threshold.
At the five cold/snow stations, annual maximum snow-state median ratios ranged
from 1.060 to 1.170 and annual snowmelt ratios from 0.981 to 1.031. Other cold-
response ratio summaries were dominated by baseline-zero pairs and are better
represented by archived signed differences and availability counts. [E06]
[E11]

## Limitations and validity

The primary internal-validity limitation is the exploratory access boundary:
limited candidate values were inspected while successor analysis contracts
were repaired. Frozen candidate definitions and thresholds and the uniformly
negative eligibility result reduce, but do not erase, selection-bias risk. A
future promotion study must be newly frozen and prospective. [E09]

Construct validity is bounded in several ways. Daymet is a gridded estimate,
and fitting and primary scoring use the same product family across a temporal
split. GHCN adds a point-record sensitivity but shares upstream data lineage.
The project `noleap_365` mapping differs from Daymet's official civil-calendar
interpretation. Gate 5 detects divergence from faithful storm descriptors but
does not validate those descriptors against observations. Gate 6 covers air-
temperature/freezing proxies, not snowpack or soil freeze–thaw physics. The
bootstrap intervals are report-only and have low corpus availability for
Gates 1 and 4. [E02] [E04] [E07]

External validity is limited to these 17 stations, the 1980–2025 Daymet
snapshot and eight GHCN sensitivities, the registered 30/100-year horizons,
the pinned WEPP executable/decks, and the seven exact version-1 candidates.
The experiment does not compare multisite spatial coherence, future nonstationary
climates, alternative fit products, or other implementations of EOF, VAR, HMM,
and spectral methods. The WEPP ratios measure response under one controlled
campaign; they do not establish physical correctness or universal causal
multipliers.

Coefficient estimation used only 30 annual vectors per station for 36 monthly
features. Shrinkage, Fourier compression, rank selection, and model-specific
regularization made that fit executable, but the 216–666 runtime coefficient
counts are not independent degrees of freedom. The bootstrap resampled the
held-out target and did not refit candidates, so it does not quantify
coefficient-fit uncertainty or separate architecture, source-product,
finite-record, and regularization effects. Exact-version failures therefore
cannot diagnose the capability of the broader EOF, VAR, HMM, or spectral
model families. [E02] [E03]

### Gate calibration limitations

The post-acceptance advisory concurred with no promotion and did not find a
threshold relaxation that could rescue these candidates. It identified five
prospective weaknesses in the evaluation contract: [E13]

1. Gates 3 and 4 express candidate distance as a ratio to faithful's residual
   distance. When that denominator is small, the ratio can look severe without
   communicating absolute physical error or observed-target uncertainty. The
   registered failures remain failures, but a successor should scale absolute
   distance by observed uncertainty while retaining hard preservation bounds.
2. Gate 5 permits no excursion among 408 descriptor cells. With eight faithful
   replicates, nearest-rank p05–p95 is the observed minimum–maximum envelope;
   no empirical false-failure rate was measured. A faithful-clone null
   candidate or paired cell test should calibrate the guard prospectively.
3. The Gate 1 and Gate 4 bootstrap surfaces were available in only 221 and 8
   of 2,000 corpus resamples. A successor should diagnose the missing cells and
   make the uncertainty surface informative before treating it as decision
   support.
4. No numeric WEPP response bound existed. A successor must register either a
   response bound or an explicit scientific justification for keeping WEPP
   descriptive.
5. Precipitation clips, temperature repairs, and dewpoint caps had no rate
   ceiling. Their station-day rates should become an explicit guard.

These are calibration limitations of revision 3, not grounds for retrospective
rescoring. In particular, the Gate 3 and Gate 4 ratios were far above their
registered 1.10 bounds, so post-hoc relaxation would remain exploratory model
selection. [E02] [E06] [E13]

## Conclusions

None of the seven A5b candidate versions is eligible for promotion. This is a
version-bounded no-promotion result, not a rejection of interannual climate
modeling. Spectral random phase, vector AR, and Fourier/EOF each exposed a
different partial strength, but no defensible ranking can substitute for the
failed joint contract.

The most actionable result is structural: adding an unconstrained annual
overlay did not preserve CLIGEN's fixed monthly climate surface or its daily
precipitation structure, and a narrow fixed-count event-relocation
counterfactual was insufficient. Before another campaign, the project should
derive the monthly moment budget and reject candidate classes that are
gate-infeasible by construction. A state-conditioned year/block resampler is
the lower-risk first successor because it can reallocate low-frequency
behavior while retaining daily and storm sequences; conditioning occurrence
and amount parameters with analytic moment compensation is a more invasive
alternative [R03] [R06] [R07].

The successor should freeze `SPEC-A5-EVALUATION` revision 4 before output,
including uncertainty-scaled Gates 3/4, a faithful-clone null candidate for
empirical false-failure measurement, repaired Gate 1/4 bootstrap availability,
an explicit WEPP-bound decision, and station-day intervention-rate guards.
It should retain the complete downstream campaign and assess hierarchical or
regional coefficient pooling because 30 annual vectors are insufficient to
separate the present model and estimation weaknesses. These recommendations
do not select or salvage a current candidate. Faithful generation remains the
default and no public extension profile was created. [E13]

## Reproducibility and data availability

The experiment was executed and accepted at source commit
`7273829517121011edd8bb815ff72fefd3742bcb`. The evidence-identity manifest
binds the deterministic gzip climate analysis (archive SHA-256
`540a72530d5a6b6b063a951d65c91cb0a903a474e14935a26c8ee88580fef78c`,
decompressed SHA-256
`7243a51bbb81782d14e8faea1b4d3f01566e7f1c5071b159ca1e6f85dd88f0ac`)
and the WEPP analysis (SHA-256
`221347acedbf0556ace91d3d64dce99d9e5407855d258f7e097f3bfab4ae873e`).
Large generated climate and WEPP evidence files are stored through Git LFS;
specifications, manifests, scripts, and reports are ordinary Git objects.
[E07] [E10] [E11]

The exact Daymet and GHCN objects are archived under the A5a third-party data
notice with source hashes and citations; the repository license does not
relicense them. The A5b gate record lists every verifier and repository command,
and the accepted independent closure review records its recomputation and
exploratory-boundary correction. This report has its own strict hash manifest,
claim ledger, consolidated multi-lens review, and reproducible report verifier.
[E08] [E09] [E12]

### Revision history

Revision 1 was accepted at report SHA-256
`8f6b4b18e8e1761ab3a5ae9651f201060fc0c9ebebe801e98c4ed9909f7f83e4`.
Revision 2 incorporates the operator-requested post-acceptance advisory: it
adds the variance-reallocation interpretation, prospective gate-calibration
work, the successor design sequence, and an exact 34.4% dewpoint-cap rate in
place of the advisory's approximate “one fifth” derivation. It changes no
experiment table, gate outcome, hypothesis outcome, or no-promotion decision.
[E13]

## References

### Publications and datasets

- **R01.** Richardson, C. W. (1981). Stochastic simulation of daily precipitation, temperature, and solar radiation. *Water Resources Research*, 17(1), 182–190. [DOI 10.1029/WR017i001p00182](https://doi.org/10.1029/WR017i001p00182).
- **R02.** Katz, R. W., & Parlange, M. B. (1998). Overdispersion phenomenon in stochastic modeling of precipitation. *Journal of Climate*, 11, 591–601. [DOI 10.1175/1520-0442(1998)011<0591:OPISMO>2.0.CO;2](https://doi.org/10.1175/1520-0442(1998)011%3C0591:OPISMO%3E2.0.CO;2).
- **R03.** Wilks, D. S., & Wilby, R. L. (1999). The weather generation game: a review of stochastic weather models. *Progress in Physical Geography*, 23(3), 329–357. [DOI 10.1177/030913339902300302](https://doi.org/10.1177/030913339902300302).
- **R04.** Meyer, C. R. (undated). *General description of the CLIGEN model and its history*. USDA ARS NSERL. No DOI. [Official report](https://www.ars.usda.gov/ARSUserFiles/50201000/WEPP/cligen/CLIGENDescription.pdf).
- **R05.** Meyer, C. R., Renschler, C. S., & Vining, R. C. (2008). Implementing quality control on a random number stream to improve a stochastic weather generator. *Hydrological Processes*, 22(8), 1069–1079. [DOI 10.1002/hyp.6668](https://doi.org/10.1002/hyp.6668).
- **R06.** Chen, J., Brissette, F. P., & Leconte, R. (2010). A daily stochastic weather generator for preserving low-frequency of climate variability. *Journal of Hydrology*, 388, 480–490. [DOI 10.1016/j.jhydrol.2010.05.032](https://doi.org/10.1016/j.jhydrol.2010.05.032).
- **R07.** Steinschneider, S., & Brown, C. (2013). A semiparametric multivariate, multisite weather generator with low-frequency variability for use in climate risk assessments. *Water Resources Research*, 49, 7205–7220. [DOI 10.1002/wrcr.20528](https://doi.org/10.1002/wrcr.20528).
- **R08.** Fatichi, S., Ivanov, V. Y., & Caporali, E. (2011). Simulation of future climate scenarios with a weather generator. *Advances in Water Resources*, 34, 448–467. [DOI 10.1016/j.advwatres.2010.12.013](https://doi.org/10.1016/j.advwatres.2010.12.013).
- **R09.** Yu, B. (2000). Improvement and evaluation of CLIGEN for storm generation. *Transactions of the ASAE*, 43(2), 301–307. [DOI 10.13031/2013.2705](https://doi.org/10.13031/2013.2705).
- **R10.** Zhang, X. C., & Garbrecht, J. D. (2003). Evaluation of CLIGEN precipitation parameters and their implication on WEPP runoff and erosion prediction. *Transactions of the ASAE*, 46(2), 311–320. [DOI 10.13031/2013.12982](https://doi.org/10.13031/2013.12982).
- **R11.** Wang, W., Flanagan, D. C., Yin, S., & Yu, B. (2018). Assessment of CLIGEN precipitation and storm pattern generation in China. *Catena*, 169, 96–106. [DOI 10.1016/j.catena.2018.05.024](https://doi.org/10.1016/j.catena.2018.05.024).
- **R12.** Srivastava, A., Flanagan, D. C., Frankenberger, J. R., & Engel, B. A. (2019). Updated climate database and impacts on WEPP model predictions. *Journal of Soil and Water Conservation*, 74(4), 334–349. [DOI 10.2489/jswc.74.4.334](https://doi.org/10.2489/jswc.74.4.334).
- **R13.** Thornton, M. M., Shrestha, R., Wei, Y., Thornton, P. E., & Kao, S.-C. (2022). *Daymet: Daily Surface Weather Data on a 1-km Grid for North America, Version 4 R1*. ORNL DAAC. [DOI 10.3334/ORNLDAAC/2129](https://doi.org/10.3334/ORNLDAAC/2129).
- **R14.** Thornton, P. E., Shrestha, R., Thornton, M., Kao, S.-C., Wei, Y., & Wilson, B. E. (2021). Gridded daily weather data for North America with comprehensive uncertainty quantification. *Scientific Data*, 8, 190. [DOI 10.1038/s41597-021-00973-0](https://doi.org/10.1038/s41597-021-00973-0).
- **R15.** Menne, M. J., et al. (2012). *Global Historical Climatology Network–Daily, Version 3*. NOAA National Climatic Data Center. [DOI 10.7289/V5D21VHZ](https://doi.org/10.7289/V5D21VHZ).

### Repository records and reproducibility artifacts

- **E01.** [A5b preregistration](../work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts/a5b-pre-registration.md) — research questions, fixed matrix, and pre-output rules.
- **E02.** [SPEC-A5-EVALUATION revision 3](../specifications/SPEC-A5-EVALUATION.md) — aggregation, gates, uncertainty, and downstream response contract.
- **E03.** [SPEC-A5B-CANDIDATES revision 1](../specifications/SPEC-A5B-CANDIDATES.md) — exact candidate mathematics, identities, and overlay behavior.
- **E04.** [Daily source assessment](../work-packages/20260713-a5b-coefficient-source-assessment/artifacts/daily-source-assessment.md) — Daymet selection and source limitations.
- **E05.** [A5b experiment package](../work-packages/20260713-a5b-interannual-candidate-spike/package.md) — execution scope, access boundary, and terminal status.
- **E06.** [A5b results](../work-packages/20260713-a5b-interannual-candidate-spike/artifacts/results.md) — accepted human-readable result tables and interpretation.
- **E07.** [Analysis evidence manifest](../work-packages/20260713-a5b-interannual-candidate-spike/artifacts/analysis-evidence-v1.json) — canonical climate/WEPP content identities.
- **E08.** [A5b gate results](../work-packages/20260713-a5b-interannual-candidate-spike/artifacts/gate-results.md) — exact verification commands and completion counts.
- **E09.** [A5b independent closure review](../work-packages/20260713-a5b-interannual-candidate-spike/artifacts/review.md) — independent recomputation and exploratory-boundary disposition.
- **E10.** [Canonical climate analysis](../work-packages/20260713-a5b-interannual-candidate-spike/artifacts/climate/a5b-analysis-v1.json.gz) — deterministic gzip machine analysis; content identity stated above.
- **E11.** [Canonical WEPP analysis](../work-packages/20260713-a5b-interannual-candidate-spike/artifacts/wepp/a5b-wepp-analysis-v1.json) — paired downstream analysis and response evidence.
- **E12.** [A5a third-party data notice](../../references/observed/a5a-v1/THIRD_PARTY_DATA_NOTICE.md) — dataset citations, reuse boundaries, and archived-source provenance.
- **E13.** [Post-acceptance advisory review](../work-packages/20260714-interannual-candidate-exp-001-report/artifacts/post-acceptance-advisory-review.md) — prospective gate calibration and successor-design recommendations; its approximate dewpoint-cap rate is corrected in revision 2.
