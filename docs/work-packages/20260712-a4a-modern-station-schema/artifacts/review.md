# A4a Adversarial Review and Disposition

Review: delegated Codex subagent, read-only
Final verdict: **ACCEPT WITH P3 OBSERVATIONS**
Date: 2026-07-12

## P1/P2 disposition

No P1 remained. Five P2 boundary defects were found during review and
remediated before close:

| Finding | Disposition |
|---|---|
| `stations convert` resolved the station-cache environment before dispatch | Accepted. Convert now dispatches before collection context; its integration test removes all cache/home environment variables. |
| YAML `null` could bypass the exactly-one station selector | Accepted. A strict string visitor rejects null/non-string present values; runtime and JSON Schema vectors cover both nullable siblings. |
| Conversion accepted independently supplied model state and source bytes | Accepted. `from_legacy_par` accepts one `ParFile` and hashes its own retained bytes, preventing cross-station lineage pairing. |
| Replacing public `RunInputs.par_bytes` and `sta_parms(&ParFile)` exposed unvalidated model entry and broke the existing API | Accepted. Both public validated legacy boundaries are restored; crate-private typed seams serve resolved modern documents. |
| Published JSON Schema admitted non-ASCII fixed strings and out-of-i32 integers rejected by runtime | Accepted. Exact ASCII patterns and i32 bounds were added; Draft 2020-12 validation rejects the adversarial vectors. |

Post-remediation review found no remaining P1/P2.

## P3 disposition

| Observation | Disposition |
|---|---|
| `RunError::fmt` reached the CRAP threshold with no direct coverage | Remediated. A four-variant rendering test covers Par, station document, observed, and storm errors; the final CRAP gate retains margin. |
| Repository test introspection is not a full Draft 2020-12 validator | Accepted with external Ran gate. Python `jsonschema 4.23.0` validates 24 canonical documents and rejects Unicode-width, i32-overflow, and f32-overflow mutations; recorded in `gate-results.md`. No runtime dependency added. |
| Converter writes directly to the destination, so a mid-write I/O failure can leave a partial file | Accepted as non-blocking hardening. The current contract promises collision safety and deterministic bytes, both gated; it does not promise atomic replacement. Cross-platform no-clobber atomic publication is deferred to a focused file-publication change rather than adding an unreviewed dependency here. |

## Independent checks

The reviewer independently confirmed faithful `f32` bits, negative zero,
fixed-width strings, wind orientation, quality hash semantics, legacy public
APIs, exactly-one selection, all 12 trajectories, the full collection scan,
format/Clippy/tests, LLVM coverage, and CRAP.
