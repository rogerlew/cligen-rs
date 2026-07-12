# Continuous and Observed Mode Branch Matrix

Status: static traceability artifact for `SPEC-FAITHFUL-GENERATION`.

## Authority and notation

The controlling source is `day_gen`, `clgen`, `windg`, `ranset`, and
`timepk` (`reference/cligen532/cligen.f:1094-1515,2020-2119,2188-2236,
2971-3191,4002-4340`). The port owners are `modes::day_gen`,
`daily::clgen`, `daily::windg`, `rng::ranset`, and `storm::{wet_day_duration,
storm_block,timepk}`.

In the tables below:

- `P`, `X`, and `N` mean the observed precipitation, Tmax, and Tmin fields;
- `M` means that the field equals the integer sentinel `9999`;
- `O` means that a non-sentinel observed value is retained;
- `G` means that the generator overwrites the observed assignment;
- `l` is `clgen`'s persistent daily wet/dry selector; and
- `ell` is `ranset`'s separate persistent refill-time wet/dry selector.

The sentinel classifications happen after a successful observed read and
before calendar conversion or `clgen` (`cligen.f:3067-3094`; Rust
`modes::day_gen`). They affect daily consumers, not whether the month's
random matrix is filled.

## Run and year control

| Control | Continuous (`iopt=5`) | Observed (`iopt=6`) |
|---|---|---|
| beginning year | required/resolved simulation year; it is a calendar label and drives leap-year tests | explicit beginning year when supplied; otherwise columns 11-15 of the first `.prn` record (`ioyr`) |
| year count | requested positive count | requested count, or source default 100; it is a cap, not a promise that enough records exist |
| record alignment | not applicable | positional: one record per internal day; record date columns are not validated after the first-year lookahead |
| days per year | Gregorian 365/366 test on current `iyear` | same Gregorian test; EOF may stop before that many rows |
| normal year boundary | clear yearly output grids, preserve generator state, increment year if under count | same only when no stop is returned; sentinel latch can stop at year end and EOF can stop earlier |

The first-record year lookahead is followed by a backspace/reader reset, so
the same first record remains the first daily record (`cligen.f:3557-3574`;
Rust `observed::PrnReader::initial_year`, `storm::sing_stm`, and
`modes::run_to_cli`).

## Work performed for every successfully read/generated day

The following work is common to continuous and observed mode after the
observed-read branch, if any:

1. Resolve the internal Julian day to month/day; record date columns do not
   participate.
2. On a month change, refill and condition all nine monthly matrix columns.
   This occurs even when observed values make some columns unused that day.
3. Run the selected precipitation and temperature branches.
4. Always generate dew point, radiation, and wind.
5. For positive precipitation, generate duration and then call the event
   chain a second time for time-to-peak and peak intensity.
6. Convert units, emit one row, and advance the internal Julian day.

Monthly refill is column-major. It advances `k1`, `k2`, `k3`, `k4`, `k6`,
`k8`, and `k9` for every calendar day in the month, subject to QC retries.
It advances `k5` only where the refill-time `ell` chain marks a wet day.
Continuous mode advances `k10` where the column-5 value is positive;
observed mode zero-fills column 9. The first refill of either mode still
draws the nine `last_r` initializers, including one draw from `k10`
(`cligen.f:4098-4117`; Rust `rng::initialize_ranset_streams`). Failed QC
attempts consume more stream draws without rewinding seeds.

## Continuous stochastic mode (`iopt = 5`)

`generation_setup` sets `nsim = msim = 1`; continuous `day_gen` does not
change them. Every day therefore follows this matrix.

| Branch | Daily matrix consumer | Persistent daily state | Direct output effect |
|---|---|---|---|
| precipitation occurrence | column 1 / `k1` | generated dry sets `l=2`; generated wet sets `l=1` | selects `xr=0` or a generated amount |
| precipitation amount, wet only | column 5 / `k5`; a zero predecessor triggers an extra direct `k5` draw | wet amount advances rolling `v7`; dry does not | generated precipitation, minimum `0.01 in` before conversion |
| Tmax/Tmin/dew point | columns 2, 3, and 8 / `k2`, `k3`, `k9` | advances `v1`, `v3`, and `v11` | generated `tmxg`, `tmng`, and `tdp` |
| radiation | column 4 / `k4` | advances `v5` | generated `radg` |
| wind direction | column 6 / `k6` | no rolling pair | generated `th` and calm/non-calm selection |
| wind speed, non-calm only | column 7 / `k8` | advances `v9`; calm leaves it unchanged | generated `wv`; calm writes zero speed/direction |
| duration, positive rain only | first `alphb` call; `dstg` draws from `k7` | advances `k7` and persistent `dstg` batch/cursor state | `dur` |
| peak chain, positive rain only | second `alphb`/`k7`, then column 9 / `k10` | advances `k7`; `k10` was advanced during refill rather than here | `tpr`, `xmav` |

