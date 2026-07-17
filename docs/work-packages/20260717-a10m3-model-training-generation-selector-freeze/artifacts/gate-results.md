# Gate results

Evidence date: 2026-07-17

## Package gates

- `python3 -m py_compile research/a10/m3_contract.py
  research/a10/test_m3_contract.py .../verify-a10m3.py` — PASS.
- JSON parse over four A10M3 schemas and four package JSON artifacts — PASS.
- `python3 .../verify-a10m3.py` — PASS: 8 immutable authorities, 4 strict
  schemas, 15 executable vectors, and exact 560-hour resource reconciliation.
- Positive model/checkpoint/stream records — PASS.
- Unknown field, legacy runtime, parameter overflow, missing checkpoint RNG,
  and non-nested generation mutations — rejected.
- B0/B1, both-horizon, positive-margin, upper-confidence, missing-B1,
  noninferiority, breadth, runtime-label, and deterministic tie-break vectors —
  PASS.
- Runtime `4.999999 -> PASS`, `5.0 -> WARN`, `9.999999 -> WARN`, and
  `10.0 -> FAIL` — PASS using unrounded inputs.
- Candidate fits: 0. Candidate outputs: 0. Confirmation target access: false.
  GPU/Slurm allocations: 0.

## Repository gates

- `git diff --check` — PASS.
- `cargo fmt --check` — PASS.
- `cargo clippy --all-targets -- -D warnings` — PASS.
- `cargo test` — PASS; all non-ignored library, binary, integration, and doc
  tests passed. Evidence-only and external-data tests retained their registered
  ignored status.

Coverage/CRAP did not run because this package changes no production function
under `crates/`.
