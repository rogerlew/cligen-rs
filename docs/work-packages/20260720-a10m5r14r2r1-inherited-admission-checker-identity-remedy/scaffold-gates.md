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

## Prepublication result

All scaffold gates that can be exercised before publication pass. The exact
R14R2 parent and all child assets were authenticated; the changed-file roster
was exactly the frozen 11-file operational allowlist; frozen science surfaces
were byte-identical; and the real derived inherited checker passed its complete
control-role `check()` path. Tamper, reorder, stale identity, symlink, hardlink,
wrong authority, and receipt-projection failures were exercised and failed
closed.

The source-exact preparation, fresh authority and plan, submit-lock
materialization, live role execution, collection, cleanup, and replay-twice
items are intentionally re-exercised after publication and recorded as run
evidence rather than claimed from this prepublication scaffold.
