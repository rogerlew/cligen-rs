# CLIGEN 5.32.3 Fortran Decomposition

Status: **Ratified**, rev 3 — first pass (Claude Code) → Codex
source-verification review (rev 2, findings applied) → ratification
package (rev 3: mechanical extraction of unit boundaries, per-unit
common-block usage, live/commented call graph, complete precision-site
census, dead-code adjudication, aliasing census).
Evidence mode: Static + Ran — the rev-3 tables derive from an extraction
script run over the source
(`docs/work-packages/20260709-decomposition-ratification/artifacts/`:
`extract.py`, `unit-extraction.md`, `precision-sites.md`,
`deadcode-adjudication.md`) plus targeted source reads.
Source: `reference/cligen532/cligen.f` (7,657 lines) + `.inc` files.

## 1. Shape of the program

Lines 1–381 are the header changelog (no code). The program proper is
**50 units**: the main program (`program cligen`, 382–984 — `getarg`
option parsing at 645–660, usage text at 780–784, mode dispatch), a
`block data` unit initializing seeds, QC accumulators, and command
defaults (1037–1093), and 48 subprograms — including an embedded,
double-precision ACM special-function library (§2.7). The code is the
C. R. Meyer recode (1999–2004) whose header states the intent: "Recoded
by the WEPP F-77 Coding Conventions. The logic is greatly simplified; the
structure of the code is much improved; and the in-line documentation is
greatly expanded." The changelog documents the storm-duration/`DSTG` bug
history and is a port asset: a ready-made list of behaviors needing
pinned tests.

Live include files: 11 — `cbk1/3/4/5/7/9.inc`, `ccl1.inc`,
`cinterp.inc`, `command6.inc`, `crandom3.inc`, `csumr.inc`.
(`crandom.inc` is superseded by `crandom3.inc`; `ctap2.inc` appears only
on commented include lines. Confirmed by extraction: no live unit
includes either.)

A load-bearing structural fact: **the QC self-tests are
trajectory-load-bearing, not passive diagnostics.** `dstg` calls
`ks_tst` during generation (1732), and `ranset` calls `ks_tst`,
`conflm`, and `confls` (4227–4246), with `confls` reaching the ACM
`cdfchi` chain (4691). A QC rejection triggers regeneration, which
consumes additional RNG draws — so the QC and ACM code participate in
the stochastic trajectory and must port with the deviates, not after
them. Fixture evidence confirms the path fires in practice (K-S
failure/regeneration messages in the golden-fixture run logs).

## 2. Program-unit inventory by functional cluster

Line numbers refer to `reference/cligen532/cligen.f`. The full
mechanical table (per-unit includes and callees) is in
`unit-extraction.md`; the tables below carry roles and the load-bearing
facts.

### 2.1 RNG and random deviates

| Unit | Lines | Role |
|---|---|---|
| `randn` | 1980–2019 | Uniform (0,1). **Pure integer arithmetic** — 4-integer seed with carries (1994–2009); uniform assembled from four `float(k)` f32 multiply-adds (2010–2011); rejection loop outside (0,1). Live callers: program, `clgen`, `dstg`, `timepk`, `ranset`. |
| `dstn1` | 1789–1816 | Standard normal deviate. Live callers: `clgen`, `windg`, `ranset`. |
| `dstg` | 1651–1788 | Gamma deviate via rejection sampling — drives `alpha_0.5` peak intensity. `double precision fu, xx` (1696); `SAVE array, iarrct`; calls `ks_tst` in its QC filter (1732). Only live caller: `alphb`. |
| `ranset` | 4002–4341 | Seed initialization + QC battery (`ks_tst`, `conflm`, `confls`); `SAVE ell, last_r`. |

### 2.2 Daily stochastic core

| Unit | Lines | Role |
|---|---|---|
| `clgen` | 1094–1515 | The daily generation loop (precip occurrence/amount, temperatures, radiation, dew point). Calls `randn`, `dstn1`, `ranset`, and the generation-time interpolators `fouri2`/`ryf2`. |
| `alphb` | 3817–3897 | `alpha_0.5` (max 30-min / total rainfall ratio), Bofu Yu 1999 latitude-responsive rewrite — **the live path** (`day_gen:3119,3141`). Calls `dstg`. |
| `r5monb` | 3898–4001 | Monthly max-.5-h rainfall statistics, Yu variant — live, called once per run (`cligen:878`). |
| `windg` | 2020–2122 | Wind generation (calls `dstn1`); called from `day_gen`. |

