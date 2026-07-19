# cligen-rs

A Rust implementation of CLIGEN, the stochastic weather generator of the
WEPP model family — executed as a **source-code-authority port** of CLIGEN
5.32.x, then extended.

CLIGEN generates daily (and event/breakpoint) climate series — precipitation
occurrence and depth, storm duration and peak intensity, temperatures, solar
radiation, dew point, wind — from fitted station parameter (`.par`) files.
Its outputs drive WEPP, openWEPP, and the wepppy/WEPPcloud stack.

## Why this project exists

CLIGEN is a fitted statistical machine, not a physics model: the thousands
of station `.par` files were fitted to *this generator's* distributional
machinery, and there is no external physical truth to re-derive it from.
The Fortran source therefore *is* the definition of the model — and owning
that definition in Rust is what makes meaningful augmentation possible:

- modified storm duration / peak-intensity derivation from station
  coefficients and event depth
- NOAA (Atlas 14 class) design-storm curve representation
- float64 parquet observed-series input replacing quantized `.prn` files
- automated leap-year imputation
- single-pass variable substitution (no flatfile → wepppyo3 → flatfile
  round-trips)
- post-event month-by-month and global scaling
- native `.cli.parquet` output with full generation provenance
- typed station-par database management and provenance-stamped par
  mutation utilities
- a PyO3 API surface for wepppy

The governing decision — including the faithful/native dual-mode design and
what "faithful" means — is [ADR-0001](docs/decisions/0001-source-code-authority-port.md).

**This port was written by AI systems in one day.** If that makes you
skeptical, good — [METHODOLOGY.md](METHODOLOGY.md) explains why the
correctness case does not depend on trusting anyone: acceptance is
bit-identity against a provenance-pinned reference build, ~46 million
interior values plus twelve end-to-end golden outputs are verified
byte-for-byte, and every gate is re-runnable from this repository.

## Posture, in two sentences

The pinned Fortran source in [`reference/cligen532/`](reference/cligen532/)
is the specification for **faithful mode**; acceptance is trajectory
identity against golden fixtures generated from a provenance-pinned
reference build. Divergence from the Fortran is never accidental: it is a
labeled extension carried in a versioned **generation profile** that every
output file declares.

This is deliberately a different posture from openWEPP's (where legacy
source is a flag, not an authority): openWEPP models nature and can be
wrong about it; CLIGEN defines a stochastic model, and the definition
lives in the source.

## Repository layout

| Path | Purpose |
|---|---|
| `crates/cligen/` | The library crate (generator core, par model, I/O) |
| `reference/cligen532/` | Pinned public-domain CLIGEN 5.32.3 Fortran source — the faithful-mode specification |
| `docs/decisions/` | Architecture decision records |
| `docs/standards/` | Coding standards (the Rust scientific/port standard) |
| `docs/specifications/` | Interface specifications: file formats, API seams, producer/consumer surfaces |
| `docs/port/` | Fortran decomposition analysis and port plan |
| `docs/work-packages/` | Execution record — one package per unit of work |
| `docs/ROADMAP.md` | Forward-only work queue |

## Status

**The faithful-mode port is complete** (2026-07-09, ROADMAP items
1-8): `cligen run` on the 12 golden runspecs reproduces the reference
build's `.cli` files byte-identically, on top of full-trajectory
interior identity (~47M captured generator records, 189,207
cold-start days, 57.3M adjudicated formatted fields). The forward
queue is the augmentation series (provenance/parquet first) —
see [docs/ROADMAP.md](docs/ROADMAP.md).

## Stochastic PRISM mode

Cargo installs the PRISM-aware command surface but does not place the 60 MB
normals runtime in the crate. Acquire the immutable, hash-pinned runtime once,
then query or run entirely from the local cache:

```console
cligen prism sync
cligen stations sync us-2015
cligen prism query --longitude -117.0 --latitude 46.73 --json
cligen prism run --longitude -117.0 --latitude 46.73 --years 30 \
  --output-dir pullman-prism
```

For an air-gapped installation, download the registered
`prism-normals-runtime-2026.07.tar.gz` release asset and use
`cligen prism sync --from <directory>`. A separate exact-source asset retains
all 36 official PRISM ZIPs for audit and reconstruction. Only `sync` can use
the network; query and generation fail closed unless the registered local
bundle and the `us-2015` station collection are present. The scientific and
artifact contract is
[SPEC-A10-STOCHASTIC-PRISM-COMPARATOR](docs/specifications/SPEC-A10-STOCHASTIC-PRISM-COMPARATOR.md).

PRISM data attribution: PRISM Group, Oregon State University,
https://prism.oregonstate.edu, data accessed 2026-07-18. PRISM supplies the
monthly normals; localized CLIGEN artifacts are not official PRISM products.

## Provenance and licensing

CLIGEN is a USDA-ARS work in the public domain; the pinned copy and its
lineage are documented in
[`reference/cligen532/PROVENANCE.md`](reference/cligen532/PROVENANCE.md).
The Rust code is licensed under [Apache-2.0](LICENSE). The full
authorship lineage of the model this port reproduces — four decades of
it — is recorded in [CREDITS.md](CREDITS.md).
