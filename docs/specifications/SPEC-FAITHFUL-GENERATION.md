# SPEC-FAITHFUL-GENERATION — Continuous and Observed Climate Generation

Status: active (rev 1; work package
`20260712-faithful-generation-spec`)
Surface: the complete climate-generation behavior of the
`faithful_5_32_3` profile with `qc_filter: faithful` for continuous
stochastic and hybrid observed time series.

## Purpose and authority

This document is the behavioral baseline for future CLIGEN extensions. It
specifies what state is initialized, what parameters and random values are
consumed, what is computed each day, and which behavior changes in observed
mode. A future generation profile states its differences from this baseline;
it does not amend the baseline.

The pinned Fortran source in `reference/cligen532/` is authoritative under
ADR-0001. Source citations below are to `cligen.f`. Rust names and test
references are traceability aids, not competing authorities. When this
document, Rust, and Fortran disagree, the Fortran decides faithful behavior
and the other two must be corrected.

Companion specifications own adjacent surfaces:

- `SPEC-PAR` — legacy station-file grammar and typed station values;
- `SPEC-GENERATOR-CORE` — state ownership and faithful function shapes;
- `SPEC-OBSERVED-INPUT` — legacy `.prn` grammar and cursor semantics;
- `SPEC-RUNSPEC` — user-facing modes, year plans, and input validation;
- `SPEC-GENERATION-PROFILES` — declared non-faithful behavior knobs;
- `SPEC-QUALITY-REPORT` — scientific assessment of extension profiles.

## Scope

Included modes are:

- continuous stochastic generation (`iopt = 5`); and
- hybrid observed generation (`iopt = 6`).

The daily duration, time-to-peak, and peak-intensity calculations are included
because both modes produce them for every daily output row. Standalone
single-storm (`iopt = 4`) and design-storm (`iopt = 7`) orchestration, intake,
date rules, overrides, and mode-specific output are deferred to a later
companion. They are deprecated in WEPPcloud.

This document stops at the typed `DailyRow` semantic boundary. `.cli` text
formatting is not model behavior. Native-f64 execution, parquet formats,
interannual station parameters, and all other augmentations are out of scope.

## Faithful configuration

The behavior in this specification is selected only by:

```yaml
generation_profile: faithful_5_32_3
qc_filter: faithful
```

`qc_filter: off` deliberately changes accepted monthly random batches and is
therefore an extension configuration, even when the RNG backend remains the
faithful backend. `fast_batch_v0` is outside this specification.

Except for source-declared f64 islands in `dstg` and the QC/ACM library, model
arithmetic is REAL*4/f32. Expression order, conversions, constants, and pinned
transcendentals are part of the result. The precision contract is normative in
the Rust scientific coding standard.

## Model overview

CLIGEN is a stateful daily generator driven by fixed monthly station
climatologies. The faithful model has no station-level interannual latent
state: the same monthly parameter arrays apply every year. Variation across
years emerges from daily stochastic processes, their persistence, the
calendar, and the trajectory-load-bearing random-batch conditioner.

One run follows this order (`cligen.f:702-902,3589-3811`):

1. Construct the ten fixed RNG streams and apply the requested burn.
2. Parse the station file, distribute its parameters, and compute load-time
   derived state and optional interpolation coefficients.
3. Convert the station maximum-30-minute precipitation parameters for the
   event-intensity model and initialize constants, persistent state, and
   rolling random pairs.
4. For each simulation year, choose 365 or 366 days and clear the yearly
   output grids.
5. For each day, resolve the calendar date; in observed mode consume one
   record and choose observed or generated precipitation/temperature paths.
6. At the first day of each month, generate and condition a complete monthly
   random matrix.
7. Generate or retain precipitation and temperatures, then generate dew
   point, radiation, wind, duration, time-to-peak, and peak-intensity ratio.
8. Convert the output-boundary units and emit one typed daily row.

The state is never reset between days, months, or years unless a step below
explicitly says so. In particular, RNG seeds, rolling normal-pair uniforms,
wet/dry state, QC accumulators, `dstg` state, and the observed stop flag persist
across year-loop calls.

## Station parameters and load-time transformations

