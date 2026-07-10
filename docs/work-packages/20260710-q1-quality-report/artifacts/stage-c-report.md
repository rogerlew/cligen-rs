# Stage C Report — Group P, Schema, and Edge Vectors

Date: 2026-07-10
Executor: Codex (openai gpt-5.6-sol)
Disposition: `STAGE-C-COMPLETE`; Stage R2 remains Claude's.

## Outcome

Ran: faithful golden `.cli` bytes remain identical while run-emitted
sidecars now carry group P. Post-hoc `cligen quality` reports keep
`process: null`. `fast_batch_v0` run reports carry a process object with
`qc_filter: null`; Q3 still owns off-style counterfactual verdicts.

The run-scoped `ProcessCounters` is owned by `GenState`. It observes:

- rejected attempts and accepted batches per parameter 1..=9 × month;
- every shared-`iredo` cap give-up in occurrence order;
- final acceptance statistics in occurrence order;
- `bk7.v7 == 0.0` recovery draws and Tdew range checks; and
- returned `randn` deviates per stream k1..k10.

Static: no counter value is read by generation code. Counter writes occur
after an existing draw or branch verdict. The source give-up `println!`
remains unchanged.

## Acceptance-statistics schema decision

The metrics-version-1 field is `process.acceptance_statistics`, an array
in occurrence order. Each exiting `ranset` batch records `parameter`,
`month`, `year`, `ks_level`, `mean_level`, and `variance_level`. Existing
`ranset_quality_levels` outputs are copied without new floating-point
computation. Non-applicable `-1` mean/variance sentinels serialize as
`null`. Observed-mode parameter 9, which bypasses source QC, records an
accepted batch with all three statistics `null`.

The 31-year New Meadows vector records 3,348 accepted batches and seven
cap give-ups. The seventh is parameter 9/month 9/year 26: parameter 5 had
already reached the shared cap, so the later failing parameter is accepted
without another source print. This confirms that print counting would
undercount the source semantics.

## RANDN call-site audit

Static:

| Surface | Streams | Disposition |
|---|---|---|
| `Cbk7State::burn_observed` | k1..k9 | run path counted; legacy `burn` remains for direct fixture APIs |
| generation setup | k1, k2..k5, k7..k9 | counted before `GenState` construction, then accumulator moved into `GenState` |
| `initialize_ranset_streams` | k1..k6, k8..k10 | counted |
| `draw_ranset_value` | k1..k6, k8..k10 | counted per returned deviate |
| `gen_precip` recovery | k5 | counted and increments `v7_recovery_count` |
| `dstg` refill | k7 | 30 returned deviates per refill counted; internal open-interval retry iterations are not separate draws |
| observed `timepk` | k10 | counted |

Ran: the New Meadows exact draw census is pinned by
`faithful_run_emits_ordered_process_metrics_without_missing_draw_sites`:
`[12970, 17739, 17602, 17489, 124405, 11779, 50101, 12432, 17507,
263759]` for k1..k10.

## JSON Schema and edge vectors

`docs/specifications/quality-report.schema.json` is draft 2020-12 and
matches the Rust envelope field-for-field. Schema `properties` are written
in Rust serialization order; all report objects reject additional
properties. No dependency was added. A lightweight Rust structural
validator resolves the schema's `$ref` and `anyOf` forms and checks
required/additional keys, object/array/scalar types, and array shapes over
both post-hoc and run-emitted reports. Serde round-trips remain the exact
Rust-type check.

Ran edge vectors cover wrong mid-file field counts, non-numeric fields,
misordered dates, a zero-row table (typed rejection), n=2 precipitation
skew (`generated`, `abs_err`, and `rel_err` null in January with `n: 2`),
12 years split into decade `n_years` `[10, 2]` in groups A/B/C, the
single-storm envelope, and Fish Springs' trailing 2026 partial year with
`n_days: 188`.

## Gate evidence

Every successful command below completed with exit code 0.

| Evidence | Command | Result |
|---|---|---|
| Ran | `cargo fmt --check` | clean |
| Ran | `cargo clippy --all-targets -- -D warnings` | clean |
| Ran | `cargo test --release` | 87 passed, 0 failed; 12/12 golden outputs identical |
| Ran | two direct `cargo test --release --test ... -- --ignored` invocations: daily+format with absolute `CLIGEN_FMT_SWEEP`, then modes+par+storm+tap | 9 ignored identity tests passed, including 57,341,160 format fields |
| Ran | `cargo llvm-cov --workspace --lcov --output-path target/lcov.info` | 89.95% regions, 85.31% functions, 92.18% lines |
| Ran | `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above` | 292 functions; none above 30; `run_to_cli` maximum 29.0 |
| Ran | `cargo deny check` | advisories, bans, licenses, and sources all ok |

The first ignored-suite attempt used the kickoff's relative capture path;
daily identities passed, then the format test failed because integration
tests resolve that environment value from the crate directory. The
absolute-path daily+format run passed with exit code 0; the remaining
ignored binaries were run directly together and also passed with exit
code 0.

The first CRAP run failed: adding profile-to-QC mapping inside
`run_to_cli` raised CC to 31. Moving that mapping into the covered
`process_qc_filter` helper restored `run_to_cli` to CC/CRAP 29; coverage
and CRAP were regenerated and passed. No allow-list was used.

## What these gates do not cover

- They establish local and legacy-fixture identity, not cross-platform
  quality-report byte identity; R1 finding C-R1-002 addresses `powf`.
- The structural schema validator deliberately does not implement every
  draft-2020-12 validation keyword. It exercises the keywords used for
  field/type/shape conformance; external consumers should use a complete
  JSON Schema validator.
- Q3 owns `qc_filter: off` and fast-batch counterfactual verdicts. The
  active spec conflict is C-R1-003.
- Intake does not reject every impossible Gregorian date; C-R1-001.
