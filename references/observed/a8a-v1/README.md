# A8a observed-source archive, revision 1

This directory contains the immutable source extracts for the A8a dry-regime
applicability study. The exact 20-station panel was selected and frozen from
the public `us-2015` station catalog and parameter metadata before any file in
this directory was requested or inspected.

- `daymet/` contains deterministic-gzip copies of Daymet V4 R1 single-pixel
  CSV responses for the frozen coordinates.
- `ghcn/` contains byte-for-byte GHCN-Daily by-station gzip responses where the
  deterministic U.S. Cooperative identifier maps to an official station within
  the frozen coordinate tolerance.
- `metadata/` contains the deterministic-gzip official GHCN station-list
  snapshot used to verify identifiers and coordinates.

These are third-party data, not Apache-2.0 project code. See
[`THIRD_PARTY_DATA_NOTICE.md`](THIRD_PARTY_DATA_NOTICE.md). Exact source,
archive, logical-record, coverage, calendar, URL, and access identities are in
the A8a work-package source manifest. Do not replace files in place; a refresh
requires a new observed-source revision.
