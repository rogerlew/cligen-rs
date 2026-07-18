# A10M4O2 scaffold and pre-publication gates

Ran on `rmm` from `main` before the live authority was created:

- 49 Lemhi-toolkit unit/acceptance tests: PASS;
- all toolkit remote and A10M4O2 job scripts under `sh -n`: PASS;
- revision-2 example plan JSON parse: PASS;
- `git diff --check`: PASS;
- `cargo fmt --check`: PASS;
- `cargo clippy --all-targets -- -D warnings`: PASS; and
- `cargo test`: PASS (repository-declared ignored evidence tests remained
  ignored).

The targeted executable-mode fixture passed and confirms rejection during
`prepare`, before stage, SSH mutation, or Slurm allocation. Read-only live
preflight confirmed both warm masters, `/usr/bin/nvidia-smi`, the Slurm
`ElapsedRaw`, `NodeList`, `Restarts`, and `State` fields, and `sacct -D`
allocation plus step records.
