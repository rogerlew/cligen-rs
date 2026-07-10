# `clgen` Draw-Order and Month-Boundary Characterization

Evidence mode: Static (full source read of `clgen` 1094-1515, `windg`
2020-2122, `alphb` 3817-3897, `r5monb` 3898-4001; cross-checked against
the item-3 tap-replay record) + Ran where marked.

## The batch protocol (the design-setting fact)

`clgen` consumes **no fresh `randn` draws on the normal path**. All
daily uniforms come from the `ranary(31,9)` batch columns, indexed by
the day-of-month cursor `dax` and read through the item-3 EQUIVALENCE
accessors (`vvx`, `v2x`, `v4x`, `v6x`, `v8x`, `fxx`, `v10x`, `v12x`,
`zx`):

| Column | Consumer | Variable |
|---|---|---|
| 1 `vvx` | clgen | precip occurrence uniform `vv` |
| 2 `v2x` | clgen | Tmax pair second element |
| 3 `v4x` | clgen | Tmin pair second element |
| 4 `v6x` | clgen | radiation pair second element |
| 5 `v8x` | clgen | precip-amount pair second element |
| 6 `fxx` | windg | wind direction uniform `fx` |
| 7 `v10x` | windg | wind-speed pair second element |
| 8 `v12x` | clgen | dew-point pair second element |
| 9 `zx` | timepk (item 6) | — |

**Month boundary** (`cligen.f:1206-1212`): on `mo ≠ mox`, clgen sets
`mox = mo`, `dax = 1`, and calls `ranset(ntd, iyear)` — the only live
`ranset` call site and the only `mox` writer (re-confirms the item-3
mox≠0 characterization). Otherwise `dax = dax + 1`. `windg` reuses the
same `dax` (it must run after `clgen` on the same day; `day_gen` order
is clgen → windg → alphb).

