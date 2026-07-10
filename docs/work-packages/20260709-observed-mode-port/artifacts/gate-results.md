# Gate Results — Stages S/C/R1

Evidence mode: Ran (2026-07-09). Exit codes checked directly.

| Gate | Command | Exit |
|---|---|---:|
| Format / Lints / Tests | `cargo fmt --check`; `clippy -D warnings`; `cargo test` (incl. the cold-start sample gate: 10 cases × first ~400 days from block-data seeds, ~3,700 rows) | 0 / 0 / 0 |
| **Cold-start full replay** | `cargo test --release --test modes_identity -- --ignored` — **80,906 days across the 10 replay cases with ZERO injected state**: block-data seeds (+ `-r` burn) → `sta_parms` → the ported main setup → `day_gen` year by year, every `DailyRow` bit-equal to the capture-derived expectation | 0 |
| Coverage / CRAP | `cargo llvm-cov`; `cargo crap --fail-above` — 156 functions, none above 30 | 0 |

## What cold start proves

Every prior suite injected some captured state (first-record seeds,
per-day externals). This gate injects none: the run derives from the
`.par`/`.prn` bytes and the seed constants alone. It transitively
re-verifies the entire stack — parse, setup, ranset batches, clgen,
windg, the storm chain, timepk, the observed sentinel/EOF protocol —
through the production `day_gen` driver rather than test harness
loops. The truncated observed case exercises the 5.323 EOF stop
mid-year; the padded case exercises the `q_gen_started` stop at year
end; both terminate exactly where the captures end (asserted).

## Notes

- Year plans `(iyear, ntd, nbt)` come from the captured B-lines; the
  `wxr_gen` year loop (leap rules, per-year ccl1 zeroing — the
  zeroing is transcribed in the harness with the source cited) is
  item 8.
- No new transcendentals; no new taps (the existing 24-run captures
  cover the whole surface).

## Stage C and R1 final gates

Evidence mode: Ran (2026-07-09). Each command's exit code was captured
directly; no tolerance was introduced or widened.

| Gate | Command | Result | Exit |
|---|---|---|---:|
| Format | `cargo fmt --check` | Clean | 0 |
| Lints | `cargo clippy --all-targets -- -D warnings` | No warnings | 0 |
| Tests | `cargo test` | 48 passed; eight evidence tests ignored by default | 0 |
| RNG/deviates full replay | `cargo test --release --test tap_identity -- --ignored --nocapture` | 19,784,955 `randn`; 26,402,148 `dstn1`; 30,268 `dstg`; 2,584 `ranset`, all bit-identical | 0 |
| Par/monthlies full replay | `cargo test --release --test par_state_identity -- --ignored --nocapture` | 380,436 `fouri2`; 275,452 `ryf2`; 36,889 `lintrp`, all bit-identical | 0 |
| Daily full replay | `cargo test --release --test daily_identity -- --ignored --nocapture` | 189,207 days; 72,130 `alphb`; 24 `r5monb`, all bit-identical | 0 |
| Storm full replay | `cargo test --release --test storm_identity -- --ignored --nocapture` | 189,207 days + 36,065 `timepk` calls, all bit-identical | 0 |
| Cold-start mode replay | `cargo test --release --test modes_identity -- --ignored --nocapture` | 189,207 days across all 24 captures, zero injected state; every case's count, final date, and exit matched | 0 |
| Coverage | `cargo llvm-cov --workspace --lcov --output-path target/lcov.info` | LCOV report written; `day_gen` 95.0% | 0 |
| CRAP | `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above` | 156 functions; none above CRAP 30 (`day_gen` 19.0) | 0 |
| Documentation | `markdown-doc lint` | Repository Markdown clean | 0 |

The release commands execute all eight ignored evidence tests across five
integration-test binaries. Their source-faithful RANSET quality warnings are
expected diagnostics; every direct command exit was zero.

The mode edge suite covers short-record `PAD='YES'`, all-blank fields,
nonnumeric and non-ASCII rejection, LF/CRLF equivalence, missing observed
input, and the main-program `nt = 0` initialization. The full gate refuses
extra rows after a captured endpoint rather than silently truncating them.
