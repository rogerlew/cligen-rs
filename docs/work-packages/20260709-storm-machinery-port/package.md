# Storm Machinery Port

Status: `STAGE-C-R1-COMPLETE` (Stage C and Codex R1 landed 2026-07-09;
Claude Code Stage R2 remains open)
Stage C/R1 outcome: typed `sing_stm` intake and fail-closed deferrals
landed; the ignored storm replay now covers all 24 captures (189,207
days + 36,065 timepk calls bit-identical); all 48 sd/tp manifest
digests matched; one Low documentation finding was fixed; all gates
exited 0 directly.
Stage S outcome: characterizations recorded (chain lives in day_gen;
sing_stm is intake-only; transient-infinity path; F→C seam); 24-run
capture 12/12 noninvasive; timepk + wet_day_duration + storm_block
ported with the day-loop replay green (80,906 days + 15,468 timepk
calls bit-identical, all ten seed streams asserted per record); no
new transcendentals (alog already pinned).
Date: 2026-07-09
Evidence mode: Static + Ran (Stages S/C/R1; see artifacts)
Execution model: staged, two executors (the item-3/4/5 pattern) —
Claude Code writes the design-setting spine; Codex completes and runs
gates; each reviews the other; Claude closes with Stage R2.

## Objective

Port the storm machinery — ROADMAP item 6: `timepk` (2188-2236, the
time-to-peak draw that finally closes the `zx` batch column and the
`k10` stream), the **duration/Ipeak chain** embedded in `day_gen`'s
storm block (`cligen.f:3114-3176`: `dur = 3.99/(−2·alog(1−r1))`,
`xr`/`tpr`/`r5p`/`xmav` with every clamp and the `iopt` 4/7
overrides — scope discovery at scaffold: the roadmap's "duration/Ipeak
chain" lives here, not in `sing_stm`), and `sing_stm` (3325-3493 —
characterized at scaffold as **intake/file-open plumbing only**: the
interactive storm-parameter reads and the unit-7/8 open-with-overwrite
protocol; no numeric surface).

This is the contested code (decomposition §2.3: "Storm duration was
getting hosed", the 4.607 → 9.210 → 3.99 coefficient history) — the
port pins the *live* 5.32.3 behavior; the changelog variants are the
A5 augmentation surface, not this package.

## Acceptance (whole package)

- **`timepk` per-call taps**: entry `iopt`/`dax`/`k10`, the `z` source
  (fresh `randn(k10)` under `iopt = 6`, `zx(dax)` otherwise), and the
  result — bit-identical across the fixture matrix.
- **Storm-day chain taps**: one record per storm-branch day at the
  unit-7 write seam (`jd mo iyear` + `xr dur tpr xmav` + the second
  `alphb`'s `r1`) — bit-identical through the combined day-loop
  replay. This seam is deliberately the `.cli` daily row's numeric
  input surface — pre-work for item 8.
- **`sing_stm`**: typed non-interactive intake (the fixture stdin
  values become typed arguments) with characterization; interactive
  prompts and the overwrite dialog get the `sta_name` treatment.
- **Non-invasiveness**: patched-binary golden `.cli` outputs
  byte-identical, all 12.

## Stages

### Stage S — Spine (Claude Code)

1. Phase A: storm-chain characterization (which fixture modes exercise
   which branches — `iopt ≥ 4` includes continuous mode 5, so the
   chain and `timepk` run on every wet day of every fixture; `iopt 7`
   is fixture-unreachable → fail-closed-or-defer with evidence; the
   live `tap4 = 0.0` dead store at 3153 documented). Transcendental
   census: `alog` only — already pinned (`logf_pinned`), no new
   adjudications expected.
2. Tap schema + capture on a copied tree (timepk per-call + storm-day
   records), 24-run matrix, non-invasiveness gate.
3. Port `timepk` + the chain as `storm.rs` pure functions (chain
   signature owns `dur` as a value; `Ccl1State` stays with modes/item
   8). State: `Cbk4State` gains `dtp`/`dmxi` (block data 1065-1066);
   `tymax` is a main-program constant table (`cligen.f:602`), cited in
   `storm.rs`. Replay tests extend the item-5 combined day loop.
4. Spine handoff + Codex kickoff (repo/branch/push-target explicit).

### Stage C — Completion + gates (Codex)

`sing_stm` typed intake port on the characterized paths; full-matrix
`#[ignore]` gates; all gates with direct exit checks.

### Stage R1 — Cross-review (Codex)

Transcription fidelity (the clamp cascade and iopt-override order are
the risk surface), precision-map compliance (REAL*4-clean expected),
state-translation compliance, test/evidence alignment.
`artifacts/review-codex.md`; accepted findings fixed before handback.

### Stage R2 — Final sanity review (Claude Code)

Gates re-run independently; targeted reads (the iopt-4 override path
against the single-storm goldens; the timepk observed-mode fresh-draw
branch); R1 disposition; close or bounce.
`artifacts/final-review-claude.md`.

## Execution & dispatch

Both executors work on **`main`**: start from current `origin/main`,
push to `main`. No side branches (AGENTS.md branch discipline).

## Scope exclusions

No `day_gen`/`wxr_gen` orchestration port (modes package — the chain
is extracted as pure functions the modes port will call, exactly as
the item-5 replay harness stands in for `day_gen`). No `.cli`
emission (item 8; the storm-day tap seam feeds it). No changelog
variants (4.607/9.210 coefficients, `alph`/`r5mon`) — A5 surface.

## Authority

`reference/cligen532/cligen.f`: `timepk` 2188-2236, the `day_gen`
storm block 3114-3176, `sing_stm` 3325-3493; `tymax` main:602,
`dtp`/`dmxi` block data 1065-1066; the item-3/4/5 tap captures.

## Gates

Stage S ports carry bit-identity tests before Stage C begins; Stage C
runs the full suite, exit codes verified directly; reviews
dispositioned before close; final close by Stage R2.

## Exit criteria

`EXECUTED-COMPLETE`: `timepk` and the chain bit-identical across the
fixture matrix through the combined replay; `sing_stm` intake
characterized and ported on the live paths; both reviews
dispositioned; gates green. Holds: an `iopt 7` semantics question the
source + fixtures cannot settle (name it and defer fail-closed).

## Artifacts

- `artifacts/storm-chain-characterization.md`
- `artifacts/tap-schema.md` (+ patch, digests)
- `artifacts/spine-handoff.md`, `artifacts/kickoff-codex.md`
- `artifacts/review-codex.md`, `artifacts/final-review-claude.md`
- `artifacts/gate-results.md`
