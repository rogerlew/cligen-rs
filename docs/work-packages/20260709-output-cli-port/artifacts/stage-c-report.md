# Stage C Report — Runspec Intake and `cligen` Binary

Date: 2026-07-09
Executor: Codex
Evidence mode: executional unless marked Static.

## Delivered

- `cligen::runspec`: schema-versioned, deny-unknown-field YAML intake;
  field-addressable validation; `(document, base_dir)` lexical-path
  resolution; `.par`/`.prn` parsing; defaults; canonical header echo;
  and non-interactive overwrite handling.
- The `cligen` binary with `run <inp.yaml>` and `validate <inp.yaml>`.
  Validation opens/parses declared inputs and deliberately neither stats
  nor creates the output path.
- Published [`runspec.schema.json`](../../../specifications/runspec.schema.json)
  and 12 golden `inp.yaml` fixtures under
  `crates/cligen/tests/fixtures/runspec/`.
- Binary-level golden parity plus fail-closed/schema/orchestration
  vectors. They include design storm, both fixture-unreachable
  interpolation choices, explicit observed-year controls, canonical
  echo, both overwrite branches, source storm-calendar dates, and
  invoked-path (symlink) resolution.
- Explicit `deny.toml` policy for the workspace's Apache-2.0, MIT,
  BSL-1.0, and Unicode-3.0 dependency licenses.

## Gate record

| Evidence | Result |
|---|---|
| Ran: `cargo fmt --check` | pass (exit 0) |
| Ran: `cargo clippy --all-targets -- -D warnings` | pass (exit 0) |
| Ran: `cargo test --release` | pass (exit 0); includes `runspec_cli` 12/12 binary golden parity and 9 runspec vectors |
| Ran: `CLIGEN_FMT_SWEEP=/home/workdir/cligen-rs/target/stage-c-fmt/fmt_pairs.txt cargo test --release -- --ignored --quiet` | pass; ignored identity suites and 57,341,160-field formatting sweep completed |
| Ran: format probe build | `gfortran 14.2.0`, `-O0 -ffp-contract=off -fprotect-parens -fno-fast-math`; 6,371,240 lines, SHA-256 `df8596f4e105fcfb5df156efea08e759b149e49b9c945b7e61c011d61a877777` |
| Ran: `cargo llvm-cov --workspace --lcov --output-path target/lcov.info` | pass (exit 0); wrote `target/lcov.info` |
| Ran: `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above` | pass (exit 0); 217 functions analyzed, 0 above CRAP 30 |
| Ran: `cargo deny check` | pass (exit 0): advisories, bans, licenses, and sources all OK |
| Static: schema/link check | `runspec.schema.json` is valid JSON (loaded in `runspec_vectors`) and is linked from SPEC-RUNSPEC |

The first generic ignored-suite invocation correctly failed before a
`CLIGEN_FMT_SWEEP` path was supplied; it did not become evidence. The
captured probe above was regenerated in ignored `target/` storage and
the suite was then rerun successfully with its absolute path.
