# Spine Handoff — Q1 Stage S → Stage C

Date: 2026-07-10
Author: Claude Code (Stage S executor)
Status at handoff: all gates green (`gate-results.md`), pushed to
`main`. Stage C executes from `kickoff-codex.md`.

## What landed (module map)

| Surface | File | Notes |
|---|---|---|
| `.cli` text intake | `crates/cligen/src/quality/intake.rs` | 13-field daily table (SPEC-CLI-DIFF shape), f64 values, fail closed on malformed rows, non-finite fields, non-chronological dates. Dedicated parser — adjudication §2. |
| Pinned estimators | `crates/cligen/src/quality/estimators.rs` | f64, n−1, adjusted Fisher–Pearson, average-rank Spearman; null-not-NaN everywhere. |
| Group A targets | `crates/cligen/src/quality/targets.rs` | as-parsed + source use-time corrections; unit-mapped — adjudication §1. |
| Groups A-D | `crates/cligen/src/quality/groups.rs` | decade slices, Markov transitions, dispersion, correlations, tails. |
| Envelope + types | `crates/cligen/src/quality/report.rs` | schema-ordered serde structs; `null_run_only_surfaces()`; `to_json_bytes()` (pretty, trailing newline). **`ProcessMetrics` is the typed group P target — not yet produced.** |
| Orchestration | `crates/cligen/src/quality/mod.rs` | `compute_report(cli_text, par_bytes, provenance)`; SHA-256; single-event rule (1 row → D + identity only). |
| Run emission | `crates/cligen/src/runspec.rs` | `output.quality` (default true), `PreparedRun::{quality_sidecar_path, quality_provenance, write_quality_sidecar}`; sidecar always rewritten when enabled. |
| Post-hoc CLI | `crates/cligen/src/bin/cligen.rs` | `cligen quality <file.cli> --par <file.par>` → stdout. |
| Acceptance gates | `crates/cligen/tests/quality_report.rs` + extended `runspec_cli.rs` | see gate-results.md. |

Specs revved in the same change: SPEC-QUALITY-REPORT → active rev 3
(findings F1-F3 in `package.md`); SPEC-RUNSPEC → rev 4
(`output.quality` accepted); `runspec.schema.json` updated; registry
rows updated.

## Group P observation seam — design for Stage C

Group P (`process`) is run-emitted only, keyed on `qc_filter` alone.
Stage C implements the **`qc_filter: faithful`** side (the only
conditioning behavior that exists today) plus `fast_batch_v0`'s
`qc_filter: null` case; the `off` counterfactual verdicts are Q3.

### Design principles (binding)

1. **Observation-only.** Counters never feed a generation decision,
   consume an RNG draw, or perform float arithmetic whose result
   re-enters generation. The 12-golden byte gate and every ignored
   identity suite must pass unchanged — that is the seam's
   acceptance, not a formality.
2. **Typed, run-scoped, threaded — no globals.** One
   `ProcessCounters` accumulation struct owned by
   `modes::GenState` (which is Rust orchestration state, not a
   common-block mirror — adding a field there does not violate the
   state-translation rules). It flows out of `run_to_cli` alongside
   the `.cli` text.
3. **The faithful stdout prints stay.** The `*** ERROR ***` give-up
   println in `rng.rs:339` is source behavior; counters observe the
   same event, they do not replace or gate the print.

### Instrumentation points

| Metric (`ProcessMetrics` field) | Site | What to count |
|---|---|---|
| `retries[].rejected_attempts` | `rng.rs::ranset` retry loop (`failed` branch, cligen.f:4302-4332) | one per rejected attempt, per parameter (j+1) × current month |
| `retries[].accepted_batches` | same loop, accept exit | one per accepted batch per parameter × month (observed-mode parameter 9 bypasses statistics — count it as accepted-without-QC or add a dedicated field; pin it in the schema either way) |
| `cap_give_ups[]` | the `iredo == 10_000` arm | `{parameter, month, year}` in occurrence order. Note the source semantics the counters must respect: `iredo` is shared across all nine parameters within one `ranset` call, and once the cap is hit every subsequent failing attempt in that call is accepted — count each such acceptance as a give-up event. |
| `v7_recovery_count` | `daily.rs::gen_precip` band-aid draw (cligen.f:1253, `bk7.v7 == 0.0`) | one per recovery draw |
| `tdew_rangecheck_count` | already counted as `GenState.tdew_events` (`ClgenEvents`) | lift into the counters struct (keep or alias the existing field; do not double-count) |
| `randn_draws` | every `randn(&mut bk7.kN)` call site | one per **returned deviate** per stream k1..k10 (randn's internal (0,1) rejection loop is not a draw — pin this in the schema description). Sites to audit: `Cbk7State::burn`, `generation_setup*`, `rng.rs::initialize_ranset_streams`, `rng.rs::draw_ranset_value`, `gen_precip`'s band-aid, `deviates.rs::dstg` (k7). `grep -n "randn(" crates/cligen/src/` and account for every hit. |

"Final acceptance statistics" (spec group P) is **not yet pinned** by
the typed skeleton: recommend capturing, per parameter × month at
each accepted batch, the final K-S `level1`/`conflm`/`confls` values
(available at the accept site with zero extra computation), and
extending `ProcessMetrics` accordingly. That extension is yours to
finalize together with the JSON Schema — keep field order fixed and
document the choice in your stage report; it is a schema-shape
decision inside metrics_version 1 (the field is landing for the first
time, so no version bump).

### Plumbing route

`run_to_cli` currently returns `Result<String, RunError>`. Extend to
return the counters (e.g. a `RunOutput { cli: String, process:
ProcessMetrics }` or a tuple), thread through
`PreparedRun::generate()` (keep a `.cli`-text-only accessor for the
existing parity tests or update call sites — your choice, gates
decide), and pass `Some(process)` into `compute_report`, which gains
a `process: Option<ProcessMetrics>` parameter (currently hardcoded
`None` — one line in `mod.rs`). `cligen quality` keeps passing
`None`. `qc_filter` inside `ProcessMetrics` mirrors
`PreparedRun::quality_provenance().qc_filter`.

Determinism: `retries` ordered by parameter 1..=9; `cap_give_ups` in
occurrence order; all counters integers. Byte-determinism then holds
trivially.

## Known seams and non-goals Stage C should not "fix"

- Group A targets deliberately ignore interpolation (adjudication §1
  caveat) — do not per-day-integrate targets.
- Group C `by_decade` is decade-level by rev 3 ruling F2 — do not
  add month × decade cells.
- The intake's strictly-increasing-date rule is deliberate (decade
  blocking + Markov transitions); a `.cli` violating it fails closed.
- `decade` is a 0-based block index; `start_year` is authoritative.
- The sidecar is always rewritten when enabled (rev 3 ruling F3);
  `output.overwrite` governs the `.cli` only.
