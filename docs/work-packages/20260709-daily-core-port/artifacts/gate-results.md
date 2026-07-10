# Gate Results — Stage S

Evidence mode: Ran (2026-07-09). Exit codes checked directly.

## Gate suite (Stage S state)

| Gate | Command | Exit |
|---|---|---:|
| Format | `cargo fmt --check` | 0 |
| Lints | `cargo clippy --all-targets -- -D warnings` | 0 |
| Tests | `cargo test` (incl. `clgen_replays_fortran_cg_samples`: 10 cases × 500-record committed prefixes, ~5,000 calls, every internal-state and output field bit-exact) | 0 |
| Full cg replay | `cargo test --release --test daily_identity -- --ignored` — **80,906 clgen calls** across the 10 replay cases, bit-identical (all seeds/rolling state/`l`/`mox`/`dax`/skew-clamp assertions + full generated surface per call) | 0 |
| Coverage | `cargo llvm-cov --workspace --lcov --output-path target/lcov.info` | 0 |
| CRAP | `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above` — 137 functions, none above 30 (`clgen` decomposed along source blocks: solar/precip/temps×2/radiation/interp-dispatch) | 0 |

## Transcendental adjudication (Ran)

Recorded in transcendental-census.md: `libm` crate `tanf`/`acosf`/`expf`
all REJECTED against the reference runtime (2.06% / 79.6% / 0.69%
divergence over 8M-input sweeps each); pinned transcriptions
(`tanf_pinned`, `acosf_pinned`, `expf_pinned`) land **0 mismatches over
24.7M in-domain swept inputs** total. `expf_pinned` is exercised by
Stage C's `alphb`; it is landed and adjudicated now so Stage C consumes
a pinned function, not a candidate.

## Replay-protocol notes (established this stage)

- External per-record inputs (set from capture, not asserted): `mo`,
  `ida`, `nsim`, `msim`, observed `r(ida)`, entry `tmxg`/`tmng`
  (day_gen mutates them F→C in place between calls), `v9` (windg's
  rolling pair), `k7` (dstg via alphb), `k10` (timepk).
- Everything else is asserted per record before the call: `k1-k6`,
  `k8`, `k9`, `v1/v3/v5/v7/v11`, `l`, `mox`, `dax`, the clamped
  `rst(mo,3)` — desync localizes to the exact day.
- `-I1` replay must call `lintrp` before `clgen` per day
  (`day_gen:3090-3093`); the jd it needs equals clgen's post-boundary
  `dax`, which the C-line assertion re-verifies.
- The ported `ranset` runs live inside the replay at every month
  boundary (~2,650 calls across the full gate), reproducing every
  batch column consumed — cross-verified by the per-record column
  assertions.
