# Gate Results — Stage S (spine)

Date: 2026-07-09
Evidence mode: **executional** — every row below is a command run this
session; exit codes checked directly, never piped through `tail`.

| Gate | Command | Result | Exit |
|---|---|---|---|
| Format | `cargo fmt --check` | clean | 0 |
| Lints | `cargo clippy --all-targets -- -D warnings` | clean (one `nonminimal_bool` fixed: the Gregorian `.not.(mod-100==0)` transcribed to `!= 0`, comment cites the source form) | 0 |
| Tests | `cargo test --release` | all suites green; includes `cli_parity::goldens_reproduced_byte_identically` — **12/12 golden `.cli` byte-identical from typed run inputs** — and `format_identity::f_edit_matches_gfortran_sample` (180,000 committed-sample fields, 0 mismatches) | 0 |
| Identity suites | `CLIGEN_FMT_SWEEP=<capture> cargo test --release -- --ignored` | tap (`full_tap_streams`), monthlies, storm, daily/cg/combined, ranset, cold-start replay (`cold_start_full_runs_bit_identical`), **full format sweep `f_edit_matches_gfortran_full_sweep`: 57,341,160 fields, 0 mismatches (15.8 s)** | 0 |
| Coverage | `cargo llvm-cov` | TOTAL 90.57% regions / 91.94% functions / 91.97% lines | 0 |
| CRAP | `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above` | 164 functions; none above threshold 30. Top: `run_to_cli` 29.0 (CC 29, 98.2% cov), `ryf1` 21.3, `gratio_core` 20.0 | 0 |

Not run: `cargo deny` (unchanged dependency set — no new dependencies
added by this stage; last clean run stands from the prior package).

## Notes

- The full-sweep format test is `#[ignore]`d and env-gated
  (`CLIGEN_FMT_SWEEP`); the committed 20,000-line sample runs in the
  default suite. Capture SHA-256 in the adjudication artifact.
- `run_to_cli` at CRAP 29.0 is the highest score in the crate — under
  threshold, but Stage C must not grow it: runspec→`RunInputs`
  resolution belongs in its own module (see kickoff §Structure).
- `cligen-cli-diff` binary helpers show 0% coverage (dev tool,
  pre-existing).
