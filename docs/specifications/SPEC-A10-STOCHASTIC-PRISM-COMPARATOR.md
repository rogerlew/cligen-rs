# SPEC-A10-STOCHASTIC-PRISM-COMPARATOR — Localized `.par` Comparator

Status: active public preprocessing/orchestration surface

Revision: 3 (public bundle/mode pedigree and limitations, 2026-07-18)

## Identity and claim boundary

`stochastic_prism_localized_par_v1` is the independently versioned
stochastic-plus-PRISM comparator required by ADR-0005 and
SPEC-A10-REFINEMENT-TRAJECTORY. It is a preprocessing and orchestration mode:
it selects a legacy station, localizes six monthly `.par` rows, then runs the
unchanged `faithful_5_32_3` generator. It is not a neural model, a new random
number generator, or a new cligen-rs generation profile. It is a public
Cargo-installed CLI surface under `cligen prism`.

The required scientific request is exactly longitude, latitude, and number of
years. All three are explicit and validated. Revision 1 fixes the simulation
begin year to 1, the faithful burn to 0, monthly interpolation to `none`, and
the station collection to `us-2015` version `2026.07`. Changing one of those
constants creates a new comparator revision.

## PRISM normals and redistribution

The input surface is PRISM Group Norm91m 1991--2020, CONUS 4 km, monthly
precipitation release M4 and Tmax/Tmin release M5: 36 official source
archives. The registered bundle retains those archives byte-for-byte, a
strict manifest, source URLs, archive and embedded-raster SHA-256 values,
PRISM dataset version/create-date metadata, the access date, and this
attribution:

> PRISM Group, Oregon State University,
> https://prism.oregonstate.edu, data accessed 2026-07-18.

Cargo distributes code plus a strict embedded distribution manifest, not the
maps. Two immutable, mutually bound release assets follow SPEC-STATION-DB:

- a runtime bundle containing a cell-major little-endian f32 grid, validity
  mask, grid/source manifests, build receipt, and attribution; and
- a source bundle preserving the exact 36 official ZIP archives and the same
  source manifest and attribution.

The runtime grid retains the source float32 values in layer order ppt Jan--Dec,
Tmax Jan--Dec, Tmin Jan--Dec. Its grid manifest pins width, height, CRS,
affine transform, units, byte order, layout, mask convention, and hashes. The
producer records its script hash and Python/Rasterio/NumPy versions. The
source manifest binds every official URL, ZIP hash, TIFF hash, PRISM release,
and create date. `cligen prism sync` fetches only the runtime bundle by default,
verifies its registered size/hash and internal identities, and atomically
publishes it under the ordinary cligen data cache. `--from` accepts the exact
runtime archive for air-gap installation. Generation never performs network
I/O and has no network fallback.

At the requested coordinate, each monthly value is the containing valid
raster cell's value (equivalently, nearest cell center on the regular grid).
Interpolation, lapse-rate adjustment, and nearest-valid-cell searching are
not part of revision 1. A masked, non-finite, out-of-bounds, or non-CONUS
query fails closed. Precipitation is converted from monthly millimetres to
inches and temperatures from Celsius to Fahrenheit only after extraction.

## Pedigree and authority boundary

The original concept is USDA Forest Service FSWEPP/Rock:Clime. Elliot,
Scheele, and Hall's 1999 Rock:Clime documentation identifies the browser
interface to CLIGEN and its expanded station database; the accompanying CD
documentation describes selecting a station, consulting a 4 km PRISM
precipitation/elevation cell, and modifying a custom climate. Hall and Elliot
(2001) and Elliot (2004) document the PRISM-assisted FSWEPP workflow.

WEPPcloud/`wepppy` subsequently automated station selection and `.par`
localization. The exact reviewed identity is commit
`3ee74d02df445a30968ef92975e5e3e2f6084669`, file SHA-256
`4071cc72165d174851316349c0d96a3f4fa06fcf0b2d91e5b67de439f39a42c1`.
Its implementation is prior art, not port authority. The cligen-rs behavior
specified below deliberately differs in selector axes, data acquisition,
numeric failure behavior, rendering, mandatory intensity adjustment, and
provenance.

Every successful run emits `method.json`, exact record schema version 1 and
method ID `stochastic_prism_localized_par_v1`. It records this layered
pedigree and the normative limitations. The top-level artifact manifest binds
its bytes. Pedigree does not imply behavior identity or transfer a validation
claim from FSWEPP or WEPPcloud.

## Station selection

The selector is a deterministic adaptation of the `wepppy` rank-sum
heuristics to the three request axes the operator froze: distance, latitude,
and monthly normals. It does not add an elevation service because elevation
is not supplied by this contract.

1. Order all `us-2015` stations by SPEC-STATION-DB haversine distance and
   station ID, and retain the nearest ten.
2. Within that pool, assign zero-based ranks for distance, absolute latitude
   difference, Euclidean monthly precipitation-normal error, Euclidean Tmax-
   normal error, and Euclidean Tmin-normal error. Station precipitation
   normals are the `.par` expected totals described below; temperatures are
   the `.par` monthly means. Every component tie breaks by station ID.
3. Compute
   `score = distance_rank + latitude_rank + 3*ppt_rank +
   1.5*tmax_rank + 1.5*tmin_rank`.
4. Select the minimum `(score, distance_km, station_id)`.

This is intentionally not a claim of exact identity with the current
`wepppy` US selector: that code includes an elevation rank and only a
precipitation-normal rank. The weights for the three normal families follow
the all-normal `wepppy` EU/Australia heuristic. The distinction is recorded
because silently calling the two selectors identical would make provenance
false.

