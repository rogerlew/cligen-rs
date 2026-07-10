# Stage R1 Review — Codex

Reviewer: Codex
Date: 2026-07-09
Evidence mode: Static source-to-port review + Ran gates and capture checks
Status: `R1-COMPLETE` — four Medium findings accepted and fixed; no open R1
findings

Stage R2 remains assigned to Claude Code. This review does not close the
package.

## Scope and method

Reviewed the complete observed-mode/day-loop package, including the Stage S
spine and Stage C completion, against the vendored authority:

- `cligen.f:865-902`, the main-program generation setup and cold-start draw
  order;
- `cligen.f:2971-3195`, especially the observed read block at 3067-3083,
  `th * clt`, ccl1 writes, the Fahrenheit-to-Celsius seam, unit-7 operands,
  loop exit, and saved stop flag;
- `cligen.f:3758-3781`, the year-plan and ccl1 zeroing logic transcribed by
  the harness, plus `ccl1.inc` storage;
- `modes.rs`, `observed.rs`, `ccl1.rs`, the core/observed interface specs,
  the 24-capture endpoint table, edge vectors, and all formal gates.

## Findings and dispositions

1. **Medium — `generation_setup` omitted the source's unconditional
   `nt = 0`.** The source writes `/bk4/::nt` at `cligen.f:881`, but the
   Stage S function retained whatever value arrived in `Cbk4State`.
   Cold-start replay stayed green because its caller constructed default
   state with `nt == 0`, leaving the public setup surface under-specified.
   **Accepted and fixed:** `generation_setup` now mutates `bk4.nt` at the
   source-order point between `ab1` and `pit`; a focused regression starts
   with `nt = 1` and asserts the reset.

2. **Medium — missing observed input caused an undocumented panic.** The
   public `day_gen` signature models the mode-dependent reader as an
   `Option`, but `iopt = 6` used `expect` when it was absent. That violated
   the typed, fail-closed input posture and the function's stated error
   surface. **Accepted and fixed:** `PrnError::MissingStream` is returned
   before any daily generation; its display and branch are directly tested.

3. **Medium — the observed/day-loop interfaces had no active specification.**
   Stage S landed `PrnReader`, `DayGenState`, `GenState`, `DailyRow`, and
   `day_gen` while the registry still marked SPEC-OBSERVED-INPUT planned and
   SPEC-GENERATOR-CORE still called `modes` future work. This conflicted with
   ADR-0001's interface rule. **Accepted and fixed:** SPEC-OBSERVED-INPUT rev
   1 now defines the legacy grammar, errors, sentinel/EOF protocol,
   precision, and A3 extension boundary; SPEC-GENERATOR-CORE rev 8 records
   current ownership and the `DailyRow` seam; the registry marks the
   compatibility surface active.

4. **Medium — the cold-start acceptance header overstated direct tap
   coverage.** It claimed the modes gate reproduced complete cg/wg/sd/tp
   tap streams, but the harness directly compares the complete `DailyRow`
   stream reconstructed from cg/wg/sd. The earlier unit suites, not this
   harness, retain the finer internal and tp-record assertions. **Accepted
   and fixed:** module/package language now states the exact evidence
   boundary, and row-derivation comments cite the F-to-C, wind-direction,
   and unit-7 operand source lines.

No R1 finding remains open. No file under `reference/cligen532/` was
modified.

## Required-focus review

### Transcription fidelity

- The observed block preserves source order: `msim = nsim = 0`; EOF arm;
  saved-flag assignment; individual `nsim`/`msim` sentinel flags; then
  unconditional precipitation and temperature assignments. The
  counterintuitive source rule is retained: `q_gen_started` observes
  `irida` or `itmxg`, not an `itmng`-only sentinel.
- `PrnReader` implements `(15x,3i5)` with columns 16-30, ASCII-space
  `BLANK='NULL'`, short-record padding, and typed failure. LF and CRLF
  records produce identical values. EOF returns `DayGenExit::Stop` before
  `jlt`; sentinel-triggered generation returns Stop at the natural year end.
- `windg` precedes the in-place `th = th * 57.296` conversion. `prcip`,
  `tgmx`, and `tgmn` are written before temperature conversion; `radg` is
  written after `tmxg`, `tmng`, and `tdp` convert to Celsius. The emitted
  `DailyRow` follows the source's unit-7 operand order exactly.
- Main setup preserves the source draw/order sequence, including
  `r5monb`, `ab`/`ab1`, the restored `nt = 0`, pinned latitude sin/cos,
  wet/dry selector, `rn1`, six rolling warms, and final `msim`/`nsim`.

### Precision and state translation

- Static search found no f64 faithful value, standard float transcendental,
  fast-math configuration, static generator state, or interior mutability in
  `modes.rs`, `observed.rs`, or `ccl1.rs`. Main setup routes f32 sin/cos
  through pinned implementations; `day_gen` adds only source-order f32
  scaling and conversions.
- `DayGenState.q_gen_started` is the caller-owned translation of the sole
  SAVE local and is constructed once per run, outside yearly calls.
  `GenState` owns each common/unit state once; `Ccl1State` is the sole owner
  of `/cl1/` and its per-year reset overwrites every cell.

### Test and evidence alignment

- Stage C enumerates all 24 capture cases, including seed-17 and every
  interpolation variant. Each case asserts its independent capture count,
  final `(year, month, day)`, emitted endpoint, and final `DayGenExit`.
  The harness now rejects extra rows after the capture instead of ignoring
  them.
- Ran result: 189,207 `DailyRow`s bit-identical from zero injected state.
  Fish Springs padded runs end `(2026, 12, 31, Stop)` via saved sentinel
  state; truncated runs end `(2026, 7, 7, Stop)` via EOF; Mt. Wilson ends
  `(2010, 12, 31, YearComplete)` after its requested natural year.
- Row derivation cites `day_gen:3104` for `th * CLT`, 3110-3112 for f32
  F-to-C conversion, and 3175 for unit-7 field order. Earlier release gates
  remain the direct assertion surface for internal cg/wg/sd/tp/ab records.
- Format, clippy, ordinary tests, all eight ignored release tests, coverage,
  CRAP, and Markdown commands exited 0 directly. CRAP analyzed 156
  functions with none above 30.

## R1 disposition

Stage C and R1 are ready for the independently assigned Stage R2 review.
The package remains open and is not moved off the roadmap by this review.
