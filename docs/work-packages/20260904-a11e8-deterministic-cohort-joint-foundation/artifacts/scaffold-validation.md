# Scaffold Validation

Date: 2026-09-04

Candidate-output access: false

Confirmation-target access: false

## Deterministic contract

The frozen Python 3.12.14 / NumPy 2.3.5 Darwin-arm64 runtime reported:

- canonical manifest SHA-256:
  `6aa07fd460acb5b30ed4e9863b38a26787f75891a3d67caae0113844ec711aa1`;
- station `az026481`, cohort 0, candidate 0 seed:
  `13423984198280203969`;
- station `az026481`, cohort 0, candidate 7 seed:
  `8137402885486637624`; and
- candidate 0 sixteen-state canonical SHA-256:
  `10ef6054ab6af5c76ed596bc552149d3b6a05ca4e2a66038eee1034ef2bcdf79`.

`test_contract.py` passed five tests. `test_execute.py` passed four tests,
covering rank-one recovery, exact fixed-width overlay isolation and temperature
difference preservation, deterministic contract identity, and independent
component/selector gates. The executor's manifest-validation entry point
returned the canonical manifest digest above.

## Repository gates

The following commands completed with exit status zero:

```text
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
git diff --check
```

Changed-document relative links were resolved against the repository and all
existed. Coverage/CRAP was not triggered because the scaffold changes no
production function under `crates/`.
