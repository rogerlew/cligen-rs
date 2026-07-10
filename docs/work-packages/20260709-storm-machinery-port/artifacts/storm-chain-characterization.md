# Storm-Chain and `timepk` Characterization

Evidence mode: Static (full source reads: `timepk` 2188-2236, the
`day_gen` storm block 3105-3176, `sing_stm` 3325-3493) + Ran notes
from the existing captures where marked.

## `timepk` (2188-2236)

- **Draw source splits on `iopt`** (`cligen.f:2217-2221`): `iopt = 6`
  (observed) takes a **fresh `randn(k10)` draw**; every other mode
  reads batch column 9, `zx(dax)` — the column no prior package
  consumed. Both write the drawn uniform to common `z`.
- Search: `i = 1..12`, first `timpkd(i) ≥ z` (loop exits at `i = 12`
  regardless); `ratio = (timpkd(i) − z)/(timpkd(i) − timpkd(i−1))`;
  `timepk = 0.08333·i − ratio·0.08333`. **`timpkd(0)` (the caller-set
  0.0 sentinel) is live** when `i = 1` — the same 0-based array whose
  aliasing quirk item 4 characterized; here the sentinel is read, not
  aliased.
- k10 evolution: only `iopt = 6` advances it (plus the `-r` burn's
  exclusion — k10 is *not* burned). This closes the last external
  stream in the item-5 replay protocol.

## The duration/Ipeak chain (`day_gen:3114-3176`)

Runs inside the daily loop after clgen/windg. Order (all REAL*4; the
only transcendental is `alog`, already pinned as `logf_pinned`;
domain `1 − r1 ∈ (0,1)`):

1. **Wet-day duration** (3114-3127): `r(ida) ≤ 0` → normalize to 0,
   `dur(mo,jd) = 0`; else first `alphb` call, then
   `dur = 3.99/(−2·alog(1−r1))` (the B. Yu 6/99 coefficient — the
   3.99 replaced 9.210 which replaced 4.607; only 3.99 is live),
   clamped to 24.
2. `iopt ∈ {4,7}` → `dur(mo,jd) = 0.0` (3136).
3. **`iopt ≥ 4` block** (3138-3171) — includes continuous mode 5, so
   this executes for **every fixture day**:
   - wet: second `alphb`; `xr = r·25.4`; `tpr = timepk(timpkd,k10)`
     clamped to 0.99; `r5p = −2·xr·alog(1−r1)` clamped to
     `tymax(itype)`; `xmav = r5p/(xr/dur)`; if mean temp ≤ 0 →
     `xmav = 1.01`; floor 1.01.
     **Transient ∞ is real behavior**: for `iopt ∈ {4,7}` the just-
     zeroed `dur` makes `xr/dur = +∞` and `xmav = r5p/∞ = 0`, then
     the 1.01 floor applies, then the override recomputes — IEEE f32
     reproduces this exactly; do not guard it.
   - dry: `xr = 0`, `xmav = 0`, `tpr = 0`, plus a **live dead store
     `tap4 = 0.0`** (3153 — an implicitly-typed local left from
     removed instrumentation; no observable effect; not transcribed).
   - `iopt = 4` override: `dur = usdur`, `xr = damt·25.4`,
     `tpr = ustpr`, `xmav = (uxmav·25.4)/(xr/dur)`, floor 1.01.
   - `iopt = 7` override: `dur = 24`, `xr = damt·25.4`,
     `xmav = tymax(itype)/(xr/dur)`, floor, `tpr = dtp(itype)` —
     **fixture-unreachable** (no `-t7` capture); ported as written
     (pure arithmetic, no draw), flagged as unexercised in tests.
4. The unit-7 row write (3175: `jd mo iyear xr dur tpr xmav tmxg tmng
   radg wv th tdp`) — the seam the storm-day tap instruments; its
   numeric inputs are exactly the item-8 `.cli` daily-row surface.

Constant tables: `tymax(4)` is main-program DATA (`cligen.f:602`,
`180.34/154.94/307.34/330.2`); `dtp(4)`/`dmxi(4)` are block data
(1065-1066) in `/bk4/` — `Cbk4State` gains both (`dmxi` write-only
dead per the source comment, carried for block completeness).

## `sing_stm` (3325-3493) — intake only

No numeric computation. Live fixture path (`iopt = 4`, stdin from
`single-storm.inp`): reads `mo jd ibyear`, `damt`, `usdur`, `ustpr`,
`uxmav`; sets `iyear = ibyear`; `outfil ≠ "XXX"` (from `-o`) skips the
filename prompt; opens unit 7 `status='new'` with the overwrite
dialog (`force` short-circuits). For `iopt = 6`: defaults
`ibyear/numyr` when unset. For `iopt = 5`: only the file-open path.
Port treatment (the `sta_dat` precedent): typed parameter struct in
place of the stdin reads; file-open/overwrite belongs to the CLI
binary; interactive prompts get the `sta_name` fail-closed treatment.
Note `sing_stm` **writes `mo` into `/bk4/`** on the 4/7 path (the
storm month) — the one state effect the typed port must keep.

## Fixture branch coverage

| Branch | Exercised by |
|---|---|
| `timepk` batch path (`zx(dax)`) | stochastic + single-storm runs |
| `timepk` fresh-draw path (`randn(k10)`) | observed runs (`iopt = 6`) |
| chain wet path | all runs (wet days) |
| chain dry path | all runs (dry days) |
| `iopt = 4` override + transient-∞ | single-storm goldens |
| `iopt = 7` override | none — ported unexercised, noted |
