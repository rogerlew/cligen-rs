# Kickoff Prompt — Stage S (Claude Code)

Paste-ready dispatch prompt, authored at scaffold time. Per the
branch-discipline convention adopted after item 4, it states repo,
branch, and push target explicitly.

---

Execute Stage S (the spine) of the work package at
`docs/work-packages/20260709-daily-core-port/package.md` in
/workdir/cligen-rs (github.com/rogerlew/cligen-rs). **Work on `main`:
start from current `origin/main`, commit in logical chunks, push to
`main`.** You are the Stage S executor; Codex (openai codex-5.6-sol)
executes Stage C afterward from the kickoff prompt you author last.
Work from the repository record — do not assume prior session memory.

Read first, in order:

1. `docs/work-packages/20260709-daily-core-port/package.md` — the
   staged plan; you own Stage S only.
2. The item-4 package's proven patterns — your exemplars:
   `docs/work-packages/20260709-par-monthlies-port/artifacts/`
   (`tap-schema.md`, `tap-manifest.md`, `spine-handoff.md`,
   `atanf-pinned-provenance.md` — the §1.3 adjudication template
   including the probe hazards: GCC MPFR constant folding requires
   argv-driven `-fno-builtin` probes; fdlibm bit-pattern comments can
   be stale) and the item-3 artifacts for the stream-tap and
   stateful-replay patterns.
3. The spine code the daily units consume:
   `crates/cligen/src/{rng,deviates,cbk7,cinterp,monthlies,libm_pinned}.rs`,
   `crates/cligen/src/par/`, and the tests
   `crates/cligen/tests/{tap_identity,par_state_identity}.rs`.
4. `docs/standards/rust-scientific-coding-standard.md` (§1.3
   transcendental adjudication, §5 state translation, faithful-shape
   clippy allows) and `docs/specifications/SPEC-GENERATOR-CORE.md`
   (rev 4 — signature shapes, the narrow plain-argument rule).
5. `docs/port/fortran-decomposition.md` §2.2 (your units + line
   ranges), §2.10 (block ownership), §2.11 (call graph) — then the
   source: `reference/cligen532/cligen.f` `clgen` 1094-1515, `windg`
   2020-2122, `alphb` 3817-3897, `r5monb` 3898-4001, and the
   `cbk3.inc`/`cbk5.inc` layouts. `reference/cligen532/` is
   read-only, hard rule.

Stage S deliverables (package §Stage S):

- **Phase A characterizations FIRST, recorded as artifacts**:
  (a) `clgen`'s draw-order and month-boundary protocol (`mox` write +
  `ranset` call at `cligen.f:1204-1209`; which seed streams feed which
  variable; `nsim`/`msim` observed-mode gating per branch);
  (b) the f32 transcendental census across all four units — `exp` at
  `alphb:3852` is already known; enumerate `clgen`'s. Each new
  function/domain is adjudicated empirically against captured
  reference values before use (`libm` crate candidate first; pinned
  transcription on divergence — the `atanf` precedent, including its
  provenance-record obligations).
- **Tap schema extension + additive patch on a COPIED build tree**
  (never `reference/` — gitignore this package's tap-build/tap-runs
  dirs): per-call `clgen`/`windg`/`alphb` output taps (Z8.8 hex via
  EQUIVALENCE) + the once-per-run `r5monb` snapshot, captured across
  the 12 golden invocations. Non-invasiveness gate: patched-binary
  `.cli` outputs byte-identical to all 12 goldens. Add capture-only
  variants only if the characterization shows a golden-unreachable
  branch that needs pinning.
- **Port `clgen`** with per-day bit-identity tests against its tap
  stream: state extensions per the incremental-block pattern (new
  `Cbk3State`/`Cbk5State`; `Cbk7State` generation members;
  `Cbk4State`/`Cbk1State` slices — record each in
  SPEC-GENERATOR-CORE), CRAP ≤ 30 via source-internal decomposition.
  This package should be REAL*4-clean with no SAVE state per the
  census — treat any contrary site you find as a discovery to record,
  not silently absorb.
- **`artifacts/spine-handoff.md`** (patterns, remaining unit list,
  exact acceptance commands) + **`artifacts/kickoff-codex.md`**
  written LAST, citing landed code, and **stating repo, branch
  (`main`), and push target (`main`)** per AGENTS.md branch
  discipline.

Gates before you stop: `cargo fmt --check`; `cargo clippy
--all-targets -- -D warnings` (verify exit code directly — never
trust a piped tail); `cargo test`; the full-matrix tap identity for
everything you port; `cargo llvm-cov` + `cargo crap --fail-above`
(CRAP ≤ 30).

Process cautions from the record: python-heredoc replaces silently
no-op when fmt has reflowed an anchor — assert every replace or use
targeted edits; no pre-filled evidence in artifacts (mark IN FLIGHT,
fill verbatim from real runs); commit with
`Co-Authored-By: Claude <the running model's attribution>`; push when
green.

STOP after Stage S: commit, push, report what was established and any
holds, and hand `kickoff-codex.md` back to the operator for Codex
dispatch. Do not begin Stage C work yourself.
