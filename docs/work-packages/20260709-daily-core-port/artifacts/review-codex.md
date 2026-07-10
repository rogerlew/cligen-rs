# Stage R1 Review — Codex

Reviewer: Codex
Date: 2026-07-09
Evidence mode: Static source-to-port review + Ran gates and capture checks
Status: `R1-COMPLETE` — three findings accepted and fixed; no open findings

## Scope and method

Reviewed the complete daily-core package, including the Stage S spine and
Stage C completion, against the vendored authority:

- `cligen.f:1094-1515` (`clgen`), including interpolation dispatch,
  month-boundary/RANSET order, precipitation, both temperature branches,
  dew-point clamps, and radiation clamps;
- `cligen.f:2020-2119` (`windg`), `3817-3895` (`alphb`), and
  `3898-3996` (`r5monb`), plus the `day_gen:3086-3141` call sites;
- common-block layouts `cbk1.inc`, `cbk3.inc`, `cbk4.inc`, `cbk5.inc`,
  `cbk7.inc`, `cbk9.inc`, and SPEC-GENERATOR-CORE rev 6;
- the three new pinned transcendentals, tap schemas/digests, committed
  sample fixtures, ignored full-stream replays, and formal quality gates.

## Findings and dispositions

1. **Medium — the ignored “full” daily gates covered only the 10-case
   committed-sample selection, not the 24-run capture matrix.** The handoff
   requires full-matrix ignored gates (`spine-handoff.md:60-62`), and the
   tap manifest distinguishes 10 committed cases from 24 full captures
   (`tap-schema.md:52-68`). At pre-review commit `bd14748`, all three
   ignored loops reused the 10-entry `CASES` array. **Accepted and fixed:**
   `daily_identity.rs:71-167` now declares all 24 `FULL_CASES`, and the
   ignored combined, standalone-unit, and `clgen` loops use it
   (`daily_identity.rs:797-855`). Ran result: 189,207 daily calls, 72,130
   `alphb` calls, and 24 `r5monb` snapshots, all bit-identical.

2. **Low — state/specification prose still described already-landed daily
   fields as future work.** At pre-review commit `bd14748`, `cbk1.rs:10-12`
   said `wv`/`th`/`pi2`/`tdp` would arrive when `windg` ports, while the
   fields were already present; SPEC-GENERATOR-CORE likewise called
   `Cbk4State` only the `iopt` slice and described `Cbk3State` as deferred.
   **Accepted and fixed:** `cbk1.rs:10-12` now leaves only `ang` for the
   storm package, and SPEC-GENERATOR-CORE rev 6 lines 9-33 and 56-62
   describe the current common-block homes and the historical `fouri2`
   exception accurately.

3. **Low — the draw-order characterization and combined harness did not
   fully spell out `day_gen`'s wet-day protocol.** The source first
   normalizes `r(ida) <= 0` to zero (`cligen.f:3114-3116`), calls `alphb`
   once for positive rain (`3117-3119`), and calls it a second time for
   `iopt >= 4` (`3138-3141`). The Stage S artifact summarized this as one
   draw on wet days, and the first combined harness used only an equivalent
   `r > 0` test for existing captures. **Accepted and fixed:** the
   characterization now records the exact one-or-two-call protocol
   (`clgen-draw-order-characterization.md:73-78`), and the harness
   transcribes normalization and both calls (`daily_identity.rs:673-695`).

## Review conclusions

### Transcription fidelity

- `interp_val` preserves the source's four-way branch arithmetic and
  parameter-specific call order. The expanded full matrix exercises direct,
  linear, Fourier, and Yoder-Foster paths.
- The observed-temperature branch retains the source's overwritten
  `twiddle`/`twiddld` calculations (`daily.rs:218-236` versus
  `cligen.f:1322-1341`); generated temperature ordering matches
  `cligen.f:1414-1445`.
- Solar `ch >= 1` / `ch <= -1` branches and radiation upper/lower clamps
  match `cligen.f:1189-1202,1504-1507`. Precipitation skew and wind-speed
  skew mutate station state in place as required (`daily.rs:141-160` and
  `433-440`).
- `windg`, `alphb`, and `r5monb` preserve REAL*4 expression order and the
  source literals. `r5monb` trusts the live body rather than its stale
  common-block comments and writes only `wi`.

### Precision and state translation

- Static search found no f64 local, standard float transcendental, SAVE,
  static generator state, or fast-math configuration in the four daily
  units. The only f64 work reached by `alphb` is `dstg`'s source-declared
  island.
- Common storage remains single-home: `Cbk3State` owns `j`/`ida`,
  `Cbk5State` owns `r`/`sml`, and `Cbk9State` now owns
  `wi`/`ab`/`ab1`/`rn1`/`r1`. `DstgState` and `RansetState` remain explicit
  caller-owned SAVE translations.
- SPEC-GENERATOR-CORE rev 6 matches the implemented state and free-function
  shapes. No silent profile extension was introduced.

### Pinned transcendental provenance

- `tanf_pinned` and `acosf_pinned` are fdlibm/SunPro float-lineage
  transcriptions covered by the full notice in `libm_pinned.rs` and the
  preserved `fdlibm-sunpro-LICENSE.txt` artifact. The daily census records
  zero mismatches over 7,833,328 and 8,290,688 swept inputs respectively.
- `expf_pinned` is the ARM optimized-routines N=32 algorithm, covered by
  the module's ARM attribution and the preserved
  `arm-optimized-routines-LICENSE.txt` (verified SHA-256
  `650afbf...caf9346`). The daily census records 0/8,551,812 mismatches.
- `logf_pinned` was already adjudicated and licensed by the RNG/deviates
  package. No unadjudicated transcendental entered a faithful path.

### Test and evidence alignment

- Ran SHA-256 verification of all 96 manifest records (`cg`/`wg`/`ab`/`r5`
  across 24 cases) against the local capture: 96/96 matched.
- Committed tap samples call each production unit before the combined
  harness; ignored release tests cover the full capture and assert entry and
  exit state record-by-record. The combined replay makes `k7` and `v9`
  internal while leaving only the unported `timepk` stream `k10` external.
- Format, clippy, tests, all ignored release suites, llvm-cov, and CRAP gates
  passed with direct exit 0. CRAP analyzed 141 functions; none exceed 30.

Stage R2 remains assigned to Claude Code. This review does not close the
package.