At year boundaries only the yearly output grids are cleared. Seeds, rolling
pairs, `l`, `ell`, matrix QC accumulators, `dstg`, and month cursor state
persist. December-to-January causes a normal month-change refill.

## Observed hybrid mode (`iopt = 6`)

Before each read, `day_gen` sets `nsim = msim = 0`. A successful read first
assigns all three raw values, including sentinels, then sets the flags shown
below (`cligen.f:3067-3083`; Rust `modes::day_gen:268-291`). Missing either
temperature regenerates the pair.

| Missing fields (`9999`) | `nsim` | `msim` | Precipitation result | Tmax/Tmin result | Latch `q_gen_started`? |
|---|---:|---:|---|---|---|
| none | 0 | 0 | P = O | X = O, N = O | no change |
| P only | 1 | 0 | P = G | X = O, N = O | yes, through P |
| X only | 0 | 1 | P = O | X = G, N = G | yes, through X |
| N only | 0 | 1 | P = O | X = G, N = G | **no change** |
| P + X | 1 | 1 | P = G | X = G, N = G | yes |
| P + N | 1 | 1 | P = G | X = G, N = G | yes, through P |
| X + N | 0 | 1 | P = O | X = G, N = G | yes, through X |
| P + X + N | 1 | 1 | P = G | X = G, N = G | yes |

The latch is set by exactly `P == 9999 || X == 9999`; Tmin is absent from
that expression. It is never cleared by a later successful record.

### Daily branch, RNG, and state effects

| Classification | Daily consumers beyond the already-completed monthly refill | Persistent state consequence |
|---|---|---|
| P = O | no daily use of columns 1 or 5 | does not change `l` or `v7`; a later generated P is conditioned on the last generated day, not this observation |
| P = G | column 1; column 5 only if the generated occurrence is wet; possible direct `k5` recovery draw | generated dry/wet updates `l`; generated wet advances `v7` |
| X,N = O | column 8 only | advances dew-point rolling value `v11`; leaves Tmax/Tmin rolling values `v1` and `v3` unchanged |
| X,N = G | columns 2, 3, and 8 | advances `v1`, `v3`, and `v11`; a present temperature counterpart is discarded |
| every successful day | column 4 for radiation and column 6 for wind direction; column 7 only if wind is non-calm | advances `v5`; non-calm advances `v9`, calm does not |

The positive-rain storm branch is independent of whether P was observed or
generated:

| Final P after substitution | Event work | RNG/state effect |
|---|---|---|
| `P <= 0` | normalize to zero; `dur=tpr=xmav=0` | no `k7`/`dstg` or daily `k10` consumption |
| `P > 0` | two independent `alphb` calls, then `timepk` | advances `k7` through two `dstg` values; draws one fresh `k10` uniform because observed-mode column 9 is always zero |

Thus a present positive observed precipitation value still advances both
event RNG systems. A missing-P day advances them only when the generated
occurrence is wet.

## EOF, sentinel latch, and year/cap termination

| Condition | Rows/RNG on the attempted day | Exit and outer-year effect |
|---|---|---|
| EOF before the next observed record | `msim`/`nsim` were reset to zero before the read; no calendar conversion, refill, daily RNG consumption, climate-state update, or row follows | immediate `Stop`; `wxr_gen` does not advance the year and omits the normal run-end blank line |
| successful final calendar day, latch false | normal complete day | `YearComplete`; outer loop advances `iyear` and continues until the requested/default year cap |
| successful final calendar day, latch true | normal complete day | `Stop` at year end; no next year, even if the cap permits one |
| requested/default year cap reached with latch false | all planned rows emitted | normal termination; no extra read is attempted after the cap |

A sentinel does **not** stop its day or the remainder of its current year.
It only latches the year-end stop. EOF is the only observed-input condition
that stops before processing the attempted day. `DayGenState::q_gen_started`
is caller-owned SAVE state and persists across calls, although normal
`run_to_cli` orchestration stops after the first year-end at which it is true.

## First downstream trajectory divergences

This condensed comparison identifies the earliest state seam affected by a
future substitution-policy change.

| Proposed change | First faithful divergence |
|---|---|
| make observed P update wet/dry history | `l` on that day; next generated-P occurrence probability |
| generate only the missing temperature | `v1` or `v3` consumption on that day; all later generated values on that rolling chain |
| skip monthly columns for observed values | assigned stream during that month's refill, including QC retry trajectory |
| use batch time-to-peak in observed mode | `k10` at the first positive-rain observed day; batch column 9 is faithfully zero |
| share one alpha draw between duration and peak | `k7`/`dstg` at the second event call on the first wet day |
| treat Tmin-only missing like Tmax for stopping | `q_gen_started` on that record; run termination at current year end |
| validate or key by record date | record selection before `jlt`; current behavior is strictly positional |
