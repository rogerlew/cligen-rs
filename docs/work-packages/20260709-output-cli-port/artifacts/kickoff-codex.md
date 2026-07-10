# Stage C Kickoff — Codex (openai codex-5.6-sol)

Package: `docs/work-packages/20260709-output-cli-port/package.md`
Stage: C (completion + gates), then R1 (cross-review)
Date: 2026-07-09

## Repository / branch discipline

- Repository: `github.com/rogerlew/cligen-rs`, checkout `/workdir/cligen-rs`.
- Work on **`main`**. Start from current `origin/main`, commit to
  `main`, push to `origin main`. **No side branches.**
- `reference/` is READ-ONLY. Never modify anything under it.

## Context

Stage S (spine) is complete and pushed: the library now reproduces all
12 golden `.cli` files **byte-identically** from typed run inputs
(`cli_parity::goldens_reproduced_byte_identically`), on top of an
adjudicated formatting module (57.3M-field sweep, 0 mismatches — see
`artifacts/format-rounding-adjudication.md` and
`artifacts/spine-handoff.md`). Your stage wraps this proven core in the
SPEC-RUNSPEC `inp.yaml` interface. **No formatting, physics, or
orchestration decisions remain open** — if you believe one does, stop
and flag it in R1 rather than deciding it locally.

## Read first

1. `docs/specifications/SPEC-RUNSPEC.md` (rev 2) — the normative
   contract, including §Field invariants, §Header echo, §Golden
   equivalence (pins every value for all 12 goldens, `command_echo`
   verbatim), §validate-vs-run.
2. `artifacts/spine-handoff.md` — what exists, the `RunInputs` seam.
3. `crates/cligen/src/modes.rs` — `RunInputs`, `RunError`, `run_to_cli`.
4. `crates/cligen/tests/cli_parity.rs` — the golden table your runspec
   fixtures must mirror.

## Deliverables

1. **Runspec intake**: serde structs for the SPEC-RUNSPEC document
   (deny unknown fields), schema-version check, §Field-invariant
   validation as typed errors (every invariant in the spec, each error
   naming the field path). Emit a JSON Schema artifact
   (`docs/specifications/runspec.schema.json` or per spec).
2. **The `cligen` binary**: `cligen run <inp.yaml>` and
   `cligen validate <inp.yaml>`. Path resolution at the
   `(document, base_dir)` boundary — paths resolve relative to the
   runspec file, resolution happens outside `run_to_cli`. Overwrite
   policy per spec (`output.overwrite`, never a prompt). Canonical
   echo renderer for when `output.command_echo` is absent (spec
   §Header echo, canonical default form).
3. **Golden runspec fixtures**: 12 `inp.yaml` files mirroring
   SPEC-RUNSPEC §Golden equivalence; an integration test drives
   `cligen run` (the binary surface, not just the library) and asserts
   byte identity against the goldens.
4. **Validate vectors**: fail-closed tests per §Field invariants +
   labeled schema/orchestration vectors for fixture-unreachable
   branches (design_storm mode intake, linear/mmp interpolation
   selection, overwrite refusal, canonical echo rendering).
5. **Gates**: `cargo fmt --check`, `cargo clippy --all-targets -- -D
   warnings`, `cargo test --release`, ignored suites, `cargo llvm-cov`,
   `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**'
   --fail-above`, `cargo deny check` (you are adding dependencies —
   serde/serde_yaml/clap or equivalents — so deny MUST be re-run).
   Check exit codes directly.

## Structure constraint

`run_to_cli` is at CRAP 29.0 (threshold 30). Do not grow it: the
runspec→`RunInputs` resolution, path handling, and echo rendering live
in a new module (e.g. `runspec.rs`) and/or the binary crate — the
existing seam takes `RunInputs` fully resolved.

## Evidence discipline

- Truthfulness: label every claim Ran vs Static; never report a gate
  you did not run.
- No pre-filled evidence: write results only after the command ran.
- Artifacts: `artifacts/stage-c-report.md` (what you built, gate
  table), then `artifacts/review-codex.md` (R1: format fidelity,
  orchestration fidelity vs wxr_gen:3758-3800, SPEC-RUNSPEC
  conformance, test/evidence alignment — findings with severity, no
  fixes without a finding first).
- Update `package.md` Status to `STAGE-C-COMPLETE` when done; Claude
  Code closes with R2.