## `.par` localization

Let month `m` have average length
`D = [31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]`. From the selected
station, let `u` be mean precipitation on a wet day, `pww` be P(wet|wet),
`pwd` be P(wet|dry), and `I` be raw `MX .5 P` intensity in inches/hour. Define

`q = pwd / (1 - pww + pwd)` and `C = D * q * u`,

where `C` is the station's expected monthly precipitation total. Let `P` be
the PRISM monthly precipitation total in inches and `delta = P / C`.
Malformed/non-finite values or a zero denominator fail closed.

For months where both `P` and `C` are at least 0.05 inches, set the target
wet-day count to the station count multiplied by `(1 + delta) / 2`, then clamp
it to 50--200% of the station count and to `[0.1, D - 0.25]`. Below that
threshold, preserve the station wet-day count. Let `q*` be the resulting
count divided by `D`.

The transition update preserves the station persistence ratio
`r = pwd / pww`:

`pww* = 1 / (1 - r + r / q*)`

`pwd* = ((pww* - 1) * q*) / (q* - 1)`.

The localized wet-day mean is `u* = P / (D * q*)`. The intensity update is
the existing bounded `wepppy` rule:

`I* = I * clamp(delta, 0.5, 2.0)`

for months above the 0.05-inch threshold, and `I* = I` otherwise. This is a
comparator heuristic, not a PRISM intensity observation. An alternative
conditional-wet-day scaling is not admitted without a new revision and a
falsifiable adjudication.

The localized `.par` changes only records 4 (`MEAN P`), 7 (`P(W/W)`), 8
(`P(W/D)`), 9 (`TMAX AV`), 10 (`TMIN AV`), and 15 (`MX .5 P`). All other
records and the unread tail remain byte-identical. Mutated monthly fields use
SPEC-PAR's canonical six-column, two-decimal rendering and are reparsed by
`ParFile`. No silent 0.01 floor is permitted: if fixed-width quantization
would make a positive target unrepresentable or violate probability/ordering
constraints, localization fails. Provenance reports both requested values and
the values reparsed from the actual `.par` bytes.

## Execution and artifacts

The Cargo CLI is:

- `cligen prism sync [--from <directory>] [--force]` — the only PRISM
  network-touching command;
- `cligen prism query --longitude <deg> --latitude <deg> [--json]` — local
  verified monthly normals and cell/source receipt; and
- `cligen prism run --longitude <deg> --latitude <deg> --years <n>
  --output-dir <path>` — local query, station selection, localization, and
  faithful generation. The output directory is an operational destination,
  not a fourth scientific input.

After localization, the mode writes and validates a revision-1 runspec with
`mode: continuous`, `begin_year: 1`, requested `years`, `rng.burn: 0`,
`generation_profile: faithful_5_32_3`, `qc_filter: faithful`, and
`interpolation: none`. It invokes the current cligen-rs executable against the
localized `.par` and retains the ordinary `.cli`, provenance, and quality
companions.

Every successful request atomically publishes:

- canonical request JSON;
- canonical method/pedigree/limitations JSON;
- PRISM query receipt with bundle/manifest/grid hashes, source metadata,
  raster cells, raw values, converted values, and attribution;
- station-selection receipt with all ten candidates, component errors/ranks,
  scores, collection identity, source `.par` path, and source hash;
- source and localized `.par` files plus a field-level mutation receipt;
- runspec, `.cli`, ordinary cligen-rs provenance, and quality report; and
- a top-level manifest hashing every artifact and the cligen executable.

Failure publishes no final output directory. Rerunning the same request with
the same registered inputs and executable must produce byte-identical
preprocessing artifacts and faithful outputs.

## Acceptance

The implementing package must establish:

- byte/hash identity for all 36 PRISM archives and all extracted rasters;
- explicit acquisition/mirror attribution and a no-network generation test;
- independent extraction vectors at interior, boundary, and masked cells;
- deterministic selector vectors, including component and final-score ties;
- independent algebra vectors proving stationary wet fraction, persistence-
  ratio preservation, bounds, dry-threshold behavior, and intensity clamps;
- differential mutation agreement with the registered `wepppy` formulas for
  identical source station and monthly inputs;
- byte identity for every untouched `.par` record and tail, plus successful
  SPEC-PAR reparse of the localized file;
- exact repeatability and at least one end-to-end longitude/latitude/years run;
- an ensemble check that encoded target precipitation and temperatures are
  reflected within prospectively frozen Monte Carlo tolerances; and
- no neural generated-output or protected-role access.

## Limitations

PRISM contributes monthly normals, not daily observations, occurrence
probabilities, or subdaily intensity. The selected station supplies remaining
variance, skew, persistence, storm shape, radiation, dew point, and wind
structure. Wet-day and `MX .5 P` changes are bounded continuity heuristics,
not PRISM observations.

The point query uses one containing 4 km cell with no interpolation,
lapse-rate adjustment, elevation input, terrain downscaling, or nearest-valid
fallback. Fixed 1991--2020 normals do not represent event-specific gradients,
trends, climate change, or year-to-year spatial anomalies. Independent point
runs do not establish coherent watershed storms or a shared daily state.

The registered station selector is neither FSWEPP's user selection nor the
current WEPPcloud US heuristic. Operational history and comparator performance
do not certify general climate accuracy or fitness for a particular WEPP
application. Network overlap between PRISM and station sources also means the
comparator is independently implemented and versioned, not statistically
independent climate evidence. Localized output is not an official PRISM
product. Observations and unmodified faithful CLIGEN remain distinct evidence
arms wherever climate quality is evaluated.
