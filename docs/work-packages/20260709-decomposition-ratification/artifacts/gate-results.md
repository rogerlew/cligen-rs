# Gate Results — Decomposition Ratification

Evidence mode: Ran (commands executed at close, 2026-07-09).

| Gate | Result |
|---|---|
| `cargo fmt --check` | PASS |
| `cargo clippy --all-targets -- -D warnings` | PASS |
| `cargo test` | PASS (8 integration tests; no Rust code changed in this package) |
| Inventory rows carry source-line evidence | PASS — extraction tables + doc tables cite lines throughout |
| No `unread` markers on load-bearing units | PASS — rev 3 has none |
| Dead-code verdicts state call-graph evidence | PASS — `deadcode-adjudication.md`; independently confirmed by Codex incl. EXTERNAL/procedure-argument search |
| Codex review dispositioned before close | PASS — 3 findings accepted and applied (`review-codex.md`) |

## Post-close independent audit (Codex, 2026-07-09)

Dispatched against the already-closed package; executed as an audit.
Codex's run reported: `extract.py` re-run reproduced the committed
artifacts exactly; the precision census confirmed (391 `cligen.f` sites,
388 in QC/ACM, outside sites 1073/1074/1696); no unresolved markers,
dead-code evidence and review dispositions present; fmt/clippy/test
re-run green. No changes needed; worktree clean.
