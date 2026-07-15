# SPEC-A5E0-PILOT -- Direct Annual-State Feasibility Pilot

Status: closed (revision 1; exploratory execution held, not promoted)
Owning work package: `20260714-a5e0-direct-annual-state-pilot`
Execution-base commit: `27e5e7754bdfafcca649a71d0f5576910433d0d3`

## Outcome-access disclosure and authority disposition

This file was created before fitting and reached its current pre-campaign form
before candidate climate output, but it was not committed or independently
hash-sealed at either boundary. It was corrected after H0 output and before
the climate matrix to use the exact `100003` faithful skip multiplier. The
analyzer was likewise not committed before candidate output and reached its
recorded form after the matrix. The execution-base commit above contains the
committed scaffold and its decision thresholds, not this specification or the
implementation.

Consequently, the 2026-07-14 execution cannot demonstrate the immutable
prospective boundary claimed by the package. H0--H3 are retained as
exploratory measurements against these intended rules, and the package
decision is `EXECUTED-HOLD-PROSPECTIVE-BOUNDARY`; `CLOSE-MECHANISM` in the
analysis artifact is only the provisional H1--H3 climate mapping. The package
does not authorize A5e1. The descriptor guard was also worded differently here
and in the committed scaffold; a post-output audit evaluates both readings and
finds both passing, without repairing or changing the terminal hold.

## Surface and authority boundary

A5e0 tests one deliberately small successor mechanism: one independent
standard-normal annual state changes four existing monthly generator inputs.
It does not change faithful CLIGEN, the public generation-profile enum, the
station-document grammar, runspec, or provenance v1. The public faithful path
must remain byte-identical. A5e0 is identified only by the research profile
`a5e0_direct_annual_state_v1` and its sealed campaign record.

The vendored Fortran remains authoritative for every faithful operation.
A5e0 owns only these declared extension operations:

1. annual occurrence transition probabilities;
2. annual mean wet-day precipitation amount;
3. annual maximum-temperature monthly mean; and
4. annual minimum-temperature monthly mean, with the same anomaly added to
   the monthly dew-point mean.

The four changes are installed before a generated year and are visible to the
existing faithful daily machinery. The effective occurrence probabilities are
the same values supplied to both `ranset` and `gen_precip`; their distinct
faithful state chains remain distinct. `r5monb` is evaluated once from the base
station during setup. No annual state changes it. The research baseline uses
the same segmented faithful RNG initialization but installs no extension.

## Producers and consumers

The package fitter produces one `a5e0_coefficients_v1` bundle. The package
runner consumes that bundle and the fixed monthly station documents, emits
research `.cli` files and diagnostics, and invokes the existing quality-report
instrument. The package analyzer consumes those run products and emits one
`a5e0_campaign_evidence_v1` record. The verifier is the final authority for
schema, hash, matrix, identity, and cross-record closure.

Malformed, incomplete, duplicate-key, nonfinite, out-of-range, or
identity-inconsistent inputs fail closed. JSON uses UTF-8, sorted object keys,
shortest-round-trip finite decimal numbers, comma/colon separators, and one
trailing LF. Artifact SHA-256 values are over exact stored bytes.

## Frozen identities and station matrix

| Item | Identity |
|---|---|
| research profile | `a5e0_direct_annual_state_v1` |
| coefficient grammar | `a5e0_direct_annual_state_coefficients_v1` |
| fit recipe | `a5e0_direct_monthly_loading_fit_v1` |
| observed snapshot | `daymet_v4r1_a5a17_fit1980_2009_noleap_v1` |
| extension PRNG | `splitmix64_box_muller_v1` |
| faithful partition | `cbk7_skip_ahead_segments_v1` |
| campaign evidence | `a5e0_campaign_evidence_v1` |

The fixed station order is:

1. `ca042319`, dry stress case;
2. `co051660`, cold/winter stress case; and
3. `ms227840`, wet stress case.

The fit interval is exactly 1980--2009. Daymet input is the hash-pinned A5a
archive. The calendar is `noleap_365_v1`; month lengths are
`[31,28,31,30,31,30,31,31,30,31,30,31]`. A wet day has precipitation at
least 0.254 mm. Post-2009 observations are counted for boundary verification
but never enter a fit value. Missing years/days, duplicate ordinal days,
Daymet sentinels, negative precipitation, or Tmax below Tmin are fatal.

## Frozen coefficient fit

All fitting arithmetic is binary64. Sample variance uses denominator 29.
Summations use Python `math.fsum` in chronological order unless an operation
below names NumPy/SciPy. No detrending or tuning against A5e0 output is
permitted.

For each station, year, and month compute these four features in variable-major
order (occurrence months, amount months, Tmax months, Tmin months):

* `wet_fraction = wet_day_count / days_in_month`;
* `log_wet_mean = ln((sum_wet_mm + base_mean_wet_mm) /
  (wet_day_count + 1))`;
* arithmetic mean Daymet Tmax in degrees C; and
* arithmetic mean Daymet Tmin in degrees C.

