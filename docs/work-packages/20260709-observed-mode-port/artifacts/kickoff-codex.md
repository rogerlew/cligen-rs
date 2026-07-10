# Kickoff Prompt — Stage C (Codex)

---

Execute Stage C of
`docs/work-packages/20260709-observed-mode-port/package.md` in
/workdir/cligen-rs. **Work on `main`: start from current
`origin/main`, commit in logical chunks under your own attribution,
push to `main`. No side branches.** Stage S is complete: `day_gen` /
`generation_setup` / `PrnReader` / `Ccl1State` are landed and the
cold-start replay is green (80,906 days, zero injected state). After
Stage C you also perform Stage R1.

Read first: package.md; `artifacts/spine-handoff.md` (work list +
hazards); `artifacts/daygen-characterization.md`;
`artifacts/gate-results.md` (extend);
`crates/cligen/src/{modes,observed,ccl1}.rs` and
`crates/cligen/tests/modes_identity.rs` (pattern-normative); source
`day_gen` 2971-3195. `reference/cligen532/` is read-only, hard rule.

Your work: (1) extend the cold-start `#[ignore]` gate to all 24
capture cases with per-case end-day assertions; (2) `.prn` edge
tests per the handoff; (3) all gates green, exit codes direct — the
seven `--ignored` suites now include `modes_identity`.

Stage R1 (after C): independent review of the package including the
spine — transcription fidelity (the observed block's flag/assignment
order vs cligen.f:3067-3083; the moveto/EOF protocol; `th·clt` and
the F→C seam placement; the ccl1 write order), precision-map and
state-translation compliance (`DayGenState` SAVE, `GenState`
ownership), test/evidence alignment (row-derivation formulas cite
their lines). Findings to `artifacts/review-codex.md`; fix accepted
findings before handback. Stage R2 belongs to Claude Code; do not
close the package.
