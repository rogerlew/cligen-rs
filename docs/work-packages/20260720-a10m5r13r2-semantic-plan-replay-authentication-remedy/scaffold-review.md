# Scaffold review and disposition

Disposition: `CHANGES-REQUIRED-ADDRESSED; READY-FOR-RE-REVIEW`

The remedy is bounded to the missing authentication edge. It does not copy or
rewrite R13R1 evidence and does not introduce a new science surface. Replay
accepts two unambiguous plan inputs, proves the raw plan's exact toolkit
semantic identity against the authenticated publication receipt, and obtains
the collection allowlist only from that authenticated semantic object.

The remedy script distinguishes the R13R1 evidence source commit from its own
publication head: input collection, raw plan, receipt, and asset manifest stay
pinned to `927c6147f879ed3a9a56ff1218ffaa3953bef93c`, while executable replay
bytes and the predecessor pin must equal the new `HEAD == origin/main`.

Focused fail-closed tests cover the original gap and the relevant tampering
classes. No HPC action occurs during scaffold or replay authentication tests.

The independent-review additions freeze every mutable R13R1 local input in a
committed pin, bind that pin to published remedy bytes, prove the R13R1 source
is in the remedy head's ancestry, authenticate the asset manifest both from
the pin and the semantic plan, and require the collection's present/absent
partition to account for the full authenticated allowlist exactly once. The
replay vendors the toolkit's exact integer-only RFC-8785 and strict I-JSON
helpers so no mutable repository module executes before publication binding;
test-only parity checks compare those local canonical bytes with the toolkit
implementation, including Unicode key ordering and fail-closed JSON cases.

The first published attempt exposed one overextension: the integer-only
toolkit-record parser was used for authenticated science JSON containing
legitimate floats. The correction separates record/semantic parsing from
float-valued science parsing without relaxing byte authentication. A focused
`1289.0` regression proves science JSON is admitted while toolkit records
continue to reject floats. Attempt 1 stopped before selector and cleanup, as
recorded in `execution-note.md`.