`sta_parms` loads records 2-83 and prepares generator state
(`cligen.f:2656-2970`; Rust `par::sta_parms`). The following table identifies
the climate fields and explicitly marks a retained field with no daily
consumer. Monthly arrays contain 12 calendar-month values; `timpkd(1:12)`
instead contains 12 probability bins in one station-wide CDF.

| Parameter | Source storage | Meaning and source units | Live use |
|---|---|---|---|
| wet-day precipitation mean | `rst(:,1)` | daily wet-day depth, in | wet-day amount location |
| wet-day precipitation SD | `rst(:,2)` | daily wet-day depth SD, in | wet-day amount scale |
| wet-day precipitation skew | `rst(:,3)` | dimensionless | wet-day amount shape |
| wet-after-wet probability | `prw(:,1)` | probability | precipitation occurrence; expected wet days in `r5monb` |
| wet-after-dry probability | `prw(:,2)` | probability | precipitation occurrence; expected wet days in `r5monb` |
| Tmax/Tmin mean | `obmx`, `obmn` | daily temperature, °F | generated temperatures and dew-point anchoring |
| Tmax/Tmin SD | `stdtx`, `stdtm` | daily temperature SD, °F | generated temperatures and dew-point anchoring |
| radiation mean/SD | `obsl`, `stdsl` | Langley/day | generated radiation |
| max 30-minute precipitation | `wi` | file: in/h; load state: in | event duration/intensity preparation |
| mean dew point | `rh` | °F | generated dew-point anchoring |
| time-to-peak CDF | `timpkd(1:12)` | cumulative probability | event time-to-peak |
| directional wind parameters | `wvl(16,4,:)` | percent, mean m/s, SD m/s, skew | direction and speed by sector |
| calm percentage | `calm` | percent | retained input with no generation-time consumer; calm behavior is the residual of the directional cumulative distribution |
| station latitude | `ylt` | degrees north | source-scaled latitude sine/cosine in the astronomical radiation bound |
| station storm type | `itype` | integer 1-4 | selects `tymax = [180.34,154.94,307.34,330.2]` mm/h for `xmav` |

Load-time transformations occur in source order:

1. `wi[m] = 0.5 * wi[m]`, converting the input maximum 30-minute
   intensity to a 30-minute depth (`cligen.f:2804-2812`).
2. Interpolation setup runs, when selected, over parameter indices 1-14
   (`cligen.f:2829-2868`).
3. Elevation is converted from feet to integer metres; temperature and
   radiation coefficients of variation are derived as retained diagnostic
   display state (`cligen.f:2884-2904,2955-2957`). They drive neither the
   daily equations nor the `.cli` header.
4. Directional percentages are cumulatively summed by month and scaled by
   0.01 to form `dir[m,1:17]` (`cligen.f:2910-2925`).

Before generation, `r5monb` replaces each `wi[m]` with a dimensionless
maximum-30-minute/total-rain ratio (`cligen.f:3898-4001`). It first takes the
three-month circular mean of `wi`, estimates expected wet days from `prw`,
uses `rst(:,1)` as mean rain per wet day (with source guards), and applies:

```text
smm = 0.0006944                                   when P(W|D) == 0
      days_in_month * P(W|D)
          / (1 - P(W|W) + P(W|D))                otherwise
r25 = 0.001                                       when wet_day_mean == 0
      wet_day_mean                                otherwise
f   = -1 / log(1 / (smm + 0.5))
wi  = (f * sm, or sm when f is outside (0,1]) / r25
```

`days_in_month` comes from the fixed non-leap `nc` calendar, so February is
28 days in this once-per-run transformation even when generated years are
leap years.

The `prw(:,1:2)`, `wi`, and wind values used at generation time remain fixed
calendar-month values; `timpkd` remains one fixed station-wide CDF. Although
interpolation setup computes state for parameter indices 4, 5, 12, and 14,
CLIGEN 5.32.3 has no generation-time evaluator call for those indices. That
setup state is behaviorally unused.

## Monthly-to-daily interpolation

Interpolation applies only to wet-day precipitation mean/SD/skew (indices
1-3), Tmax/Tmin mean and SD (6-9), radiation mean/SD (10-11), and mean dew
point (13). Each use is evaluated independently at its equation site
(`cligen.f:1240-1509`; Rust `daily::interp_val`).

