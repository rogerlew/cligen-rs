# Gate Results — Q1 Stage S (spine)

Date: 2026-07-10
Evidence mode: **Ran** — every row is a command executed this
session with its exit code checked directly (`echo $?` immediately
after the command, never after a pipe).

## Standard gates

| Gate | Command | Result | Exit |
|---|---|---|---|
| Format | `cargo fmt --check` | clean | 0 |
| Lints | `cargo clippy --all-targets -- -D warnings` | clean | 0 |
| Tests | `cargo test --release` | **81 passed, 0 failed** across all suites — includes `cli_parity` (12/12 golden `.cli` byte-identical from typed inputs), the extended `runspec_cli` gate (12/12 golden byte identity through the binary **with** the sidecar asserted present and removed per case), and the new 8-test `quality_report` suite | 0 |
| Identity suites | `CLIGEN_FMT_SWEEP=/workdir/cligen-rs/target/stage-c-fmt/fmt_pairs.txt cargo test --release -- --ignored` | **9 passed, 0 failed**: tap/monthlies/daily(cg/combined/windg)/cold-start replays and the full format sweep `f_edit_matches_gfortran_full_sweep` (57,341,160 fields, 0 mismatches, 18.7 s) against the retained item-8 capture (455 MB) | 0 |
| Coverage | `cargo llvm-cov --workspace --lcov --output-path target/lcov.info` | TOTAL 89.55% regions / 84.38% functions / 91.75% lines | 0 |
| CRAP | `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above` | **281 functions analyzed; none exceed threshold 30.** No allow-lists. (First run flagged `QualityIntakeError::fmt` at CRAP 72 — CC 8, uncovered; closed by adding intake fail-closed unit tests, not by allow-listing.) `run_to_cli` remains the crate maximum at 29.0 — untouched by this package. | 0 |
| Dependencies | `cargo deny check` | advisories ok, bans ok, licenses ok, sources ok — run because this package adds `serde_json` (feature `float_roundtrip`) and `sha2` (both previously absent from `Cargo.lock`) | 0 |

## Package acceptance evidence (all Ran)

| Acceptance | Evidence | Result |
|---|---|---|
| 12/12 golden byte identity unchanged; sidecars emitted | `runspec_cli::cligen_binary_runs_all_golden_runspecs_byte_identically` (now also asserting sidecar presence per case), plus a direct `cmp` of a fresh `cligen run` output against `goldens/new-meadows-id-seed0.cli` | pass; `cmp` reported identity |
| Post-hoc == run-emitted after nulling run-only surfaces, ≥ 4 goldens spanning modes | `quality_report::post_hoc_equals_run_emitted_after_nulling_run_only_surfaces` — **5 goldens**: new-meadows seed0 + jeogla seed17 (continuous), mt-wilson seed0 (observed, sentinel-padded), fish-springs truncated seed17 (observed, hard EOF), new-meadows single-storm seed0. Byte equality of serialized reports after nulling group P, `identity.provenance`, and `par_convergence.observed_passthrough` (F1). Binary-level: `cligen_quality_stdout_matches_run_emitted_sidecar_after_nulling` (sidecar file vs `cligen quality` stdout) | pass |
| Raw legacy-Fortran production `.cli` measures cleanly | `quality_report::legacy_fortran_production_cli_measures_cleanly` — `fixtures/new-meadows-id/wepp.cli` (11,322 records) and `fixtures/jeogla-au/wepp.cli` (15,340 records), the raw stochastic production files per the fixture-manifest cross-reference addendum; full report computed, serialized, and round-tripped | pass |
| Determinism | `report_computation_and_serialization_are_deterministic` (in-process ×2) and `repeated_runs_emit_byte_identical_sidecars` (binary ×2, byte-compared sidecars) | pass |
| Single-storm: group D + identity only | `single_storm_reports_carry_tails_and_identity_only` — groups A/B/C and P all null; days 1; the one event in `tails` | pass |
| `output.quality: false` opts out | `cligen_run_emits_sidecar_by_default_and_output_quality_false_opts_out` | pass |

> Correction (Stage R2, C-R1-004): this row originally transcribed
> the capture path as the relative `target/stage-c-fmt/fmt_pairs.txt`;
> the command actually run used the absolute path now shown. The
> relative form is **not** reproducible — `format_identity` resolves
> `CLIGEN_FMT_SWEEP` from the test process working directory, not the
> repo root (established Ran in Stage C).

## What these gates do not cover

- **Group P** is not implemented (by design — Stage C); every report
  carries `process: null`. The `ProcessMetrics` type and the seam
  design exist but no counter is produced or asserted.
- The published JSON Schema (`quality-report.schema.json`) does not
  exist yet (Stage C deliverable); envelope shape is pinned only by
  the Rust types and the round-trip tests.
- Edge vectors (malformed `.cli` beyond the intake unit tests, empty
  run, n < 3 skew cells asserted numerically, partial-decade cell
  values) are Stage C scope.
- Group A on interpolated runs includes interpolation-method bias by
  design (adjudication §1); no gate quantifies that bias.
- `cargo deny` covers policy, not vulnerability discovery beyond the
  advisory DB as of today.
- Coverage/CRAP were computed **without** `CLIGEN_FMT_SWEEP` (default
  suite instrumentation), matching prior packages' practice.

## Cross-check observed during smoke runs

`cligen run` on new-meadows emits the source's faithful retry-cap
give-up messages (`*** ERROR *** Could not produce desired level of
quality in parameter 9/5 ... years 17-27`) — live instances of the
cap-hit events group P must report (spec group P; lit-review finding
6), on the record here as Stage C motivation.