Standardize each of the 48 feature columns by its 30-year sample mean and
sample standard deviation. A zero-SD column becomes 30 exact zeros. Form the
48 by 48 sample correlation matrix and use `numpy.linalg.eigh`. Choose the
largest eigenvalue; an eigenvalue tie within
`1e-12 * max(1, abs(largest))` is resolved by the lexicographically smallest
absolute eigenvector. Orient the vector so the sum of its first 24 components
is positive; if exactly zero, orient its lowest-index nonzero component
positive. A component sign is `+1` when the oriented component is zero.

For month `m`, define base stationary occurrence

`q_m = pwd_m / (1 - pww_m + pwd_m)` and
`rho_m = pww_m - pwd_m`.

The observed occurrence variance is the sample variance of annual monthly wet
fractions. The base finite-month variance is

`q_m*(1-q_m) * (n + 2*sum_{k=1}^{n-1} (n-k)*rho_m^k) / n^2`.

The occurrence loading magnitude is

`sqrt(max(observed_variance - base_variance, 0)) /
 max(q_m*(1-q_m), 1e-12)`.

The amount feature variance is the sample variance of `log_wet_mean`. Its base
sampling approximation is

`(base_amount_sd/base_amount_mean)^2 / (base_expected_wet_days + 1)`,

where `base_expected_wet_days = n*q_m`. The amount loading magnitude is the
square root of the positive excess. Temperature loading magnitudes are

`sqrt(max(observed_monthly_mean_variance - base_daily_sd^2/n, 0))`.

Each magnitude receives its corresponding oriented leading-component sign.
Occurrence and amount loadings are dimensionless; temperature loadings are
stored in degrees C. No empirical multiplier, cap, shrinkage, or output-driven
adjustment is allowed.

## Analytic moment preservation

Let `z` be the annual standard normal. All Gaussian expectations below use a
32-node Gauss-Hermite rule from `numpy.polynomial.hermite.hermgauss`, with
`z_i=sqrt(2)*x_i` and weight `w_i/sqrt(pi)`, evaluated in ascending node order.

### Occurrence

For each month,

`q_m(z) = logistic(a_m + lambda_occ_m*z)`,
`pwd_m(z) = (1-rho_m)*q_m(z)`, and
`pww_m(z) = rho_m + (1-rho_m)*q_m(z)`.

The 12 intercepts `a_m` are solved jointly. For a fixed `z`, propagate the
expected wet-state probability day by day through the 365-day calendar.
Represent the annual map as `p_end=A(z)*p_start+B(z)`. Its unconditional
stationary start is `E[B]/(1-E[A])`. Starting there, the quadrature-weighted
expected wet count in every month must equal the corresponding count under the
unmodified base 12-month Markov calendar. Solve the 12 residuals using
`scipy.optimize.root(method="hybr", options={"xtol": 1e-12,
"maxfev": 20000})`, initialized at `logit(q_m)`. Success requires solver
success and maximum absolute monthly count error no greater than `1e-10` day.

### Wet-day amount

Let `W_m(z)` be the conditional expected wet-day count obtained from the
solved occurrence calendar. For every month choose the centering constant

`c_m = ln(E[W_m] / E[W_m*exp(lambda_amount_m*z)])`.

With base mean `mu_m` and base SD `sigma_m`, the effective mean is

`mu_m(z)=mu_m*exp(c_m+lambda_amount_m*z)`.

The conditional residual variance is constant across years and equals

`mu_m^2 + sigma_m^2 -
 E[W_m*mu_m(z)^2]/E[W_m]`.

It must be at least `-1e-12`; a value in `[-1e-12,0)` is stored as zero.
Weighted mean and second-moment reconstruction errors must each be no greater
than `1e-10 * max(1, target)`.

### Temperature and dew point

For each temperature variable, the residual daily SD is

`sqrt(base_daily_sd^2 - loading_fahrenheit^2)`,

where `loading_fahrenheit = 1.8*loading_celsius`. A radicand below `-1e-12`
is infeasible; a value in `[-1e-12,0)` becomes zero. In year `y`, add
`loading_fahrenheit*z_y` to the monthly Tmax or Tmin mean. Add the same Tmin
anomaly to monthly dew-point mean. This preserves the base monthly
Tmin-minus-dew-point relationship exactly.

## Feasibility hypothesis H0

H0 passes only if all 144 loadings are finite, occurrence probabilities stay
strictly between zero and one at every quadrature node, the joint occurrence
solver meets its tolerance, every amount/temperature residual variance is
feasible, and all reconstruction checks meet tolerance. Failure of any item is
a valid `H0=FAIL` result and closes A5e0 without generating the run matrix.
The fit must emit a complete feasibility record whether H0 passes or fails.

An all-zero 48-loading station is an exact base-bit bypass. A zero loading in
a mixed station takes the local base-bit bypass for amount or temperature.
Zero occurrence loadings remain in the joint calendar solve, but their
effective transition probabilities must be exact base bits. These rules are
verified before the campaign.

## Runtime numerics