| Runspec value | Source mode | Daily behavior |
|---|---|---|
| `none` | 0 | use the current calendar month's value unchanged |
| `linear` | 1 | blend the current and adjacent month around month midpoints using `lintrp` weights |
| `fourier` | 2 | evaluate a six-harmonic series prepared from the 12 monthly values |
| `monthly_mean_preserving` | 3 | evaluate the Yoder-Foster piecewise curve prepared from monthly means |

The Fourier evaluator uses the source phase convention
`dd = (Julian_day + 15.5) / 366` in leap and non-leap years. It is a
deterministic within-year interpolation of one fixed climatology, not an
interannual-variation mechanism (`cligen.f:7338-7423`).

Linear interpolation state is recomputed once per day before `clgen`.
Yoder-Foster uses noon (`day_of_month - 0.5`) and distinct leap-February
endpoints. Full arithmetic and sentinel details remain normative in
the source units `lintrp`, `fouri1/2`, and `ryf1/2`
(`cligen.f:7252-7657`) and are implemented in `monthlies.rs`.

## Random-number system

### Streams, fixed seeds, and burn

Ten separately stateful `randn` streams are initialized by block data
(`cligen.f:1054-1063`). Each is four integers:

| Stream | Initial state | Assigned process |
|---|---|---|
| `k1` | `[9, 98, 915, 92]` | precipitation occurrence |
| `k2` | `[135, 28, 203, 85]` | Tmax normal pairs |
| `k3` | `[43, 54, 619, 33]` | Tmin normal pairs |
| `k4` | `[645, 9, 948, 65]` | radiation normal pairs |
| `k5` | `[885, 41, 696, 62]` | wet-day amount normal pairs |
| `k6` | `[51, 78, 648, 0]` | wind direction |
| `k7` | `[227, 57, 929, 37]` | event alpha/gamma rejection sampler |
| `k8` | `[205, 90, 215, 31]` | wind-speed normal pairs |
| `k9` | `[320, 73, 631, 49]` | dew-point normal pairs |
| `k10` | `[22, 103, 82, 4]` | time-to-peak |

`rng.burn = N` discards exactly N returned uniforms from each of `k1` through
`k9`; `k10` is not burned (`cligen.f:723-737`). This is a burn count, not a
replacement seed.

`randn` updates its four-integer state by the source's multiply-by-three and
carry algorithm, assembles an f32 value, and retries until the result lies in
the open interval `(0,1)` (`cligen.f:1980-2019`; Rust `rng::randn`).

### Cold-start sequence

After station loading and `r5monb`, generation setup executes this exact
sequence (`cligen.f:865-902`; Rust `modes::generation_setup`):

1. Set snowmelt scratch `sml = 0`, `ab = 0.02083`, `ab1 = 1-ab`, and the
   source angle constants.
2. Compute latitude sine/cosine using `latitude / 57.296`.
3. Draw once from `k1`; initialize wet/dry selector `l = 2`, then set
   `l = 1` when the draw is greater than January `P(W|W)`. This apparently
   inverted initialization is faithful.
4. Draw once from `k7` into the retained `rn1` warm value. The live `alphb`
   and `dstg` path never reads `rn1`; the draw matters only because it advances
   `k7`.
5. Draw once from `k2`, `k3`, `k4`, `k5`, `k8`, and `k9` into the rolling
   values `v1`, `v3`, `v5`, `v7`, `v9`, and `v11`.
6. Set precipitation and temperature generation flags `nsim = msim = 1`.

At the first `ranset` call, its own first-call initialization draws a previous
value for each of its nine columns, including `k1`, `k6`, and `k10`, and
overwrites the rolling values used by daily pairs. The earlier setup draws
still matter because they advanced their seed streams. This initialization
runs only once. Thereafter `RansetState.last_r` advances inside refill/QC work,
while the daily `v1`-`v11` predecessors advance only when their daily consumers
run; later monthly refills do not overwrite the daily predecessors.

### Monthly random matrix

On the first day whose month differs from `mox`, `clgen` sets `mox` to the
calendar month, sets day cursor `dax = 1`, and calls `ranset`; later days
increment `dax` (`cligen.f:1206-1212`). `ranset` fills one column at a time for
every day in that month, rather than drawing all variables day by day.

