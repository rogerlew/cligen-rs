# CLIGEN 5.32.3 Fortran Decomposition

Status: Draft, rev 2 — first pass corrected by a Codex source-verification
review (2026-07-09, all eight findings applied; verbatim review in
`docs/work-packages/20260709-repo-scaffold/artifacts/review-codex-fortran-decomposition.md`).
Evidence mode: Static — Claude Code targeted reads plus Codex full-source
verification of the inventory, precision map, call dependencies, and unit
roles. Full ratification (complete common-block ownership map) remains
ROADMAP item 2.
Source: `reference/cligen532/cligen.f` (7,657 lines) + `.inc` files.

## 1. Shape of the program

One Fortran 77 file: a main program (`cligen.f:382–981` — `getarg` option
parsing at 645–660, usage text at 780–784), a `block data` unit
initializing seeds and command defaults (1037–1089), and **48 subprograms**
— including an embedded, double-precision ACM special-function library
(§2.7) that a name-based scan misses. The code is the C. R. Meyer recode
(1999–2004) whose header states the intent: "Recoded by the WEPP F-77
Coding Conventions. The logic is greatly simplified; the structure of the
code is much improved; and the in-line documentation is greatly expanded."
The in-line changelog (lines ~40–470) is dense and candid — it documents
the storm-duration/`DSTG` bug history and constant changes — and is a port
asset: a ready-made list of behaviors needing pinned tests.

Include files: 13 `.inc` files exist, but two are not part of the live
build surface — `crandom.inc` is superseded by `crandom3.inc` (the actively
included RNG/QC state, e.g. `cligen.f:515, 1047, 1172`), and `ctap2.inc`
appears only on commented include lines. The live set is 11.

A load-bearing structural fact (Codex finding 3): **the QC self-tests are
trajectory-load-bearing, not passive diagnostics.** `dstg` calls `ks_tst`
during generation (`cligen.f:1732`), and `ranset` calls `ks_tst`, `conflm`,
and `confls` (4227–4230, 4243–4246), with `confls` reaching into the ACM
`cdfchi` chain (4691). A QC rejection triggers regeneration, which consumes
additional RNG draws — so the QC and ACM code participate in the stochastic
trajectory and must port with the deviates, not after them.

## 2. Program-unit inventory by functional cluster

Line numbers refer to `reference/cligen532/cligen.f`.

### 2.1 RNG and random deviates

| Unit | Line | Role |
|---|---|---|
| `randn` | 1980 | Uniform (0,1). **Pure integer arithmetic** — 4-integer seed with carries (1994–2009); uniform assembled from four `float(k)` f32 multiply-adds (2010–2011); rejection loop for results outside (0,1) (2012–2013). Trivially bit-replicable. |
| `dstn1` | 1789 | Standard normal deviate (from uniforms). |
| `dstg` | 1651 | Gamma deviate via rejection sampling — drives `alpha_0.5` peak-intensity ratio. `double precision fu, xx` (1696); `SAVE array, iarrct` (1710–1711); calls `ks_tst` in its QC filter (1732). Long bug history in the changelog. |
| `ranset` | 4002 | Seed initialization; `SAVE ell, last_r` (4052–4057); runs the QC batch tests (4227–4246). |
| `nrmd` | 2123 | Inverse standard-normal approximation for a probability (2126–2147). Source comment says it "does not seem to be used" (line 426) — confirm dead-code status during ratification; if dead, record and do not port. |

### 2.2 Daily stochastic core

| Unit | Line | Role |
|---|---|---|
| `clgen` | 1094 | The daily generation loop (precip occurrence/amount, temperatures, radiation, dew point); calls `RANDN` and `DSTN1`. |
| `alph` / `alphb` | 985 / 3817 | `alpha_0.5` (ratio of max 30-min to total rainfall). `alphb` is the Bofu Yu 1999 latitude-responsive rewrite; **the live path calls `alphb`/`r5monb`** (878, 3118–3119, 3140–3141) — the originals are retained history. |
| `r5mon` / `r5monb` | 1904 / 3898 | Monthly max-.5-hour rainfall statistics (original / Yu variant, as above). |
| `windg` | 2020 | Wind generation. |

### 2.3 Storm shape and event machinery

