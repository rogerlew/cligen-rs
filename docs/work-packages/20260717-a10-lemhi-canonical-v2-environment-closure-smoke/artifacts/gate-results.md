# Gate results

| Gate | Result |
|---|---|
| Environment entry diagnosis and closure | PASS (`LD_LIBRARY_PATH` present, then cleared) |
| CPython 3.11.15 / NumPy 2.2.6 / PyTorch 2.7.1+cu128 | PASS |
| Exactly one L40, CUDA autograd, checkpoint | PASS |
| Rust 1.92 locked offline metadata/build | PASS |
| Loader, capacity, and supervisor paths | PASS |
| Scheduler settlement and exact cleanup | PASS |
| Candidate Cargo-vendor archive SHA-256 | FAIL (`8f69ea...` vs `13d7f4...`) |
| Smoke attestation/designation | PROHIBITED |

Terminal: `HOLD-A10-CANONICAL-V2-SMOKE-ASSET-IDENTITY`.