| Column/view | Stream | Daily consumer | Conditional zero rule |
|---|---|---|---|
| 1 `vvx` | `k1` | precipitation occurrence | never |
| 2 `v2x` | `k2` | Tmax rolling pair | never |
| 3 `v4x` | `k3` | Tmin rolling pair | never |
| 4 `v6x` | `k4` | radiation rolling pair | never |
| 5 `v8x` | `k5` | wet-day amount rolling pair | zero when the refill-time wet/dry chain is dry |
| 6 `fxx` | `k6` | wind direction | never |
| 7 `v10x` | `k8` | wind-speed rolling pair | never |
| 8 `v12x` | `k9` | dew-point rolling pair | never |
| 9 `zx` | `k10` | continuous-mode time-to-peak | zero when column 5 is zero; always zero in observed mode |

The refill-time wet/dry selector in `ranset` is persistent state separate from
the daily occurrence selector in `clgen`. It uses column 1 with `prw` to decide
which column-5 entries receive `k5` draws. In continuous mode column 9 receives
a `k10` draw only where column 5 is positive. In observed mode column 9 is
zero-filled because observed `timepk` draws directly from `k10` when needed.

### Rolling normal pairs

`dstn1(previous, current)` is the Box-Muller expression:

```text
sqrt(-2 * log(previous)) * cos(6.283185 * current)
```

clamped to `[-10,10]` (`cligen.f:1789-1816`). After a consumer uses a pair,
`current` becomes the next day's `previous`. Separate rolling chains exist for
Tmax, Tmin, radiation, wet-day amount, wind speed, and dew point. Skipped
branches do not necessarily advance a rolling chain; therefore substitutions
can affect later generated values even when monthly batches are unchanged.

### Trajectory-load-bearing quality conditioning

`ranset` accumulates statistics by parameter and calendar month across the
run. Each proposed parameter column is subjected to a K-S uniform test.
Columns 2, 3, 4, 5, and 8 (Tmax, Tmin, radiation, precipitation amount, and
dew point) also receive mean and variance confidence tests over their normal
transforms; wind-speed column 7 remains uniform-test-only despite its later
normal transform (`cligen.f:4190-4335`). A failed attempt is removed from the
statistical accumulators and regenerated. Its RNG draws are not restored. The
previous rolling value and refill wet/dry state are restored where the source
restores them, so the retry begins from the same logical predecessor but later
seed states.

The K-S test uses 20 cumulative bins and automatically passes while the
cumulative positive count `chi_n < 100`; at 100 or more it rejects when
`max_difference/sqrt(chi_n) > 0.8276`. The mean and variance comparison
threshold arrays are initialized to `50.0`. Their denominator is cumulative
calendar-day count `g_dimi` for columns 2, 3, 4, and 8, but cumulative wet
amount count `g_dimp` for column 5 (`cligen.f:1068-1078,4210-4272,
4453-4704`).

The retry counter is shared across the nine columns within one monthly refill.
At 10,000 failures the source emits a warning and accepts the still-failing
attempt. Observed-mode column 9 bypasses the statistical tests. These rules
mean the conditioner changes future stochastic trajectories, not merely a
diagnostic score (`cligen.f:4002-4340`; Rust `rng::ranset`, `qc`, and `acm`).

`dstg`, used by event calculations, has a second trajectory-load-bearing
conditioner. It draws `k7` uniforms in batches of 30, applies the K-S test, and
uses pairs in a gamma rejection sampler. Its saved batch and cursor persist
across event, month, and year boundaries. After a failed K-S batch the source
subtracts bin counts for only the first 20 of the 30 rejected values, leaving
the last 10 in persistent QC state. Failed K-S or gamma attempts consume
additional `k7` draws.

For candidate pair `(rn1,rn)`, with `xn1 = 6.28`, the source computes:

```text
xx = f64(f32(rn1 * ai))
fu = xx^f64(xn1) * exp(f64(xn1) * (1 - xx))
accept and return rn1 when fu >= f64(rn)
```

The K-S retry counter `itryct` advances once per proposed 30-value batch. The
gamma counter advances once for every candidate pair and a second time when
that pair is rejected, so its equality-at-10,000 escape occurs after 5,000
pairs in an all-reject sequence. Both escapes accept with source warnings
(`cligen.f:1651-1788`).

## Calendar and daily control flow

