# A5c Gate Results

Run date: 2026-07-14
Repository: `/Users/roger/src/cligen-rs`
Starting commit: `8d00f8c2108910f257b29c02341c0e1fca9e4dd9`

## Package-specific verification

Command:

```text
python3 docs/work-packages/20260714-a5c-interannual-profile-adjudication/artifacts/verify-a5c-decision.py
```

Result: PASS (exit 0).

```text
A5c verification: PASS
locked evidence: 24 files
candidate/horizon rows: 14, eligible: 0
promoted profiles: 0; public surfaces changed: 0
mutation self-tests: 6/6 rejected (plus non-finite JSON)
```

The mutation set covers duplicate keys, evidence-hash mismatch, fabricated
eligibility, fabricated promotion, public-surface change, and changed public
default. Non-finite JSON rejection is an additional parser test.

## Repository gates

| Gate | Result |
|---|---|
| `cargo fmt --check` | PASS (exit 0) |
| `cargo clippy --all-targets -- -D warnings` | PASS (exit 0) |
| `cargo test` | PASS (exit 0) |

The default test suite completed with no failures. Tests explicitly marked as
local evidence gates remained ignored by their existing test annotations.

The coverage/CRAP gate does not apply because A5c adds or changes no production
function in `crates/`.

## Closure checks

- Evidence lock: 24/24 paths present and SHA-256 identities matched.
- A5b results: 14/14 expected candidate/horizon rows present; 0 eligible.
- Accepted report manifest: revision 2, status `ACCEPTED`, 0 eligible rows,
  0 promoted candidates, exploratory model-selection classification.
- Public generation-profile enum/default: unchanged.
- Public A5b profile-ID leakage: none across the locked accepted surfaces.
- ADR, roadmap, and work-package catalog: mutually consistent.
