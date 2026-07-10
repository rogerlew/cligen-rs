# Daily Stochastic Core Port

Status: `EXECUTED-COMPLETE` (Stage R2 closed 2026-07-09;
`artifacts/final-review-claude.md`)
Stage S outcome: Phase A characterizations recorded (clgen draw-order/
month-boundary protocol; transcendental census — libm-crate
tanf/acosf/expf all REJECTED on sweep evidence, three pinned
transcriptions landed at 0/24.7M mismatches); 24-run tap capture with
12/12 golden non-invasiveness; `clgen` ported (decomposed, CRAP-clean)
with the sequential replay gate green at 80,906 calls bit-identical;
new Cbk3State/Cbk5State + cbk1/cbk4/cbk7 extensions
(SPEC-GENERATOR-CORE rev 5).
Date: 2026-07-09
Evidence mode: — (per stage on execution)
Execution model: staged, two executors (the item-3/item-4 pattern,
operator-ratified) — Claude Code writes the design-setting spine; Codex
completes and runs gates; each reviews the other; Claude closes with
Stage R2.

## Objective

Port the daily stochastic core — ROADMAP item 5, ratified port-order
step 4: `clgen` (the daily generator: precip occurrence/amount,
temperatures, radiation, dew point), `alphb` (α₀.₅ intensity ratio,
Bofu Yu latitude-responsive rewrite), `r5monb` (once-per-run monthly
max-.5-h statistics), and `windg` (wind generation) → `daily.rs` per
the ratified module map. This is the first package whose units consume
the full existing surface at generation time: seeds/`randn`/`dstn1`/
`dstg`/`ranset` (item 3) and `fouri2`/`ryf2`/`lintrp` + station state
(item 4).

State extensions per the incremental-block pattern
(SPEC-GENERATOR-CORE): new `Cbk3State` (`{j, ida}` — the live `/bk3/`
slice; note `j` is a loop index in COMMON) and `Cbk5State`
(`{r(366), sml}`); `Cbk7State` gains the generation scratch members
(`ra`, `tmxg`, `tmng`, `rmx`, `yls`, `ylc`, `pit`, `nsim`, `msim`,
`l`); `Cbk4State` gains the slices these units read (`mo`, …);
`Cbk1State` gains `wv`/`th`/`pi2`/`tdp`. The spine settles each
block's final field list from the source census and records it.

## Acceptance (whole package)

Bit-identity, not tolerance, wherever the tap machinery can reach it:

- **Per-day generated surface**: per-call taps for `clgen` (the daily
  values and state it writes: `r(ida)`, `tmxg`, `tmng`, `ra`, dew
  point, and the rolling-pair state), `windg` (`wv`, `th`), and
  `alphb` (`r1`), verified per-record across the full fixture matrix
  (both hemispheres — jeogla exercises `alphb`'s southern-latitude
  seasonal inversion).
- **`r5monb` setup snapshot**: bit-exact post-call dump of everything
  it writes (once per run, the par-snapshot pattern).
- **Draw-order oracle (free cross-check)**: the item-3 `rn`/`n1`/`dg`
  full streams already record every uniform/normal/gamma draw with
  self-identifying seed state; a ported `clgen`/`windg`/`alphb`
  day-sequence replay must consume draws in exactly the captured
  order. Any divergence in draw count or order desynchronizes the
  seed-state assertions immediately.
- **Non-invasiveness**: the tap patch (copied build tree,
  `reference/cligen532/` read-only, hard rule) reproduces all 12
  golden `.cli` files byte-identically.

## Stages

### Stage S — Spine (Claude Code)

1. **Phase A characterizations FIRST, recorded as artifacts**:
   (a) `clgen`'s draw-order and month-boundary protocol — which seed
   streams are consumed where, the `mox` write + `ranset` call
   protocol at month changes (`cligen.f:1204-1209`), and the
   `nsim`/`msim` observed-mode gating of each generation branch;
   (b) the f32 transcendental census for all four units (known
   already: `exp` at `alphb:3852`; `clgen`'s precip-amount and
   radiation math to be enumerated) — each new function/domain gets
   the §1.3 empirical adjudication against captured values before
   use (`libm` crate first, pinned transcription on divergence — the
   `atanf` precedent).
