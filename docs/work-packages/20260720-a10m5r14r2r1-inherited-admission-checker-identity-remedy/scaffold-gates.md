# Scaffold gates

- exact authenticated R14R2 abort receipt and zero GPU usage
- exact R14R2 parent asset-manifest identity
- ratified A10M5O1R3 `checker_assets/ordered-plan-assets-v1` contract
- distinct ordered outer and inherited checker identities
- outer wrapper authenticates itself as slot 0 and its delegate as slot 1
- inherited checker derives its remote-root-relative logical name, requires
  slot 1, and authenticates `Path(__file__)` against that exact plan asset
- materializer publishes the exact ordered receipt projection
- no `__file__` aliasing and no removal of the inherited self-identity gate
- plan/prepared/transfer/receipt equality under the submit lock
- tampered, reordered, and stale identities fail before reservation
- unchanged R14R2 two-role plan and 995 GPU-minute-equivalent ceiling
- unchanged science, calendar, role map, selector, and evidence surfaces
- protected and solar roles sealed
- package tests, Python syntax, JSON parsing, shell syntax, and `git diff --check`

Coverage/CRAP is not triggered because no production function under `crates/`
changes.
