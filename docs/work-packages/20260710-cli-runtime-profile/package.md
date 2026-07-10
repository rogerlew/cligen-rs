# Profile the CLI Runtime Outlier

Status: `EXECUTED-COMPLETE`
Date: 2026-07-10
Evidence mode: Mixed

## Objective

Identify where the Rust CLI spends time in the Jeogla seed-17 workload that
the CLI runtime benchmark measured at 6.21× the no-fast-math legacy median.
Compare it with Jeogla seed 0 and with the legacy process, while preserving
the established golden-output workload identity.

## Scope

Included:

- A reproducible `perf` runner driven by the benchmark workload manifest.
- Counter profiles (five process samples each) and sampled call-graph
  reports for Rust and legacy Jeogla seed 0/17 runs.
- SHA-256 validation of every profiled output against the named golden,
  before a profile result is accepted.
- A report that distinguishes measured hot spots from hypotheses.

Excluded:

- Any optimization or behavior change.
- Profiling other fixture families, a cross-host claim, or a native-mode
  comparison.
- Modifying `reference/cligen532/`.

## Authority

- ADR-0001: faithful behavior remains pinned by the source and goldens;
  performance instrumentation does not authorize numerical changes.
- `20260710-cli-runtime-benchmark/artifacts/benchmark-cases.json`:
  legacy/runspec workload correspondence and output oracle.
- `perf(1)` process counters and sampled call graph, subject to host kernel
  availability.

## Plan

1. Declare the two seed-paired Jeogla workloads and measurement method.
2. Implement the profile runner with target-only legacy work directories,
   counter collection, sample reports, and hash checks.
3. Execute it against release Rust and the no-fast-math legacy build.
4. Record measured attribution, caveats, and package gates.

## Gates

- `cargo fmt --check`
- `cargo clippy --all-targets -- -D warnings`
- `cargo test --release`
- `perf stat` succeeds for all four implementation/case combinations,
  five times each.
- Every process output matches the selected golden SHA-256.
- `perf record` and text report succeed for all four combinations.

## Exit criteria

`EXECUTED-COMPLETE`: profile runner, counter data, sample reports, and an
evidence-labeled conclusion are committed. A legitimate hold identifies the
kernel-permission/tooling restriction and retains any completed counter
evidence.

## Artifacts

- `artifacts/profile-plan.md`
- `artifacts/perf-stat.json`
- `artifacts/{rust,legacy}-{seed0,seed17}.perf.txt`
- `artifacts/profile-report.md`
