# Fast Batch RNG Spike Benchmark

Date: 2026-07-10
Evidence mode: Ran. Interpretations are explicitly limited below.

## Conclusion

**Measured:** `fast_batch_v0` reduced the sum of the twelve per-case Rust
medians from **5.651 s** to **0.471 s** on the Xeon E5-2697 v2 host, a
**12.0x** speedup. The seed-17 outliers that motivated the profile collapse
most sharply: Jeogla changes from 3.807 s to 0.0715 s (**53.2x**) and Mt
Wilson observed changes from 1.211 s to 0.0636 s (**19.1x**).

**Measured:** every one of the 96 faithful process executions matched its
named golden SHA-256. Every one of the 96 fast-profile executions produced
the same per-case SHA-256 across the warm-up and seven samples, and passed
the UTF-8, required-profile-marker, CLI-header, daily-row shape, and finite
numeric-value checks.

**Inference:** the faithful monthly QC/retry protocol, rather than process
intake or output writing, is responsible for nearly all of the pathological
seed-17 tail on this non-FMA host. This first spike measures the combined
effect of bypassing that protocol and using a four-lane batch producer; it
does **not** isolate ISA SIMD throughput and does **not** establish
stochastic parity, calibration, or production suitability.

## Per-case medians

| Case | Faithful (s) | Fast batch (s) | Speedup |
|---|---:|---:|---:|
| New Meadows seed 0 | 0.148 | 0.0546 | 2.72x |
| New Meadows seed 17 | 0.0966 | 0.0544 | 1.78x |
| Jeogla seed 0 | 0.111 | 0.0721 | 1.54x |
| Jeogla seed 17 | 3.807 | 0.0715 | 53.2x |
| Mt Wilson observed seed 0 | 0.0963 | 0.0638 | 1.51x |
| Mt Wilson observed seed 17 | 1.211 | 0.0636 | 19.1x |
| Fish Springs padded seed 0 | 0.0325 | 0.0229 | 1.42x |
| Fish Springs padded seed 17 | 0.0617 | 0.0228 | 2.71x |
| Fish Springs truncated seed 0 | 0.0293 | 0.0206 | 1.42x |
| Fish Springs truncated seed 17 | 0.0531 | 0.0210 | 2.53x |
| New Meadows single storm seed 0 | 0.00194 | 0.00181 | 1.07x |
| New Meadows single storm seed 17 | 0.00199 | 0.00184 | 1.08x |
| **Sum of medians** | **5.651** | **0.471** | **12.0x** |

## What fast_batch_v0 changes

- Faithful runs use the original `ranset` implementation unchanged.
- The fast profile selects `MonthlyBatchBackend::FastBatchV0` only through
  `generation_profile: fast_batch_v0`.
- It derives four deterministic SplitMix64 lanes from the faithful
  post-burn, post-warm seed surface and fills all nine columns and 31 slots
  of the existing `Crandom3State.ranary` matrix with 24-bit f32 uniforms in
  the open interval `(0, 1)`.
- It does not run `ranset`'s K-S, normal-mean, normal-variance, or retry
  machinery, and does not advance its source seed streams during refill.
- It preserves downstream daily consumption, weather transforms, `dstg`,
  and output formatting. Its CLI header appends
  `--generation-profile fast-batch-v0` even if the runspec supplied a
  custom command echo.

The four lanes are a portable, safe batch layout; this package makes no
claim that a particular target emitted SIMD instructions. The speedup must
therefore be read as a first upper-bound measurement for this behavioral
change, not as a vectorization-only result.

## Reproduction

```sh
cargo build --release --bin cligen
python3 scripts/bench_fast_batch_runtime.py
```

The runner uses the established 12-case manifest, one warm-up, seven
alternating faithful/fast samples, and process-level timing. It rejects a
faithful golden mismatch, a missing/malformed fast output, an absent profile
marker, or a fast-output hash that changes between runs. Exact raw samples,
binary and manifest hashes, host metadata, and per-case fast output hashes
are in [`fast-batch-results.json`](fast-batch-results.json), with the compact
table in [`fast-batch-results.csv`](fast-batch-results.csv).

## Limitations and next decision

This was one shared 48-logical-CPU Xeon E5-2697 v2 host without CPU pinning
or a fixed governor. More importantly, deterministic repeatability is not
stochastic parity. A follow-on campaign must compare distributional and
downstream properties over a declared seed × station corpus before this
profile can be recommended beyond experimentation.
