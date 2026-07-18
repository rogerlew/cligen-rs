# Canonical-v2 smoke handoff

Successor package:
[`20260717-a10-lemhi-canonical-v2-smoke`](../../20260717-a10-lemhi-canonical-v2-smoke/package.md)

Candidate: `lemhi-a10-py311-l40-v2-candidate`
Semantic SHA-256:
`5addee9c5db3592ee247eab2b5266ed5567fd9aaf24ed78dcb321ecbb001e22d`

The successor is scaffolded, not dispatched. Its explicit operator dispatch
will authorize the warm-master/VPN path, one 15-minute L40 primary, and one
conditional exact-node 5-minute recovery contingency under a cumulative
20-L40-GPU-minute ceiling. It must validate the exact v2 profile/provider,
runtime/framework/toolchain, environment, storage supervision, telemetry, raw
collection/projection, accounting, and cleanup contracts.

A passing smoke produces an immutable
`lemhi-canonical-smoke-attestation-1`; it still does not designate the
candidate current. A subsequent local designation-index package must bind the
attestation and advance the pointer. Failure or incomplete cleanup holds A10M5
without candidate mutation or v1 fallback.
