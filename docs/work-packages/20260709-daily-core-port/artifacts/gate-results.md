# Gate Results — Stages S and C

Evidence mode: Ran (2026-07-09). Exit codes checked directly; no command
was judged from piped or truncated output.

## Gate suite (Stage S state)

| Gate | Command | Exit |
|---|---|---:|
| Format | `cargo fmt --check` | 0 |
| Lints | `cargo clippy --all-targets -- -D warnings` | 0 |
| Tests | `cargo test` (incl. `clgen_replays_fortran_cg_samples`: 10 cases × 500-record committed prefixes, ~5,000 calls, every internal-state and output field bit-exact) | 0 |
| Full cg replay | `cargo test --release --test daily_identity -- --ignored` — **80,906 clgen calls** across the 10 replay cases, bit-identical (all seeds/rolling state/`l`/`mox`/`dax`/skew-clamp assertions + full generated surface per call) | 0 |
| Coverage | `cargo llvm-cov --workspace --lcov --output-path target/lcov.info` | 0 |
| CRAP | `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above` — 137 functions, none above 30 (`clgen` decomposed along source blocks: solar/precip/temps×2/radiation/interp-dispatch) | 0 |

## Gate suite (Stage C/R1 handback state)

| Gate | Command | Exit |
|---|---|---:|
| Format | `cargo fmt --check` | 0 |
| Lints | `cargo clippy --all-targets -- -D warnings` | 0 |
| Tests | `cargo test` — committed tap samples green for all four daily units plus the combined source-order replay (4,501 days; 1,552 internally-driven `alphb` calls) | 0 |
| RNG/deviate full streams | `cargo test --release --test tap_identity -- --ignored --nocapture` — 19,784,955 `randn`, 26,402,148 `dstn1`, 30,268 `dstg`, and 2,584 `ranset` calls bit-identical | 0 |
| Monthlies full streams | `cargo test --release --test par_state_identity -- --ignored --nocapture` — 380,436 `fouri2`, 275,452 `ryf2`, and 36,889 `lintrp` calls bit-identical | 0 |
| Daily full streams | `cargo test --release --test daily_identity -- --ignored --nocapture` — all 24 capture runs: 189,207 `clgen`/`windg` calls, 72,130 `alphb` calls, 24 `r5monb` snapshots; standalone and combined replays bit-identical | 0 |
| Coverage | `cargo llvm-cov --workspace --lcov --output-path target/lcov.info` | 0 |
| CRAP | `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above` — 141 functions, zero above 30 (`windg`: CC/CRAP 10 at 100% coverage) | 0 |
| Capture integrity | SHA-256 comparison of all 96 manifest records (`cg`/`wg`/`ab`/`r5` × 24 runs) against `artifacts/tap-runs/` | 0 |

The full-stream runs print the source-faithful RANSET quality warnings
for captured regeneration paths. Those diagnostics do not indicate test
failures; every replay and its direct command exit remained zero.

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

## Stage C replay upgrade

- The standalone unit fixtures pin `windg` (`wv`, `th`, `v9`, `j`),
  `alphb` (`k7` entry and `r1` exit), and `r5monb` (all 12 converted
  `wi` values) before the combined harness calls them.
- The combined harness runs `r5monb` once, then `clgen` → `windg` →
  `alphb` in source order. It normalizes non-positive rain exactly as
  `day_gen:3114-3116`, calls `alphb` once for positive rain and again
  when `iopt >= 4`, and upgrades both `k7` and `v9` from injected inputs
  to per-record internal-state assertions.
- The 10 committed cases remain fast sample gates. The ignored suites
  enumerate the separate 24-case full matrix from `tap-schema.md`,
  including both hemispheres, observed padded/truncated input, all four
  interpolation modes, both seed variants, and both single-storm runs.
