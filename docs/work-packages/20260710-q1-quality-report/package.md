# Q1 — The Quality-Report Instrument (SPEC-QUALITY-REPORT)

Status: `STAGE-S-COMPLETE` — spine landed (quality module, sidecar
emission, `cligen quality`, SPEC-QUALITY-REPORT ratified active rev 3,
SPEC-RUNSPEC rev 4); all gates green (`artifacts/gate-results.md`);
Stage C dispatches from `artifacts/kickoff-codex.md`.
Date: 2026-07-10
Evidence mode: Stage S **Ran** (`artifacts/gate-results.md`; every
gate exit code checked directly)
Execution model: staged, two executors (the item-3..8 pattern) —
Claude Code writes the design-setting spine (Stage S); Codex
(openai gpt-5.6-sol) completes and runs gates (Stage C); each reviews
the other (R1); Claude closes with Stage R2.

## Objective

Build ADR-0002's ruling #2: every generated climate file self-reports
a versioned, machine-readable quality-metric vector, and the same
instrument measures any WEPP-format `.cli` post hoc — including
legacy-Fortran output. This package ratifies SPEC-QUALITY-REPORT from
draft rev 2 to active, implements the metric groups A-D over the
parsed `.cli` text surface, emits the `<name>.cli.quality.json`
sidecar by default from `cligen run` (accepting `output.quality` in
the runspec schema and revving SPEC-RUNSPEC in the same change — the
F3 discipline), and adds the `cligen quality <file.cli> --par
<file.par>` post-hoc subcommand. Group P (process metrics) is
designed as an observation seam in Stage S and implemented by Codex
in Stage C.

**The inviolate**: faithful golden byte identity. The sidecar is
computed from the already-produced `.cli` text + `.par` bytes; the
`.cli` byte stream is untouched, and the 12-golden gates must pass
unchanged.

## Scope

Included (Stage S):
- `crates/cligen/src/quality/` — `.cli` daily-row intake from text
  (never in-process f32 state); pinned deterministic estimators (f64
  accumulation, n−1 sample stats, adjusted Fisher–Pearson skew with
  n ≥ 3 else null, average-rank Spearman, top-N tie-break by earlier
  date then row index, fixed 10-year decade blocks with
  trailing-partial `n_years`); metric groups A (convergence-to-par),
  B (interannual, with `by_decade`), C (covariation), D (tails);
  report envelope (`metrics_version` top-level, `identity.content` /
  `identity.provenance` split, schema-ordered keys, byte-deterministic
  serialization).
- Emission: `cligen run` writes the sidecar by default;
  `output.quality: false` opts out (runspec schema + SPEC-RUNSPEC
  rev in this change). `cligen quality` post-hoc mode with
  `identity.provenance` and group P null.
- Group P observation-seam design (typed read-only counters threaded
  through generation) — documented in `artifacts/spine-handoff.md`,
  not implemented.
- Estimator adjudications: group A targets (as-parsed vs
  post-source-correction `.par` values), `.cli` parser reuse vs
  dedicated intake — `artifacts/estimator-adjudication.md`.

Included (Stage C — see `artifacts/kickoff-codex.md`):
- Group P instrumentation per the Stage S seam design (`qc_filter:
  faithful` side; the `off` counterfactuals are Q3).
- `docs/specifications/quality-report.schema.json`.
- Validate/edge vectors: malformed `.cli`, empty run, n < 3 skew,
  partial decades.
- R1 cross-review of the Stage S spine.

Excluded:
- `qc_filter` implementation and its runspec acceptance (Q3).
- Any generation-behavior change; any `.cli` byte change.
- Observed-data comparison, thresholds, gating (non-goals in the
  spec).
- `.cli.parquet` metadata embedding (A1).

## Authority

- Extension surface: [SPEC-QUALITY-REPORT](../../specifications/SPEC-QUALITY-REPORT.md)
  (draft rev 2 in; ratified active by this package — rev 3 records
  the contract defects implementation exposed, as findings, never
  silent edits), under
  [ADR-0002](../../decisions/0002-quality-metrics-authority.md)
  ruling #2.
- Runspec surface: [SPEC-RUNSPEC](../../specifications/SPEC-RUNSPEC.md)
  (rev 3 in; rev 4 accepts `output.quality`).
- For group A target semantics: the source's own use-time parameter
  corrections (`cligen.f:1237-1238` skew clamp; `cligen.f:1244-1246`
  zero-skew replacement) — the target is what the generator was
  *asked* to reproduce.
- The quality module is observation-only interface code (standard §2
  public-API naming), not a ported Fortran unit: zero interaction
  with RNG state, generation order, or output formatting.

