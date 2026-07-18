# Operational amendment 007 — finite scientific JSON projection

## Trigger

After all twelve R7 jobs reached terminal state, toolkit collection first
correctly rejected absent recovery placeholders. Once explicit "not invoked"
placeholders existed, collection quarantined the complete allowlisted archive
and then failed sanitization on the first benchmark value `1.0`.

The v2 evidence projector reused the toolkit's authority-record parser, which
intentionally prohibits floating-point numbers. That rule is appropriate for
hash-chained authority and ledger records but incompatible with scientific
evidence containing finite losses, timings, dispersion, and resource metrics.
The raw evidence was complete and valid; no forbidden path or identity leaked.

## Controller correction

Evidence projection revision 3 now has a separate strict scientific-JSON
parser. It:

- accepts finite JSON integer and floating-point values;
- continues to reject duplicate keys, malformed JSON, NaN, positive or
  negative Infinity, and overflow to non-finite values;
- emits deterministic UTF-8 JSON with sorted keys and compact separators; and
- retains typed longest-first replacement, forbidden-substring checks, raw
  parent hashes, sanitized hashes, and token counts.

Authority, plan, ledger, receipt, and state canonicalization remain on the
existing float-prohibiting parser. Regression tests cover finite scientific
numbers, duplicate keys, NaN, Infinity, and numeric overflow.

## Evidence posture

R7 raw job evidence and its source commit are unchanged. The controller fix is
committed and pushed before collection is retried. Projection receipts identify
sanitizer `lemhi-evidence-projection-3`, so the operational transformation is
explicit and auditable.