### 2.3 Storm shape and event machinery

| Unit | Lines | Role |
|---|---|---|
| `timepk` | 2188–2239 | Time-to-peak within storm (calls `randn`). |
| `sing_stm` | 3325–3496 | Single-storm mode; self-contained computation; opens output units 7/8 itself (3445–3455). |

This cluster plus `dstg`/`alphb` is the **augmentation surface** for
storm duration/intensity derivation and NOAA design-storm curves — and
the code with the most documented historical churn ("Storm duration was
getting hosed"; duration constant 4.607 → 9.210; the `DSTG` gamma QC
saga).

### 2.4 Generation orchestration and modes

| Unit | Lines | Role |
|---|---|---|
| `program cligen` | 382–984 | Option parsing, station intake (`sta_dat`), mode dispatch to `usr_opt`/`sing_stm`/`wxr_gen`; runs `r5monb` once per run. |
| `wxr_gen` | 3589–3816 | "The guts of the weather generating code" (3598–3599): top-level generation orchestrator — drives `day_gen` and `opt_calc`, writes WEPP unit-7 headers (3722–3754), uses `jdt`. |
| `day_gen` | 2971–3195 | Per-day driver: `jlt`, `lintrp`, `clgen`, `windg`, `alphb`, `timepk`; observed-mode `9999` handling (`nsim`/`msim` flags, 3076–3079) and the 5.323 EOF fix; writes daily unit-7 rows; `SAVE q_gen_started`. |
| `opt_calc` | 3196–3324 | Output options 1–3; writes unit 8; calls `clmout`. |
| `usr_opt` | 3497–3588 | Interactive option selection; opens observed input files. |

### 2.5 Station parameters and monthly-to-daily interpolation

| Unit | Lines | Role |
|---|---|---|
| `sta_dat` | 2240–2485 | Station `.par` intake driver; calls `header`, `sta_name`, `sta_parms`. |
| `sta_name` | 2486–2655 | Station selection. |
| `sta_parms` | 2656–2970 | Parameter handling; EQUIVALENCE views `rst1/rst2/rst3` and `prw1/prw2` onto the `rst`/`prw` parameter arrays (2783–2787); runs the par-time interpolation setup `fouri1`/`ryf1`. |
| `lintrp` | 7252–7337 | Linear interpolation (generation-time, from `day_gen`). |
| `fouri1` / `fouri2` | 7338–7386 / 7387–7423 | Fourier interpolation: setup at par time (`sta_parms`), evaluation at generation time (`clgen`). |
| `ryf1` / `ryf2` | 7424–7544 / 7545–7657 | Yoder–Foster monthly-mean-preserving interpolation: same setup/evaluation split. |

### 2.6 Output and display

| Unit | Lines | Role |
|---|---|---|
| `clmout` | 1516–1650 | Interactive screen summaries (options 1/2), via `opt_calc` — **not** the `.cli` writer. |
| `header` | 2153–2187 | Output header support (via `sta_dat`). |

**`.cli`/WEPP file output has no single owner**: spread across
`sing_stm` (opens units 7/8), `wxr_gen` (unit-7 headers), `day_gen`
(daily unit-7 rows), and `opt_calc` (unit 8), on hard-coded shared unit
numbers. The Rust `output` module centralizes this surface; faithful-mode
byte parity is judged on the produced files, not the unit plumbing.

### 2.7 QC statistics and the embedded ACM special-function library

Trajectory-load-bearing (§1). Home of 388 of the source's 391
double-precision sites (§5).

| Unit | Lines | Role |
|---|---|---|
| `ks_tst` | 4453–4588 | Kolmogorov–Smirnov test — live from `dstg` and `ranset`. |
| `conflm` / `confls` | 4589–4649 / 4650–4704 | Confidence limits on mean / variance (live from `ranset`); `confls` uses `dble()` and calls `cdfchi`. |
| ACM support | 4705–7251 | `cdfchi`, `cumchi`, `cumgam`, `dinvr`, `dzror`, `erf`, `erfc1`, `exparg`, `gam1`, `gamma`, `gratio`, `ipmpar`, `rexp`, `rlog`, `spmpar`. Double precision with `D` literals throughout; `SAVE` and `ENTRY` (`dstinv` is an ENTRY of `dinvr`, `dstzr` of `dzror`; `cdfchi` calls `dstinv`, `dinvr` calls `dstzr`). Published ACM algorithms: faithful mode replicates the embedded versions; native mode may substitute a vetted Rust special-function source. |

