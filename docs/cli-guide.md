# cligen Command-Line Guide

This is the human-facing guide to the `cligen` executable. Normative details
remain in the linked specifications, but ordinary use should not require
reading the specification set.

## Install and inspect

```console
cargo install --path crates/cligen
cligen --help
cligen stations list
```

`cligen` never downloads data during validation or generation. Station and
PRISM data are acquired only by explicit `sync` commands and are verified
against embedded sizes and SHA-256 hashes before publication to the local
cache.

## Run from a runspec

Create `inp.yaml`:

```yaml
cligen_runspec: 1
station:
  par: id106388.par
mode: continuous
simulation:
  begin_year: 1
  years: 30
  interpolation: none
rng:
  burn: 0
generation_profile: faithful_5_32_3
qc_filter: faithful
output:
  cli: climate.cli
  overwrite: false
  quality: true
```

Then validate and run:

```console
cligen validate inp.yaml
cligen run inp.yaml
```

Relative paths resolve from the runspec's directory. Existing destinations
fail closed unless `overwrite: true` is explicit. Successful generation emits
the `.cli`, provenance JSON, and—by default—a quality-report JSON companion.

## Find and cache station parameter files

```console
cligen stations sync us-2015
cligen stations nearest --lat 46.73 --lon -117.0 --collection us-2015 -n 10
```

`stations nearest` reports deterministic haversine ordering and the absolute
cached `.par` path. Put that path in a runspec for an explicit station run.
Within the station command family, only `stations sync` may contact the
network.

## Run a PRISM-localized stochastic climate

```console
cligen prism sync
cligen stations sync us-2015
cligen prism query --longitude -117.0 --latitude 46.73 --json
cligen prism run --longitude -117.0 --latitude 46.73 --years 30 \
  --output-dir pullman-prism
```

The current `prism run` command chooses a donor from the nearest ten `us-2015`
stations using the registered PRISM-aware rank-sum heuristic, localizes six
monthly `.par` rows, and runs the unchanged faithful generator. A12 evaluates
whether that automatic heuristic should remain preferred over closest-station
selection; this guide will name any future selection-mode options only after
their runtime contract is implemented.

The output directory includes the canonical request, method record, PRISM
receipt, station-selection receipt, source and localized `.par` files, runspec,
climate, ordinary provenance and quality companions, and a top-level manifest.
The selection receipt binds the selected source `.par` and executing cligen
binary by SHA-256, while the top-level manifest independently hashes the
complete artifact set.

## Choose an exact station

Today, an exact station is selected by supplying its `.par` path in a runspec.
The planned PRISM station-policy surface will add explicit user, closest, and
validated heuristic choices without removing this path-based interface.

## Related contracts

- [runspec and `run`/`validate`](specifications/SPEC-RUNSPEC.md)
- [station collections and queries](specifications/SPEC-STATION-DB.md)
- [PRISM query, selection, localization, and artifacts](specifications/SPEC-A10-STOCHASTIC-PRISM-COMPARATOR.md)
- [output provenance](specifications/SPEC-PROVENANCE.md)
- [quality report](specifications/SPEC-QUALITY-REPORT.md)