## Plan

1. **Stage S** (Claude Code, this stage): package scaffold; estimator
   adjudications; quality module (intake, estimators, groups A-D,
   envelope); emission + `cligen quality`; runspec `output.quality` +
   schema + SPEC-RUNSPEC rev 4; SPEC-QUALITY-REPORT ratification
   (rev 3 findings on the record); acceptance evidence + gates;
   spine-handoff + kickoff. Status → `STAGE-S-COMPLETE`.
2. **Stage C** (Codex): group P per the seam design; JSON Schema;
   edge vectors; gates. Status → `STAGE-C-COMPLETE`.
3. **Stage R1** (Codex): cross-review of the spine (estimator
   fidelity to the spec pins, determinism, envelope conformance,
   evidence discipline).
4. **Stage R2** (Claude Code): gates re-run; R1 disposition; close or
   bounce.

## Execution & dispatch

Both executors on **`main`**: start from current `origin/main`,
commit to `main`, push to `origin main`. No side branches.
`reference/` is read-only. The operator dispatches Codex from
`artifacts/kickoff-codex.md`; Stage S stops after pushing — it does
not begin Stage C.

## Gates

- `cargo fmt --check`
- `cargo clippy --all-targets -- -D warnings`
- `cargo test --release` (includes the 12-golden byte-identity gates,
  which must pass **unchanged**, and the extended `runspec_cli` test
  asserting the sidecar appears without altering `.cli` bytes)
- Ignored identity suites (`cargo test --release -- --ignored`)
- `cargo llvm-cov --workspace --lcov --output-path target/lcov.info`
  + `cargo crap --workspace --lcov target/lcov.info --exclude
  'tests/**' --fail-above` (CRAP ≤ 30; decompose along structure, no
  allow-lists)
- `cargo deny check` (serde_json + sha2 are new dependencies)
- Package evidence gates (all Ran, exit codes checked directly):
  - 12/12 golden byte identity unchanged; sidecars emitted.
  - Post-hoc report == run-emitted report after nulling the run-only
    surfaces (group P, `identity.provenance`,
    `par_convergence.observed_passthrough` — finding F1), on ≥ 4
    goldens spanning modes.
  - A raw legacy-Fortran production `wepp.cli` (stochastic fixture)
    measures cleanly end-to-end.
  - Determinism: repeated runs → byte-identical reports.
  - Single-storm reports carry group D + identity only.

## Exit criteria

- Stage S complete: quality module + emission + subcommand landed;
  all gates green; spec ratified active with findings on the record;
  handoff + kickoff authored; pushed to `origin main`.
- Package `EXECUTED-COMPLETE` after Stage C, R1, and R2 close with
  gates green and dispositions recorded. Legitimate holds: a
  contract defect that requires operator adjudication (hold with the
  defect named), or a gate regression traceable to the sidecar path
  (hold; the `.cli` byte surface is inviolate).

## Findings (contract defects exposed by implementation)

| # | Finding | Disposition |
|---|---|---|
| F1 | Rev 2 acceptance ("post-hoc equals run-emitted after nulling group P and `identity.provenance`") is not satisfiable as written: `par_convergence.observed_passthrough` is also run-only (true/false when mode is known, null post-hoc), so byte equality fails for every mode. | SPEC-QUALITY-REPORT rev 3: the null set for the post-hoc equality acceptance is extended to all three run-only surfaces. Same principle as the rev 2 finding-2 disposition (exclude *all* run-only fields). |
| F2 | The groups preamble ("all per-month groups key on calendar month … and additionally per decade block") applied literally to group C produces month × decade wet-day correlation cells with n ≈ tens — statistically empty and schema-bloating. | SPEC-QUALITY-REPORT rev 3: group C `by_decade` blocks are decade-level (correlations, contrast, daily range over each decade's days); groups A/B keep full month × decade. |
| F3 | Rev 2 is silent on sidecar collision semantics and the post-hoc output destination. | SPEC-QUALITY-REPORT rev 3: the sidecar is always rewritten when enabled (derived data; `output.overwrite` governs the `.cli` only); `cligen quality` writes the report to stdout. |

## Artifacts

- `artifacts/estimator-adjudication.md` — group A target decision,
  parser reuse decision, estimator pins as implemented.
- `artifacts/gate-results.md` — Stage S gate evidence (Ran).
- `artifacts/spine-handoff.md` — module map + the group P
  observation-seam design for Stage C.
- `artifacts/kickoff-codex.md` — Stage C dispatch prompt (repo,
  branch, push target stated).
