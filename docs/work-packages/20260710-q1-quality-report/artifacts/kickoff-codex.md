# Stage C Kickoff — Codex (Q1 quality-report instrument)

Dispatched by: operator, from the Stage S record
Executor: Codex (openai gpt-5.6-sol)
Package: `docs/work-packages/20260710-q1-quality-report/`

## Repository / branch discipline

- Repository: github.com/rogerlew/cligen-rs, checkout
  `/workdir/cligen-rs`.
- **Start from current `origin/main`, commit to `main`, push to
  `origin main`. No side branches.**
- `reference/` is READ-ONLY.

## Read first (in this order)

1. `docs/work-packages/20260710-q1-quality-report/package.md` — the
   package scope, stages, and findings F1-F3.
2. `docs/work-packages/20260710-q1-quality-report/artifacts/spine-handoff.md`
   — the module map and the **group P observation-seam design you are
   implementing**. Its "Design principles" are binding.
3. `docs/specifications/SPEC-QUALITY-REPORT.md` (active rev 3) —
   especially §Metric groups group P and §Determinism.
4. `docs/work-packages/20260710-q1-quality-report/artifacts/estimator-adjudication.md`
   — the pins your schema must encode.
5. `crates/cligen/src/quality/` (the spine), `crates/cligen/src/rng.rs`
   (`ranset` — your main instrumentation site), `crates/cligen/src/modes.rs`
   (`GenState`, `run_to_cli`).
6. `AGENTS.md` + `docs/standards/rust-scientific-coding-standard.md`.

## The inviolate

Faithful golden byte identity. Your instrumentation must be
observation-only: no RNG draws, no float feedback, no reordering.
`cargo test --release` (12-golden gates) and the ignored identity
suites must pass **unchanged**. If a byte gate moves, stop and record
a hold — do not adjust the gate.

## Deliverables

1. **Group P instrumentation** per the seam design
   (spine-handoff.md §Group P): `ProcessCounters` on `GenState`;
   ranset retry/accept/cap-give-up counts; `v7` recovery count; Tdew
   rangecheck lift; per-stream randn draw totals (returned deviates,
   every call site audited); the "final acceptance statistics" shape
   you pin (recommendation in the handoff); plumbing through
   `run_to_cli` → `PreparedRun` → `compute_report` so run-emitted
   reports carry `process` while `cligen quality` keeps it null.
   `qc_filter: "faithful"` for the faithful backend, `null` for
   `fast_batch_v0` (off-style counterfactuals for v0 are **Q3**, not
   yours — carry the null).
2. **`docs/specifications/quality-report.schema.json`** — the full
   JSON Schema of the report envelope (metrics_version 1), matching
   the Rust types field-for-field and key-order documented; wire a
   test that validates emitted reports against it if a lightweight
   path exists, else assert structural conformance in Rust (document
   which).
3. **Edge vectors** (tests): malformed `.cli` (beyond the intake unit
   tests: wrong field counts mid-file, non-numeric fields, misordered
   dates), empty run / zero-row table, n < 3 skew cells (assert the
   null lands in the right cell numerically), partial decades
   (trailing-block `n_years` values asserted), single-storm envelope,
   `fish-springs` truncated observed (partial year visible in
   `tails.per_year[].n_days`).
4. **Gates** (all Ran, exit codes checked directly, never through a
   pipe): `cargo fmt --check`; `cargo clippy --all-targets -- -D
   warnings`; `cargo test --release`; ignored identity suites (the
   57.3M-field sweep capture is at `target/stage-c-fmt/fmt_pairs.txt`
   — regenerate from `fmtprobe.f` per the item-8 package if absent);
   `cargo llvm-cov` + `cargo crap --workspace --lcov target/lcov.info
   --exclude 'tests/**' --fail-above` (CRAP ≤ 30, no allow-lists);
   `cargo deny check` if you add any dependency (avoid adding one for
   schema validation unless it clearly pays).
5. **Artifacts**: `artifacts/stage-c-report.md` (evidence, Ran vs
   Static, what your gates do not cover) and
   `artifacts/review-codex.md` — your **R1 cross-review of the Stage
   S spine** (dimensions: estimator fidelity to the rev 3 pins;
   determinism; envelope conformance; the F1-F3 findings' soundness;
   test/evidence alignment; anything the spine mislabeled). Findings
   verbatim, severities, dispositions to Claude.
6. Set package Status: `STAGE-C-COMPLETE` (or
   `EXECUTED-HOLD-<reason>` with the blocker named), push, stop —
   Stage R2 is Claude's.

## Process cautions (repo record)

- Truthfulness: verbs match evidence; "ran" only if run; label
  Ran/Static; no pre-filled numbers.
- Python-heredoc edits must assert their anchors
  (`s.count(old) == 1`).
- Commit in logical chunks; imperative subjects ≤ 72 chars; your
  usual co-author line.
- The quality module remains observation-only. If implementing group
  P appears to require touching generation order, RNG state, or
  output formatting, that is a design defect — hold and record it,
  do not improvise.
