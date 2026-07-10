# `day_gen` / Observed-Input Characterization

Evidence mode: Static (full source read 2971-3195; wxr_gen year-plan
lines 3758-3781; main setup 865-902) + Ran fixture-file inspection.

## The `.prn` read protocol (`day_gen:3067-3083`)

- Per-day, inside the loop, `iopt = 6` only: `msim = nsim = 0`, then
  `read(9,'(15x,3i5)', end=199) irida, itmxg, itmng` — columns 16-20,
  21-25, 26-30, blank-stripped integers.
- **The fixture `.prn` files are CRLF** (Ran: `cat -A` shows `^M$`)
  with left-justified integers ("55   "). The CR sits beyond column
  30, so the Fortran format never touches it; the typed reader slices
  the same columns from the raw record and inherits the same
  indifference. Blank fields → 0 (BLANK='NULL'), unparseable → fail
  closed.
- Sentinels: `9999` in precip → `nsim = 1`; in either temp →
  `msim = 1`; any of them sets the SAVE'd `q_gen_started`.
  Assignments regardless: `r(ida) = irida·0.01` (hundredths of an
  inch), `tmxg = itmxg`, `tmng = itmng` (int → f32, Fahrenheit).
- **EOF = the 5.323 fix**: `moveto = 225` before the read, cleared on
  success; EOF leaves 225 and exits the day loop (`goto 181`). At the
  loop's natural end, `q_gen_started` also forces `moveto = 225`
  ("stop signal if generation started this year") — the padded
  fish-springs run stops after its sentinel-tail year exactly this
  way; mt-wilson stops via mid-loop EOF.

## Loop structure

`ida = nbt` (1 for daily modes; `ntd1` = the storm's Julian day for
`iopt` 4/7, where `ntd` is also overwritten to `ntd1` so the loop runs
exactly one day). Per day: observed block → `jlt` → `lintrp` when
`interp = 1` → `clgen` → `windg` → **`th = th·clt` (radians→degrees,
in place, `cligen.f:3104`)** → `ccl1` grid writes (`prcip`, `tgmx`,
`tgmn` store the **Fahrenheit** values; then the in-place F→C
conversion of `tmxg`/`tmng`/`tdp`; `radg = ra`) → the storm chain
(item 6) → the unit-7 row (iopt ≥ 4 only):
`jd mo iyear xr dur tpr xmav tmxg tmng radg wv th tdp` — Celsius
temps, degree wind direction. The row becomes the typed `DailyRow`;
FORMAT/file emission is item 8.

## SAVE state

`q_gen_started` (`data .false.`, SAVE) persists **across day_gen
calls/years** → `DayGenState`, caller-owned.

## Year plan (wxr_gen 3758-3781, ported in item 8; harness transcribes)

Per year: `ntd = 365`, leap (`mod 400 == 0` or `mod 4 == 0 and not
mod 100 == 0`) → 366 for options ≤3, 5, 6; **iopt 4/7 use a different
(quirky) `nt` test** (`.and.` where the daily rule has `.and..not.`)
feeding `jdt` for `ntd1 = nbt`; the `ccl1` grids are zeroed every
year; `iyear` increments per completed year. The item-7 harness takes
`(iyear, ntd)` per year from the captured B-lines and transcribes the
zeroing; the quirky iopt-4/7 `nt` computation is transcribed for the
single-storm case with the source cited.

## Main-program generation setup (865-902) — cold-start surface

`sml = 0`; the `r5max` scan (866-869) computes a local never read
afterward — dead, not ported (documented); `r5monb`; `ab = 0.02083`,
`ab1 = 1 − ab`; `nt = 0`; `clt = 57.296`, `pit = 58.13`,
`pi2 = 6.283185`; `yls/ylc = sin/cos(ylt/clt)` (pinned f32);
`vv = randn(k1)`, `l = 2`, `l = 1` if `vv > prw(1,1)`;
`rn1 = randn(k7)`; the six rolling warms `v1 = randn(k2)` …
`v11 = randn(k9)`; `msim = nsim = 1`. With this ported, a run derives
from block-data seeds (+ `-r` burn) and the input files alone — the
cold-start acceptance surface.
