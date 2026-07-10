# Kickoff Prompt — Stage C (Codex)

Paste-ready dispatch prompt. Authored at Stage S completion so every
reference cites landed code.

---

Execute Stage C of the work package at
`docs/work-packages/20260709-daily-core-port/package.md` in
/workdir/cligen-rs. **Work on `main`: start from current
`origin/main`, commit in logical chunks under your own agent
attribution, push to `main`. No side branches** (AGENTS.md §Workflow
branch discipline). Stage S is complete: `clgen` is landed with the
full-stream replay gate green (80,906 calls bit-identical across 10
cases), and the three new pinned transcendentals your units need are
adjudicated. After Stage C you also perform Stage R1: an independent
review of the whole package including the spine.

Read first, in order:

1. `docs/work-packages/20260709-daily-core-port/package.md` — you own
   Stages C and R1.
2. The package artifacts:
   `artifacts/spine-handoff.md` (your unit list — `windg`, `r5monb`,
   `alphb` — the named hazards, and the acceptance commands),
   `artifacts/clgen-draw-order-characterization.md` (the batch
   protocol and in-place station-state mutations),
   `artifacts/transcendental-census.md` (`expf_pinned`/`logf_pinned`
   are your functions; anything else stops for §1.3 adjudication),
   `artifacts/tap-schema.md` (record grammars + full-capture digests),
   `artifacts/gate-results.md` (extend its table).
3. The spine code — pattern-normative: `crates/cligen/src/daily.rs`,
   the state structs (`cbk3`, `cbk5`, extended `cbk4`/`cbk1`/`cbk7`,
   `cbk9` — you extend `Cbk9State` with `ab`/`ab1`/`rn1`/`r1`), and
   `crates/cligen/tests/daily_identity.rs` (reuse its parse/setup
   helpers; your streams interleave with its day loop).
4. `docs/standards/rust-scientific-coding-standard.md` and
   `docs/specifications/SPEC-GENERATOR-CORE.md` (rev 5).
5. The source: `reference/cligen532/cligen.f` `windg` 2020-2122,
   `alphb` 3817-3897, `r5monb` 3898-4001 — plus the `day_gen` call
   sites (3086-3141) for the wet-day `alphb` trigger you must
   characterize before wiring the combined replay.
   `reference/cligen532/` is read-only, hard rule.

Acceptance:

- Every unit ships with tap-anchored tests before anything calls it:
  committed samples in `cargo test`, full streams behind `#[ignore]`
  against `artifacts/tap-runs/` (digests in tap-schema.md), recorded
  in gate-results.md.
- The combined day-loop replay (clgen + windg + alphb in day_gen
  order, `r5monb` once in setup) upgrades `k7` and `v9` to asserted
  internal state — spine-handoff §hazards has the details.
- All gates green, exit codes verified directly (never a piped tail):
  fmt, clippy `-D warnings`, `cargo test`, all four `--ignored`
  release suites, llvm-cov + `cargo crap --fail-above` (decompose
  along source structure near CRAP 30; no `--allow` lists).
- No tolerance widening ever: a unit that cannot meet bit-identity
  within the REAL*4 map is an `EXECUTED-HOLD` with characterization.

Stage R1 (after C): independent review of the entire package including
the Stage S spine — transcription fidelity against source lines
(clgen's interp-dispatch factoring, the twiddle dead-store
transcription in `temps_observed`, the skew/wvl in-place clamps, the
solar clamp branches), precision-map compliance (REAL*4-clean, no
SAVE; any contrary site is a finding), state-translation and
SPEC-GENERATOR-CORE rev-5 compliance, the three new pinned
transcendental provenances (fdlibm/SunPro for tanf/acosf — same
notice lineage as the item-4 record; ARM for expf), and test/evidence
alignment. Findings (numbered, severity, line evidence) to
`artifacts/review-codex.md`; fix accepted findings before handback.

Evidence discipline per AGENTS.md (Ran vs Static, commands recorded).
Stage R2 (final review) belongs to Claude Code after your handback; do
not close the package yourself — leave status at your stage's end
state and report.
