# CLI Runtime Profile Closeout

Date: 2026-07-10
Evidence mode: Ran, with interpretations labeled in the package report.

## Verdict

**CLOSE — `EXECUTED-COMPLETE`.** The package met its profile and
cross-host follow-on gates without changing generator behavior.

## Delivered evidence

- Five `perf stat` samples and one sampled call graph for each of Rust and
  legacy Jeogla seed 0/17 executions on the Xeon E5-2697 v2 baseline.
- Golden SHA-256 checks passed for all 24 profiled executions.
- The full 12-case benchmark matrix ran on `wepp1` at the recorded `main`
  commit, with seven samples plus one warm-up per implementation and 192
  accepted golden-verified executions.
- `wepp1` reduced the sum of per-case Rust medians from 5.626 s to 2.295 s,
  but seed-17 outliers remained. The package therefore identifies a
  hypothesis, not an optimization or a stochastic-equivalence result.

## Gates

The evidence-only follow-on re-ran `cargo fmt --check`,
`cargo clippy --all-targets -- -D warnings`, and `cargo test`; all passed.
The original profile runner's package gates and artifacts remain recorded in
[`package.md`](../package.md) and
[`profile-report.md`](profile-report.md).

## Follow-on

The next package, `20260710-fast-batch-rng-spike`, introduces an explicitly
labeled non-faithful batch-RNG profile solely to measure the performance
effect of bypassing `ranset` QC retries. It does not carry a stochastic
parity claim.
