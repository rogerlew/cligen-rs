# SPEC-A5B-CANDIDATES -- Interannual Candidate Spike

Status: active (revision 1; experimental, not promoted)
Surface: A5b coefficient-augmented station bundles, candidate plans, overlay
runtime, and run records

## Purpose and compatibility boundary

A5b compares seven interannual structures without changing faithful CLIGEN.
The faithful generator first produces an exact typed daily trajectory under
`faithful_5_32_3 + qc_filter: off`. A separately versioned A5b overlay applies
an independently seeded annual climate state. The legacy RNG streams and
generator state are never read by, written by, or advanced by the overlay.

A5b is a spike, not a public generation surface. It therefore does not extend
SPEC-RUNSPEC, provenance v1, station-document v1, CLI-Parquet v1, or the
public generation-profile enum. A strict A5b run record carries the candidate
lineage. The quality report is intentionally computed post hoc and retains
the frozen envelope 2 / metrics 3 with `identity.provenance: null` and
`process: null`. A5c must specify and implement any promoted public model.

## Normative schemas

| Schema | Identity |
|---|---|
| `a5b-augmented-station-v1.schema.json` | station bundle grammar 1 |
| `a5b-overlay-plan-v1.schema.json` | finite-run overlay plan grammar 1 |
| `a5b-run-record-v1.schema.json` | experimental run lineage grammar 1 |
| `a5b-candidate-evidence-v1.schema.json` | sealed matrix evidence grammar 1 |

Schema validity is necessary but not sufficient. The A5b verifier enforces
array shapes, fixed candidate order, independent identities, exact hashes,
source limits, matrix closure, cross-record relationships, and the numerical
invariants below. Parsing rejects duplicate keys and nonfinite JSON tokens
before schema validation.

## Frozen identities

| Candidate | Station-model ID | Generation-profile ID |
|---|---|---|
| rank-one monthly SD | `interannual_rank_one_monthly_sd_v1` | `a5b_rank_one_monthly_sd_v1` |
| full monthly covariance | `interannual_full_monthly_covariance_v1` | `a5b_full_monthly_covariance_v1` |
| Fourier/EOF | `interannual_fourier_eof_v1` | `a5b_fourier_eof_v1` |
| vector AR | `interannual_fourier_eof_var1_v1` | `a5b_vector_ar_v1` |
| Gaussian HMM | `interannual_fourier_eof_hmm2_v1` | `a5b_gaussian_hmm_v1` |
| spectral random phase | `interannual_fourier_eof_spectral_v1` | `a5b_spectral_random_phase_v1` |
| precipitation counterfactual | `interannual_fourier_eof_precip_counterfactual_v1` | `a5b_fourier_eof_precip_counterfactual_v1` |

The coefficient payload schema is `a5b_interannual_coefficients_v1`. The
source snapshot is `daymet_v4r1_a5a17_fit1980_2009_noleap_v1`. The primary
fit recipe is `a5b_monthly_state_fit_v1`. The extension PRNG is
`splitmix64_box_muller_v1`; model/profile and station IDs are SHA-256 domain
labels before its first state transition. Each standard normal consumes
exactly two consecutive open-interval uniforms and returns
`sqrt(-2*ln(u1))*cos(2*pi*u2)`; the sine mate is discarded and never cached.
The initial state is digest bytes 0--7 interpreted unsigned big-endian from
`SHA-256("cligen-a5b-extension-v1\0" + station_id_ascii + "\0" +
profile_id_ascii + "\0" + seed_u64_big_endian_bytes)`. Candidate 7 derives
its event-relocation state identically with domain
`"cligen-a5b-counterfactual-v1\0"`. The annual-state-table hash is SHA-256
over UTF-8 compact JSON of the `annual_states` array only, with object keys
sorted, ASCII escaping enabled, comma/colon separators, no nonfinite values,
and no trailing LF.

## Source and preprocessing

The only primary fit inputs are the 17 gzip objects already archived under
`references/observed/a5a-v1/daymet/`. Each archive SHA-256 must equal the A5a
corpus config. The reader validates the complete header, requested latitude
and longitude, returned Lambert x/y, tile, grid elevation, software version,
units, and 365 unique ordinal days for each year. It opens and materializes
only rows with `1980 <= year <= 2009`; encountering a missing fit row,
duplicate, sentinel, nonfinite number, negative precipitation, Tmax below
Tmin, or a fit-period year other than the exact 30-year set is fatal.
Post-2009 rows are counted for a structural-boundary audit but never enter a
fit array or statistic.

The primary calendar transform is A5a `noleap_365_v1`: ordinal days map over
fixed month lengths `[31,28,31,30,31,30,31,31,30,31,30,31]` in every year.
An official-Daymet civil-calendar sensitivity is not promised by revision 1;
it may be run later only as an optional, report-only, non-gate follow-on and
cannot replace the A5b primary score. PRISM and gridMET are not in revision 1.

