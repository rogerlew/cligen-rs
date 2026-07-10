# Par Model + Monthlies Port

Status: `STAGE-S-COMPLETE` (spine landed 2026-07-09; Stage C/R1 with
Codex next — dispatch prompt at `artifacts/kickoff-codex.md`)
Stage S outcome: Phase A characterizations recorded (intake path,
round-trip adjudication → lexeme-preserving invariant); 24-run tap
capture with 12-golden non-invasiveness gate; SPEC-PAR active;
`ParFile`/`sta_parms`/`fouri1`/`ryf1` landed with the full-matrix
snapshot identity gate (4 stations × interp {0,1,2,3}) and byte
round-trip green; `Cbk7Seeds` renamed `Cbk7State`; `sinf_pinned` +
`atanf_pinned` adjudicated (`libm::atanf` rejected on captured 1-ULP
evidence — gate-results.md).
Date: 2026-07-09
Evidence mode: — (per stage on execution)
Execution model: staged, two executors (the item-3 pattern, operator-
ratified) — Claude Code writes the design-setting spine; Codex completes
and runs gates; each reviews the other; Claude closes with Stage R2.

## Objective

Port the station-parameter intake and monthly-to-daily interpolation —
ROADMAP item 4, ratified port-order step 3: `sta_dat`/`sta_name`/
`sta_parms`/`header` and the interpolators `lintrp`/`fouri1`/`fouri2`/
`ryf1`/`ryf2` — and establish **SPEC-PAR**, the typed `.par` model that
the A4 par-database/mutation work will later build on. This package
extends the common-block structs with the station fields
(`Cbk7Seeds` → the block's `rst`/`prw`/monthly arrays per the
incremental-block pattern; new `cinterp` state struct; `cbk1`/`cbk9`
slices as the units require).

## Acceptance (whole package)

Bit-identity, not tolerance, wherever the tap machinery can reach it:

- **Par-state snapshot**: after `sta_parms` (and its `fouri1`/`ryf1`
  setup calls) completes, the populated common-block state matches a
  bit-exact Fortran snapshot for each fixture `.par` (all four
  stations).
- **Interpolator streams**: per-call taps for the generation-time
  evaluators (`fouri2`, `ryf2`, `lintrp`) verified per-record across
  the full fixture matrix, same pattern as the item-3 `rn`/`n1`
  streams.
- **Round-trip target** (spine decision to confirm in Phase A): typed
  par parse → serialize reproduces the four fixture `.par` files
  byte-identically; if format quirks make byte round-trip unreachable,
  the spine characterizes exactly why and records the achievable
  invariant instead — no silent weakening.

## Stages

### Stage S — Spine (Claude Code)

1. **Tap schema + capture** (extends the item-3 tap patch pattern:
   recorded additive patch, copied build tree, `reference/` untouched,
   non-invasiveness gate = golden byte-identity): the par-state
   snapshot tap (bit-exact dump of the station/interp common state at
   the post-`sta_parms` seam) and per-call `fouri2`/`ryf2`/`lintrp`
   taps.
2. **SPEC-PAR** (registry: planned → active): the typed par model —
   format semantics, field units, the `rst`/`prw` EQUIVALENCE views
   (`cligen.f:2783-2787`), serialization, and the round-trip
   adjudication. This spec is load-bearing for A4; design it as the
   foundation, not a stopgap.
3. **Ports**: `sta_parms` (2656–2970: the parse + state distribution +
   EQUIVALENCE accessors) with `fouri1` (7338–7386) and `ryf1`
   (7424–7544) — both on `sta_parms`'s acceptance path, so they ride
   with the spine (the `ks_tst` precedent). State extensions:
   `Cbk7Seeds` gains the block's station fields (struct may warrant a
   rename to `Cbk7State`; spine decides and records), new
   `CinterpState`, minimal `cbk1`/`cbk9` slices.
4. **Phase A characterizations** (before porting): how `-i`
   non-interactive intake routes through `sta_dat`/`sta_name` (which
   paths are live for the fixture matrix; interactive-only surfaces
   get the fail-closed-or-defer treatment with evidence, like
   `ranset`'s `mox=0`); the round-trip adjudication.
5. **Spine handoff + Codex kickoff**, authored at spine completion,
   citing landed code.

### Stage C — Completion + gates (Codex)

Within the spine's patterns: `fouri2`/`ryf2`/`lintrp` (generation-time
evaluators with their per-call tap streams), `sta_dat`/`sta_name`/
`header` (intake drivers on the characterized live paths), full-matrix
identity tests, all gates (fmt, clippy `-D warnings` with direct exit
checks, `cargo test`, full-stream `--ignored` release taps, llvm-cov +
`cargo crap --fail-above`).

### Stage R1 — Cross-review (Codex)

Independent review of the whole package including the spine:
transcription fidelity against source lines, precision-map compliance
(this package should be REAL*4-clean — any f64 site found is a finding
against the ratified census), state-translation and EQUIVALENCE
compliance, SPEC-PAR fitness for the A4 consumers, test/evidence
alignment. Findings to `artifacts/review-codex.md`; accepted findings
fixed before handback.

### Stage R2 — Final sanity review (Claude Code)

Gates re-run independently; targeted source-vs-port reads of the
highest-risk units (`sta_parms` state distribution, one interpolator
pair's setup/eval consistency); R1 disposition review; close or bounce.
`artifacts/final-review-claude.md`.

## Scope exclusions

- No daily/storm/mode units (`clgen` consumes `fouri2`/`ryf2` in item
  5, not here). No `.cli` emission. No par database or mutation
  utilities (A4 — this package only lays their typed foundation). No
  PRISM/localization semantics.

## Authority

- `reference/cligen532/cligen.f` unit lines per the ratified
  decomposition §2.5; `cbk7.inc`/`cbk1.inc`/`cbk9.inc`/`cinterp.inc`
  layouts; the four fixture `.par` files (Idaho, California, Australia
  GHCN, Utah) as the format's concrete instances.

## Gates

- Stage S ports carry bit-identity tests before Stage C begins.
- Stage C: the full gate suite, exit codes verified directly.
- Reviews dispositioned before close; final close by Stage R2.

## Exit criteria

`EXECUTED-COMPLETE`: all in-scope units bit-identical against the
par-state snapshots and interpolator streams across the fixture matrix;
SPEC-PAR active with the round-trip adjudication recorded; both reviews
dispositioned; gates green. Holds: a format ambiguity SPEC-PAR cannot
resolve from the source + fixtures (name it); an interpolator that
cannot meet bit-identity within the REAL*4 map (stop and characterize).

## Artifacts

- `artifacts/tap-schema.md` (extension), tap patch + manifest
- `artifacts/par-roundtrip-adjudication.md`
- `artifacts/intake-path-characterization.md`
- `artifacts/spine-handoff.md`, `artifacts/kickoff-codex.md`
- `artifacts/review-codex.md`, `artifacts/final-review-claude.md`
- `artifacts/gate-results.md`
