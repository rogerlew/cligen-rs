# PRISM normals distribution plan

Status: prospective; publication belongs to A10M5R4R1 execution
Date: 2026-07-18

## Decision

Redistribute the exact official PRISM Norm91m monthly source archives as one
hash-pinned external payload. Do not commit the grids to git or include them
in the crate. This follows the station-collection split: a small manifest and
code are versioned in the repository; large immutable bytes are a release
asset acquired only by an explicit sync step.

This is preferable to using the current WEPPcloud metquery proxy because a
point response does not bind the official source archive, PRISM dataset
revision, raster cell, or response bytes. It is also preferable to downloading
36 full CONUS grids for every coordinate request. A verified local bundle
makes generation network-silent, repeatable, and efficient for many points.

## Payload contents

The version-1 payload contains, byte-for-byte:

- 12 `prism_ppt_us_25m_2020MM_avg_30y.zip` archives;
- 12 `prism_tmax_us_25m_2020MM_avg_30y.zip` archives;
- 12 `prism_tmin_us_25m_2020MM_avg_30y.zip` archives;
- a canonical JSON manifest with every official URL, archive byte count and
  SHA-256, embedded TIFF/info member and SHA-256, PRISM dataset version,
  create date, period, resolution, units, and access date; and
- `ATTRIBUTION.md` carrying the PRISM Climate Group/Oregon State University
  attribution, source URL, access date, and redistribution terms URL.

The source metadata currently identifies precipitation as dataset release M4
and both temperature variables as release M5. The manifest must require those
values; a later PRISM revision cannot reuse the version-1 comparator identity.

The execution package must build the outer archive deterministically (sorted
names, fixed owner/group/mtime, `gzip -n`), record its byte count and SHA-256,
publish it under an immutable release tag, then put the exact asset URL and
identity in the registered manifest. Source member hashes, not the mirror URL,
are the trust anchor.

## Acquisition contract

An explicit sync command supports:

- the registered release asset;
- all 36 official URLs; and
- an air-gap directory containing the registered outer archive or exact
  source members.

All paths verify hashes before extraction, reject traversal/symlinks/unknown
members, validate TIFF layout and PRISM metadata, extract to a temporary
sibling, and atomically publish the cache. Existing valid cache entries are
reused. Generation reads only a validated cache receipt and performs no
network I/O.

## Attribution and claim limits

Every user-visible query receipt and package report names:

> PRISM Climate Group, Oregon State University,
> https://prism.oregonstate.edu, data accessed 2026-07-18.

Redistribution does not turn the localized output into an official PRISM
product. PRISM supplies only the registered monthly grid values. Station
parameters and CLIGEN supply all daily and subdaily stochastic structure.

Relevant official pages:

- data and download portal: https://prism.oregonstate.edu/recent/
- data terms: https://prism.oregonstate.edu/terms/
- normals documentation: https://prism.oregonstate.edu/documents/