For each year, form a 36-vector in this exact variable-major order:

1. January--December `log1p(sum(prcp_mm))`;
2. January--December mean Tmax in degrees C; and
3. January--December mean Tmin in degrees C.

Subtract each feature's 30-year arithmetic mean. No linear detrending is
applied to the primary fit (`center_only_raw_v1`). OLS-detrended diagnostics
receive a different identity and cannot feed a candidate. All sample
covariances use denominator 29. Float64 is the coefficient science precision;
canonical JSON uses finite shortest-round-trip decimal numbers.

## Common seasonal compression and deterministic EOF convention

For Fourier candidates, each variable's 12 centered monthly values are
projected onto the orthonormal real basis containing the constant and cosine/
sine pairs for harmonics 1, 2, and 3, in order
`constant, cos1, sin1, cos2, sin2, cos3, sin3`. Month index is zero based and
the angle is `2*pi*k*m/12`. Constant normalization is `1/sqrt(12)` and every
cosine/sine normalization is `sqrt(2/12)`. The three 7-vectors concatenate in
the feature order above to 21 Fourier features.

The 21 x 21 covariance receives diagonal shrinkage
`0.95*S + 0.05*diag(S)`. Symmetrize by `(C+C.T)/2`; eigenvalues below
`1e-12 * max(1, largest_eigenvalue)` are zero. Sort decreasing. Within a tie
of `1e-12 * max(1, largest_eigenvalue)`, order lexicographically by the
absolute loading vector. Give every eigenvector the sign for which its
largest-absolute component (lowest index on ties) is positive. Retain the
smallest rank reaching 90% positive explained variance, bounded to 3--10 and
never retaining a nonpositive eigenvalue. Failure to retain three modes is a
fit failure. The stored 36 x rank reconstruction matrix includes Fourier
inverse projection and square roots of retained eigenvalues, so a standard
normal score maps directly to physical centered features.

## Candidate definitions

All samplers generate a fixed 128-year table for each extension seed. Both
30- and 100-year runs consume prefixes of that same table, so common-prefix
behavior is mandatory. After sampling, subtract the 128-year arithmetic mean
from each temperature month. Convert a precipitation log anomaly to a factor
with `q_y = exp(delta_y)`. For each month, choose the unique positive scale
`s` satisfying
`fsum_y(clamp(s*q_y, 0.05, 20.0)) == 128.0` in binary64. Locate its active
interval by a deterministic sweep over the `0.05/q_y` and `20.0/q_y`
breakpoints, then solve `s` from the active-set linear equation. After the
box projection, assign any rounded residual to the lowest-index interior
year by recomputing all other terms with `fsum`; if subtraction lands on an
adjacent float, take at most eight `nextafter` steps toward the target and
accept only an exact correctly rounded sum. Failure to obtain the exact sum
or remain in `[0.05,20.0]` is fatal. The field
`precipitation_clip_count` retains its revision-1 name but counts final values
exactly on either box bound. This fixed-table projection and temperature
centering are runtime operations, not fitted parameters.

### 1. Rank-one monthly SD

Fit the 36 sample standard deviations. Each year draws three independent
standard normals. One normal per variable multiplies that variable's 12 SDs.
Runtime parameter count: 36.

### 2. Full monthly covariance

Fit the 36 x 36 sample covariance, then apply
`0.90*S + 0.10*diag(S)`, symmetrize, and floor eigenvalues at
`1e-10 * max(1, largest_eigenvalue)`. Store the deterministic lower Cholesky
factor and draw 36 independent standard normals per year. Runtime parameter
count: 666 lower-triangular values. A nonfinite or non-positive-definite
repaired matrix is fatal.

### 3. Fourier/EOF

Use the common reconstruction matrix and draw independent standard normal EOF
scores per year. Runtime parameter count: `36*r`.

### 4. Vector AR

Project the 30 training years into retained standardized EOF scores. Fit
VAR(1) by ridge least squares with
`lambda = 0.01 * trace(X*X.T) / r`. If the transition spectral radius exceeds
0.98, multiply the entire matrix by `0.98/radius` and report an intervention.
Fit the centered innovation covariance with 0.10 diagonal shrinkage and the
same positive eigenvalue floor as candidate 2. Initialize all scores at zero,
run 256 discarded warm-up transitions, then emit 128 years. Runtime parameter
count: `36*r + r*r + r*(r+1)/2`.

### 5. Two-state Gaussian HMM

