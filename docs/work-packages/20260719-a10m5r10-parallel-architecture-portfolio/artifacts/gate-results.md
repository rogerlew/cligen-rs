# Gate results

- prospective science and machine freeze: PASS
- complete 1,200/240 core-plus-`srad` calendar preflight: PASS
- exact six-control reconstruction: PASS
- control publication and cleanup: PASS
- all ten single-attempt candidate roles submitted: PASS
- eight candidate science publications: FAIL (environment bootstrap)
- physics K1/K2 three-seed science and all-240 evaluation: PASS
- all-configuration matrix complete: FAIL
- eligibility/Pareto selector replay: NOT RUN (correct fail-closed behavior)
- protected roles sealed: PASS
- resource ceiling: PASS (103 of 935 charged GPU-minutes)
- sanitized collection: PASS
- job-local and durable cleanup: PASS
- toolkit terminal close: PASS
- committed operational result verifier: PASS
- Python compilation, shell syntax, and JSON parsing: PASS
- `git diff --check`: PASS
- `cargo fmt --check`: PASS
- `cargo clippy --all-targets -- -D warnings`: PASS
- `cargo test`: PASS

Coverage/CRAP is not applicable because no production function under `crates/`
changed.
