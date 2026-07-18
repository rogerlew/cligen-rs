# A10M5 gate results

## Scientific screen

- Exact 12-row grid and seed 147031: PASS.
- Accepted 98-object, 223,799,545-byte corpus identity: PASS for every row.
- Candidate-fit-only gradients and fit-validation gradient firewall: PASS.
- Finite proper scores, parameter ceiling, complete checkpoint state: PASS.
- Unforced support, exact prefixes, and generation order independence: PASS.
- CPU export, cold load, size, benchmark completeness, and runtime class: PASS.
- Benchmark dispersion: 11/12 PASS; `N0-l32-w128-d2-gpd` FAIL after its one
  rerun and two permitted paired discards.
- CPU-export RSS at or below 2 GiB: 0/12 PASS. Range was
  3,317,673,984--3,363,221,504 bytes.
- Promotion: zero; terminal `HOLD-A10-NO-VALID-NEURAL-FIT`.

## Operational lifecycle

- Warm gateway and target SSH masters: PASS.
- Typed L40 allocation and CUDA training: PASS.
- Sequential job-local capacity and cleanup: PASS after R2 diagnosis.
- Allowlisted collection and projection: PASS after amendments 007--009.
- Exact durable-root absence and toolkit close: PASS.
- Recovery: not invoked; reserve released.

## Repository gates

- A10M5 package verifier: PASS.
- Python compilation and 69 A10 research tests: PASS.
- `git diff --check`: PASS.
- `cargo fmt --check`: PASS.
- `cargo clippy --all-targets -- -D warnings`: PASS.
- `cargo test`: PASS.

Coverage/CRAP was not required because no production function under `crates/`
changed.
