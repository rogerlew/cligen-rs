# Canonical configuration validation

Ran on `rmm` from `main` on 2026-07-17. No VPN, remote write, Slurm job, GPU
allocation, or confirmation access was used.

## Identities

- configuration ID: `lemhi-a10-py311-l40-v1`;
- semantic SHA-256:
  `0b1115a6801259c62d9550c877a3c49a897319348ba1c2027be0d9c4f77c1179`;
- rendered configuration-file SHA-256:
  `99a7df3d4192ccf9a585944f62501087126c855a4fe59964aa6106afe42ae312`;
- specification-file SHA-256:
  `d2a898eb3fa6d474269bc082446ea7a67ad0466124d08e00035e46615c255d5c`;
- accepted gate-receipt SHA-256:
  `4a8347a5468a6ef26cee27767bed4d97b7bdfd2c1a86af1dfc7309cea8c5afcc`.

The dedicated regression test removed only
`configuration_semantic_sha256`, recomputed the toolkit canonical JSON hash,
and matched the recorded semantic identity. It then verified the exact hashes
of the toolkit profile, ordered six-provider stack, requirements lock, wheel
manifest, and accepted 19-gate receipt. Byte counts for the lock and manifest
also matched.

## Gates

| Gate | Result |
|---|---|
| canonical JSON strict parse and semantic-hash recomputation | PASS |
| repository-resident pinned identity and byte verification | PASS |
| `python3 -m unittest research.a10.lemhi_toolkit.tests.test_toolkit` | PASS — 23 tests |
| `cargo fmt --check` | PASS |
| `cargo clippy --all-targets -- -D warnings` | PASS |
| `cargo test` | PASS |
| `git diff --check` | PASS |
| specification registry, guide, toolkit README, smoke handoff, and roadmap agreement | PASS |

The consumer policy requires A10M3 and later Lemhi GPU Python packages to bind
the configuration ID and semantic hash. Python 3.8 is legacy explicit-only;
automatic fallback is prohibited. Any recorded invalidation trigger requires a
new versioned candidate and fresh bounded smoke.

Terminal: `A10-LEMHI-CANONICAL-CONFIGURATION-LOCKED`
