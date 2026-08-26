# A12R1 validation results

Source commit: `de1502ad4d80a7205ac128c24e1851a42380f5b7`

| Gate | Result |
|---|---|
| `cargo fmt --check` | PASS |
| `cargo clippy --all-targets -- -D warnings` | PASS |
| `cargo test` | PASS |
| `cargo llvm-cov --workspace --lcov --output-path target/lcov.info` | PASS |
| `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above` | PASS — 846 functions, 0 above 30 |
| Focused PRISM library tests | PASS — 21 |
| CLI parser test | PASS |
| Exact A12 default vector | PASS — exit 1, expected month-6 error, no final/staging path |
| Exact A12 explicit-repair vector | PASS — exit 0, warning, complete artifacts |
| Independent review | GO — no P0/P1 findings |
| Confirmation firewall | PASS — no confirmation target access |

The first LLVM-coverage attempt on the final logic was invalidated by a
concurrent independent-review coverage command removing the shared target
directory. It was discarded. The recorded final coverage run was performed
without concurrent target operations and passed; its LCOV SHA-256 is
`c07ca57b1e09c74d9471b5272922e3b8cb8484f13133b9d904df00c40f74b0b1`.
