# Spine Handoff — Stage S → Stage C

Author: Claude Code (Stage S executor), 2026-07-09.

## What the spine established

- `modes.rs`: `generation_setup` (main:865-902, cold-start surface),
  `day_gen` (the production day loop with typed `DailyRow` sink,
  `DayGenState` SAVE, `DayGenExit::Stop` = the moveto-225 protocol),
  `GenState` bundle. `observed.rs`: `PrnReader` (`(15x,3i5)`,
  CRLF-indifferent, fail-closed). `ccl1.rs`: the monthly grids with
  the per-year zeroing helper.
- `tests/modes_identity.rs`: the cold-start replay (sample +
  `#[ignore]` full). Expectation rows are derived from the cg/sd/wg
  captures (F→C and th·CLT transcribed with citations).

## Stage C work

1. Extend the `#[ignore]` cold-start gate to the full 24-case matrix
   (the established R1 precedent; year plans from each case's
   B-lines).
2. `.prn` edge tests: short records (PAD), blank fields (→ 0),
   non-numeric fail-closed, CRLF vs LF equivalence.
3. All gates, exit codes direct (the six-suite acceptance list in
   gate-results.md of item 6 plus `modes_identity`).

## Named hazards

- The truncated/padded stop semantics differ (mid-year EOF vs
  year-end `q_gen_started`) — the full-matrix extension must assert
  each case ends exactly at its capture's last day (the sample gate's
  `checked == expect.len()` pattern).
- `DayGenState.q_gen_started` persists across years — construct once
  per run, never per year.
- Single-storm `nbt = ntd1 = ida` from the B-line; the quirky
  iopt-4/7 `nt` leap test (`wxr_gen:3759-3761`) is NOT needed until
  item 8 ports `jdt`-based date derivation — the harness reads the
  Julian day directly from the capture.