**Rolling pairs**: each `dstn1` call takes (previous, today's-column)
and then shifts: `(v1,v2)` Tmax, `(v3,v4)` Tmin, `(v5,v6)` radiation,
`(v7,v8)` precip amount, `(v9,v10)` wind speed (windg), `(v11,v12)`
dew point. The first elements are seeded by `ranset`'s first-call
branch (`cligen.f:4099-4117`, one draw off each entry seed — the
item-3 replay asserts exactly this); the main program's own warm
draws (`cligen.f:894-899`) advance `k2,k3,k4,k5,k8,k9` **before** the
first `ranset` call but their values are then overwritten by it —
their only lasting effect is seed advancement.

**The `v7` band-aid** (`cligen.f:1253`): if `v7 == 0.0` exactly, clgen
draws `v7 = randn(k5)` — the single fresh-draw site, and the reason
the item-3 `ranset` replay treats `k5` as externally advanced.

**`l` (wet/dry Markov selector)**: initialized in main
(`cligen.f:888-890`: `vv = randn(k1)`, `l = 2`, `l = 1` if
`vv > prw(1,1)`), then written only by clgen (2 on a dry day, 1 on a
wet day). Note the initialization's inverted sense relative to clgen's
own use (main sets `l = 1` when the draw *exceeds* the wet-after-wet
probability) — transcribe, don't reason.

## Per-day call sequence and dstn1 count

1. Solar geometry from `ida` (pure transcendental math, no draws) →
   `rmx`.
2. Month-boundary block (above).
3. Precip (`nsim ≠ 0` — generation active): `vv = vvx(dax)`; dry if
   `prw(mo,l) ≤ 0` or `vv > prw(mo,l)` (sets `r(ida) = 0`, `l = 2`);
   wet path consumes `v8x(dax)` + 1 `dstn1` and sets `l = 1`,
   `r(ida) ≥ 0.01`.
4. Temps: `msim = 0` (observed temps present) consumes `v12x(dax)` +
   1 `dstn1` (dew point only, anchored to the **observed**
   `tmng`/`tmxg` already stored by `day_gen`); `msim ≠ 0` consumes
   `v2x`, `v4x`, `v12x` + 3 `dstn1` (Tmax/Tmin/Tdew with the
   SD-ordering anchor branch at 1414/1429).
5. Radiation: `v6x(dax)` + 1 `dstn1`, interp 10/11, bounds
   `[0.05·rmx, rmx]`.
6. `windg` (separate unit, same day): `fxx(dax)`; calm short-circuit
   consumes nothing else; otherwise `v10x(dax)` + 1 `dstn1`.
7. `alphb` (`day_gen:3114-3141`): after normalizing `r(ida) ≤ 0` to
   zero, the positive-rain branch calls it once at line 3119; for
   `iopt ≥ 4`, the nested positive-rain branch calls it a second time
   at line 3141. Thus each wet day consumes one `dstg` draw normally
   and a second draw on the storm path. All captured package cases use
   `iopt ≥ 4`, so their `ab` streams contain two records per wet day.

The item-3 `rn`/`n1`/`dg` full streams therefore remain a complete
draw-order oracle: any port that consumes a column or draw out of
order desynchronizes the seed/state assertions at the next record.

## Observed-mode gating

`nsim`/`msim` are per-day flags set by `day_gen` from the `.prn`
record (`9999` sentinel → generate). `nsim = 0` skips the entire
precip block (observed precip already in `r(ida)`); `msim = 0` takes
the dew-point-only temperature branch. Both flags live in `/bk7/`.

## In-place station-state mutations (port must replicate)

- `clgen:1237-1238`: the monthly precip skew `rst(mo,3)` is **clamped
  in place** to ±4.5 — `Cbk7State.rst` mutates during generation.
- `windg:2107`: wind-speed skew `wvl(j,4,mo)` is **clamped in place**
  to 0.01 when zero — `Cbk1State.wvl` mutates.
- `r5monb` (once per run, before generation): **overwrites `wi(1..12)`
  in place** — after it runs, `Cbk9State.wi` is no longer the
  .par-derived halved depth but the α = R30/R ratio. The main
  program's `r5max` scan (`cligen.f:867-869`) reads `wi` *before*
  `r5monb` converts it. Its header comments claiming `k7` read and
  `r1` write are stale — the body draws nothing and writes only `wi`.

## Live screen side effects (Ran — fixture evidence)

`clgen:1466-1467`: `tdp < -10` prints "Tdew -10 rangecheck executed."
and clamps `tdp = 1.1*tmng`. **This fires in the goldens** (7-11
occurrences per new-meadows run across the captured stdout logs;
mt-wilson/fish-springs/jeogla: none). The clamp is load-bearing
generation behavior; the message is screen-only (not on the `.cli`
surface). The port implements the clamp and surfaces the event to the
caller (count or callback — spine decides at port time); it does not
print.

## Constant surfaces

- `sml` (`/bk5/`): written exactly once, `main:865` (`sml = 0.0`);
  `alphb`'s `ei = r(ida) - sml` is `r(ida)` in every reachable run.
  Carried in `Cbk5State` for fidelity, default 0.0.
- `xx = 1.` multiplies every `dstn1` result (dead scale factor) —
  transcribed as the source shape.
- `pit = 58.13`, `pi2 = 6.283185`, `yls`/`ylc` (latitude sin/cos with
  the f32 `clt = 57.296` degree conversion) are main-program setup
  (`cligen.f:882-887`) — they land in the state constructors/setup of
  this package's harness, cited.

## State-surface additions this package makes

| Struct | New members | Source |
|---|---|---|
| `Cbk3State` (new) | `j`, `ida` | `cbk3.inc` (live slice; `j` is windg's direction-search loop index, in COMMON) |
| `Cbk5State` (new) | `r[366]`, `sml` | `cbk5.inc` live slice |
| `Cbk4State` (extend) | `nc[13]`, `nt`, `mo` | block data `nc` (`cligen.f:1064`); `mo` single-writer = `day_gen`/`jlt` |
| `Cbk7State` (extend) | `ra`, `tmxg`, `tmng`, `rmx`, `yls`, `ylc`, `pit`, `nsim`, `msim`, `l` | generation scratch, `cbk7.inc` |
| `Cbk1State` (extend) | `wv`, `th`, `pi2`, `tdp` | windg/clgen writes |

`Crandom3State` already carries `mox`, `dax`, `vv`, `fx`, `z`, and the
ranary column accessors (item 3) — no extension needed.
