# Scaffold gates

The package is a no-GPU scaffold. Its local gate is:

```sh
python3 docs/work-packages/20260720-a10m5r13-selector-aligned-continuous-hierarchy/artifacts/verify_freeze.py
```

This rematerializes both contracts from exact R12R1 parents, verifies the
ratified selector sections byte-semantically, checks the official evidence
profile identity, compiles job Python, and executes dependency-free builder and
replay tests. Run the NumPy/Torch-dependent calendar and annual-loss gate with
the pinned science runtime (the candidate job also runs these before training):

```sh
python3 artifacts/verify_freeze.py --science-python /path/to/pinned/python
```

Before publication, also run the repository gates:

```sh
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
```

## Results

| Gate | Result |
|---|---|
| Contract/freeze verifier | PASS |
| Calendar 5,844/5,840/13-origin test | PASS |
| Selector-family, scale, perturbation, and finite-gradient tests | PASS |
| Exact transitive staged R12/R13 CPU self-tests | PASS |
| Authority/plan builder fixture | PASS |
| Full parent-asset authentication/drift fixture | PASS |
| Pre-cleanup replay contract fixture | PASS |
| Exact predecessor data-root and six-site PRISM replay pin | PASS |
| Python compile, JSON parse, shell syntax | PASS |
| Lemhi toolkit tests | PASS (84/84) |
| `cargo fmt --check` | PASS |
| `cargo clippy --all-targets -- -D warnings` | PASS |
| `cargo test` | PASS |

The science tests ran under an isolated CPython 3.10.14 environment with
NumPy 2.2.6 and PyTorch 2.7.1. That run exposed and then verified the fix for
the zero-variance correlation backward path: the variance product is clamped
before its square root, preventing a non-finite derivative without changing
the selector's 1e-6 denominator floor.

HPC execution remains unauthorized until publication, fresh authority,
calendar preflight, and per-submit admission materialization.
