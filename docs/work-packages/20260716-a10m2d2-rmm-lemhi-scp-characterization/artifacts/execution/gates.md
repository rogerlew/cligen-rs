# A10M2D2 gate results

Run on 2026-07-16 from the completed execution worktree.

| Gate | Result | Note |
|---|---|---|
| Frozen driver | PASS | `stage1=complete` |
| Command/status ledger | PASS | 38 rows; only expected I256 status 124 is nonzero |
| Integrity ledger | PASS | 27 of 27 registered verdicts pass |
| Logical payload | PASS | 5,206,187,008 <= 5,368,709,120 bytes |
| Peak remote retention | PASS | approximately 1,938.503 MiB < 2 GiB |
| Remote cleanup | PASS | exact run absent |
| Local cleanup | PASS | exact fixture directory absent |
| Slurm/GPU use | PASS | zero jobs, allocations, and GPU time |
| Sensitive-data scan | PASS | no user identity/path, credential, Duo, key, or socket material |
| Review | PASS | zero open P1/P2 findings; two documented P3 findings |
| `bash -n` | PASS | frozen driver parses under Bash |
| Python bytecode compilation | PASS | timer compiles with Python 3 |
| `git diff --check` | PASS | no whitespace errors |
| `cargo fmt --check` | PASS | |
| `cargo clippy --all-targets -- -D warnings` | PASS | |
| `cargo test` | PASS | full suite passed with local-loopback permission |
| Coverage/CRAP | NOT TRIGGERED | no production function changed |

The first sandboxed `cargo test` attempt denied two tests permission to open
their loopback fixture servers (`Operation not permitted`). The full suite was
rerun with local-loopback permission and passed. This was an execution-sandbox
restriction, not a code or assertion failure.