The annual extension state is generated in binary64. Runtime exponentials,
logarithms, square roots, cosine, and logistic operations use pinned `libm`,
never Rust standard-library float methods. Effective occurrence and amount
values are narrowed once to faithful binary32 station units. Temperature
loadings are multiplied by exact binary64 `1.8`, added in degrees F, then
narrowed once. Base-bit bypasses do not perform arithmetic before copying the
base binary32 value.

The annual-state seed is the unsigned big-endian integer in digest bytes 0--7
of

`SHA-256("cligen-a5e0-annual-state-v1\0" + station_id_ascii + "\0" +
 master_seed_u64_big_endian_bytes)`.

SplitMix64 uses its standard wrapping-u64 transition and finalizer. One normal
consumes exactly two consecutive open-interval uniforms
`((u64 >> 11)+0.5)/2^53`, returns
`sqrt(-2*ln(u1))*cos(2*pi*u2)`, and discards the sine mate. There is no cache.
The angle uses binary64 `std::f64::consts::TAU`. The generator draws exactly
one state immediately before each synthetic year.
There is no finite state table, recentering, normalization, selection, or
ordering. Standalone 30- and 100-year runs therefore consume the same prefix.

## Faithful RNG partition

Canonical `Cbk7State` seeds are advanced before setup by an exact integer
skip-ahead. Station ordinal is its zero-based position in the frozen station
order. For replicate `r` in 1--8,

`segment = 8*station_ordinal + (r-1)` and
`raw_skip = segment*500000`.

Each mixed-radix stream state is encoded as
`x=k0+1000*k1+10^5*k2+10^8*k3` modulo `10^10`. Raw recurrence skip-ahead is
`x' = 100003^raw_skip*x mod 10^10`: the source's `3*k` terms plus its two
cross-word additions are together multiplication by 100003. Skip-ahead is
computed by integer modular exponentiation, then decoded to the four fields.
No floating arithmetic or iterative skipping is permitted. The verifier checks
known skip vectors, each canonical stream
period, segment uniqueness, and a conservative per-stream 100-year raw-update
bound below 500,000. It also records observed returned-draw process counters.

The eight master seeds, indexed 1--8, are:

`0x0c8862ed55f21e2e`, `0x0c268832683959b1`,
`0x1a237b2016b95a3f`, `0x91328e5fa9a0e916`,
`0x0ee45605e7d362c3`, `0xc59c065475f321a3`,
`0x9d9ef1d097f866ab`, `0x50984769b3e59a89`.

## Campaign and hypotheses

If H0 passes, run both `research_baseline` and `candidate`, all three stations,
all eight replicates, begin year 1, for 100 years: 48 physical runs. The first
30 years of every run are a nested evaluation horizon, giving 96
arm/horizon/station/replicate cells. Generation is continuous stochastic,
`qc_filter: off`, and interpolation `none`.

H1, H2, and H3 use the exact metric definitions and target-cell construction
from SPEC-A5-EVALUATION and the package's frozen section 8 vector. Ratios are
candidate error divided by research-baseline error; exact zero divided by
zero is 1, positive divided by zero is infinity. Aggregate replicates within
station first, then stations. Missing/nonfinite required cells fail the
hypothesis.

* H1 annual/interannual variability: three-station median ratio at most 0.90
  and no station above 1.25, separately at 30 and 100 years.
* H2 monthly/daily fidelity: monthly-contract and interannual-mean/precipitation
  structure subfamilies have median at most 1.10 and no station above 1.25;
  daily-range and dew-point station-contract subfamilies have median at most
  1.25 and no station above 1.50; the cold-station winter subfamily is at most
  1.25.
* H3 dependence/low frequency: the annual dependence and low-frequency
  three-station median is at most 2.0 and no station above 3.0. Each of the
  three normalized storm-descriptor subfamilies has median at most 0.50 and no
  station above 0.75.
* H4 engineering: all identity, strict-parser, zero-bypass, nested-prefix,
  RNG-partition, process-counter, schema, hash, and repository gates pass.

The final decision is `CONTINUE-A5E1` only when H0--H4 pass. Any valid H0--H3
failure yields `CLOSE-MECHANISM`; H1--H3 are `NOT-EVALUATED` after H0 failure.
An execution or evidence-contract defect yields the applicable package hold;
it does not authorize model expansion. Daymet is an evaluation target, not
confirmation evidence.

## Evidence and provenance obligations

The coefficient and campaign schemas define the retained machine records. The
campaign record pins the execution-base commit, uncommitted implementation
tree, executable, Cargo.lock, fitter, analyzer, verifier, specifications,
schemas, coefficient bundle, source observations, station documents, every
run product, conformance products, analysis, and post-output descriptor audit.
The separate report manifest binds the campaign record, report, and review so
the records do not create a circular content-hash dependency.
Every run declares arm, station, replicate, master seed, faithful segment and
skip, horizon, annual-state hash (candidate only), and process counters. The
verifier recomputes all hashes and exact matrix closure.

Raw `.cli`, quality JSON, and diagnostics remain package-local under
`target/a5e0/`; they are reproducible evidence and are not committed. Compact
manifests, coefficient/feasibility evidence, analysis tables, report, review,
and gate results live in the work package. Execution never commits or pushes
without a separate operator instruction.
