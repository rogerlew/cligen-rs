# Gate Results — Stage S

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
