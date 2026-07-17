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
