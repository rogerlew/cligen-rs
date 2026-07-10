# Stage S Spine Handoff — Output Writer, Orchestration, Library Byte Parity

Date: 2026-07-09
Author: Claude Code (Stage S executor)
Evidence mode: **executional** — all gates below were run this session;
each command's exit code checked directly.

## What the spine delivers

Stage S closes the *library-level* faithful surface: typed run inputs
→ complete `.cli` text, byte-identical to all 12 goldens. Stage C wraps
this in the SPEC-RUNSPEC `inp.yaml` interface — no physics, no
formatting, and no orchestration decisions remain open.

### New modules

- `crates/cligen/src/fortran_format.rs` — adjudicated `Fw.d`/`Iw`
  output editing (exact u128 integer decimal rounding, ties-to-even;
  d=0 trailing dot; −0.0 sign; leading-zero drop; asterisk fill).
  Authority: `artifacts/format-rounding-adjudication.md` — 57,341,160
  probe fields, 0 mismatches.
- `crates/cligen/src/output.rs` — `write_cli_header` (formats
  642/778/644/500/520/555/648 incl. the SPEC-RUNSPEC §Header echo
  `command_echo` verbatim + its one trailing blank), `write_daily_row`
  (format 2000), `write_run_end`. Three record-level discoveries are
  documented in the adjudication artifact §Byte-level record semantics
  (echo trailing blank; trailing-X-emits-nothing; stop-path suppresses
  the run-end blank line).
- `crates/cligen/src/modes.rs` — `RunInputs`/`RunError`/`run_to_cli`:
  the whole-run orchestration (burn → par parse → sta_parms → bk4 →
  optional PrnReader + `initial_year` → sing_stm intake →
  generation_setup → wxr_gen year plan incl. the quirky iopt-4/7 `nt`
  test vs the Gregorian `ntd` test → per-year ccl1 zeroing → day_gen →
  rows → run-end). `opt_calc` is a characterized no-op for iopt ≥ 4.
- `crates/cligen/src/observed.rs` — `PrnReader::initial_year`
  (usr_opt:3572-3574, non-consuming, cols 11-15, fail-closed).

### Gate results (Ran, this session)

| Gate | Result |
|---|---|
| `cargo fmt --check` | clean |
| `cargo clippy --all-targets -- -D warnings` | clean |
| `cargo test --release` | all green — incl. `cli_parity::goldens_reproduced_byte_identically` (**12/12 goldens byte-identical**) and `format_identity::f_edit_matches_gfortran_sample` (180,000 committed-sample fields) |
| `cargo test --release -- --ignored` (with `CLIGEN_FMT_SWEEP`) | all green — tap/monthlies/storm/daily/ranset/cg identity suites, item-7 cold-start replay, and the **full 57,341,160-field format sweep, 0 mismatches** |
| `cargo llvm-cov` / `cargo crap --fail-above 30` | see `artifacts/gate-results.md` |

### Parity-iteration record

The 12-golden gate reached byte identity in four localized steps, each
a first-divergent-line find with a source citation (details in the
adjudication artifact): (1) echo trailing blank (cligen.f:670-682);
(2) format-500 trailing `1x` emits nothing at end of record;
(3) stop-path run-end suppression (cligen.f:941-978); (4) — none
further; the remaining eight goldens passed unchanged.

## What Stage C owns (unchanged from package.md)

Serde runspec structs + JSON Schema + §Field-invariant validation, the
`cligen` binary (`run`/`validate`, `(document, base_dir)` path
resolution, canonical echo renderer, overwrite policy), 12 golden
runspec fixtures wired to `run_to_cli`, validate vectors, full gates.
`RunInputs` is the seam: the runspec resolves to exactly its fields
(SPEC-RUNSPEC §Golden equivalence table pins every value, including
`command_echo` verbatim per golden).

## Deferred / out of scope (typed, ratified)

iopt 1-3 (opt_calc branches, clmout, CREAMS unit 8); `.cli.parquet`
(A1); PyO3 (A6). No holds — the FORMAT-rounding escalation clause was
not triggered (semantics pinned platform-independently).
