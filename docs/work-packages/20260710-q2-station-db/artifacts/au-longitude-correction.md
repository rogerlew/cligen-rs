# Addendum — AU Longitude Correction + Public Hosting (au 2026.07.1)

Date: 2026-07-10 (same-day addendum to the closed package; operator
directions: "I flipped cligen-rs public. please correct the AU
longitudes")
Evidence mode: **Ran** throughout.

## The defect

The au collection's seven Victoria stations carried **negative
longitudes** in both surfaces — the par `LONG=` fields and the
python-produced `au_stations.db` catalog (e.g. Melbourne −144.96; the
stations are at ~145-147°E). Flagged at package close as a
carried-verbatim producer quirk; the operator directed correction.

## The fix (at the source, per the producer boundary)

- `jimf-cligen532` commit `ddfa671d` (pushed): all seven pars'
  `LONG=` signs flipped with f7.2 column alignment preserved
  (anchored single-occurrence replaces), and
  `UPDATE stations SET longitude = -longitude WHERE longitude < 0`
  on `au_stations.db`. Both surfaces now agree, east-positive.
- Note: the par `LONG` field feeds only the `.cli` header longitude
  (`yll` is not used in generation), so generated trajectories are
  unchanged; the header longitude for au stations changes sign. No
  golden references an au station.

## Payload re-release (immutability honored)

`au 2026.07` is superseded, not mutated: new archive
`au-2026.07.1.tar.gz` (sha256
`47f68a07b91c06ea4a542da62af7f052ad03aa8f6241b865d99b7f8969e566d1`,
5,302 bytes) built with the same deterministic-tar recipe and
uploaded to release `station-db-2026.07` (asset 472904725). The
embedded manifest bumps au to 2026.07.1 with a lineage note naming
both the correction and the superseded behavior. The 2026.07 asset
remains on the release for the record. Test fixture, pinned au
oracle, and the five-collection oracle artifact regenerated — the
au query point flips to (−37.5, **+145.5**); pinned distances are
unchanged (haversine is invariant under mirroring both longitudes),
verified by regeneration.

## Public hosting verified (Ran)

With the repository now public: `cligen stations sync` with **no
token** (`env -u CLIGEN_SYNC_TOKEN`) fetched and verified all five
collections, au arriving at 2026.07.1. A real-coordinate Melbourne
query (−37.81, 144.96) returns Melbourne at 0.00 km. Oracle compare
over the tokenless cache: 35/35, exit 0. Full gates re-run: fmt
clean, clippy clean, 105/105 release tests.

The gate-results "tokenless path never exercised" residual and the
ROADMAP standing decision are both discharged by this addendum.
