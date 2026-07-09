# RNG + Deviates Port (with the QC/ACM chain)

Status: `STAGE-S-COMPLETE` (Stage C/R1 with Codex next, then Stage R2
closes)
Date: 2026-07-09
Evidence mode: Stage S — Ran (tap capture, full-stream identity, all
gates; see `artifacts/gate-results.md`)

Stage S outcome: tap schema + non-invasive patch + 12-fixture capture
(non-invasiveness proven by golden byte-identity); `randn`/`dstn1`/
`ks_tst`/`dstg` ported with **full-stream bit-identity** — 19,784,955 +
26,402,148 + 30,268 records, QC-regeneration draws included; state
structs (`Crandom3State`, `Cbk7Seeds`, `DstgState`) and
SPEC-GENERATOR-CORE established; the f32 transcendental adjudication
resolved by exhaustive evidence (`libm_pinned`, standard §1.3 amended);
handoff + Codex kickoff in `artifacts/`.
Execution model: staged, two executors (operator-ratified 2026-07-09) —
Claude Code writes the design-setting spine; Codex completes the
mechanical volume and runs gates; each reviews the other; Claude holds
the final sanity review after handback.

## Objective

Port the first generator code under faithful-mode acceptance: `randn`,
`ranset`, `dstn1`, `dstg` plus the QC/ACM chain they call (`ks_tst`,
`conflm`, `confls`, the ACM special-function cluster) and the calendar
utilities — ROADMAP item 3, covering ratified port-order steps 1–2. The
package also establishes the patterns every later port package imitates:
the common-block state structs, the tap schema, and the faithful-mode
function shapes. `nrmd` and `chitst` are ratified dead and are not
ported.

## Acceptance (whole package)

Bit-identical deviate streams against Fortran taps for **all fixture
seeds, including the QC-regeneration draws** (the QC-rejection path
consumes extra RNG draws; a port that skips it diverges silently). Tap
comparison is on exact bit patterns, not decimal renderings — the tap
format decision (Stage S) must make comparisons formatting-proof.

## Stages

### Stage S — Spine (Claude Code)

Design-setting work; everything downstream imitates it.

1. **Tap schema + patch**: define what interior values are tapped
   (uniform stream from `randn`, normal stream from `dstn1`, gamma
   stream + rejection/QC-regeneration events from `dstg`, seed state
   snapshots from `ranset`) and the emission format (bit-exact — e.g.
   hex/raw — so no decimal-formatting ambiguity enters acceptance). The
   patch is recorded under `artifacts/`, applied to a copied build tree,
   never to `reference/`. Capture tap fixtures for all golden-fixture
   seeds using the pinned build profile from the fixture-harness
   provenance.
2. **State structs**: `Crandom3State` (seed integers, `ranary` with the
   nine views as accessor methods, f64 `g_dsum`/`g_ssum` accumulators),
   plus the minimal slices of other blocks that `ranset` reads —
   establishing the block-to-struct pattern of coding standard §5,
   block-data initializers as cited constructors.
3. **Ports**: `randn`, `dstn1`, `ks_tst` (on the `dstg` acceptance
   path), `dstg` (the f64 `fu`/`xx` island, `SAVE` state as struct
   fields, the QC-filter call seam) — each with attribution header,
   symbol glossary, precision-map annotation, and bit-identity tests
   against the tap fixtures.
4. **SPEC-GENERATOR-CORE** (seed/state surface: how seeds enter, what
   state flows, faithful-mode signature shapes) — authored, registered.
5. **Spine handoff**: `artifacts/spine-handoff.md` naming the
   established patterns, the remaining unit list, and the exact
   acceptance commands; plus the Codex kickoff prompt (authored at spine
   completion so it cites real code, not intentions).

### Stage C — Completion + gates (Codex)

Within the spine's patterns: `conflm`, `confls`, the ACM cluster
(`cdfchi` … `spmpar` — uniformly f64; `ENTRY` points `dstinv`/`dstzr` as
separate functions on shared state per standard §5), `ranset` (seed
init + QC battery), `jdt`/`jlt`. Full-matrix bit-identity tests (every
fixture seed, QC-regeneration draws included) and all gates: fmt, clippy
`-D warnings`, test, CRAP ≤ 30 via llvm-cov + cargo-crap.

### Stage R1 — Cross-review (Codex)

Independent review of the whole package **including the spine** —
transcription fidelity against source lines, precision-map compliance,
state-translation compliance, test/evidence alignment. Findings to
`artifacts/review-codex.md`; accepted findings fixed before handback.

### Stage R2 — Final sanity review (Claude Code)

After handback: spot-verification of Codex's stage (gates re-run,
tap-identity re-run, targeted source-vs-port reads of the highest-risk
units — `ranset`, `dstg` seam, one ACM `ENTRY` translation), review of
R1 dispositions, close or bounce with named blockers.
`artifacts/final-review-claude.md`.

## Scope exclusions

- No `nrmd`/`chitst` (dead). No daily/storm/mode/output units. No
  native-f64 mode. No `.cli` emission. No profile/provenance surfaces
  beyond what SPEC-GENERATOR-CORE itself needs.

## Authority

- `reference/cligen532/cligen.f` per ADR-0001 (unit lines in the
  ratified decomposition §2); precision sites per the ratification
  census; tap constraint carried from the fixture-harness provenance
  (interior-taps deferral note).

## Gates

- Stage C: fmt / clippy `-D warnings` / test / CRAP ≤ 30; full-seed-matrix
  tap bit-identity including QC-regeneration draws.
- Stage S ports carry their own bit-identity tests before Stage C begins.
- Reviews dispositioned before close; final close by Stage R2.

## Exit criteria

`EXECUTED-COMPLETE`: all in-scope units ported and bit-identical against
taps across the fixture seed matrix; SPEC-GENERATOR-CORE registered;
both reviews dispositioned; gates green. Holds: tap capture cannot
reproduce deterministically (name the source); a unit cannot meet
bit-identity within the faithful precision map (stop and characterize —
do not widen tolerances).

## Artifacts

- `artifacts/tap-schema.md`, `artifacts/tap-patch.diff`,
  `artifacts/tap-fixtures/` (or manifest + hashes if bulky)
- `artifacts/spine-handoff.md`, `artifacts/kickoff-codex.md`
- `artifacts/review-codex.md`, `artifacts/final-review-claude.md`
- `artifacts/gate-results.md`
