# Kickoff Prompt — Stage C (Codex)

Paste-ready dispatch prompt, citing landed code.

---

Execute Stage C of the work package at
`docs/work-packages/20260709-storm-machinery-port/package.md` in
/workdir/cligen-rs. **Work on `main`: start from current
`origin/main`, commit in logical chunks under your own agent
attribution, push to `main`. No side branches** (AGENTS.md branch
discipline). Stage S is complete: `timepk` and the duration/Ipeak
chain are landed with the day-loop replay green (80,906 days +
15,468 timepk calls bit-identical, all ten seed streams asserted).
After Stage C you also perform Stage R1.

Read first: the package.md; `artifacts/spine-handoff.md` (your unit
list and hazards); `artifacts/storm-chain-characterization.md`
(especially the `sing_stm` intake analysis and the fixture
branch-coverage table); `artifacts/tap-schema.md` +
`artifacts/gate-results.md` (extend the table);
`crates/cligen/src/storm.rs` and
`crates/cligen/tests/storm_identity.rs` (pattern-normative); the
source `sing_stm` 3325-3493. `reference/cligen532/` is read-only,
hard rule.

Your work: (1) the `sing_stm` typed intake per the handoff (typed
storm parameters; observed-mode ibyear/numyr defaulting; the `mo`
write into `Cbk4State`; interactive/file-management surfaces get
typed-error deferrals — no prompt loops, no unit plumbing); (2)
extend the `#[ignore]` storm gates to the full 24-case matrix; (3)
all gates green, exit codes verified directly. No tolerance widening
ever; `iopt = 7` stays fixture-unreachable — test its arithmetic with
constructed vectors and label them as such.

Stage R1 (after C): independent review of the whole package including
the spine — transcription fidelity (the clamp cascade and override
order in `storm_block`; the F→C seam in the replay; `timepk`'s
search/interpolation and the timpkd(0) sentinel), precision-map
compliance (REAL*4-clean, `alog` via `logf_pinned` only),
state-translation compliance (`Cbk4State` extension, `TYMAX`
placement), test/evidence alignment (full-matrix coverage, digest
verification). Findings to `artifacts/review-codex.md`; fix accepted
findings before handback. Stage R2 belongs to Claude Code; do not
close the package — leave status at your stage's end state and
report.
