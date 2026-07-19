# SPEC-A10-STOCHASTIC-PRISM-COMPARATOR — Localized `.par` Comparator

Status: research-only

Revision: 1 (A10M5R4R1 scaffold, 2026-07-18)

## Identity and claim boundary

`stochastic_prism_localized_par_v1` is the independently versioned
stochastic-plus-PRISM comparator required by ADR-0005 and
SPEC-A10-REFINEMENT-TRAJECTORY. It is a preprocessing and orchestration mode:
it selects a legacy station, localizes six monthly `.par` rows, then runs the
unchanged `faithful_5_32_3` generator. It is not a neural model, a new random
number generator, or a public cligen-rs generation profile.

The required scientific request is exactly longitude, latitude, and number of
years. All three are explicit and validated. Revision 1 fixes the simulation
begin year to 1, the faithful burn to 0, monthly interpolation to `none`, and
the station collection to `us-2015` version `2026.07`. Changing one of those
constants creates a new comparator revision.

## PRISM normals and redistribution

The input surface is PRISM Group Norm91m 1991--2020, CONUS 4 km, monthly
precipitation, Tmax, and Tmin: 36 official source archives. The registered
bundle retains those archives byte-for-byte, a strict manifest, source URLs,
archive and embedded-raster SHA-256 values, PRISM dataset version/create-date
metadata, the access date, and this attribution:

> PRISM Climate Group, Oregon State University,
> https://prism.oregonstate.edu, data accessed 2026-07-18.

The payload is distributed outside the crate as one immutable, hash-pinned
release asset, following SPEC-STATION-DB. An explicit sync/acquisition command
may fetch either the registered mirror or the official archives and must
verify the same file hashes before atomic publication to a local cache.
Generation never performs network I/O and has no network fallback. An air-gap
source is accepted only after identical verification.

At the requested coordinate, each monthly value is the containing valid
raster cell's value (equivalently, nearest cell center on the regular grid).
Interpolation, lapse-rate adjustment, and nearest-valid-cell searching are
not part of revision 1. A masked, non-finite, out-of-bounds, or non-CONUS
query fails closed. Precipitation is converted from monthly millimetres to
inches and temperatures from Celsius to Fahrenheit only after extraction.

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

After localization, the mode writes and validates a revision-1 runspec with
`mode: continuous`, `begin_year: 1`, requested `years`, `rng.burn: 0`,
`generation_profile: faithful_5_32_3`, `qc_filter: faithful`, and
`interpolation: none`. It invokes the current cligen-rs executable against the
localized `.par` and retains the ordinary `.cli`, provenance, and quality
companions.

Every successful request atomically publishes:

- canonical request JSON;
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

PRISM contributes monthly means, not daily observations, occurrence
probabilities, or subdaily intensity. The selected station supplies all
remaining variance, skew, persistence, storm shape, radiation, dew point, and
wind structure. Network overlap between PRISM and station sources means the
comparator is independently implemented and versioned, not statistically
independent climate evidence. Later A10 reports must retain observations and
unmodified faithful CLIGEN as separate arms.
