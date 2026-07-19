# PRISM normals distribution plan

Status: executing; operator selected Cargo distribution on 2026-07-18
Date: 2026-07-18

## Decision

Redistribute two mutually bound external payloads: a query-optimized runtime
grid fetched by the Cargo-installed binary, and a source-preservation bundle
containing the exact official PRISM archives. Neither payload is committed to
git or included in the crate. A strict distribution manifest and all runtime
code ship through Cargo; large immutable bytes are acquired only by
`cligen prism sync`.

This is preferable to the current WEPPcloud metquery proxy because a point
response does not bind the official source archive, PRISM dataset revision,
raster cell, or response bytes. It is preferable to downloading 36 full CONUS
grids for every coordinate request, and it avoids Python/GDAL/TIFF runtime
dependencies in the Cargo binary.

## Source payload

The source payload preserves byte-for-byte:

- 12 `prism_ppt_us_25m_2020MM_avg_30y.zip` archives;
- 12 `prism_tmax_us_25m_2020MM_avg_30y.zip` archives;
- 12 `prism_tmin_us_25m_2020MM_avg_30y.zip` archives;
- `source-manifest.json` with every official URL, archive byte count and
  SHA-256, embedded TIFF/info member and SHA-256, PRISM dataset version,
  create date, period, resolution, units, and access date; and
- `ATTRIBUTION.md` carrying the PRISM Group/Oregon State University
  attribution, source URL, access date, and redistribution terms URL.

The source metadata identifies precipitation as release M4 and both
temperature variables as release M5. The manifest requires those values; a
later PRISM revision cannot reuse this comparator or payload identity.

## Runtime payload

The runtime payload contains:

- `normals.f32le` — cell-major little-endian source float32 values in order
  ppt Jan--Dec, Tmax Jan--Dec, Tmin Jan--Dec;
- `validity-mask.bin` — one bit per grid cell, set only when all 36 layers are
  valid;
- `grid-manifest.json` — dimensions, EPSG:4269, affine transform, layer order,
  source units, byte order/layout, file hashes, and source-manifest hash;
- `source-manifest.json`, `BUILD-RECEIPT.json`, and `ATTRIBUTION.md`.

The 1405 by 621 by 36 grid is 125,640,720 bytes before outer compression. A
cell-major layout makes one coordinate query a mask check and one contiguous
144-byte read.

## Producer and publication

The bundle producer is tooling in this work package, not a Cargo build script
or runtime dependency. It consumes the 36 source ZIPs (or the exact-source
release asset), validates metadata/layout, proves all grids share one
transform, writes
the source and runtime payload trees, and records its SHA-256 plus pinned
Python, Rasterio, and NumPy versions in `BUILD-RECEIPT.json`.

Both outer archives are deterministic: sorted names, fixed owner/group/mtime,
and `gzip -n`. They are published under one immutable release tag and pinned
by URL, byte count, and SHA-256 in the crate's embedded distribution manifest.
Hashes, not mirror URLs, are the trust anchor.

## Runtime acquisition contract

`cligen prism sync` supports the registered runtime release asset and an
air-gap directory containing the exact runtime archive. It verifies size and
outer SHA-256 before extraction, rejects traversal/symlinks/unknown members,
validates all internal hashes and manifest relationships, extracts to a
temporary sibling, and atomically publishes the cache. Existing valid entries
are reused. `query` and `run` read only a validated cache receipt and perform
no network I/O.

The exact-source bundle is preservation evidence and is not fetched by the
ordinary runtime sync path.

## Attribution and claim limits

Every query receipt and package report names:

> PRISM Group, Oregon State University,
> https://prism.oregonstate.edu, data accessed 2026-07-18.

Redistribution does not turn localized output into an official PRISM product.
PRISM supplies only registered monthly values. Station parameters and CLIGEN
supply all daily and subdaily stochastic structure.

Relevant official pages:

- data terms: https://prism.oregonstate.edu/terms/
- normals: https://prism.oregonstate.edu/normals/
- documentation: https://prism.oregonstate.edu/documents/
