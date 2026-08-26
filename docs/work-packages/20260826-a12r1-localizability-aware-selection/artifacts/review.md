# Independent review disposition

Final disposition: **GO** for A12R1 publication. No P0 or P1 findings remain.

The independent reviewer traced the CLI choice through localization, fixed-width
encoding, v2 receipts, method and artifact manifests, faithful-run command
provenance, warnings, and atomic publication. The reviewer independently ran
the exact A12 point: default failed without a final or staging directory, while
the explicit profile succeeded and all source/binary/profile cross-checks
matched.

Findings disposition:

- Replaced the misleading finite repaired-month `precipitation_ratio` with JSON
  `null` and an explicit zero-source-total reason in the separate v2 receipt.
- Preserved the public v1 receipt/result shapes and introduced additive v2
  types for the extension.
- Added schema-2 method provenance and repair-specific climate command
  provenance without changing ordinary artifacts.
- Changed probability snapping to use the exact F6.2 formatter and added a
  half-grid regression.
- Added v1 byte-golden, v2 rewrite/reparse/receipt, target-anchor, tiny-target,
  other-degenerate, intensity-overflow, warning, method, and runspec tests.
- Clarified the receipt locations and ordinary/extension method schemas in the
  user and normative documentation.

Non-blocking P2: retain the exact source-identity execution receipt as the
run-level propagation and atomicity evidence; a future hermetic orchestration
integration test may supplement it.
