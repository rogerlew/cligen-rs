# CLI Runtime Benchmark Against Legacy CLIGEN

Date: 2026-07-10
Evidence mode: Ran

## Result

On this host, the release Rust `cligen run` process was slower than the
equivalent no-fast-math legacy process for every multi-year/observed case.
The two single-storm medians were effectively tied within this small
process-level measurement. The strongest regressions are the Jeogla and
Mt Wilson seed-17 workloads, at 6.21× and 4.63× legacy-to-Rust median
runtime respectively. This package diagnoses no cause and makes no
performance change; it establishes the reproducible baseline.

The sum of independently measured per-case medians was 5.626102 s for
Rust and 1.349938 s for legacy, making Rust 4.17× slower for this matrix
composite. This is a descriptive aggregate, not the median of one
combined process workload.

| Case | Rust median (s) | Legacy median (s) | Rust / legacy |
|---|---:|---:|---:|
| new-meadows-id-seed0 | 0.146527 | 0.094215 | 1.56× |
| new-meadows-id-seed17 | 0.097481 | 0.084252 | 1.16× |
| jeogla-au-seed0 | 0.109595 | 0.101745 | 1.08× |
| jeogla-au-seed17 | 3.791807 | 0.610949 | 6.21× |
| mt-wilson-ca-observed-seed0 | 0.098008 | 0.063964 | 1.53× |
| mt-wilson-ca-observed-seed17 | 1.201182 | 0.259190 | 4.63× |
| fish-springs-ut-observed-padded-seed0 | 0.032160 | 0.023468 | 1.37× |
| fish-springs-ut-observed-padded-seed17 | 0.062537 | 0.046946 | 1.33× |
| fish-springs-ut-observed-truncated-seed0 | 0.030724 | 0.021301 | 1.44× |
| fish-springs-ut-observed-truncated-seed17 | 0.051968 | 0.039645 | 1.31× |
| new-meadows-id-single-storm-seed0 | 0.002039 | 0.002054 | 0.99× |
| new-meadows-id-single-storm-seed17 | 0.002075 | 0.002208 | 0.94× |

## Method

The committed [`benchmark-cases.json`](benchmark-cases.json) maps each of
the twelve established runspec fixtures to its legacy argv/stdin workload
and golden `.cli` file. The runner creates fresh target-only legacy working
directories, removes the Rust runspec output before each process, and
computes SHA-256 after every warm-up and timed run. A mismatch aborts the
benchmark before it writes results.

Ran command:

```sh
cargo build --release --bin cligen
python3 scripts/bench_cli_runtime.py --build-legacy --samples 7 --warmups 1
```

Every one of the 12 legacy/Rust warm-up and timed outputs matched the
corresponding golden hash. Each implementation received one warm-up per
case and seven samples; Rust-first and legacy-first order alternated by
sample. Timing begins immediately before process creation and ends at
process exit, so it includes process startup, command intake, input reads,
generation, and the complete output write. Hashing occurs after timing.

## Provenance and limitations

- Host: `forest`, Linux 6.8.0-111-generic, glibc 2.39; Intel Xeon
  E5-2697 v2 @ 2.70 GHz; 48 logical CPUs. The process affinity mask was
  CPUs 0–47; no dedicated-core or frequency-governor control was available.
- Rust binary: `target/release/cligen`, SHA-256
  `6abf356f469ec0465cf065a46774b32602816e81fd9a3e226e7b5c1b6ea5db65`.
- Legacy: gfortran 14.2.0, built only under `target/` with
  `-O3 -ffp-contract=off -fprotect-parens -fno-fast-math`; SHA-256
  `e86a2ad3278a75f4d8706cf801c6dbbf22112d51812e5c782bb06d0feca3e3a8`.
  This is an optimized but no-fast-math comparison build, not the
  conservative `-O0` fixture producer. Its entire measured output matrix
  nevertheless matched the same goldens byte-for-byte.
- Reference source: `reference/cligen532/cligen.f`, SHA-256
  `3dfd51db98fedfbfb155d4227099cf9133043d4d699093268ed21ce16ec4267c`.

Raw per-sample data, means, and standard deviations are in
[`results.json`](results.json) and [`results.csv`](results.csv).
