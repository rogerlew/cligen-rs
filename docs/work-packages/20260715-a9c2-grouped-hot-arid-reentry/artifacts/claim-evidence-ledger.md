# A9c2 claim and evidence ledger

Status: corrected after independent methods extraction and before report drafting

Report ID: `a9c2-hot-arid-roster-feasibility`

Question: Can the frozen A9c2 metadata rule supply at least five
confirmation-safe hot-arid USCRN development locations while retaining Yuma
and Stovepipe Wells?

## Hypothesis/outcome crosswalk

The criteria were prospectively frozen before outcome access, but the H1--H3
labels were assigned afterward for reporting. They are therefore retrospective
mappings, not formally preregistered hypotheses.

| ID | Provenance | Decision rule | Outcome | Evidence |
|---|---|---|---|---|
| H1 | retrospective mapping | Accept at least five distinct stations under the complete frozen rule | Not supported; 2 of 5 required stations accepted | E01, E03, E04 |
| H2 | retrospective mapping | Both required retained sites pass the same rule | Supported; Yuma and Stovepipe Wells accepted | E03, E04 |
| H3 | retrospective mapping | Roster work accesses no station series, candidate output, or confirmation series | Supported; every access flag is false | E02, E03, E04 |

## Accepted claims

| Claim | Class | Statement | Evidence | Scope guard |
|---|---|---|---|---|
| C01 | Ran | The metadata-base census contains 113 sites. | E03, E04 | Active, operational USCRN, commissioned by 2010-01-01. |
| C02 | Ran | Three sites match the A8a hot-arid descriptor crosswalk. | E04 | Yuma, Stovepipe Wells, and Mercury only under the exact nearest-descriptor rule. |
| C03 | Ran | Mercury is locked confirmation, leaving two accepted development sites. | E03, E04, E08 | The confirmation roster is not amended or substituted. |
| C04 | Ran | The package returns `HOLD-A9C2-HOT-ARID-ROSTER`. | E01, E04 | First registered hold; downstream work is not executed. |
| C05 | Ran | The recorded execution accessed no station series, candidate output, or confirmation series. | E02, E03, E04, E10 | Metadata-only roster stage; declaration and program-input boundary. |
| C06 | Interpretation | This is an infeasibility result for the exact frozen design, not a physical census of hot-arid climates. | E04, E05, E06 | A8a uses legacy parameter/catalog climatology, not PET. |
| C07 | Derived | The two accepted sites are 498.859 km apart. | E04, E11 | Haversine sphere radius 6,371.0088 km; the sole accepted-site pair. |

## Evidence identities

Evidence IDs, paths, roles, and hashes are frozen in
`report-evidence-freeze-v1.json`. E10 pins the deterministic roster program;
E11 completes the accepted-site distance requirement identified during
independent extraction. R01 is the authoritative NOAA station-listing page.
The execution uses the already committed, hash-pinned listing snapshot; it
does not depend on mutable web content for its result.

## Residual uncertainty before drafting

- Nearest-neighbor legacy CLIGEN descriptors may not characterize the exact
  USCRN point, even within the frozen 75 km crosswalk radius.
- The A8a screen is a campaign descriptor stratum, not a PET-based physical
  aridity classification.
- Later-commissioned USCRN sites, inactive stations, and other subhourly
  networks are outside this census.
- A different prospective corpus or stratum definition could produce a larger
  roster, but changing either inside A9c2 after this result would be
  outcome-time repair.
