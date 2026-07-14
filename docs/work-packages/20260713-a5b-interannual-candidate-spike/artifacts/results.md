# A5b Interannual Candidate Results

Status: complete exploratory experiment; no candidate supported for promotion
Decision scope: evidence only; no public model, profile, or format promoted

## Executive result

All seven candidates fitted successfully at all 17 stations, generated the
complete 1,904-run climate matrix, and produced the complete 2,176-record WEPP
campaign. The 2,000-replicate observed-target bootstrap also completed. No
candidate passed all six climate gates at both horizons. Gate 7 subsequently
passed for every row when the complete downstream campaign was attached, but
that does not cure a climate-gate failure.

Under the frozen thresholds, **none of the A5b candidates is eligible for
promotion under SPEC-A5-EVALUATION revision 3.** This no-promotion disposition
is numerically robust, but the final analyses remain exploratory for
model-selection purposes. The retained post-climate and post-output
amendments disclose candidate response and metric-value inspection while
successor executable contracts were repaired. A5c should record the
conservative no-promotion disposition from this evidence; promotion of one of
these model families would require a new prospective study rather than
selection from the present exploratory results.

## Gate results

`P` and `F` below are the deterministic pass/fail results. G1 is primary
held-out Daymet improvement; G2 is independent GHCN sensitivity; G3 is fixed
monthly-contract preservation; G4 is daily precipitation structure; G5 is
the storm-descriptor no-regression guard; G6 is the winter-climate guard; G7
is complete climate and WEPP evidence.

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

### Primary and guard magnitudes

Ratios are candidate observed-distance divided by the matched faithful-off
distance; smaller is better. G1 requires composite and low-frequency ratios
at most 0.90, at least 11 improved stations, and every regime at most 1.05.
G3 and G4 require a corpus ratio at most 1.10 plus their registered
station-level conditions. G5 reports failed cells out of 408.

| Candidate | Years | G1 composite | G1 low-frequency | Improved stations | Worst regime | G3 | G4 | G5 failed | G6 |
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

No single architecture dominates even within G1. Spectral random phase has
the only composite ratio below 0.90 (100 years), but its low-frequency ratio
is 1.091. Vector AR is the only candidate below 0.90 on low frequency at 100
years and meets the station/regime conditions there, but its composite is
0.925. Fourier/EOF has only two descriptor failures at each horizon, but its
low-frequency and monthly-contract results miss by substantial margins.

The universal G3/G4 failures are the decisive structural warning. Improving
interannual properties by applying an unconstrained annual overlay does not
preserve CLIGEN's fitted monthly surface or its daily precipitation
structure. The narrow precipitation counterfactual does not solve that
problem: its G3 ratios are 2.570 and 3.243 and its G4 ratios are 1.849 and
2.021.

## Fit and runtime evidence

Every station fit reported `ok`; there were no fit warnings or execution
failures. The HMM fitter recorded two deterministic state-relabeling
interventions. Parameter counts remain an independent model-version property
and are not collapsed into the station-schema version.

| Candidate | Runtime parameters per station | Median run time (ms) | Precipitation clips | Temperature-order repairs |
|---|---:|---:|---:|---:|
| Rank-one monthly SD | 36 | 765.5 | 9,816 | 35,657 |
| Full monthly covariance | 666 | 765.5 | 8,900 | 8,867 |
| Fourier/EOF | 216–360 | 767.0 | 1,170 | 2,850 |
| Vector AR | 273–515 | 812.0 | 1,000 | 2,807 |
| Gaussian HMM | 242–402 | 794.5 | 1,214 | 2,994 |
| Spectral random phase | 306–510 | 765.5 | 1,212 | 2,883 |
| Precipitation counterfactual | 276–420 | 729.5 | 1,174 | 2,975 |

All candidates also triggered about 2.22 million dewpoint caps across their
272 runs. Those counts are diagnostics, not silently discarded behavior.
Rank-one SD and full covariance need markedly more clipping/repair than the
other dynamic candidates, reinforcing their poor gate results.

## Downstream WEPP response

All 2,176 response and execution records validated. The evidence includes 17
stations, two horizons, eight replicates, the faithful-off baseline, and all
seven candidates. The fixed-width recovery audit records four `EffInt`
overflows, 13,473 `Sm` overflows, 152 source-anchored `PeakRO` recoveries, and
seven same-day duplicate element rows; all were handled under the frozen
campaign contract. There were no campaign failures.

The table below reports the median across stations of paired candidate /
faithful-off ratios for the annual-mean response statistic. These ratios are
descriptive; revision 1 intentionally registers no downstream numeric pass
bound. Exact signed differences and every station/replicate pair remain in
the canonical analysis. Baseline-zero pairs are null rather than converted
to zero or infinity.

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

These are large downstream changes, not compatibility-scale perturbations.
The five cold/snow stations show much smaller median snow-state changes:
annual maximum snow-water-state ratios range from 1.060 to 1.170 and annual
snowmelt ratios from 0.981 to 1.031. Rain-on-snow, winter-runoff, and
winter-soil-loss corpus medians are dominated by baseline-zero pairs, so the
archived signed differences and availability counts are the meaningful
record rather than a synthetic ratio.

## Uncertainty and sensitivities

The report-only uncertainty analysis used the preregistered 2,000 circular
moving-block bootstrap replicates with five-year blocks. It emitted all
registered scalar-cell, station-variable, station-family, station-gate,
regime-gate, and corpus-gate intervals. It did not alter deterministic gate
outcomes. Six registered full-period/detrended Daymet and GHCN sensitivity
projections also completed for every candidate/horizon combination.

## Interpretation and next action

A5b rejects the initial production-form candidate versions; it does not
reject interannual modeling as a direction. The most useful design evidence
is:

1. A future model must enforce the fixed monthly climate contract during
   realization rather than rely on unconstrained annual scaling.
2. Daily precipitation occurrence, amount persistence, and multi-day
   extremes must be modeled jointly with the interannual latent state. The
   narrow after-the-fact precipitation counterfactual is insufficient.
3. Vector AR, spectral random phase, and Fourier/EOF expose complementary
   strengths worth retaining as design components, but none is a promotable
   profile in its present form.
4. Downstream WEPP sensitivity is large enough that future climate-gate
   improvements must continue to carry the complete response campaign.

The immediate roadmap action is A5c as a short formal no-promotion
adjudication. A subsequent prospectively registered A5d study should test a
monthly-constrained latent model with integrated daily precipitation
structure. Faithful generation remains the default throughout.

## Evidence identities

The canonical identities are machine-readable in
[`analysis-evidence-v1.json`](analysis-evidence-v1.json). The 135,677,893-byte
climate JSON is retained as deterministic gzip because its raw form exceeds
GitHub's single-object limit. Decompression reproduces SHA-256
`7243a51bbb81782d14e8faea1b4d3f01566e7f1c5071b159ca1e6f85dd88f0ac`.
The uncompressed WEPP analysis SHA-256 is
`221347acedbf0556ace91d3d64dce99d9e5407855d258f7e097f3bfab4ae873e`.
