# A10M1 handoff

Terminal: `A10M1-CORPUS-READY`

A10M3/M4 may consume only the v2 identities in
`normalized-manifest-v1.json` and `offline-transfer-manifest-v1.json`.
`daymet-selected-v1.json` and `daymet-shard-manifest-v1.json` are failed audit
evidence and are prohibited training inputs.

Downstream invariants:

- fit normalization is limited to the 152 rows in
  `normalization-statistics-v1.json` and role `candidate_fit`;
- validation objects may support early stopping/fit diagnostics only;
- the 32 inherited development objects remain development-only;
- confirmation remains metadata-only and inaccessible until the separately
  sealed conditional confirmation stage;
- hot-arid has no eligible USCRN fit station under the current firewall; a
  downstream design must expose that absence rather than borrowing a locked
  or development station;
- PRISM/gridMET remain optional source sensitivities, not implicit fillers;
- every Daymet leap December 31 is a masked source-calendar absence; and
- offline staging verifies SHA-256 before use and follows the A10M2D2 archive
  and partial-file rules.

The transfer set is 98 objects / 223,799,545 bytes. A10M2 stage 2 should use
this real manifest to test durable-to-job-local staging, bounded reads,
checkpoint-style copy-back, and exact cleanup. This corpus terminal alone does
not authorize A10M3: `A10M2-COMPUTE-READY` is still absent.
