# CLI Runtime Benchmark Against Legacy CLIGEN

Status: `EXECUTED-COMPLETE`
Date: 2026-07-10
Evidence mode: Mixed

## Objective

Measure end-to-end process runtime of the faithful Rust `cligen run`
surface against a no-fast-math build of the vendored CLIGEN 5.32.3 legacy
binary. The result is a reproducible assessment, not a throughput claim
outside the measured host and fixture matrix.

## Scope

Included:

- A benchmark manifest covering all 12 byte-parity goldens and recording
  both the runspec invocation and the corresponding legacy argv/stdin
  interaction.
- A standard-library benchmark runner that builds the legacy binary only
  into `target/`, warms each process command, alternates timed order,
  validates every output SHA-256 against its golden, and emits JSON/CSV
  results.
- One measured execution with host, compiler, binary, and source
  provenance recorded.

Excluded:

- Any change to generator behavior or the read-only `reference/` tree.
- A cross-machine performance claim, profiler-guided optimization, or a
  native-mode comparison.

## Authority

- ADR-0001 §§1 and 4: the vendored Fortran is source authority and its
  build provenance is evidence-bearing.
- SPEC-RUNSPEC: the Rust command is `cligen run <inp.yaml>`; the legacy
  invocation is used only as a measurement baseline, not as a public
  compatibility surface.
- `docs/work-packages/20260709-golden-fixture-harness/artifacts/fixture-runs.tsv`
  and its golden SHA-256 manifest define the equivalent workloads.

## Plan

1. Record the 12 workload mappings before writing the runner.
2. Implement a target-only legacy build plus alternating process-time
   harness with golden-hash preflight and result serialization.
3. Build release Rust and legacy binaries, execute the measurement, and
   record the statistics with exact commands/provenance.
4. Run the relevant Rust quality gates and inspect the runner output.

## Gates

- `cargo fmt --check`
- `cargo clippy --all-targets -- -D warnings`
- `cargo test --release`
- Benchmark preflight: every legacy and Rust output SHA-256 matches its
  named golden before timing results are accepted.
- Benchmark execution: 1 warm-up and 7 alternating timed samples per
  implementation/case, with JSON and CSV result artifacts.

## Exit criteria

`EXECUTED-COMPLETE`: the runner and workload manifest are committed, the
complete matrix preflight passes, and a report records median/mean/stddev
and legacy-to-Rust median ratio with reproducible provenance. A legitimate
hold names the binary/output identity failure or host limitation.

## Artifacts

- `artifacts/benchmark-cases.json` — fixture workload manifest.
- `artifacts/benchmark-report.md` — executed result and provenance.
- `artifacts/results.json`, `artifacts/results.csv` — raw timing summary.
