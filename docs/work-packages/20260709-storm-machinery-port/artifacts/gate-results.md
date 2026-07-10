# Gate Results — Stages S/C/R1

Evidence mode: Ran (2026-07-09). Exit codes checked directly.

| Gate | Command | Exit |
|---|---|---:|
| Format | `cargo fmt --check` | 0 |
| Lints | `cargo clippy --all-targets -- -D warnings` | 0 |
| Tests | `cargo test` (incl. `storm_chain_replays_fortran_samples`: 10 cases × 500-day prefixes, ~5,000 days, chain + timepk asserted) | 0 |
| Full storm replay | `cargo test --release --test storm_identity -- --ignored` — **80,906 days + 15,468 timepk calls** bit-identical across the 10 replay cases, with **all ten seed streams asserted per record** (k7 and k10 are internal in this loop) | 0 |
| Coverage | `cargo llvm-cov` | 0 |
| CRAP | `cargo crap --fail-above` — 144 functions, none above 30 | 0 |

## Replay-protocol notes (established this stage)

- The chain runs after `day_gen`'s in-place F→C conversion
  (`cligen.f:3110-3112`) — the mean-temp `xmav` floor reads Celsius;
  the replay transcribes the conversion between clgen and the chain
  (caught live: the first wet January day of new-meadows floors
  `xmav` to 1.01 because the Celsius mean is ≤ 0).
- The `T` record's `k10` is timepk **exit** state (tap writes before
  return): post-draw under `iopt = 6`, unchanged on the batch path.
- The `jd = dax` equivalence holds for the daily modes only; the
  single-storm mode jumps to the storm date (jd = 15, dax = 1).
- `windg` is not driven in this loop (nothing in the chain consumes
  it); `v9` stays a per-record external input, exactly as in the
  item-5 cg replay.
- `r5monb` runs once in setup (main:878 order) so the chain's `alphb`
  calls read the converted `wi`.

## Transcendental census

`alog` only, both chain sites (`dur`, `r5p`) — already pinned
(`logf_pinned`, domain `1 − r1 ∈ (0,1)`). No new §1.3 adjudications.

## Stage C and R1 final gates

Evidence mode: Ran (2026-07-09). Each command's exit code was captured
directly; no tolerance was introduced or widened.

| Gate | Command | Result | Exit |
|---|---|---|---:|
| Format | `cargo fmt --check` | Clean | 0 |
| Lints | `cargo clippy --all-targets -- -D warnings` | No warnings | 0 |
| Tests | `cargo test` | 43 passed; seven evidence tests ignored by default | 0 |
| RNG/deviates full replay | `cargo test --release --test tap_identity -- --ignored --nocapture` | 19,784,955 `randn`; 26,402,148 `dstn1`; 30,268 `dstg`; 2,584 `ranset`, all bit-identical | 0 |
| Par/monthlies full replay | `cargo test --release --test par_state_identity -- --ignored --nocapture` | 380,436 `fouri2`; 275,452 `ryf2`; 36,889 `lintrp`, all bit-identical | 0 |
| Daily full replay | `cargo test --release --test daily_identity -- --ignored --nocapture` | 189,207 days; 72,130 `alphb`; 24 `r5monb`, all bit-identical | 0 |
| Storm full replay | `cargo test --release --test storm_identity -- --ignored --nocapture` | 189,207 days + 36,065 `timepk` calls across all 24 captures, all bit-identical | 0 |
| Coverage | `cargo llvm-cov --workspace --lcov --output-path target/lcov.info` | LCOV report written; `sing_stm` 100% | 0 |
| CRAP | `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above` | 148 functions; none above CRAP 30 | 0 |
| Storm manifest | Direct line-count + SHA-256 comparison against `tap-schema.md` | 48/48 sd/tp entries matched | 0 |

The ordinary storm suite additionally anchors typed `sing_stm` intake to
the committed `single-storm.inp`, exercises exact option-6 `-1`
defaulting and typed deferrals, and checks the fixture-unreachable option-7
override with explicitly labeled constructed arithmetic vectors.
