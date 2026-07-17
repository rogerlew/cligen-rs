# Gate results

## Execution gates

| Gate | Result |
|---|---|
| published scaffold before remote mutation | PASS (`8b7e751`) |
| published amendments before affected submissions | PASS |
| warm MFA bootstrap / noninteractive agent path | PASS |
| `icrews` / `gpu-icrews` / typed L40 authorization | PASS |
| corrected CUDA 12.8 + `/usr/bin/g++` kernel | PASS |
| complete no-index hash-locked reconstruction / `pip check` | PASS |
| one-L40 PyTorch tensor/autograd/optimizer/checkpoint reload | PASS |
| A10M1 98-object stage 2, fallback, and local cleanup | PASS |
| two distinct L40s / NCCL all-reduce / DDP / clean shutdown | PASS |
| Slurm signal / atomic checkpoint / classified `75:0` | PASS |
| manual resume equals uninterrupted control | PASS |
| all attempts accounted / requested use <= 60 GPU-min | PASS (53) |
| evidence retrieved and sanitized / no confirmation access | PASS |
| exact remote cleanup and empty queue | PASS |
| no open P1/P2 review finding | PASS |

## Static and repository gates

- CPython 3.8 grammar parse for authored Python: PASS;
- local Python bytecode compilation: PASS;
- `bash -n` for every submitted script: PASS;
- Linux no-index dependency resolution with `--require-hashes`: PASS;
- unchanged CUDA source hash:
  `5913c87819a6c4f1451c564102c771051a52718c9923e7edb0c8e28674d00e8d`;
- `git diff --check`: PASS;
- `cargo fmt --check`: PASS;
- `cargo clippy --all-targets -- -D warnings`: PASS;
- `cargo test`: PASS outside the filesystem sandbox required by two loopback
  listener tests. The initial sandbox run's two permission denials were not
  product failures.

Coverage/CRAP is not triggered because no production function under `crates/`
changed.
