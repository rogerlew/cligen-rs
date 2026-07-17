# Scaffold validation

Date: 2026-07-17 PDT

- warm `login-ui` and `lemhi` control masters: PASS;
- noninteractive Lemhi hostname/queue probe: PASS, no user job present;
- canonical Python 3.11.11 and CUDA 12.8 paths: PASS;
- unchanged CUDA source identity against original A10M2 J1:
  `5913c87819a6c4f1451c564102c771051a52718c9923e7edb0c8e28674d00e8d`;
- 98 A10M1 objects / 223,799,545 logical bytes present and hash-verified while
  constructing the deterministic bundle: PASS;
- 25-wheel Linux closure replayed with `--no-index --require-hashes`: PASS;
- authored Python compilation with a sandbox-writable bytecode cache: PASS;
- all four `sbatch` scripts pass `bash -n`: PASS;
- `git diff --check`: PASS;
- `cargo fmt --check`: PASS;
- `cargo clippy --all-targets -- -D warnings`: PASS;
- `cargo test`: initial sandbox run reached two loopback-bind denials; the
  authorized unrestricted rerun passed the complete suite. No product test
  failed.

No remote write, environment installation, or Slurm submission occurred while
producing this scaffold evidence.

The scaffold's Python 3.11 lock was later rejected by compute-node P0 before
installation. Amendment 02 and the current `environment/` directory supersede
that selection while preserving the original evidence in commit `8b7e751`.
