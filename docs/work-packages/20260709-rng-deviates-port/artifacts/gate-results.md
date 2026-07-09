# Gate Results — Stage S (spine)

Evidence mode: Ran (all commands executed 2026-07-09; Stage C re-runs
and extends this table).

## Bit-identity acceptance

| Gate | Result |
|---|---|
| Tap capture non-invasive | PASS — all 12 patched-binary runs byte-identical to committed goldens (`cmp`, per-case) |
| `randn` full-stream identity | PASS — **19,784,955** records, every entry-state→value pair bit-identical |
| `dstn1` full-stream identity | PASS — **26,402,148** records bit-identical |
| `dstg` full-stream replay | PASS — **30,268** records across 10 fixtures, sequential replay with per-record `k7`/`iarrct` state assertions and result bit-identity (QC-regeneration draws included by construction) |
| `-r` burn + warm-draw semantics | PASS — `Cbk7Seeds::burn` + one warm draw reaches the first `dstg` entry state on all 10 dg fixtures |
| Committed-sample tests (`cargo test`) | PASS — 4 tap-identity tests + 4 ks_tst vector tests + 8 cli_diff tests |

Full-stream command (release): `cargo test --release --test tap_identity
-- --ignored --nocapture` → `full-stream identity: randn=19784955
dstn1=26402148 dstg=30268`, 13.14 s.

## The transcendental adjudication (recorded decision)

First test run failed `dstn1` at 1 ULP (record 5 of the first sample).
Probe + exhaustive scan over all 26,402,148 captured `dstn1` records:
`libm` crate f32 `logf` diverges from the reference runtime (glibc 2.39)
on 1,975,439 records and `cosf` on 334,643; `std` (system libm) matched
the Fortran on **all** records. Resolution per ADR-0001 §4 ("unless
fixture evidence forces another choice"): `src/libm_pinned.rs`
transcribes the glibc/ARM `logf`/`cosf` algorithms (FMA-contracted as
the running glibc's x86-64 ifunc variants are built), verified
bit-exact over the full capture. f64 `pow`/`exp` remain on the `libm`
crate — proven identical through the `dstg` replay. Coding standard
§1.3 and AGENTS.md amended accordingly.

## Rust gates

| Gate | Result |
|---|---|
| `cargo fmt --check` | PASS |
| `cargo clippy --all-targets -- -D warnings` | PASS (exit 0 verified directly; faithful-shape lints suppressed per the new standard rule, targeted `#[allow]` with source citations) |
| `cargo test` | PASS — 6 suites ok |
| `cargo llvm-cov` + `cargo crap --fail-above` | PASS — 39 functions analyzed, none exceed CRAP 30 |

## Reference hygiene

`reference/cligen532/` untouched (patch applied to the gitignored
`tap-build/` copy only; `git status` clean for `reference/`).
