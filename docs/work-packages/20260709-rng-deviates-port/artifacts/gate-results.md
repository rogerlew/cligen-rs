# Gate Results — Stages S, C, and R1

Evidence mode: Ran (all commands executed 2026-07-09; Stage C re-runs
and extends the Stage S results below).

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
bit-exact over the full capture. f64 `pow` and `dstg`'s `exp` remain on
the `libm` crate — proven identical through the `dstg` replay. Stage C
later adjudicated ACM's broader `exp` domain separately (below). Coding
standard §1.3 and AGENTS.md were amended accordingly.

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

## Stage C fixture and identity acceptance

| Gate | Result |
|---|---|
| Stage C tap build | PASS (exit 0) — GNU Fortran 14.2.0, pinned `-O0 -ffp-contract=off -fprotect-parens -fno-fast-math` profile |
| Final direct-vector non-invasiveness | PASS (exit 0) — `new-meadows-id-seed0` generated `.cli` byte-identical by direct `cmp`; initial additive patch also passed all 12 cases |
| Calendar/ACM/QC direct fixture | PASS — 919 copied-Fortran records; 804 calendar results, 71 ACM scalar/CDF/cumulative results plus exact reverse traces, and 6 confidence results |
| `ranset` committed replay | PASS — 122 complete calls across all 12 cases, every captured entry/exit state, `ranary`, accumulator, and QC bin asserted |
| `ranset` full replay | PASS — **2,584** complete calls across all 12 cases; exact seed consumption, SAVE state, common-block state, and QC-regeneration behavior |
| `ranset(mox=0)` decision | PASS — unreachable in the live call graph, exact under-run aliases characterized, Rust fails closed; see `ranset-mox0-characterization.md` |
| ACM transcendental adjudication | PASS — direct reference vectors retained exact f64 `log`/`sin`; `libm::exp(-10)` one-ULP hold resolved with pinned ARM scalar `exp`, then exact vectors |

Full ignored command (release), run as a separate process:
`cargo test --release --test tap_identity -- --ignored --nocapture`.
Exit 0 in 15.98 s process wall time / 13.81 s test time:

```
full ranset replay: calls=2584
full-stream identity: randn=19784955 dstn1=26402148 dstg=30268
test result: ok. 2 passed; 0 failed; 0 ignored; 6 filtered out
```

## Post-R1 Rust gates

Each command below was run separately after all accepted R1 fixes; the
reported status is the command's direct exit code, not a pipeline status.

| Gate | Result |
|---|---|
| `cargo fmt --check` | PASS (exit 0) |
| `cargo clippy --all-targets -- -D warnings` | PASS (exit 0) |
| `cargo test` | PASS (exit 0) — 26 passed, 0 failed, 2 ignored |
| `cargo test --release --test tap_identity -- --ignored --nocapture` | PASS (exit 0) — both complete stream gates above |
| `cargo llvm-cov --workspace --lcov --output-path target/lcov.info` | PASS (exit 0) |
| `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above` | PASS (exit 0) — 98 production functions analyzed, 0 above CRAP 30 |

## Stage R1

Ran + Static: six findings (2 High, 3 Medium, 1 Low), all accepted and
fixed; full dispositions and source/port line evidence are in
`review-codex.md`. The post-review gates above are green. Stage R2 remains
pending and is the package-closing review.

Reference hygiene was rechecked after Stage C/R1: `git diff --
reference/cligen532` is empty. Both tap patches were applied only to ignored
copied trees; the vendored reference remains unchanged.