Continuous mode treats `simulation.begin_year` as a year index and produces
exactly `simulation.years` year loops. Observed mode uses the requested year
or the first record's year and treats `simulation.years` (default 100) as a
cap. Both use the Gregorian test on the current `iyear`: divisible by 400, or
divisible by 4 and not by 100, produces 366 days (`cligen.f:3758-3781`).

At the start of each year the daily output grids are cleared. `day_gen` begins
at Julian day 1 and processes through `ntd` unless observed EOF stops it first.
For each successful day the source order is (`cligen.f:3065-3183`):

1. Read and classify the observed record when `iopt = 6`.
2. Convert Julian day to calendar month/day with `jlt`.
3. Compute linear interpolation weights when selected.
4. Run `clgen`: solar geometry, monthly refill, precipitation branch,
   temperature/dew-point branch, dew-point clamps, radiation.
5. Run `windg` and convert direction from radians to degrees.
6. Store precipitation and Fahrenheit temperatures in the internal yearly
   grids, then convert Tmax, Tmin, and dew point in place to Celsius.
7. Derive duration and the daily storm descriptors.
8. Emit the typed daily row and advance the Julian-day cursor.

Monthly refill occurs even in observed mode and even when the day's supplied
precipitation and temperatures need no replacement. Unused batch columns and
their QC retries therefore still advance their assigned RNG streams.

## Precipitation occurrence and amount

### Continuous and generated-observation days

The daily occurrence state `l` is `1` after a generated wet day and `2` after
a generated dry day. With calendar month `m` and occurrence uniform `u` from
column 1 (`cligen.f:1214-1277`):

```text
p = prw[m,l]
dry when p <= 0 or u > p
wet otherwise
```

A dry result writes precipitation `0 in` and `l = 2`. A wet result writes
`l = 1` and transforms a standard-normal deviate to a skewed amount. Before
the interpolation dispatch, the source clamps only the current calendar
month's stored `rst(m,3)` to `[-4.5,4.5]`. Under linear interpolation, the
adjacent month's value is not clamped by this step; Fourier and Yoder-Foster
use coefficients prepared from the original values at station-load time.
Let `s` be the resulting dispatched skew after replacing an effective zero by
`0.01`; let `z` be the rolling `dstn1` value and `r6 = s/6`:

```text
x   = (z - r6) * r6 + 1
xlv = (x*x*x - 1) * 2 / s
rain_in = max(0.01, mean + xlv * SD)
```

If the rolling predecessor `v7` is exactly zero, the source draws a fresh
`k5` value before this transform. This recovery path advances `k5` outside
`ranset` and is part of the trajectory. The guard checks only the predecessor:
if the current batch value `v8x(dax)` is zero, the source still evaluates
`dstn1(v7,0)` and then assigns `v7 = 0`. The direct recovery draw occurs only
on the next generated wet amount.

The occurrence chain and amount generator are coupled but not identical:
daily occurrence uses the daily `l` state, whereas availability of the
column-5 amount uniform was decided earlier by `ranset`'s separate synthetic
wet/dry chain. The zero-predecessor recovery handles a desynchronization.

### Observed precipitation

When the `.prn` precipitation field is not `9999`, `nsim = 0`; the raw integer
is multiplied by `0.01` and retained as inches. The entire occurrence/amount
block is skipped. Consequently, observed wetness does not update daily state
`l`. A later missing-precipitation day is conditioned on the last generated
wet/dry state, not the preceding observed day (`cligen.f:3067-3083,1214-1277`).

When the field is `9999`, the raw assignment occurs but `nsim = 1` causes the
generated precipitation block to overwrite it.

## Tmax, Tmin, and dew point

All temperature equations operate in °F until the output-boundary conversion.
Define interpolated monthly values:

```text
mu_x, sigma_x = Tmax mean and daily SD
mu_n, sigma_n = Tmin mean and daily SD
mu_d          = mean dew point
z_x, z_n, z_d = rolling standard-normal deviates
sigma_bar     = (sigma_x + sigma_n) / 2
```

When temperatures are generated (`cligen.f:1346-1446`):

