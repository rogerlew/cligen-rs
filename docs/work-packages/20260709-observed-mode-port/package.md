# Observed Mode / Day-Loop Driver Port

Status: `STAGE-S-COMPLETE` (spine landed 2026-07-09; Stage C/R1 with
Codex next — `artifacts/kickoff-codex.md`)
Stage S outcome: day_gen/generation_setup/PrnReader/Ccl1State ported;
**cold-start replay green — 80,906 days with zero injected state**
(block-data seeds + burn + real inputs through the production driver);
EOF/sentinel stop semantics pinned by both fish-springs cases; no new
taps or transcendentals needed.
Date: 2026-07-09
Evidence mode: — (per stage on execution)
Execution model: staged, two executors (the item-3..6 pattern) —
Claude Code writes the design-setting spine; Codex completes and runs
gates; each reviews the other; Claude closes with Stage R2.

## Objective

Port ROADMAP item 7: `day_gen` (2971-3195) — the production day-loop
driver whose behavior every prior package's replay harness has been
imitating piece by piece — together with the observed-mode `.prn`
input path it embeds (the `(15x,3i5)` per-day read, the `9999`
sentinel → `nsim`/`msim` protocol, the 5.323 EOF fix via
`moveto = 225`, and the `q_gen_started` SAVE flag that persists
across years), the `Ccl1State` monthly-grid arrays, and the
main-program generation setup (`cligen.f:865-902`) needed for **cold
start**.

The prize: with `day_gen` ported, the acceptance harness no longer
injects any captured state — a run derives from block-data seeds +
burn + warm setup + the `.par`/`.prn` inputs alone, and every existing
tap stream (cg/wg/sd/tp, plus ab internally) must fall out
bit-identical. First full-trajectory replication from cold start.

## Acceptance (whole package)

- **Cold-start replay**: for each fixture case, drive the ported
  `day_gen` year by year (year plan `(iyear, ntd, nbt)` derived from
  the captured B-lines; the `wxr_gen` year loop itself is item 8) and
  assert the complete cg/wg/sd/tp streams with **zero injected
  state** — all seeds from block data (+`-r` burn), all rolling
  values from the ported warm setup, observed values from the real
  `ws.prn` files.
- **Typed daily rows**: `day_gen` emits the unit-7 row values
  (`jd mo iyear xr dur tpr xmav tmxg tmng radg wv th tdp`, with the
  in-place `th·clt` degree conversion) through a typed sink — item
  8's writer input, cross-checked against values reconstructed from
  the captures.
- **EOF/sentinel semantics**: the truncated and padded fish-springs
  cases pin the 5.323 EOF exit and the sentinel-fill path end to end.
- No new taps are needed — the existing 24-run captures already cover
  the entire surface; no new transcendentals are expected (`day_gen`
  adds only integer parsing and the `th·clt` multiply).

## Stages

### Stage S — Spine (Claude Code): characterization (`.prn` read
protocol, EOF/moveto, SAVE, `th·clt`, per-year `ccl1` zeroing,
single-storm `nbt = ntd1`); ports — `ccl1.rs` (`Ccl1State`),
`observed.rs` (typed `.prn` reader, fail-closed), `modes.rs`
(`generation_setup`, `day_gen` + `DayGenState`, `DailyRow`); the
cold-start replay for the 10 committed cases; handoff + kickoff.

### Stage C — Completion + gates (Codex): full 24-case cold-start
`#[ignore]` gates; `.prn` edge tests (short records, non-numeric
fail-closed); all gates, exit codes direct.

### Stage R1 — Cross-review (Codex): transcription fidelity (the
observed block's flag/assignment order; the moveto protocol;
`th·clt`), precision-map compliance, state-translation compliance
(`Ccl1State`, `DayGenState` SAVE), test/evidence alignment.

### Stage R2 — Final sanity review (Claude Code): gates re-run;
targeted reads (the sentinel/EOF block against both fish-springs
cases; cold-start setup vs main:865-902); R1 disposition; close or
bounce.

## Execution & dispatch

Both executors on **`main`**: start from current `origin/main`, push
to `main`. No side branches.

## Scope exclusions

No `wxr_gen`/`opt_calc`/`usr_opt`/program-dispatch port and no unit-7
FORMAT/file writing (item 8 — `DailyRow` is its input seam). No
`.prn` → parquet typing (A3).

## Authority

`cligen.f`: `day_gen` 2971-3195, main setup 865-902, the `wxr_gen`
year-plan lines 3758-3781 (read for harness fidelity, ported in item
8); `ccl1.inc`; the fixture `ws.prn` files and the 24-run captures.

## Gates

Stage S ports carry cold-start bit-identity before Stage C; Stage C
the full suite; reviews dispositioned; close by R2.

## Exit criteria

`EXECUTED-COMPLETE`: cold-start replay bit-identical across the full
matrix; EOF/sentinel cases pinned; `DailyRow` seam recorded for item
8; both reviews dispositioned; gates green. Holds: any cold-start
divergence traceable to un-ported main/orchestration state (name the
line and characterize).

## Artifacts

- `artifacts/daygen-characterization.md`
- `artifacts/spine-handoff.md`, `artifacts/kickoff-codex.md`
- `artifacts/review-codex.md`, `artifacts/final-review-claude.md`
- `artifacts/gate-results.md`
