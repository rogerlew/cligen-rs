# Scaffold gates

```sh
python3 docs/work-packages/20260720-a10m5r13r1-admission-controller-materialization-remedy/artifacts/verify_freeze.py \
  --science-python /Users/roger/.cache/cligen-rs/a10m5r13-scaffold-python/bin/python \
  --real-parent-assets /Users/roger/.cache/cligen-rs/a10m5r13-selector-aligned-continuous-hierarchy/assets
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
```

The verifier creates neither authority nor scheduler state.

## Results

| Gate | Result |
|---|---|
| Full pinned freeze verifier | PASS |
| Exact 46-asset real-parent preparation | PASS |
| Admission receipt and inherited-source behavioral tests | PASS |
| Builder and transitive-builder authentication | PASS |
| Replay manifest metadata and byte-drift tests | PASS |
| Calendar, selector loss, and staged science self-tests | PASS |
| `cargo fmt --check` | PASS |
| `cargo clippy --all-targets -- -D warnings` | PASS |
| `cargo test` | PASS |