```text
if sigma_x >= sigma_n:
    Tmin = mu_n + sigma_n * z_n
    Tmax = Tmin + (mu_x - mu_n) + sqrt(sigma_x^2 - sigma_n^2) * z_x
    Tdew = Tmin + (mu_d - mu_n)
                 + sqrt(abs(sigma_bar^2 - sigma_n^2)) * z_d
else:
    Tmax = mu_x + sigma_x * z_x
    Tmin = Tmax - (mu_x - mu_n) - sqrt(sigma_n^2 - sigma_x^2) * z_n
    Tdew = Tmax - (mu_x - mu_d)
                 + sqrt(abs(sigma_bar^2 - sigma_x^2)) * z_d
```

If generated Tmin exceeds generated Tmax, Tmin becomes
`Tmax - 0.2*abs(Tmax)`.

When both observed temperatures are present (`msim = 0`), Tmax and Tmin pass
through unchanged and only `z_d` is consumed. Dew point uses the same branch
selection and final formula above, anchored to the observed Tmin in the first
branch or observed Tmax in the second (`cligen.f:1280-1345`).

After either path:

```text
if Tdew > 0.99 * (Tmax + Tmin) / 2:
    Tdew = 0.99 * (Tmax + Tmin) / 2
if Tdew < -10 F:
    Tdew = 1.1 * Tmin
```

The second condition also raises the source's screen diagnostic; the Rust port
surfaces a mode-independent diagnostic event instead of printing. The
assignment affects output in both modes and is faithful behavior.

In observed mode, a `9999` in either Tmax or Tmin sets `msim = 1`, so both
temperatures are generated. A present counterpart is not retained. This is a
pair-level substitution rule, not independent per-field imputation.

## Solar radiation

Before monthly refill, `clgen` computes the day's astronomical upper bound
from Julian day and the source-scaled station latitude
(`yls = sin(latitude_deg/57.296)`, `ylc = cos(latitude_deg/57.296)`;
`cligen.f:882-887,1185-1202`):

```text
sd  = 0.4102 * sin((ida - 80.25) / 58.13)
ch  = -yls * tan(sd) / ylc
h   = 0 when ch >= 1; 3.1416 when ch <= -1; acos(ch) otherwise
rmx = 711 * (h*yls*sin(sd) + ylc*cos(sd)*sin(h))
```

Radiation is generated every day from its rolling normal pair:

```text
ra = interpolated_mean + interpolated_SD * z_radiation
ra = min(ra, rmx)
ra = max(ra, 0.05 * rmx)
```

It is not conditioned on precipitation occurrence or observed wetness in the
faithful model (`cligen.f:1469-1509`). Units are Langley/day.

## Wind direction and speed

Wind is generated every day from the current month's fixed direction and
sector-speed tables (`cligen.f:2020-2122`). Column-6 uniform `u` selects the
first of 16 cumulative directional sectors whose `dir` value exceeds `u`.
If no sector exceeds it, speed and direction are both zero (calm).

Within a selected sector `j`, the uniform's fractional position `g` linearly
places direction within the 1/16-circle sector:

```text
theta_rad = 6.283185 * (g + (j-1) - 0.5) / 16
```

Negative results wrap by adding `6.283185`. `day_gen` later multiplies by
`57.296` to produce degrees.

Wind speed uses the sector's mean, SD, and skew with the same cubic
Pearson-III-style transform used for precipitation amount. A stored zero skew
is changed in place to `0.01`. After transformation, a negative speed is
replaced by `0.1 m/s`. Calm days do not consume or advance the wind-speed
rolling pair.

## Duration, time-to-peak, and peak-intensity ratio

These descriptors are generated after precipitation, temperatures, radiation,
wind, and the Fahrenheit-to-Celsius conversion (`cligen.f:3114-3176`). A dry
day normalizes non-positive precipitation to zero and returns:

```text
xr = 0 mm; duration = 0 h; time_to_peak = 0; peak_ratio = 0
```

Every positive-rain day calls `alphb` twice. The calls consume distinct `dstg`
values from `k7`.

For each `alphb` call, let `r` be precipitation in inches, `sml = 0`, and `wi`
the transformed monthly ratio. The source sets:

```text
ai  = (1 - 0.02083) / (wi - 0.02083)
ajp = 1                                      when r < 1 in
      1 - exp(-(125/25.4)/r)                 otherwise
g   = dstg(ai, k7)
r1  = (r*(0.02083 + g*(ajp-0.02083))) / r
```

The first call supplies duration:

