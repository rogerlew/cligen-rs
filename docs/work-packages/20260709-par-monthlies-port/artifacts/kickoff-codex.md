# Kickoff Prompt — Stage C (Codex)

Paste-ready dispatch prompt. Authored at Stage S completion so every
reference below cites landed code, not intentions.

---

Execute Stage C of the work package at
`docs/work-packages/20260709-par-monthlies-port/package.md` in
/workdir/cligen-rs. Stage S (the spine) is complete: `ParFile` +
`sta_parms` + `fouri1` + `ryf1` are landed with the full-matrix
par-state snapshot identity gate green (4 stations × interp {0,1,2,3},
every snapshot value bit-exact) and the byte round-trip gated on all
four fixture `.par` files. Your stage completes the package's remaining
units inside the spine's established patterns, then runs all gates.
After Stage C you also perform Stage R1: an independent review of the
whole package including the spine.

Read first, in order:

1. `docs/work-packages/20260709-par-monthlies-port/package.md` — the
   staged plan; you own Stages C and R1.
2. `docs/work-packages/20260709-par-monthlies-port/artifacts/spine-handoff.md`
   — your unit list, the named hazards, and the acceptance commands.
   Then the package's other artifacts:
   `intake-path-characterization.md` (which `sta_dat` paths are live —
   your intake drivers implement exactly those),
   `par-roundtrip-adjudication.md`, `tap-schema.md` (the record
   grammars your tests parse), `tap-manifest.md` (full-capture hashes
   for the `#[ignore]` gates), `gate-results.md` (extend its table).
3. The spine code — your exemplars, pattern-normative:
   `crates/cligen/src/par/{mod.rs,file.rs,sta_parms.rs}`,
   `crates/cligen/src/{monthlies,cinterp,cbk1,cbk9,cbk7}.rs`,
   `crates/cligen/src/libm_pinned.rs` (note `atanf_pinned`'s
   adjudication story), and
   `crates/cligen/tests/par_state_identity.rs` (the snapshot parser
   you will reuse for evaluator-state setup).
4. `docs/standards/rust-scientific-coding-standard.md` — §1.3
   (adjudicate any new faithful-path transcendental empirically before
   use; your units need only the already-pinned `cosf_pinned`) and §5
   (faithful-shape clippy `#[allow]`s with source citations).
5. `docs/specifications/SPEC-PAR.md` and `SPEC-GENERATOR-CORE.md`
   (rev 3: `Cbk7State` rename, new state homes).
6. `docs/port/fortran-decomposition.md` §2.5 and the source:
   `reference/cligen532/cligen.f` — `fouri2` 7387-7423, `ryf2`
   7545-7657, `lintrp` 7252-7337, `sta_dat` 2240-2483, `sta_name`
   2486-2652, `header` 2153-2184. `reference/cligen532/` is read-only,
   hard rule.

Your units (spine-handoff §Stage C unit list): `fouri2`/`ryf2`/`lintrp`
→ extend `monthlies.rs` (generation-time evaluators; per-record tap
vectors are already captured and committed under
`fixtures/taps/par/<station>-I<n>/{f2,y2,li}-sample.tap`, grammar in
tap-schema.md); `sta_dat`/`header` intake drivers on the characterized
live paths; `sta_name` fail-closed/deferred per the characterization.
No new tap capture pass is needed — the Stage S matrix captured your
streams; add the `#[ignore]`-gated full-stream tests against
`artifacts/tap-runs/` and record the run.

Acceptance:

- Every evaluator ships per-record vector tests before anything calls
  it: load the station's `.par`, run `sta_parms` with the combo's
  `interp` (the identity gate already proves that state bit-exact),
  then assert each tap record's result bits. Committed samples run in
  `cargo test`; full streams behind `#[ignore]` against the local
  `tap-runs/` tree (hashes in tap-manifest.md), recorded in
  gate-results.md.
- All gates green, exit codes verified directly (never a piped tail):
  fmt, clippy `-D warnings`, `cargo test`, both `--ignored` release
  tap suites, llvm-cov + `cargo crap --fail-above` (decompose along
  source structure if a unit approaches CRAP 30; `ParFile::parse`
  precedent in gate-results.md — no `--allow` lists).
- No tolerance widening ever: a unit that cannot meet bit-identity
  within the REAL*4 precision map is an `EXECUTED-HOLD` with
  characterization, not an accommodation.

Stage R1 (after C): independent review of the entire package including
the Stage S spine — transcription fidelity against source lines
(sta_parms distribution order, the parameter-14 `timpkd` window, the
`ryf2` leap-February `xes` indexing), precision-map compliance (this
package must be REAL*4-clean; any f64 site is a finding), EQUIVALENCE
and state-translation compliance, SPEC-PAR fitness for the A4
consumers, the `atanf_pinned` SunPro-license provenance note, and
test/evidence alignment. Findings (numbered, severity, line evidence)
to `artifacts/review-codex.md`; fix accepted findings before handback.

Evidence discipline per AGENTS.md throughout (Ran vs Static, commands
recorded). Update `artifacts/gate-results.md` (extend the Stage S
table), commit in logical chunks per AGENTS.md commit style under your
own agent attribution, and push when green. Stage R2 (final review)
belongs to Claude Code after your handback; do not close the package
yourself — leave status at your stage's end state and report.
