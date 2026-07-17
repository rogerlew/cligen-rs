# A10M1 execution amendments

## A1 — nullable excluded-row elevation

Date: 2026-07-17
Series-access state: no Daymet, Daily01, or Subhourly01 target series accessed.

The first metadata-only inventory pass read the current official 255-row
USCRN station table and stopped because the non-operational `TN Oakridge 0 N`
test-site row represents elevation as `UN`. The prospective eligibility rule
already excludes this row (`OPERATION=Non-operational`), but the inventory
must still preserve it. The parser now maps only that documented nonnumeric
metadata token to null. It does not alter station eligibility, source frames,
roles, periods, variables, target access, or any scientific rule.

## A2 — exact-distance candidate-construction prefilter

Date: 2026-07-17
Series-access state: no Daymet, Daily01, or Subhourly01 target series accessed.

The corrected inventory was interrupted during local Daymet lattice
construction because it evaluated haversine trigonometry against every
protected coordinate for every lattice point. Candidate construction now
first rejects protected coordinates that are more than 1 degree latitude or
1.5 degrees longitude away, then applies the unchanged exact 100 km haversine
test to the remaining pairs. At the frozen CONUS latitudes a point within 100
km cannot fall outside that conservative bounding box. Source frames, the
distance rule, accepted coordinates, roles, and all access rules are unchanged.

## A3 — lattice latitude progression

Date: 2026-07-17
Series-access state: no Daymet, Daily01, or Subhourly01 target series accessed.

Inspection after the interrupted metadata-only run found that the lattice loop
advanced longitude but omitted the latitude increment. The loop now advances
latitude by the already frozen 0.25-degree step after each longitude row. This
implements the published finite lattice; it does not change that lattice or
any scientific/access rule.

## A4 — documented Daymet multi-year query form

Date: 2026-07-17
Series-access state: 72 Daymet requests returned full-period responses; all
were rejected before retention or normalization. No USCRN or confirmation
target series was accessed.

The first request batch encoded the frozen integer years as `start=1980` and
`end=2009`. The live service treated those as invalid date values, ignored the
range, and returned 16,790 rows (all current years) rather than 10,950. The
official web-service guide specifies either ISO date strings or the
comma-separated `years` parameter. Requests now use the documented explicit
`years=1980,...,2009` form. The 72 rejected access identities remain in the
ledger and count against the 2,400-request ceiling; the same frozen points may
be retried because the rejection diagnosed request encoding, not source
unavailability. The fit period, points, variables, roles, and target selection
are unchanged.

## A5 — live Daymet day-length header spelling

Date: 2026-07-17
Series-access state: 216 rejected Daymet requests total; a separate permitted
two-year response for one already-requested fit point was read only through
its CSV header and discarded. No USCRN or confirmation target series was
accessed.

With the corrected `years` query, responses contained the required 10,950
rows, but the live CSV header identifies day length as `dayl (s)` rather than
the guide's semantic unit spelling `s/day`. The parser now binds the exact
source key `dayl (s)` while normalized objects and the field glossary retain
the unambiguous `s/day` unit. All 144 responses in this wave were rejected
before retention; they remain in the request ledger and count against the
ceiling. The source variable and normalized meaning are unchanged.

## A6 — fail-closed boundary-tile repair version

Date: 2026-07-17
Series-access state: the v1 permitted Daymet and USCRN fit sources have been
accessed and normalized; confirmation access remains false. No Daymet climate
value was inspected to define this correction.

The first full leakage audit invalidated `daymet-selected-v1`: four geographic
tile IDs have opposite roles in the complete published candidate partition,
and three appeared in v1. This arose because the tile-role hash included the
regime even where two sampling frames share a boundary. Roles may not be
relabeled and the gate may not be waived.

The bounded v2 correction therefore excludes all four ambiguous tiles,
retains every unaffected v1 location under its original role, and restores the
exact per-regime quotas using 25 surplus accepted candidates that already
carry the required role in the published pre-series partition. A stricter
fresh-replacement construction was attempted before writing the v2 freeze but
was impossible because all eligible hot-arid validation candidates had already
been requested. V2 makes no new request. Its deterministic selection uses only
the published partition order, tile, role, access-ledger status, and source
availability; it cannot read or rank climate values or derived statistics.
The v1 selection and shards remain immutable invalid evidence. V2 receives new
selection, shard, and coverage identities within the same cohesive A10M1
package.

## A7 — distinct external v1/v2 shard paths

Date: 2026-07-17
Series-access state: all permitted sources complete; confirmation access false.

Independent closure inspection found that v2 materialization initially reused
the external v1 shard pathnames. V2 hashes were correct, but the v1 manifest's
historical paths then resolved to v2 bytes. The materializer now retains v1 at
`raw/training/daymet/` and v2 at `raw/training/daymet-v2/`; both selections
are deterministically rematerialized from the already retained source objects.
No source is reacquired and neither selection, role, value, nor object content
changes. Both valid and invalidated evidence can now be hash-verified in place.