```text
duration_h = min(24, 3.99 / (-2 * log(1-r1)))
```

The second supplies peak quantities. Precipitation is converted to
`xr = r*25.4 mm`. Time-to-peak samples the station's 12-bin cumulative CDF and
linearly interpolates inside the selected `1/12` interval using the source
literal `0.08333`. Continuous mode uses monthly batch column 9. Observed mode
draws a fresh `k10` uniform for each wet day. Values above `0.99` are clamped
to `0.99`.

Continuous mode does not reconcile the refill-time and daily wet/dry chains.
If the refill mask made column 9 zero but the daily chain is wet, `timepk`
consumes that zero without a recovery draw; with a nonzero first CDF bin the
formula yields `tpr = 0`. Conversely, a `k10` value drawn into column 9 is
unused when the daily chain is dry. The faithful legacy parameter path does
not validate CDF monotonicity/range, guard a zero bin width, or apply a lower
clamp to `tpr`. `timepk` uses the raw entries: a zero-width landed interval
divides by zero, a terminal CDF below the draw extrapolates from bin 12, and
only results greater than `0.99` are clamped. A modern station schema must
define and fail closed on its CDF invariants rather than attributing stricter
validation to the Fortran algorithm.

The source specifies `r5p` as peak rainfall rate in mm/h and clamps it against
the type-specific `tymax` rate limit, also in mm/h. Its implemented expression
uses `xr` in millimetres exactly as shown; the faithful path must not insert a
unit correction or duration factor. The normalized output ratio is:

```text
r5p = min(-2*xr*log(1-r1), tymax[station_type])
xmav = r5p / (xr/duration_h)
```

If mean daily temperature in Celsius is `<= 0`, `xmav` becomes `1.01`.
Otherwise it is still floored at `1.01`. Thus observed positive precipitation
receives stochastic duration, time-to-peak, and peak ratio even when no
precipitation value was generated.

## Observed mode as a hybrid generator

Observed mode is sequential substitution, not date-keyed replay and not a
complete observed-climate pass-through. Records are consumed one per internal
calendar day. Columns 1-15 are ignored during daily reads; only columns 11-15
of the first record are separately read once to obtain the default initial
year. No later record date is checked against the internal date.

For every record, `msim = nsim = 0` is set before sentinel classification.
All three values are assigned to generator state even when they equal `9999`.
The generation flags then determine whether those assignments survive.

| `.prn` condition | Precipitation | Tmax/Tmin | Other daily variables | Persistent stop flag |
|---|---|---|---|---|
| no sentinel | observed | both observed | dew point, radiation, wind, and storm descriptors generated | unchanged |
| precipitation `9999` | generated | both observed unless a temperature is also missing | generated | set |
| Tmax `9999` | observed unless precipitation is also missing | both generated | generated | set |
| Tmin `9999` only | observed | both generated | generated | **not set** |
| both temperatures `9999` | observed unless precipitation is also missing | both generated | generated | set through Tmax |

The stop flag (`q_gen_started`) is SAVE state and persists across yearly
`day_gen` calls. At natural year end, a true flag returns the same stop signal
as EOF. The source sets it only for missing precipitation or missing Tmax, not
for a Tmin-only sentinel (`cligen.f:3075-3083,3189`).

EOF is armed before each observed read. If no next record exists, generation
stops before calendar conversion, random consumption, or output for that day.
Thus EOF may end a run mid-year. A successful read clears the conceptual stop
condition. Malformed fields fail closed under `SPEC-OBSERVED-INPUT`.

Observed substitutions have these stochastic-state consequences:

- monthly `ranset` refill and QC still run;
- observed precipitation does not update the daily wet/dry state;
- observed temperatures consume only the dew-point rolling pair;
- one missing temperature consumes and advances Tmax, Tmin, and dew-point
  rolling pairs because both temperatures are regenerated;
- observed wet days use fresh `k10` draws rather than batch column 9; and
- every positive observed precipitation consumes two `dstg` event draws from
  `k7`.

These consequences are part of the faithful result and are mandatory inputs
to any future one-pass substitution design.

## Typed daily output boundary

After generation, one `DailyRow` contains:

