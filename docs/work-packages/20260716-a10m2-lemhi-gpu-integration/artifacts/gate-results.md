# Gate results

Date: 2026-07-16 PDT
Host: `rmm` (Apple M1, 16 GB)

## Evidence gates

- A10M0 published predecessor terminal — PASS.
- Both SSH masters live before execution — PASS.
- Remote staged source hashes — PASS for all nine files in both attempts.
- Attempt 1013515 manifest versus published `6c92102` — PASS.
- Attempt 1013516 manifest versus published `2d4a014` — PASS.
- Typed `gpu:l40:1` scheduling on `gpu-icrews` — PASS.
- One L40 and driver/toolkit identity — PASS.
- CUDA compile/kernel smoke — FAIL; terminal hold recorded.
- Fail-closed stop before J2--J4b — PASS.
- Resource ceiling — PASS: 20 submitted GPU-minutes, 0.0167 actual
  GPU-minute, below one GPU-hour.
- Exact remote cleanup and no remaining user job — PASS.
- Sensitive username/path/credential scan — PASS.
- Review with zero open P1/P2 — PASS.

## Static and repository gates

- `bash -n` on all Slurm/keepalive shell — PASS. `shellcheck` was not installed
  on `rmm`; no result is claimed.
- Python bytecode compilation for all job sources — PASS under isolated
  `/tmp` bytecode cache.
- `git diff --check` — PASS.
- `cargo fmt --check` — PASS.
- `cargo clippy --all-targets -- -D warnings` — PASS.
- `cargo test` — PASS; registered evidence-only tests remained ignored.

Rust environment: Cargo 1.97.1 and rustc 1.97.1,
`stable-aarch64-apple-darwin`. No production function changed, so the
coverage/CRAP gate is not triggered.