2. **Tap schema + capture** (extends the item-3/4 patch pattern):
   per-call `clgen`/`windg`/`alphb` output taps + the `r5monb`
   snapshot, captured across the 12 golden invocations (plus
   capture-only variants only if a branch the goldens never reach
   needs pinning — characterize first). Non-invasiveness gate as
   above.
3. **Port `clgen`** — the design-setting unit (state threading across
   seven common blocks, draw order, `ranset` integration, interp-mode
   dispatch) — with per-day bit-identity tests against its tap
   stream, plus the state-struct extensions and their
   SPEC-GENERATOR-CORE recording. Decompose along source-internal
   structure to hold CRAP ≤ 30 (the unit is ~420 source lines).
4. **Spine handoff + Codex kickoff** authored at spine completion,
   citing landed code and the remaining unit list.

### Stage C — Completion + gates (Codex)

Within the spine's patterns: `alphb` (3817-3897), `r5monb`
(3898-4001), `windg` (2020-2122); the day-sequence replay harness that
drives clgen/windg/alphb in captured order (day_gen itself stays with
the modes package); full-matrix identity tests; all gates (fmt, clippy
`-D warnings` with direct exit checks, `cargo test`, full-stream
`--ignored` release taps, llvm-cov + `cargo crap --fail-above`).

### Stage R1 — Cross-review (Codex)

Independent review of the whole package including the spine:
transcription fidelity against source lines, precision-map compliance
(REAL*4-clean per the census — no SAVE and no f64 site exists in any
of the four units; any found is a finding), state-translation
compliance, test/evidence alignment, and any new pinned-transcendental
provenance. Findings to `artifacts/review-codex.md`; accepted findings
fixed before handback.

### Stage R2 — Final sanity review (Claude Code)

Gates re-run independently; targeted source-vs-port reads of the
highest-risk surfaces (clgen's month-boundary/ranset protocol, alphb's
hemisphere handling, one transcendental adjudication); R1 disposition
review; close or bounce. `artifacts/final-review-claude.md`.

## Execution & dispatch

Both executors work on **`main`**: start each stage from current
`origin/main` and push to `main`. No side branches for package work
(AGENTS.md §Workflow branch discipline; item-4 R2 reconciliation
precedent). Stage S dispatch prompt: `artifacts/kickoff-spine.md`
(paste-ready). Stage C kickoff is authored by the spine at its
completion.

## Scope exclusions

- No `timepk`/`sing_stm` (item 6 storm machinery). No
  `day_gen`/`wxr_gen`/`opt_calc`/`usr_opt` orchestration (modes
  package) — the day-sequence replay harness is test scaffolding, not
  a `day_gen` port. No `.cli` emission (item 8). Dead units `alph`
  and `r5mon` stay dead (ratified §2.9).

## Authority

- `reference/cligen532/cligen.f` unit lines per the ratified
  decomposition §2.2: `clgen` 1094-1515, `windg` 2020-2122, `alphb`
  3817-3897, `r5monb` 3898-4001; `cbk3.inc`/`cbk5.inc` layouts; the
  item-3/item-4 tap captures as draw-order and state oracles.

## Gates

- Stage S ports carry bit-identity tests before Stage C begins.
- Stage C: the full gate suite, exit codes verified directly.
- Reviews dispositioned before close; final close by Stage R2.

## Exit criteria

`EXECUTED-COMPLETE`: all four units bit-identical against their tap
streams across the fixture matrix; the day-sequence replay consumes
the captured draw streams exactly; state extensions recorded in
SPEC-GENERATOR-CORE; both reviews dispositioned; gates green. Holds: a
transcendental that cannot be pinned to the reference runtime within
the REAL*4 map (stop and characterize — the §1.3 escalation path); a
clgen branch unreachable from the fixture matrix that cannot be
characterized fail-closed (name it).

## Artifacts

- `artifacts/kickoff-spine.md` (authored at scaffold)
- `artifacts/clgen-draw-order-characterization.md`
- `artifacts/transcendental-census.md`
- `artifacts/tap-schema.md` (extension), tap patch + manifest
- `artifacts/spine-handoff.md`, `artifacts/kickoff-codex.md`
- `artifacts/review-codex.md`, `artifacts/final-review-claude.md`
- `artifacts/gate-results.md`
