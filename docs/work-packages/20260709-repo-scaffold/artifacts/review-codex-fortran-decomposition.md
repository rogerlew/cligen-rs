# Codex Review — docs/port/fortran-decomposition.md (first pass)

Reviewer: Codex (dispatched via MCP, read-only sandbox, 2026-07-09;
thread 019f486a-1f63-75b3-9616-5c7e5c282631)
Scope: verify the first-pass decomposition against
`reference/cligen532/cligen.f` + includes.
Disposition: all findings ACCEPTED and applied to the doc (rev 2) by
Claude Code, same day.

Verbatim review follows.

---

**Confirmations**

- `RANDN` - CONFIRMED. Integer seed/carry updates are at `reference/cligen532/cligen.f:1994-2009`; the uniform is assembled with four `float(k(...))` terms at `cligen.f:2010-2011`; rejection of values outside `(0,1)` is at `cligen.f:2012-2013`.

- `DSTG` REAL*8 island - CONFIRMED. `double precision fu,xx` is declared at `cligen.f:1696`.

- Main program span/getarg claim - REFUTED as stated for span, CONFIRMED for behavior. The program starts at `cligen.f:382` and ends at `cligen.f:981`, not roughly 420-985. `iargc()`/`getarg` parsing is at `cligen.f:645-660`; usage text starts at `cligen.f:780-784`.

- `alphb`/`r5monb` Bofu Yu rainfall-intensity rewrites - CONFIRMED. The changelog says Bofu Yu corrections made rainfall intensity latitude-responsive and replaced `ALPH`/`R5MON` at `cligen.f:357-359`; active calls use `r5monb` and `alphb` at `cligen.f:878`, `cligen.f:3118-3119`, and `cligen.f:3140-3141`; Bofu comments are at `cligen.f:3814-3822` and `cligen.f:3898-3908`.

- Built-in distributional self-tests - CONFIRMED with caveat. `chitst`, `ks_tst`, `conflm`, and `confls` exist at `cligen.f:4342`, `cligen.f:4453`, `cligen.f:4589`, and `cligen.f:4650`; active runtime calls use `ks_tst`/`conflm`/`confls` at `cligen.f:4227-4230` and `cligen.f:4243-4246`, while `chitst` calls are commented at `cligen.f:1731`, `cligen.f:4225`, `cligen.f:4241`, and `cligen.f:4255`.

- 13 `.inc` files as active include set - REFUTED as worded. The directory has 13 `.inc` files, but `cligen.f` actively includes `crandom3.inc`, not `crandom.inc` (`cligen.f:515`, `cligen.f:1047`, `cligen.f:1172`), and `ctap2.inc` appears only on commented include lines such as `cligen.f:1169`, `cligen.f:2060`, `cligen.f:2213`, and `cligen.f:3028`.

**Findings**

1. **High** - Program-unit inventory is incomplete. The tables omit `windg` at `cligen.f:2020` and the embedded ACM support units: `cdfchi` `4705`, `cumchi` `4954`, `cumgam` `5008`, `dinvr` `5070`, `dzror` `5419`, `erf` `5703`, `erfc1` `5778`, `exparg` `5890`, `gam1` `5942`, `gamma` `6007`, `gratio` `6158`, `ipmpar` `6575`, `rexp` `7005`, `rlog` `7039`, and `spmpar` `7095`. It also omits `block data` initialization at `cligen.f:1037`. Correction: update the inventory to 48 subroutines/functions plus main program, and account for `block data` as initialization state.

2. **High** - The precision-map hazard is materially understated. `DSTG` is not the only double-precision area: `crandom3.inc` declares `g_dsum`/`g_ssum` as double precision at `reference/cligen532/crandom3.inc:15-16`; `confls` converts inputs with `dble()` at `cligen.f:4662-4663`; `cdfchi` and its support declare double precision and `D` literals throughout, starting at `cligen.f:4787-4803`; double-precision functions begin at `cligen.f:5703`, `5778`, `5890`, `5942`, `6007`, `7005`, `7039`, and `7095`. Correction: expand the precision-map section beyond `DSTG` to include QC/common-block and ACM chi-square code.

3. **High** - Port order puts `qc` last, but earlier modules call QC. `dstg` calls `ks_tst` at `cligen.f:1732`; `ranset` calls `ks_tst`, `conflm`, and `confls` at `cligen.f:4227-4230` and `4243-4246`; `confls` calls `cdfchi` at `cligen.f:4691`. Correction: either port QC/ACM support with `deviates`/`rng`, or split QC-enforced batch generation out of the early RNG milestone.

4. **Medium** - Common-block aliasing is missing from hazards/module map. `crandom3.inc` aliases `vvx`, `v2x`, `v4x`, `v6x`, `v8x`, `fxx`, `v10x`, `v12x`, and `zx` onto columns of `ranary` at `crandom3.inc:46-62`; `sta_parms` aliases `rst1/rst2/rst3/prw1/prw2` onto common arrays at `cligen.f:2783-2787` before calling `fouri1`/`ryf1` at `cligen.f:2831-2859`. Correction: document these as shared-memory views crossing `rng`, `daily`, `par`, and `monthlies`.

5. **Medium** - `wxr_gen` is misassigned as a storm/weather variant. Its own purpose is "the guts of the weather generating code" at `cligen.f:3598-3599`; it orchestrates `day_gen` and `opt_calc` at `cligen.f:3671-3673` and `cligen.f:3788-3798`, and writes WEPP output headers at `cligen.f:3722-3754`. Correction: move `wxr_gen` to a top-level generation/mode orchestration cluster and module.

6. **Medium** - Output ownership is misdescribed. `clmout` calculates option 1/2 summaries and writes screen output at `cligen.f:1519-1521`; `.cli`/WEPP output is spread across `sing_stm` opening units 7/8 at `cligen.f:3445-3455`, `wxr_gen` writing unit 7 headers at `cligen.f:3722-3754`, `day_gen` writing daily unit 7 rows at `cligen.f:3173-3176`, and `opt_calc` writing unit 8 at `cligen.f:3308-3317`. Correction: acknowledge hard-coded shared I/O units and do not map faithful text output only to `clmout/header`.

7. **Medium** - Stateful Fortran constructs are missing from hazards. `block data` initializes seeds and command defaults at `cligen.f:1037-1089`; `dstg` saves `array,iarrct` at `cligen.f:1710-1711`; `day_gen` saves `q_gen_started` at `cligen.f:3041-3042`; `ranset` saves `ell,last_r` at `cligen.f:4052-4057`; ACM routines use `SAVE` and `ENTRY` at `cligen.f:5151`, `5316`, `5485`, and `5623`. Correction: add `DATA`, `SAVE`, and `ENTRY` hazards; no computed `GOTO` was found.

8. **Low** - Several unread/name-inferred roles need correction or tightening. `nrmd` is an inverse standard-normal approximation for a probability, not a generator path, at `cligen.f:2126-2147`, and the source says it "does not seem to be used" at `cligen.f:426`. `ryf1`/`ryf2` are Yoder-Foster monthly-mean-preserving interpolation setup/evaluation at `cligen.f:7427-7441` and `cligen.f:7547-7550`. `opt_calc` handles options 1-3 at `cligen.f:3201-3203`; `usr_opt` handles user option selection and observed-file opening at `cligen.f:3500-3501` and `cligen.f:3557-3574`. Correction: replace the unread/name-only role text with these source-backed roles.