| Field | Meaning | Unit |
|---|---|---|
| `jd`, `mo`, `iyear` | calendar day, month, and current simulation/calendar year | integer |
| `xr` | daily precipitation depth | mm |
| `dur` | event duration | h |
| `tpr` | time to peak as fraction of duration | fraction |
| `xmav` | maximum/mean event-intensity ratio | dimensionless |
| `tmxg`, `tmng` | daily maximum/minimum temperature | °C |
| `radg` | daily solar radiation | Langley/day |
| `wv` | wind speed | m/s |
| `th` | wind direction | degrees |
| `tdp` | dew point | °C |

Precipitation is converted from inches to millimetres inside the storm block.
Tmax, Tmin, and dew point are converted with
`(F - 32) * (5/9)` immediately before descriptor generation. Direction uses
the source multiplier `57.296`. Text width, rounding, headers, and run-end
markers belong to the output-format surface.

## Persistent state and faithful quirks

The following are especially likely to be mistaken for implementation noise.
They are specified behavior:

| Behavior | Consequence |
|---|---|
| fixed monthly station arrays repeat every year | no explicit interannual station state exists |
| QC accumulators persist by parameter/month | acceptance in a later year depends on earlier batches |
| failed QC retries consume RNG draws | removing conditioning bifurcates the trajectory |
| failed `dstg` K-S rollback removes only 20 of 30 bin entries | rejected batches leave source-specified history in intensity QC state |
| `ranset` and daily occurrence use separate wet/dry selectors | amount availability and actual occurrence can desynchronize |
| continuous column-9 mask has no daily recovery | a wet day can consume `zx=0`, while a pre-drawn `k10` value can be unused on a dry day |
| setup wet/dry initialization has inverted-looking comparison | first generated occurrence state follows source, not intuitive semantics |
| precipitation skew and zero wind skew mutate station state | none/linear paths can observe the adjusted current precipitation month, but the linear adjacent value may be unclamped and precomputed Fourier/Yoder-Foster coefficients never observe the runtime mutation; wind uses its adjusted selected sector later |
| observed precipitation does not update daily wet/dry state | later missing precipitation ignores observed wet/dry history |
| one missing temperature regenerates both | substitution is pair-level |
| Tmin-only missing value does not set the year-end stop flag | run-length behavior differs from Tmax-only missing value |
| observed record dates are not validated after initial-year read | sequence position, not date text, aligns records to days |
| Fourier interpolation always divides phase by 366 | non-leap daily interpolation retains the source phase convention |
| two independent `alphb` calls occur on a wet day | duration and peak calculations do not share one alpha draw |
| radiation is independent of wet/dry state | wet/dry radiation contrast is structurally absent |
| generated temperature/dew-point and wind distributions do not condition on wet/dry state | cross-variable coupling occurs only inside the temperature construction and the temperature-dependent `xmav` override |

## Failure and extension boundaries

Malformed station, observed, or runspec input fails closed according to its
own specification. Rust also fails closed for source states that production
control flow cannot create safely, such as out-of-range months or a missing
observed stream. It does not infer parameters or defaults from incomplete
scientific input.

SPEC-STATION-DOCUMENT revision 1 may represent this faithful fixed-monthly
model losslessly; legacy and modern syntax converge on the same typed state
before generation. The document cannot alter this profile. A schema/model
variant containing interannual parameters must be rejected by faithful mode.
Consuming such parameters requires a versioned generation profile, output
provenance, and ADR-0002 quality adjudication. File representation and model
behavior are independently versioned decisions.

## Acceptance and traceability

Faithful acceptance remains executable identity, not this prose alone:

- 10 in-scope provenance-pinned Fortran golden `.cli` files (four continuous
  and six observed hard-EOF/sentinel cases), plus two standalone-storm
  goldens that exercise shared units but belong to the deferred companion;
- interior RNG/deviate/`ranset`, station/interpolation, daily, wind, event, and
  observed replay taps;
- 189,205 recorded in-scope full-stream days, plus two standalone-storm days
  that exercise shared units; and
- Rust end-to-end byte parity in `tests/cli_parity.rs` and
  `tests/runspec_cli.rs`.

The owning work package artifacts provide the behavior-to-source-to-Rust-to-
evidence crosswalk, parameter/output map, and observed branch matrix. A change
to a generated field, state transition, stream assignment, or draw order must
update those artifacts or demonstrate that their mapping remains unchanged.
