# A10M4O1 scaffold gates

Date: 2026-07-17
Result: `PASS`

## Review gates

- Architecture round 1: `HOLD`; AR-01--AR-08 accepted with no waivers.
- HPC safety round 1: `ACCEPT-WITH-CHANGES`; HS-01--HS-10 accepted with no
  waivers.
- Architecture round 2 found R2-AR-01, the valid-prefix ledger rollback
  overclaim. It was accepted by adding exclusive genesis, published head
  checkpoints, mandatory pre-spend scheduler reconciliation, and an explicit
  same-domain trust-boundary disclosure.
- Final architecture convergence: `CONVERGED`, no remaining P1/P2 gap.
- Final HPC safety convergence: `CONVERGED`, no remaining P1/P2 regression.

## Local validation

```text
python3 -m py_compile artifacts/verify-scaffold.py
  PASS

python3 artifacts/verify-scaffold.py
  PASS — 15 lessons; 0 remote allocations; canonical v1 raw SHA-256
  99a7df3d4192ccf9a585944f62501087126c855a4fe59964aa6106afe42ae312

python3 -m unittest discover -s research/a10/lemhi_toolkit/tests -v
  PASS — 23 tests

python3 -m py_compile research/a10/lemhi_toolkit/*.py
for script in research/a10/lemhi_toolkit/remote/*.sh; do sh -n "$script"; done
  PASS

python3 -m unittest research.a10.test_m3_contract -v
python3 .../verify-a10m3.py
  PASS — 15 tests; 8 authorities; 4 schemas; 15 vectors; 560 GPU-hour ceiling

git diff --check
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
  PASS
```

Coverage/CRAP was not triggered because scaffolding changes no production
function under `crates/`. No command initiated MFA, SSH, Slurm, remote writes,
GPU allocation, development-target access, or confirmation access.