Use the retained standardized EOF scores. The two-state HMM has a full 2 x 2
transition matrix and diagonal Gaussian emissions. Initialize states by the
lower/upper median split of each year's total precipitation-log anomaly;
empty-state initialization is fatal. Initial transition counts and every
transition M-step use Jeffreys pseudocount 0.5. Emission variances have floor
`1e-6`. Run scaled forward/backward EM for at most 200 iterations and stop
when improvement in the penalized objective
`raw_log_likelihood + 0.5*sum(log(transition_probability))` is nonnegative and
below `1e-8`. This objective matches the frozen add-0.5 transition smoothing;
raw likelihood alone is reported but is not monotone under that M-step. A
decrease in `[-1e-7,0)` is recorded as a floating-point roundoff intervention
and treated as zero improvement, while a decrease below `-1e-7`, nonfinite
objective/likelihood, or lack of convergence is fatal. Relabel
state 0 as the state with smaller reconstructed annual precipitation-log mean
(lexicographic emission mean breaks ties). Start generation from the exact
two-state stationary distribution, emit year 1 from that state, then apply
one transition before each subsequent year's emission for 128 total years.
Runtime parameter count: `36*r + 2 + 4*r` (two independent transition
probabilities and two state means/variances per score).

### 6. Spectral random phase

Use each retained training score's centered 30-year real DFT amplitudes. The
spectral fitter re-centers each mode using `fsum` in chronological year order
divided by 30. For source frequencies `k=1..14`, it evaluates the unnormalized
DFT in chronological order with
`theta=(2.0*pi*k*year)/30.0`,
`real=fsum(score*cos(theta))`, and
`imaginary=fsum(-score*sin(theta))`, then stores
`hypot(real, imaginary)`. Frequency 15 is the real Nyquist term and is stored
as `abs(fsum(score if year is even else -score))`; it does not evaluate a
sine or cosine. There is no `1/30` normalization. This explicit fixed-size
DFT is the normative fit algorithm; a generic FFT implementation is not an
equivalent byte-production path. The fit-time zero check computes sample SD
directly from the same re-centered values with `fsum` and denominator 29. The
runtime reconstructs its target sample SD from the stored amplitudes as
`sqrt((2*fsum(A_k^2 for k=1..14)+A_15^2)/(30*29))`; this
amplitude-derived value is normative. Zero training SD is fatal.

Linearly interpolate the 15 amplitudes by normalized frequency onto a fixed
128-year real spectrum, including an explicit
`(frequency=0, amplitude=0)` anchor; DC is zero and the Nyquist coefficient is
real with an independent random sign. In mode-major order, frequencies 1--63
each consume one independent uniform phase and the Nyquist sign consumes the
next draw. Inverse transform and rescale each 128-year score series to the
training sample SD. Runtime parameter count: `36*r + 15*r` (reconstruction
plus the 15 non-DC training amplitudes).

### 7. Fourier/EOF precipitation counterfactual

The annual state is exactly candidate 3 under a separately domain-separated
seed. Fit, for each month, four second-order trace-wet probabilities
`P(W_t=1 | W_{t-2},W_{t-1})` using Daymet `prcp_mm > 0` and Jeffreys 0.5
pseudocounts, resetting both history bits dry at each month boundary. Also fit
Pearson lag-one correlation of `log1p(prcp_mm)` for adjacent positive days in
that month; fewer than three pairs yields zero, otherwise clamp to
`[-0.95,0.95]` and report any clamp.

After the annual precipitation multiplier is applied, the runtime handles
each simulation year/month independently. It preserves the exact multiset and
count of faithful wet-event tuples
`(precip_mm, duration_h, time_to_peak_fraction, peak_intensity_ratio)`.
A SplitMix64 sequential fixed-count sampler proposes wet/dry days from the
four fitted probabilities and forces wet when remaining wet events equal
remaining days or dry when none remain. Generate one stationary AR(1) normal
score per wet position using the fitted amount correlation. Sort event tuples
by precipitation (original order breaks ties), sort positions by the AR score
(day breaks ties), and assign ranks. Every dry tuple is four positive zeros.
No event crosses a month boundary. Runtime parameter count: `36*r + 60`.

## Daily overlay semantics

The runtime applies the plan by simulation year and month to exact pre-format
typed rows:

- before mutation, find the maximum faithful typed f32 precipitation for each
  consumed simulation-year/month. Let `L` be the exact binary64 widening of
  the f32 literal `999.9`. The effective month factor is the requested factor
  for a dry month and otherwise
  `min(requested_factor, L/base_max_precip_mm)`. Apply that one effective
  factor to every day in the month; this is a base-dependent, prefix-local
  renderability adjustment, not a daily cap. Never scale duration, time to
  peak, or `peak_intensity_ratio`;
