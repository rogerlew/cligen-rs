# Kickoff Prompt — Stage C (Codex)

Paste-ready dispatch prompt. Authored at Stage S completion so every
reference below cites landed code, not intentions.

---

Execute Stage C of the work package at
`docs/work-packages/20260709-rng-deviates-port/package.md` in
/workdir/cligen-rs. Stage S (the spine) is complete and its full-stream
bit-identity gates are green; your stage completes the package's
remaining units inside the spine's established patterns, then runs all
gates. After Stage C you also perform Stage R1: an independent review
of the whole package including the spine.

Read first, in order:

1. `docs/work-packages/20260709-rng-deviates-port/package.md` — the
   staged plan; you own Stages C and R1.
2. `docs/work-packages/20260709-rng-deviates-port/artifacts/spine-handoff.md`
   — your unit list, the named hazards (especially `ranset`'s `mox = 0`
   under-run — characterize before porting), and the acceptance
   commands.
3. The spine code — your exemplars, pattern-normative:
   `crates/cligen/src/{rng,deviates,qc,crandom3,cbk7,libm_pinned}.rs`
   and `crates/cligen/tests/{tap_identity,qc_vectors}.rs`.
4. `docs/standards/rust-scientific-coding-standard.md` — note the two
   rules amended this stage: §1.3 (pinned transcendentals; new
   faithful-path transcendentals are adjudicated empirically before
   use) and §5 (faithful-shape clippy `#[allow]`s with source
   citations).
5. `docs/specifications/SPEC-GENERATOR-CORE.md` — state ownership and
   signature shapes; your units follow it.
6. `docs/port/fortran-decomposition.md` §2.7/§2.9 and
   `reference/cligen532/cligen.f` for your units' source.

Your units (spine-handoff §Stage C unit list): `jdt`/`jlt` →
`calendar.rs`; `conflm`/`confls` → extend `qc.rs`; the 15-unit ACM
cluster → `acm.rs` (uniformly f64; ENTRY points as separate functions
on shared state structs; `ASSIGN`/assigned-GOTO reverse-communication
as explicit state machines); `ranset` last (it consumes the others).

Acceptance:

- Every unit ships with fixture-anchored tests before anything calls
  it. The captured `randn` full stream already contains every draw
  `ranset` makes — build its replay verification the way
  `tests/tap_identity.rs::replay_dg_stream` does, with per-record
  state assertions.
- If a unit needs interior vectors beyond the captured streams, follow
  the tap-patch pattern (recorded patch under this package's
  `artifacts/`, applied to a copied tree — `reference/cligen532/` is
  read-only, hard rule) and record provenance in the tap manifest
  style.
- All gates green, exit codes verified directly (do not trust a piped
  tail): fmt, clippy `-D warnings`, `cargo test`, the full-stream
  `--ignored` tap test in release, llvm-cov + `cargo crap
  --fail-above`.
- No tolerance widening ever: a unit that cannot meet bit-identity
  within the faithful precision map is an `EXECUTED-HOLD` with
  characterization, not an accommodation.

Stage R1 (after C): independent review of the entire package including
the Stage S spine — transcription fidelity against source lines,
precision-map compliance, state-translation compliance, test/evidence
alignment, and the flagged `libm_pinned` license-provenance note.
Findings (numbered, severity, line evidence) to
`artifacts/review-codex.md`; fix accepted findings before handback.

Evidence discipline per AGENTS.md throughout (Ran vs Static, commands
recorded). Update `artifacts/gate-results.md` (extend the Stage S
table), commit in logical chunks per AGENTS.md commit style under your
own agent attribution, and push when green. Stage R2 (final review)
belongs to Claude Code after your handback; do not close the package
yourself — leave status at your stage's end state and report.
