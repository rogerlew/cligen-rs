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

By default, `prism run` chooses the closest donor that completes ordinary
localization from the nearest ten `us-2015` stations. It then localizes six
monthly `.par` rows and runs the unchanged faithful generator. Candidates that
cannot represent the requested normals are recorded and skipped; the command
fails if none of the ten is usable. It never silently switches selectors or
expands the pool.

The evaluated exploratory selectors remain available explicitly:

```console
# PRISM rank-sum over distance, latitude, precipitation, Tmax, and Tmin
cligen prism run --longitude -117.0 --latitude 46.73 --years 30 \
  --station-selection prism-rank-sum-localizable \
  --output-dir pullman-rank-sum

# WEPPcloud-like distance/latitude/elevation/precipitation reference selector
cligen prism run --longitude -117.0 --latitude 46.73 --years 30 \
  --station-selection elevation-prism-reference-localizable \
  --target-elevation-m 717 \
  --output-dir pullman-elevation-reference
```

All automatic modes rank the same nearest-ten pool and filter for ordinary
localizability. The elevation value is a user-supplied selection target; it
does not add terrain downscaling or lapse-rate adjustment.

The output directory includes the canonical request, method record, PRISM
receipt, station-selection receipt, source and localized `.par` files, runspec,
climate, ordinary provenance and quality companions, and a top-level manifest.
The selection receipt binds the selected source `.par` and executing cligen
binary by SHA-256, while the top-level manifest independently hashes the
complete artifact set.

If an exact donor has an all-dry occurrence month but PRISM has positive
precipitation, the ordinary command fails closed. An explicit research
extension can repair that month with an independent-day assumption:

```console
cligen prism run --longitude -116.5 --latitude 33.25 --years 30 \
  --station-id ca040983.par \
  --degenerate-occurrence-repair independent-prism-v1 \
  --output-dir repaired-prism
```

The command prints a warning for every repaired month. The localization
receipt records the original parameters, PRISM target, continuous limiting
frequency, F6.2-snapped wet frequency, encoded values, source `.par` SHA-256,
and distinct profile ID. The companion station-selection receipt records the
source `.par` and executable SHA-256 values. `method.json` also identifies the
ordinary base method, active repair method, governing contract, and declared
independence assumption. The mean is recomputed after the
probability snap so the serialized station remains anchored to the PRISM
monthly expectation. PRISM does not observe daily persistence; the repair's
`PWW=PWD=q` choice is an explicit independence assumption. Omitting the flag
preserves ordinary fail-closed behavior. Automatic donor eligibility is always
evaluated without repair, so toggling this flag cannot change an automatically
selected donor; repair is intended to rescue an explicitly requested source.

## Choose an exact PRISM donor

Use the bytewise, case-sensitive ID from the registered `us-2015@2026.07`
catalog, or provide a `.par` file directly:

```console
cligen prism run --longitude -117.0 --latitude 46.73 --years 30 \
  --station-id id106152.par --output-dir pullman-exact-id

cligen prism run --longitude -117.0 --latitude 46.73 --years 30 \
  --station-par /absolute/path/to/station.par --output-dir pullman-exact-par
```

Exact requests never fall back to another donor. The file form may be a
symlink; the receipt preserves both the requested and resolved path. The file
is read once, and that byte snapshot is used for parsing, localization,
publication, and SHA-256 identity.

`station-selection.json` records the requested and effective method, every
automatic candidate and rejection, the selected source `.par` SHA-256, and the
executing `cligen` binary SHA-256. `artifact-manifest.json` independently hashes every
published artifact and the executable, providing cryptographic provenance at
the preprocessing and output boundaries.

## Related contracts

- [runspec and `run`/`validate`](specifications/SPEC-RUNSPEC.md)
- [station collections and queries](specifications/SPEC-STATION-DB.md)
- [PRISM query, selection, localization, and artifacts](specifications/SPEC-A10-STOCHASTIC-PRISM-COMPARATOR.md)
- [PRISM station-source CLI](specifications/SPEC-A12R4-STATION-SOURCE-CLI.md)
- [output provenance](specifications/SPEC-PROVENANCE.md)
- [quality report](specifications/SPEC-QUALITY-REPORT.md)
