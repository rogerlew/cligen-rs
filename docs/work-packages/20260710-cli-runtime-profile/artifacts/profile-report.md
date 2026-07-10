# Jeogla Seed-17 CLI Profile

Date: 2026-07-10
Evidence mode: Ran, with inferences labeled below.

## Conclusion

**Measured:** the seed-17 gap is dominated by `ranset` and the Rust
compiler's software FMA implementation, not YAML intake or CLI text
formatting. On this Xeon E5-2697 v2 host, Rust's pinned `logf`/`cosf`
algorithm calls `f64::mul_add`; the sampled Rust executable resolves that
to `compiler_builtins::…::fma_fallback`. The seed-17 quality-control path
executes it vastly more often than seed 0.

**Inference:** the faithful FMA semantics required by the pinned
transcendental implementation are the immediate cause of the outlier on
this non-FMA CPU. The profile does not authorize replacing `mul_add`,
enabling fast math, or changing the faithful numeric path. Any remedy
must first be adjudicated against the full reference/tap corpus.

## Counter medians

Five independent `perf stat` process runs per cell, all with golden output
SHA-256 verification:

| Implementation / case | Task clock (ms) | Instructions | Cycles | Branches |
|---|---:|---:|---:|---:|
| Rust Jeogla seed 0 | 109.30 | 722.4 M | 329.9 M | 113.9 M |
| Legacy Jeogla seed 0 | 106.33 | 530.8 M | 307.7 M | 105.2 M |
| Rust Jeogla seed 17 | 3,583.15 | 26.723 B | 11.338 B | 3.819 B |
| Legacy Jeogla seed 17 | 552.33 | 3.497 B | 1.810 B | 429.2 M |

Measured ratios:

- Rust seed 17 / Rust seed 0: **32.8× task clock** and **37.0×
  instructions**.
- Legacy seed 17 / legacy seed 0: **5.2× task clock** and **6.6×
  instructions**.
- Rust seed 17 / legacy seed 17: **6.49× task clock** and **7.64×
  instructions**.

The output identity check passed for all 20 counter executions and all
four sampled-record executions (24 total). Therefore the sampled work
compares identical `.cli` outputs, not divergent trajectories.

## Sampled call-graph attribution

`perf record -F 999 -g --call-graph dwarf` captured zero lost samples.

- Rust seed 17: `fma_fallback` is 60.15% self time and named `fma` is
  another 5.86%; both call chains run through `cligen::rng::ranset`.
  `ranset` itself is 21.90% self time. The report has 3K samples.
- Rust seed 0: FMA fallback is already 32.88%, but `ranset` is only
  4.69%; formatting/string symbols make up several visible single-digit
  shares. The report has 140 samples.
- Legacy seed 17: the main work is `ranset_` (31.15%), `randn_`
  (16.73%), glibc `__cosf_sse2` (11.11%), `__logf_sse2` (9.48%), and
  `ks_tst_` (5.36%). The report has 612 samples. It has no software FMA
  fallback symbol.

The call site is consistent with the pinned-transcendental module: its
header records that `mul_add` preserves the reference runtime's contracted
operations, and `dstn1` is called twice per generated normal deviate in
the source-shaped `ranset` accumulation. Seed-17 QC re-does magnify those
calls; the source's re-do protocol is at `cligen.f:4269-4332`.

## Reproduction

```sh
cargo build --release --bin cligen
python3 scripts/profile_cli_runtime.py --build-legacy --repetitions 5
```

The legacy build is target-only gfortran 14.2.0 with `-O3
-ffp-contract=off -fprotect-parens -fno-fast-math`. Exact binary/source
hashes, event samples, and build command are in
[`perf-stat.json`](perf-stat.json); text reports are
[`rust-seed0.perf.txt`](rust-seed0.perf.txt),
[`rust-seed17.perf.txt`](rust-seed17.perf.txt),
[`legacy-seed0.perf.txt`](legacy-seed0.perf.txt), and
[`legacy-seed17.perf.txt`](legacy-seed17.perf.txt).

## Limitations

This is one shared, 48-logical-CPU host without a fixed governor or a
dedicated core. The sampling attribution is nevertheless stable enough to
separate the seed-specific FMA/ranset work from formatting and interface
cost. It is a diagnosis baseline, not a portability or optimization claim.
