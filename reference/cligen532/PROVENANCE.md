# Reference Source Provenance

This directory vendors the CLIGEN Fortran source that ADR-0001 designates
as the faithful-mode specification.

- **Version**: CLIGEN 5.32.3 (`cligen.f` + 13 common-block `.inc` files +
  `makefile`)
- **Vendored from**: the operator's working mirror at
  `jimf-cligen532/cligen532/` (2026-07-09), itself sourced from Jim
  Frankenberger's distribution
- **Upstream**: https://github.com/jfrankenberger/cligen5 and
  http://fargo.nserl.purdue.edu/cligen532/
- **License status**: USDA-ARS work, public domain
- **Known local lineage**: 5.323 (2025-09-13, Roger Lew) fixed an
  observed-mode (`-O`) bug where a partial final year in the input `.prn`
  appended an extra output day (`day_gen` end-of-file handling). 5.322
  (2024-09-10, Fred Fox) fixed a divide-by-zero in coefficient-of-variation
  when a monthly average temperature is zero.

Rules:

- This copy is **read-only reference material**. Fixes belong upstream (and
  in a refreshed vendored copy with an updated provenance entry), never
  applied silently here.
- Golden fixtures must record the source hash of this directory plus the
  full reference-build provenance (compiler, flags, libm) per ADR-0001 §4.
- Binaries are not vendored; the reference binary is built from this source
  by the fixture-harness work package.