| Unit | Line | Role |
|---|---|---|
| `timepk` | 2188 | Time-to-peak within storm. |
| `sing_stm` | 3325 | Single-storm mode; opens output units 7/8 itself (3445–3455). |
| `day_gen` | 2971 | Per-day generation used by the orchestrator; writes daily unit-7 rows (3173–3176); `SAVE q_gen_started` (3041–3042); observed-mode EOF fix (5.323) lives here. |

This cluster plus `dstg`/`alphb` is the **augmentation surface** for storm
duration/intensity derivation and NOAA design-storm curves — and the part
of the code with the most documented historical churn ("Storm duration was
getting hosed"; duration constant 4.607 → 9.210; the `DSTG` gamma QC saga).

### 2.4 Generation orchestration and modes

| Unit | Line | Role |
|---|---|---|
| main program | 382–981 | Option parsing, mode dispatch. |
| `wxr_gen` | 3589 | Self-described "the guts of the weather generating code" (3598–3599): top-level generation orchestrator — drives `day_gen` and `opt_calc` (3671–3673, 3788–3798) and writes WEPP unit-7 output headers (3722–3754). |
| `opt_calc` | 3196 | Output options 1–3 handling (3201–3203); writes unit 8 (3308–3317). |
| `usr_opt` | 3497 | User option selection; opens observed input files (3557–3574). |

### 2.5 Station parameters and monthly-to-daily interpolation

| Unit | Line | Role |
|---|---|---|
| `sta_dat` / `sta_name` / `sta_parms` | 2240 / 2486 / 2656 | Station `.par` reading, station selection, parameter handling. `sta_parms` aliases `rst1/rst2/rst3/prw1/prw2` onto common arrays (2783–2787) before interpolation calls (2831–2859). |
| `lintrp` | 7252 | Linear interpolation. |
| `fouri1` / `fouri2` | 7338 / 7387 | Fourier interpolation of monthly parameters to daily values. |
| `ryf1` / `ryf2` | 7424 / 7545 | Yoder–Foster monthly-mean-preserving interpolation, setup / evaluation (7427–7441, 7547–7550). |

### 2.6 Output and display

| Unit | Line | Role |
|---|---|---|
| `clmout` | 1516 | Interactive screen summaries (options 1/2 viewing) — **not** the `.cli` writer. |
| `header` | 2153 | Output header support. |

**`.cli`/WEPP file output has no single owner**: it is spread across
`sing_stm` (opens units 7/8), `wxr_gen` (unit-7 headers), `day_gen`
(daily unit-7 rows), and `opt_calc` (unit 8), on hard-coded shared unit
numbers. The Rust `output` module centralizes this surface; faithful-mode
byte parity is judged on the produced files, not on replicating the unit
plumbing.

### 2.7 QC statistics and the embedded ACM special-function library

Trajectory-load-bearing (§1). All double-precision.

| Unit | Line | Role |
|---|---|---|
| `chitst` | 4342 | Chi-square test — **all call sites are commented out** (1731, 4225, 4241, 4255); confirm dead-code status during ratification. |
| `ks_tst` | 4453 | Kolmogorov–Smirnov test (live: called from `dstg`, `ranset`). |
| `conflm` / `confls` | 4589 / 4650 | Confidence limits on mean / variance; `confls` uses `dble()` (4662–4663) and calls `cdfchi` (4691). |
| ACM support | 4705–7095 | `cdfchi` (4705), `cumchi` (4954), `cumgam` (5008), `dinvr` (5070), `dzror` (5419), `erf` (5703), `erfc1` (5778), `exparg` (5890), `gam1` (5942), `gamma` (6007), `gratio` (6158), `ipmpar` (6575), `rexp` (7005), `rlog` (7039), `spmpar` (7095). Double precision with `D` literals throughout (from 4787–4803); uses `SAVE` and `ENTRY` (5151, 5316, 5485, 5623). Port note: these are published ACM algorithms — port faithfully, but a well-tested Rust special-function source may serve native mode; faithful mode replicates the embedded versions. |

### 2.8 Calendar

| Unit | Line | Role |
|---|---|---|
| `jdt` / `jlt` | 1817 / 1846 | Julian-date utilities. The leap-year surface (an augmentation target) lives here and in the callers' year loops. |

### 2.9 Common blocks → typed state

Live includes: `cbk1/3/4/5/7/9.inc`, `ccl1.inc`, `cinterp.inc`,
`command6.inc`, `crandom3.inc`, `csumr.inc` (11; `crandom.inc` superseded,
`ctap2.inc` commented-only). Each becomes a named struct; the full
which-unit-reads/writes-which-block map is ROADMAP item 2's deliverable.

**Aliasing hazard** (Codex finding 4): common storage is used as shared-
memory views — `crandom3.inc` aliases `vvx/v2x/v4x/v6x/v8x/fxx/v10x/v12x/zx`
onto columns of `ranary` (crandom3.inc:46–62), and `sta_parms` aliases
scalar names onto common arrays (2783–2787). These views cross the
proposed `rng`/`daily`/`par`/`monthlies` boundaries; the typed-state design
must give each view a single owning struct with explicit accessors, and the
ratification pass must enumerate every such aliasing site.

## 3. Proposed Rust module map (to ratify in ROADMAP item 2)

```text
crates/cligen/src/
  calendar.rs        jdt, jlt (+ leap-year extension point)
  rng.rs             randn, ranset, seed state (crandom3.inc)
  qc.rs              ks_tst, conflm, confls (+ chitst if not dead)
  acm.rs             the embedded ACM special-function library (f64)
  deviates.rs        dstn1, dstg (precision map per source; QC-coupled)
  par/               sta_dat/sta_name/sta_parms: typed par model, parse/serialize
  monthlies.rs       lintrp, fouri1/2, ryf1/2
  daily.rs           clgen, alphb/r5monb (+ retained alph/r5mon history), windg
  storm.rs           timepk, sing_stm event machinery
  modes.rs           wxr_gen orchestration, opt_calc, usr_opt, day_gen driver
  observed.rs        observed-mode input (.prn; parquet extension point)
  output/            centralized .cli text writer (units-7/8 semantics); .cli.parquet later
  profile.rs         generation profiles + provenance (extension, no Fortran basis)
```

## 4. Port order (dependency spine, corrected)

1. `calendar` + `acm` + `qc` — the ACM/QC chain first, because the
   deviates call it (§1); identity-testable against Fortran taps in
   isolation.
2. `rng` + `deviates` — including the QC-coupled regeneration behavior;
   bit-identical deviate streams are the gate.
3. `par` + `monthlies` — deterministic input path.
4. `daily` (+`windg`) — first end-to-end stochastic surface.
5. `storm` + `modes` — the contested machinery and the orchestrator,
   ported against pinned tests derived from the changelog.
6. `observed` — the `.prn` path (operator has already debugged its EOF
   behavior in the Fortran).
7. `output` — centralized `.cli` writer; end-to-end byte-parity gate.

## 5. Known port hazards

- **Precision map (systemic, not localized)**: REAL*4 program with REAL*8
  throughout the QC/ACM chain (`cdfchi` and every support function),
  `dstg`'s locals, `crandom3.inc`'s `g_dsum`/`g_ssum` accumulators
  (crandom3.inc:15–16), and `confls`'s `dble()` conversions. Faithful mode
  replicates the map site-by-site; the unit-by-unit audit is part of each
  port package.
- **Stateful constructs**: `block data` (1037–1089) initializes seeds and
  command defaults; `SAVE` statics in `dstg`, `day_gen`, `ranset`, and the
  ACM routines; `ENTRY` points in the ACM code (5151, 5316, 5485, 5623).
  Each becomes explicit owned state in Rust — no hidden statics. No
  computed GOTOs exist (verified).
- **Common-block aliasing**: shared-memory views across module boundaries
  (§2.9).
- **QC-coupled trajectories**: a QC rejection consumes extra RNG draws;
  porting the deviates without the QC chain produces silently divergent
  streams (§1).
- **Transcendentals**: libm ULP differences bifurcate trajectories at
  occurrence branches; pin both sides (Rust `libm` crate; pinned-libm
  reference build).
- **FMA contraction**: gfortran contracts by default; the reference build
  disables it, with flags recorded in fixture provenance.
- **Formatted output**: Fortran `FORMAT` rounding differs from Rust
  formatting; trajectory acceptance is on in-memory values, and the `.cli`
  text writer gets its own byte-level fixture gate.
- **Sequence bifurcation**: the fixture differ must report
  first-divergent-day/variable; aggregate statistics cannot localize a
  transcription error.
- **Dead-code candidates**: `nrmd` (source's own comment) and `chitst`
  (all calls commented). Ratification confirms; dead code is recorded, not
  ported.
