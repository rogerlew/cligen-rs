# Execution disposition

Terminal: `HOLD-A10M5R7R1-NEW-RESOURCE-AUTHORITY-REQUIRED`

R1 corrected and independently verified the observation-shard path before any
allocation. Derived run `a10m5r7-architecture-r1` passed the complete
pre-submission toolkit lifecycle through verification. Both submission calls
failed closed at `RESOURCE_CEILING`; no Slurm job ID exists and no R1 GPU time
was consumed.

The refusal is deterministic. The revision-2 ledger's `_reserved_total`
counts the latest `settled` event by `requested_gpu_minutes`. R0 therefore
continues to account for its requested 60 primary minutes rather than the
three actual minutes in its settlement record, and its five-minute recovery
reserve also remains charged. This equals the 65-minute ceiling.

R1 did not create a replacement authority, expand the budget, use the recovery
allocation for scientific work, or open development-selection/confirmation
evidence. Toolkit abort could not publish the success-shaped pre-submission
allowlist and returned `EVIDENCE_INCOMPLETE`; the staged durable root was
nonetheless removed with the exact owner-marker-validated toolkit cleanup
script and independently verified absent.

The smallest decision needed is authorization for one new package-scoped L40
resource authority. The frozen scientific job requires at most 52 primary
minutes plus a five-minute recovery reserve; a less expensive authorization
may be chosen only by reducing the scientific horizon or matrix, which would
materially change the claim.
