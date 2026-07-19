# Gate results

Evidence mode: Ran on `rmm`, 2026-07-19.

- `python3 -m unittest discover -s research/a10/lemhi_toolkit/tests -v`:
  PASS, 55 tests.
- Remote shell `sh -n`: PASS.
- `artifacts/verify.py`: `A10M5O1_VERIFY_PASS`.
- Mismatched `gpus: 1` / `gpu:l40:2`: rejected with `PLAN_DRIFT` before
  adapter mutation.
- RTX A6000 under the L40 provider: rejected with `PLAN_DRIFT`.
- Two GPUs under the default one-device provider: rejected with `PLAN_DRIFT`.
- Two and four GPUs under the additive provider: accepted.
- Five GPUs under the additive provider: rejected with `PLAN_DRIFT`.
- Recovery GRES/count mismatch: rejected with `PLAN_DRIFT`.
- Four GPUs for 61 elapsed seconds: 244 actual GPU-seconds and five
  ceiling-rounded actual GPU-minutes.
- `git diff --check`: PASS.
- `cargo fmt --check`: PASS.
- `cargo clippy --all-targets -- -D warnings`: PASS.
- `cargo test`: PASS.

Coverage/CRAP was not required because no production function under `crates/`
changed.
