# A10M5R15R2 Execution-Readiness Review

Date: 2026-07-21
Reviewer: independent subagent `a10m5r15_readiness_review`
Initial disposition: `NOT READY`
First re-review disposition: `REJECT`
Final re-review disposition: pending post-publication calibration

## Initial findings and disposition

| Priority | Finding | Disposition |
|---|---|---|
| P1 | Inherited authority would compare the R1 archive to the predecessor corpus-layout pin. | Accepted. R2 now publishes its own exact archive/layout pin and verifier, rebinds the inherited authority package root, and verifies the override locally. |
| P1 | Inherited replay retained obsolete counts and lacked rev-2 calibration, matched attribution, per-treatment selection, double replay, and ADR-0006 benchmarking. | Accepted. R2 now has candidate-blind calibration, captured bootstrap sequences, two isolated replay passes, matched E1/E0 and E2/E2C attribution, per-treatment terminal logic, and a separate normative benchmark producer. |
| P1 | Streams, checkpoints, and evaluations lacked required normals, mapping, corpus/calendar, limitation, and runtime provenance. | Accepted. The candidate writer adds rev-2 provenance to every stream and seed/checkpoint record. The authenticated post-benchmark provenance closure replaces the explicit pending runtime marker with each arm's final ADR-0006 classification. |
| P2 | E0/E2C could still receive appended normals tensors. | Accepted. Descriptor-only processes never load the conditioning bundle, never install the conditioned batch wrapper, reject 42-wide tensors, and carry a lookup sentinel in the runtime self-test. |
| P2 | Generated architecture contracts cloned the R14 arm-B definition and used the 340,000 ceiling for replacement arms. | Accepted. All four generated definitions are exact and distinct; E2C/E2 carry a 330,000 per-arm ceiling that is checked after training. |
| P3 | “180 normals-only weights” was incorrect. | Accepted. The package now says 180 input columns and 720 weights. |

The initial review confirmed that model counts, matched initialization, wave
topology, 515-minute resource arithmetic, and protected-role sealing were
otherwise coherent. GPU execution remains forbidden until the corrected
source is published and fresh authority, control, occupancy, and admission
records pass.

## First re-review

The first re-review correctly rejected execution because calibration had not
yet been produced and found additional inherited-wiring defects. During that
review R2 was revised to:

- rebind the exact authority child-role matrix and the top-level materialized
  admission roles, including the new portfolio occupancy freshness predicate;
- use the science-contract configuration IDs on every temporal record;
- permit checkpoint-compatible 30/100-year generation construction while
  retaining the 5,844-day training guard;
- prebuild normals conditioning outside the warm timer;
- replace the inherited two-arm-only annual diagnostic with a source-pinned
  four-arm pairwise diagnostic without changing the bootstrap gate;
- bind calibration into assets, authority, plan, and admission before candidate
  output and remove the stale inherited replay entry point;
- emit final per-stream, per-checkpoint, and per-evaluation provenance closure;
- fully authenticate calibration/runtime receipts, publish failure terminals,
  compute the two registered non-gating diagnostics, restrict portable P2
  exports to E0/E1, and compare serialized replay bytes.

The only intentional remaining gate at this checkpoint is stage 2 of
`plan.md`: publish these producer bytes, compute candidate-blind calibration
from accepted R14 E0, commit its receipt/hash, and request final re-review.
