# Execution gates

## Scientific and operational gates

| Gate | Result |
|---|---|
| Published replay source `009d87b` equals `origin/main` at execution | PASS |
| R13R1 source is ancestor of replay source | PASS |
| Raw plan, plan receipt, collection, and asset manifest match committed pin | PASS |
| Reconstructed semantic SHA-256 equals plan ID `2dfc598e...` | PASS |
| Semantic allowlist exactly partitions collection present/absent rosters | PASS |
| Comparator, corpus, data root, selector assets, and PRISM provenance | PASS |
| Two isolated selector passes byte-identical | PASS |
| Protected and confirmation roles sealed | PASS |
| Cleanup after replay; remote absent and job-local absence verified | PASS |
| Toolkit terminal `LEMHI-TOOLKIT-RUN-CLOSED` | PASS |

The selector gate completed honestly with the HOLD terminal. A HOLD is the
scientific result, not a failed execution gate.

## Accounting

All three role receipts report `passed: true`: 20 GPU-minutes for control,
84 for the continuous hierarchy, and 81 for the shared slow state. Total
charged compute was 185 GPU-minutes against the 515-minute ceiling.

## Repository and package validation

Ran on the closeout working tree on 2026-07-20:

| Command | Result |
|---|---|
| `python3 .../artifacts/test_replay_authentication.py` | PASS |
| Python AST parse of replay and focused test | PASS |
| `cargo fmt --check` | PASS |
| `cargo clippy --all-targets -- -D warnings` | PASS |
| `cargo test` | PASS |
| `git diff --check` | PASS |

No production function under `crates/` changed, so coverage/CRAP gates do not
apply to this package.
