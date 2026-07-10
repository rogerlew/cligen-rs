# Gate Results — Q3 qc_filter + Dissection

Date: 2026-07-10
Evidence mode: **Ran** (exit codes checked directly).

| Gate | Result | Exit |
|---|---|---|
| `cargo fmt --check` | clean | 0 |
| `cargo clippy --all-targets -- -D warnings` | clean | 0 |
| `cargo test --release` | **108 passed, 0 failed** — includes the 12-golden gates unchanged, `qc_filter` acceptance (explicit `faithful` byte-identical to the golden; `off` deterministic, divergent, self-declaring, counterfactual-priced 31×12×9 batches; runspec fail-closed vectors incl. the fast_batch_v0 rejection) | 0 |
| Ignored identity suites (absolute `CLIGEN_FMT_SWEEP`) | 9 passed, 0 failed | 0 |
| `cargo llvm-cov` + `cargo crap --fail-above` | 335 functions; none above 30; no allow-lists | 0 |
| `cargo deny check` | not re-run: **no dependency change in this package** (Cargo.lock untouched); the Q2 clean run stands | — |

## Campaign evidence (all Ran)

- Observed reference: Daymet v4 single-pixel, 46 years × 17 stations
  (raw SHA-256 pinned in `observed/observed-stats.json`); GHCN-Daily
  secondary passed the completeness screen on 8/17.
- Matrix: 102/102 runs exit 0 (`run-matrix.py` → `runs.json`;
  sidecars under `target/q3-matrix/`, `.cli` bytes hash-pinned in
  `runs.json`). Analysis strictly over the pre-registered surfaces
  (`analyze-matrix.py` → `matrix-analysis.json`).
- Generation-only timing: `timing-no-sidecar.json` (best-of-3,
  100 yr, `output.quality: false`).

## What these gates do not cover

- ADR-0003 is Proposed, not ratified — no default changed; the
  runspec surface is live but conditioning remains on by default.
- The observed-reference comparison inherits Daymet grid-vs-point
  character (§frontier-analysis sensitivities); the GHCN secondary
  covers 8/17 stations only.
- All timing is this Linux host; wepp1/FMA was not measured (see the
  Q4 adjudication's caveat).
- No independent review cycle has run on Q3/Q4 yet (operator directed
  execute-and-present; a Codex review pass can follow the
  adjudications).
