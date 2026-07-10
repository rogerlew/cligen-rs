# Stage R1 Independent Review — Codex

Reviewer: OpenAI Codex, 2026-07-09.

Evidence mode: Static source/transcription review + Ran targeted and package
gates. Stage R2 remains assigned to Claude Code; this review does not close
the package.

## Outcome

Four findings were accepted and fixed: one High and three Medium. No R1
finding remains open, no tolerance was introduced or widened, and no file
under `reference/cligen532/` was modified.

## Findings

1. **High — accepted `.par` inputs could violate byte round-trip and fixed-
   column semantics.** Before R1, `ParFile::parse` used `str::lines()`, which
   accepts CRLF while removing each CR; `to_bytes()` then emitted LF, violating
   the claimed invariant for an accepted input. The parser also accepted
   non-ASCII UTF-8 despite byte-column slicing and removed tabs with
   `is_ascii_whitespace()`, although Fortran `BLANK='NULL'` applies to spaces,
   not arbitrary whitespace. **Fixed:** explicit ASCII/LF validation and
   typed errors are at `par/file.rs:24-29,284-293`; numeric fields remove only
   ASCII spaces at `par/file.rs:136-174`; CRLF, non-ASCII, and tab regressions
   are pinned at `par_state_identity.rs:579-590`. SPEC-PAR documents the same
   fail-closed envelope.

2. **Medium — the SunPro/fdlibm notice was incomplete and explicitly left
   unresolved.** The Stage S header named SunPro and the permissive grant but
   omitted parts of the notice while saying R1 still needed to adjudicate it.
   **Fixed:** `libm_pinned.rs:3-15` preserves the complete Sun notice. Static
   inspection used the GNU glibc 2.39 release tarball and Netlib fdlibm;
   tarball/source hashes, primary URLs, notice text, and disposition are in
   `atanf-pinned-provenance.md:6-36`. The existing full-matrix `fouri1`
   composition gate remains the behavioral acceptance surface.

3. **Medium — local full-stream evidence had only abbreviated digests in the
   manifest.** The kickoff describes manifest hashes as the identity of the
   ignored evidence tree, but the Stage S table retained 16-hex display
   prefixes and told reviewers to regenerate the rest. **Fixed:** direct
   `sha256sum` over all 16 non-empty files consumed by the Stage C gate is
   recorded in full at `tap-manifest.md:89-113`. The ignored replay asserts
   380,436 `fouri2`, 275,452 `ryf2`, and 36,889 `lintrp` records at
   `par_state_identity.rs:625-661`.

4. **Medium — SPEC-PAR was not yet a complete or achievable A4 mutation
   contract.** It claimed bit-exact `parse(canonical(v)) == v` for every field
   family but specified only monthly six-byte rendering; it did not say how
   records 1-3/83, skipped lexemes, overflow, or arbitrary f32 values were
   handled. An arbitrary f32 cannot necessarily survive an `F6.2` render
   bit-exactly. **Fixed:** SPEC-PAR rev 2 defines each record family, retained
   untyped spans, typed overflow errors, and rejection of f32 mutations that
   cannot survive the fixed decimal precision (`SPEC-PAR.md:141-173`). Its
   acceptance matrix now correctly names interp `{0,1,2,3}`.

## Required-focus review

- **Transcription fidelity (Static + Ran):** read `sta_parms` against
  `cligen.f:2656-2970`. Raw distribution order, `wi` halving, interpolation
  dispatch, wind reads, elevation truncation, CV derivation, and cumulative
  direction construction correspond at `par/sta_parms.rs:69-162`. The
  parameter-14 call receives `[timpkd(0), timpkd(1..11)]` exactly at lines
  80-123; `timpkd(12)` remains outside the setup window. Read all five
  interpolation units against `cligen.f:7252-7657`; no transcription finding
  remained after full replay.
- **Leap-February hazard (Static + Ran):** `ryf2` selects `pmt/pmv(13)`,
  `emv(13:14)` at `monthlies.rs:260-282`, but deliberately reads
  `xes[mo-1]` at lines 284-304, matching `cligen.f:7610-7653`. The full y2
  stream includes 5,292 leap-February records; every result is bit-identical.
- **Precision map (Static):** grep over the package's Rust production files
  found no f64 value/cast or standard transcendental call. Monthlies routes
  its only evaluator transcendental through `cosf_pinned`
  (`monthlies.rs:142-155`). All new intake/parser field values remain f32.
- **State/EQUIVALENCE translation (Static):** `/bk7/`, `/bk1/`, `/bk9/`, and
  `/interp/` each have one owner. The source `rst1..rst3`/`prw1..prw2`
  EQUIVALENCE views remain accessor-derived, never duplicated. `ida` is a
  read-only argument to `fouri2`; SPEC-GENERATOR-CORE rev 4 records why
  `Cbk3State` remains with the daily package. No global, implicit SAVE, or
  interior-mutable generator state was introduced.
- **Intake paths (Static + Ran):** `sta_dat` writes the source banner, reads
  the single `-i` path, and then calls `sta_parms` (`par/intake.rs:105-149`).
  Four fixture stations are snapshot-anchored. The uncaptured `-S`+`-s` scan
  and interactive `sta_name` path return distinct typed errors at lines
  118-128 and 152-163; neither falls back to a station.
- **Evidence alignment (Ran):** committed samples cover 4,000 records for
  each evaluator; local streams cover 692,777 total records. Snapshot state
  remains complete for four stations × four interpolation modes. The final
  fmt, clippy, ordinary tests, both ignored release suites, coverage, and CRAP
  commands all exited 0 directly; detailed counts are in `gate-results.md`.

## R1 disposition

Stage C and R1 are ready for the independently assigned Stage R2 review.
The package remains open and is not moved on the roadmap by this review.
