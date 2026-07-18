# Operational amendment 008 — restartable evidence collection

## Trigger

After projection revision 3 was committed, retrying R7 collection failed before
projection because the first failed attempt's `private/quarantine/extracted`
directory still existed. Archive extraction correctly uses `exist_ok=False` to
prevent overlay and stale-file attacks, but collection had no restart protocol.

## Controller correction

At the start of a collection attempt, a non-empty quarantine is now atomically
renamed to the first unused `quarantine.failed-N` sibling. A fresh mode-0700
quarantine is then created and the remote archive is downloaded, verified, and
extracted from scratch. Nothing from a failed attempt is deleted, overlaid, or
admitted into the new allowlist evaluation.

A regression test forces sanitization failure, corrects the fixture evidence,
retries collection, proves a collection receipt, and proves the original raw
quarantine remains retained. R7's first quarantine is therefore preserved as
private diagnostic evidence while its retry is independent.