- add the Tmax and Tmin deltas independently;
- add the Tmin delta to dew point, then cap dew point at Tmin;
- if Tmax would be below Tmin, replace the pair by their midpoint plus/minus
  0.05 C and report one relational repair; and
- leave solar radiation, wind speed, and wind direction unchanged.

Arithmetic is float64 and each emitted value is narrowed once to finite f32.
Negative precipitation, overflow, an asterisk field in fixed-width output, a
missing state, a noncontiguous date, or an unparseable rendered CLI is fatal.
Diagnostics contain exactly `12*horizon_years` ordered precipitation-factor
records with requested/effective factors, faithful monthly maximum, `L`, and
the adjustment flag, plus their exact adjusted-month count. The runtime
renders and asterisk-checks every daily row, including the F5.1 Tmax, Tmin,
and dew-point fields, before it can publish diagnostics; therefore a sealed
diagnostic `row_count` also records complete fixed-width renderability, with
no temperature or dew-point cap beyond the specified relational repairs.
All base-header bytes, monthly station vectors, and daily header lines remain
exact except the command-echo suffix. The shared faithful base ends with
`--a5b-base faithful_5_32_3 --qc-filter off`; the overlay replaces only that
suffix with `--a5b-profile <profile> --extension-seed <seed> --qc-filter off`.
No candidate Parquet is emitted under typed-output revision 1.

## Independent plan and run identity

The eight extension seeds are exactly those in the A5a preregistration. A plan
records 128 annual states, the candidate profile, seed, source coefficient
hash, state-table hash, normalization interventions, and (only for candidate
7) the daily counterfactual parameters. The plan is deterministic for
`(station bundle, profile, extension seed)` and independent of horizon/burn.

Every run record binds the A5a corpus, base `.par`, augmented station bundle,
candidate station model/profile, coefficient/fit/source IDs and hashes, plan,
extension seed/PRNG/domain, legacy burn, horizon, base runspec and typed-run
identity, candidate CLI, post-hoc quality report, executable, and diagnostics.
Its contract inventory binds both the augmented-station schema and the exact
fixed-monthly station schema resolved by that schema; validation uses a local
registry and must perform no automatic remote JSON-Schema retrieval.
The record must not represent its post-hoc report as trusted provenance.
For each station/horizon/replicate, one candidate-neutral faithful base is
generated and all seven candidates bind its exact runspec, CLI hash, and run
ID. Before target creation, the runner generates and validates all 952 real
plans in memory and records their deterministic named-byte aggregate. The 272
base runspecs and their 272 provenance-v1 companions are retained in one
canonical shared-base archive. Its ordered index binds each runspec and
provenance member, faithful CLI hash, effective-runspec run ID, and station
parameter-set hash. The independent verifier reconstructs the exact runspec
bytes and declaration-ordered effective-runspec hash, validates provenance
semantics, and cross-checks every candidate run against that shared index.
The overlay independently regenerates the faithful trajectory through the
typed-row API and must reproduce the shared base CLI hash before applying the
plan.

Candidate and shared-base archives are first written under the target's
private staging tree. The independent verifier consumes those staged bytes by
explicit directory substitution while the manifest continues to name only
the final repository paths. Only after all staged archives, retained CLIs,
records, and cross-bindings pass are the eight archives atomically published,
followed by the manifest as the seal. A failure before that seal removes every
new public archive and the new target tree; pre-existing output is never
overwritten or removed.

The sealed evidence manifest has one versioned lifecycle transition. Climate
publication writes `candidate_cli_bytes_removed_after_wepp: false`; the
evidence verifier then requires every indexed raw CLI at its deterministic
target path. The pinned WEPP campaign consumes and rehashes those bytes. Only
after all 2,176 downstream records validate may its runner delete the raw
candidate CLIs and atomically change that field to `true`. It records both
manifest hashes and proves every other manifest value is byte-for-byte
unchanged. With `true`, the verifier relies on the sealed CLI hash/byte indexes
and requires no raw climate payload. No other post-seal manifest mutation is
permitted.

## Failure and inspection rules

Fits do not silently drop stations, years, months, modes, or variables. A
candidate/station fit failure remains an explicit matrix-wide failure for that
candidate. A run intervention permitted above is counted and reported; every
other constraint violation is fatal. Candidate reports remain sealed until
all 1,904 records, station bundles, plans, hashes, report schemas, and exact
matrix keys validate. Analyzer output cannot redefine a fit or gate.

## Parameter-count rule

The primary count is the number of distinct fitted numeric coefficients read
by the runtime, using the formulas above. Fixed basis constants, source
metadata, diagnostic reconstructions, deterministic stationary distributions,
and 128-year random realizations are excluded. The fit manifest additionally
reports the total serialized numeric count so storage and duplication remain
visible. Neither count enters a promotion gate.
