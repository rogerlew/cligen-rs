# A10M2D2 artifact registry

Frozen evidence:

- `design-freeze.md` — fixed authority, safety, and transfer envelope;
- `test-matrix.md` — exact payload/repetition matrix and accounting;
- `analysis-contract.md` — timing, statistics, projection, and decision rules;
- `additional-investigations.md` — interruption/resume, quota, variability,
  real-artifact, checkpoint, and alternative-transport routing;
- `stage2-roadmap-handoff.md` — future Ceph/compute staging gate; and
- `jobs/` — bounded local orchestrator and monotonic command timer.

Execution evidence is complete under `execution/`: dispatch and control-master
receipts; sanitized remote preflight; fixture and small-file manifests; raw
timing/status TSV and integrity ledger; summary and projections;
interruption/resume receipt; alternative-transport inventory; traffic/resource
ledger; cleanup receipt; review; gate results; and terminal disposition.

Never retain fixtures, partial transfers, usernames, absolute user paths,
credentials, sockets, VPN details, unrestricted environment dumps, or verbose
SSH logs.
