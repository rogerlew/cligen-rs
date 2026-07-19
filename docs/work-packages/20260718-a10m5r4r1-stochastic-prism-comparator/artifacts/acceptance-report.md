# A10M5R4R1 acceptance report

Date: 2026-07-18
Evidence mode: Ran locally on `main`

## Distribution and extraction

- Published immutable release `prism-normals-2026.07` with a 62,509,110-byte
  runtime archive (`49fe87...c28292`) and 108,213,469-byte exact-source
  archive (`c3b832...0475c`).
- Rebuilt both deterministic archives independently; both outer SHA-256 values
  were byte-identical. The source manifest binds 36 official ZIPs and their
  TIFF/info members. The runtime retains 481,631 all-layer-valid cells.
- Air-gap sync from an empty PRISM cache verified the outer archive before
  extraction, validated all internal hashes, and published the cache
  atomically. Unit tests cover the exact member allow-list, traversal
  rejection, strict receipt, replacement publication, and missing-file close.
- At `(-117.0, 46.73)`, the Rust reader selected row 76, column 192. Independent
  Rasterio reads from all 36 official ZIPs selected the same cell and matched
  every float32 value after float32 comparison.

## Selection, localization, and orchestration

- The Pullman-area vector selected `id106152.par` from the frozen ten-station
  rank pool. The receipt retains every component error, rank, weight sum, and
  tie-break input.
- Tests exercise stationary precipitation algebra, active and dry-threshold
  localization, suppressed-leading-zero F6.2 rendering, reparsing, and exact
  identity of every record except 4, 7, 8, 9, 10, and 15.
- A 30-year run produced `.cli`, ordinary provenance, quality, query,
  selection, localization, source/localized `.par`, runspec, request, and
  top-level hash manifest artifacts. The faithful generator was not modified.
- Two distinct destination directories produced byte-identical complete
  artifact trees. Final output is now renamed from a sibling staging directory;
  no partial final directory is visible on failure.

## Prospective ensemble gate

`monte-carlo-contract.json` froze an unexamined Boise-area 100-year request
and per-month thresholds before execution: precipitation relative error at
most 0.15 and Tmax/Tmin absolute error at most 0.75 C. All 36 cells passed.
Observed maxima were 0.125465, 0.082202 C, and 0.069907 C respectively; exact
vectors and the climate artifact hash are in `monte-carlo-result.json`.

No neural output, protected role, confirmation allocation, or prior A10M5R4
generated evidence was accessed.
