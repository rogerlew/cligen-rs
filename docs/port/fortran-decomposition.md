# CLIGEN 5.32.3 Fortran Decomposition — First Pass

Status: Draft (first pass)
Evidence mode: Static — program-unit inventory, include-file listing, and
targeted reads of `RANDN`, `DSTG`, the main-program header/changelog, and
the storm-machinery changelog. Interior logic of most units has **not**
been read line-by-line yet; cluster assignments below are from unit names,
header comments, and the changelog, and are ratified or corrected by the
decomposition work package (ROADMAP item 2).
Source: `reference/cligen532/cligen.f` (7,657 lines) + 13 `.inc` files.

## 1. Shape of the program

One Fortran 77 file, one implicit main program (argument parsing and mode
dispatch, roughly lines 420–985), ~30 subprograms, 13 common-block include
files. The code is the C. R. Meyer recode (1999–2004, versions 4.x → 5.2x)
whose own header states the intent: "Recoded by the WEPP F-77 Coding
Conventions. The logic is greatly simplified; the structure of the code is
much improved; and the in-line documentation is greatly expanded." The
in-line changelog (lines ~40–470) is dense and candid — it documents the
storm-duration/`DSTG` bug history and constant changes — and is itself a
port asset: a ready-made list of behaviors that need pinned tests.

Two consequences of the Meyer recode matter for the port: the units are
small and single-purpose (the operator's "should not suck" assumption is
confirmed by inspection so far), and the program carries **built-in
statistical self-tests** (`chitst`, `ks_tst`, `conflm`, `confls`) that
validate generated distributions at run time — a free second validation
instrument for the port.

## 2. Program-unit inventory by functional cluster

Line numbers refer to `reference/cligen532/cligen.f`.

### 2.1 RNG and random deviates

| Unit | Line | Role (evidence) |
|---|---|---|
| `randn` | 1980 | Uniform (0,1). **Pure integer arithmetic** — 4-integer seed with carries, uniform assembled from four `float(k)` f32 multiply-adds; range-check rejection loop. Read in full: trivially bit-replicable. |
| `dstn1` | 1789 | Standard normal deviate (from uniforms). |
| `dstg` | 1651 | Gamma deviate via rejection sampling — drives `alpha_0.5` peak-intensity ratio. **Contains REAL*8 islands** (`double precision fu, xx`). Long QC/bug history in the changelog. |
| `ranset` | 4002 | Seed initialization per simulation. |
| `nrmd` | 2123 | Normal-deviate related (unread; name + position). |

### 2.2 Daily stochastic core

| Unit | Line | Role (evidence) |
|---|---|---|
| `clgen` | 1094 | The daily generation loop (precip occurrence/amount, temperatures, radiation, dew point); header says it calls `RANDN` and `DSTN1`. |
| `alph` / `alphb` | 985 / 3817 | `alpha_0.5` (ratio of max 30-min to total rainfall) — `alphb` is the Bofu Yu 1999 rewrite making intensity latitude-responsive. |
| `r5mon` / `r5monb` | 1904 / 3898 | Monthly max-.5-hour rainfall statistics (paired original/Yu variants like `alph`/`alphb`). |

### 2.3 Storm shape and event machinery

| Unit | Line | Role (evidence) |
|---|---|---|
| `timepk` | 2188 | Time-to-peak within storm. |
| `sing_stm` | 3325 | Single-storm mode. |
| `wxr_gen` | 3589 | Weather-generation variant mode (unread). |
| `day_gen` | 2971 | Observed-mode day generation (`-O`; the 5.323 EOF fix lives here). |

This cluster plus `dstg`/`alphb` is the **augmentation surface** for storm
duration/intensity derivation and NOAA design-storm curves — and the part
of the code with the most documented historical churn ("Storm duration was
getting hosed"; duration constant 4.607 → 9.210; `DSTG` gamma QC saga).

### 2.4 Station parameters and monthly-to-daily interpolation

| Unit | Line | Role (evidence) |
|---|---|---|
| `sta_dat` / `sta_name` / `sta_parms` | 2240 / 2486 / 2656 | Station `.par` reading, station selection, parameter handling. |
| `lintrp` | 7252 | Linear interpolation. |
| `fouri1` / `fouri2` | 7338 / 7387 | Fourier interpolation of monthly parameters to daily values. |
| `ryf1` / `ryf2` | 7424 / 7545 | Interpolation companions (unread). |

### 2.5 Modes, options, output

| Unit | Line | Role (evidence) |
|---|---|---|
| main program | ~420–985 | `getarg` argument parsing, `-` options, usage text (line 784), mode dispatch. |
| `opt_calc` / `usr_opt` | 3196 / 3497 | Option handling / interactive menus. |
| `clmout` | 1516 | Climate output writing (interactive viewing per its format strings). |
| `header` | 2153 | Output header. |

### 2.6 Built-in QC statistics

| Unit | Line | Role |
|---|---|---|
| `chitst` | 4342 | Chi-square test on generated populations. |
| `ks_tst` | 4453 | Kolmogorov–Smirnov test. |
| `conflm` / `confls` | 4589 / 4650 | Confidence limits on mean / on variance. |

### 2.7 Calendar

| Unit | Line | Role |
|---|---|---|
| `jdt` / `jlt` | 1817 / 1846 | Julian-date utilities. The leap-year surface (an augmentation target) lives here and in the callers' year loops. |

### 2.8 Common blocks (13 includes → typed state)

`cbk1/3/4/5/7/9.inc`, `ccl1.inc`, `cinterp.inc`, `command6.inc`,
`crandom.inc`, `crandom3.inc`, `csumr.inc`, `ctap2.inc`. Each becomes a
named struct; the mapping (which units read/write which block) is a
deliverable of the decomposition work package, not this first pass.
`crandom*/command6/csumr/cinterp` names suggest: RNG seed state, parsed
command options, QC accumulators, interpolation state.

## 3. Proposed Rust module map (to ratify in ROADMAP item 2)

```text
crates/cligen/src/
  calendar.rs        jdt, jlt (+ leap-year extension point)
  rng.rs             randn, ranset, seed state (crandom*.inc)
  deviates.rs        dstn1, dstg, nrmd  (precision map: f64 islands per source)
  par/               sta_parms lineage: typed par model, parse/serialize
  monthlies.rs       lintrp, fouri1/2, ryf1/2
  daily.rs           clgen, alph(b), r5mon(b)
  storm.rs           timepk, sing_stm, dstg consumers (duration/Ipeak)
  observed.rs        day_gen (.prn; parquet extension point)
  output/            clmout/header lineage: .cli text; .cli.parquet later
  qc.rs              chitst, ks_tst, conflm, confls
  profile.rs         generation profiles + provenance (extension, no Fortran basis)
```

## 4. Port order (dependency spine)

1. `calendar` + `rng` + `deviates` — identity-testable in isolation; the
   whole trajectory depends on them.
2. `par` + `monthlies` — deterministic input path; fixture-comparable
   against Fortran-parsed values.
3. `daily` — first end-to-end stochastic surface.
4. `storm` — the contested machinery, ported against pinned tests derived
   from the changelog's known behaviors.
5. `observed` — `day_gen` (the operator has already debugged this path in
   the Fortran).
6. `output` — `.cli` text writer; end-to-end faithful parity gate.
7. `qc` — port the self-tests; run them as a cross-check on both engines.

## 5. Known port hazards (established in the founding discussion)

- **Precision map**: REAL*4 program with REAL*8 islands (`dstg` proves
  they exist); faithful mode replicates the map — a mechanical audit per
  unit is part of each port package.
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