### 2.8 Calendar

| Unit | Lines | Role |
|---|---|---|
| `jdt` | 1817–1845 | Julian-date function (from `wxr_gen`). |
| `jlt` | 1846–1903 | Date decomposition (from `day_gen`). Leap-year surface lives here and in caller year loops. |

### 2.9 Dead code — ratified, not ported

Zero live references (full adjudication in `deadcode-adjudication.md`):

| Unit | Lines | Evidence |
|---|---|---|
| `nrmd` | 2123–2152 | No reference of any kind; source's own comment agrees (line 426). |
| `chitst` | 4342–4452 | All four call sites commented; K-S replaced it. |
| `alph` | 985–1036 | Only commented sites (`c call alph` above the live `call alphb`). |
| `r5mon` | 1904–1979 | Only a commented site above the live `call r5monb`. |

~330 source lines out of port scope. A future generation profile wanting
the pre-Yu intensity model would revive these as a labeled extension.

### 2.10 Common-block ownership (extraction-derived)

| Include | Including units (live) |
|---|---|
| `cbk1.inc` | program, `clgen`, `windg`, `sta_parms`, `day_gen` |
| `cbk3.inc` | `clgen`, `windg`, `day_gen`, `alphb`, `r5monb`, `fouri2` |
| `cbk4.inc` | program, blockdata, `clgen`, `clmout`, `windg`, `timepk`, `day_gen`, `opt_calc`, `sing_stm`, `usr_opt`, `wxr_gen`, `alphb`, `r5monb`, `ranset` |
| `cbk5.inc` | program, `clgen`, `day_gen`, `opt_calc`, `alphb`, `r5monb` |
| `cbk7.inc` | program, blockdata, `clgen`, `windg`, `sta_parms`, `day_gen`, `wxr_gen`, `alphb`, `r5monb`, `ranset` |
| `cbk9.inc` | program, `sta_parms`, `day_gen`, `alphb`, `r5monb` |
| `ccl1.inc` | `clmout`, `day_gen`, `wxr_gen` |
| `cinterp.inc` | program, blockdata, `clgen`, `sta_parms`, `day_gen`, `wxr_gen`, `lintrp`, `fouri1`, `fouri2`, `ryf1`, `ryf2` |
| `command6.inc` | program, blockdata, `sta_dat`, `sta_name`, `sta_parms`, `opt_calc`, `sing_stm`, `usr_opt`, `wxr_gen` |
| `crandom3.inc` | program, blockdata, `clgen`, `dstg`, `windg`, `timepk`, `ranset`, `ks_tst` |
| `csumr.inc` | `clmout`, `opt_calc` |

`cbk4.inc` is the widest surface (14 units) and will be the most
contended typed struct; `cinterp.inc` cleanly bounds the interpolation
state; `crandom3.inc` bounds RNG + QC state exactly as the module map
assumes.

**Aliasing census (complete)**: EQUIVALENCE exists at exactly two sites —
`crandom3.inc:46–62` (nine named views onto columns of `ranary`) and
`sta_parms:2783–2787` (five local views onto `rst`/`prw`). No other
EQUIVALENCE statement exists in the live source. Both translate per the
coding standard §5 (accessor methods on the owning struct).

### 2.11 Live call-graph spine

```text
program cligen ── sta_dat ─┬─ header
        │                  ├─ sta_name
        │                  └─ sta_parms ── fouri1, ryf1        (par time)
        ├─ r5monb                                              (once/run)
        ├─ usr_opt / sing_stm                                  (modes)
        └─ wxr_gen ─┬─ jdt, opt_calc ── clmout
                    └─ day_gen ─┬─ jlt, lintrp
                                ├─ clgen ── randn, dstn1, ranset,
                                │           fouri2, ryf2       (gen time)
                                ├─ windg ── dstn1
                                ├─ alphb ── dstg ── ks_tst, randn
                                └─ timepk ── randn
ranset ── randn, dstn1, ks_tst, conflm,
          confls ── cdfchi ── cumchi ── cumgam ── gratio ── erf, erfc1,
                    │                             gam1, gamma, rexp,
                    │                             rlog, spmpar ── ipmpar
                    └─ dinvr (ENTRY dstinv) ── dzror (ENTRY dstzr)
```

## 3. Rust module map (ratified)

```text
crates/cligen/src/
  calendar.rs        jdt, jlt (+ leap-year extension point)
  rng.rs             randn, ranset, seed state (crandom3.inc struct)
  qc.rs              ks_tst, conflm, confls        (chitst: dead, recorded)
  acm.rs             the embedded ACM library (f64 throughout)
  deviates.rs        dstn1, dstg (QC-coupled; the f64 fu/xx island)
  par/               sta_dat/sta_name/sta_parms + header: typed par model
                     and station-intake output header
  monthlies.rs       lintrp, fouri1/2, ryf1/2 (par-time setup +
                     generation-time evaluation, both consumers named)
  daily.rs           clgen, alphb, r5monb, windg   (alph/r5mon: dead)
  storm.rs           timepk, sing_stm
  modes.rs           wxr_gen orchestration, day_gen driver, opt_calc,
                     usr_opt, program dispatch
  observed.rs        observed-mode input (.prn; parquet extension point)
  output/            centralized .cli writer (units-7/8 semantics);
                     clmout summaries; .cli.parquet later
  profile.rs         generation profiles + provenance (extension)
```

`block data` (1037–1093) has no module of its own: its initializers land
in the constructors of the owning state structs (`crandom3`, `cbk4`,
`cbk7`, `cinterp`, `command6` per its include set), with source lines
cited per the coding standard §5.

## 4. Port order (ratified against the call graph)

1. `calendar` + `acm` + `qc` — the ACM/QC chain first: the deviates call
   it (§1), and it holds essentially all the f64 surface.
2. `rng` + `deviates` — including QC-coupled regeneration; bit-identical
   deviate streams (via the RNG package's tap patch) are the gate.
3. `par` + `monthlies` — deterministic input path, including the
   par-time `fouri1`/`ryf1` setup.
4. `daily` — `clgen`/`alphb`/`r5monb`/`windg`; consumes the
   generation-time `fouri2`/`ryf2`/`lintrp` evaluators.
5. `storm` + `modes` — the contested machinery and the orchestrator,
   ported against changelog-derived pinned tests.
6. `observed` — the `.prn` path (both fixture classes: sentinel-padded
   and hard-EOF).
7. `output` — centralized `.cli` writer; end-to-end byte-parity gate.

## 5. Known port hazards (ratified)

- **Precision map — measured, and better-bounded than feared**: 391
  double-precision sites in `cligen.f`, of which **388 sit inside the
  QC/ACM cluster** (`ks_tst`/`conflm`/`confls`/ACM; per-unit counts in
  `precision-sites.md`). The only sites outside it are `dstg`'s
  `fu`/`xx` locals (1696) and the block-data zero-inits of the
  `g_dsum`/`g_ssum` QC accumulators (1073–1074; declared
  `crandom3.inc:15–16` — include-file declarations are listed separately
  in the artifact). Faithful mode replicates these site-by-site;
  `acm.rs` is uniformly f64.
- **Stateful constructs**: block data (1037–1093); `SAVE` statics in
  `dstg`, `day_gen`, `ranset`, and the ACM routines; ENTRY points
  `dstinv`/`dstzr` with live cross-unit calls. Each becomes explicit
  owned state per the coding standard; no computed GOTOs exist.
- **Common-block aliasing**: complete census in §2.10 — two sites only.
- **QC-coupled trajectories**: a QC rejection consumes extra RNG draws;
  porting deviates without the QC chain produces silently divergent
  streams (§1).
- **Transcendentals**: libm ULP differences bifurcate trajectories at
  occurrence branches; pin both sides (Rust `libm` crate; the pinned
  reference build's glibc libm identity is recorded in the fixture
  provenance).
- **FMA contraction / build flags**: the reference build pins
  `-O0 -ffp-contract=off -fprotect-parens -fno-fast-math`; the vendored
  production makefile's reordering-permitted flags are disqualified for
  goldens (empirically, they produced byte-range-identical stochastic
  output on the same host — see the fixture manifest — but that is a
  measurement, not a license).
- **Formatted output**: Fortran `FORMAT` rounding differs from Rust
  formatting; trajectory acceptance is on in-memory values; the `.cli`
  writer gets its own byte-level gate.
- **Sequence bifurcation**: the differ reports
  first-divergent-day/variable (`SPEC-CLI-DIFF`, implemented); aggregate
  statistics cannot localize a transcription error.
- **Dead code — ratified**: `nrmd`, `chitst`, `alph`, `r5mon` (§2.9).
