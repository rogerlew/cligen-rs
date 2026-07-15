# A9c consolidated internal review

Review boundary: availability-hold report and canonical evidence
Report SHA-256: `6a4d500225f34e83c63259d566725ef79d054549a0c9b5b83e44ec8c2483032b`

## Accuracy lens

Verdict: ACCEPT

- Recounted 180 append-only USCRN access rows as 12 stations × 15 years.
- Rehashed and decompressed all 40 Daymet and 24 USCRN normalized objects;
  the source verifier reports zero confirmation access.
- Recounted candidate-blind calibration as seven statistical families × two
  horizons × 500 replicates = 7,000 identities and 14 thresholds.
- Recomputed development event counts from normalized event arrays: AZ Yuma
  27 ENE = 136 and CA Stovepipe Wells 1 SW = 97.
- Reapplied the registry: both hot-arid sites fail 150-event time-to-peak and
  peak-ratio support and 200-event joint support, yielding 0/2 available
  stations in three mandatory cells. Duration is separately eligible through
  the 6,835-event, 12-site frozen global hierarchy.
- Revalidated all five completed fit artifacts against the official A9 fit
  schema and self-hash. These fits have no role in the terminal arithmetic.

## Scientific-validity lens

Verdict: ACCEPT

- The report distinguishes an evidence-availability failure from evidence
  against either candidate probability class.
- H1--H4 provenance and outcomes match the pre-access role/campaign contracts.
- The first failed upstream gate stops the comparison before simulation,
  ranking, Pareto selection, or A9d freeze.
- Global descriptor borrowing is not extended from duration to objectives
  whose registry requires explicit station-level event counts.
- The proposed follow-on is described as a future design requirement, not as
  a demonstrated remedy.

## Consistency and public-safety lens

Verdict: ACCEPT

- Periods, station counts, event counts, objective IDs, terminal name, and
  access status agree across report, role freeze, source manifest, threshold
  artifact, availability analysis, and fit inventory.
- The report links only repository-public records. Raw NOAA station-year bytes
  are identified by hash and URL but not redistributed; normalized objects and
  null replicates are LFS-managed.
- No confirmation station-year URL, object hash, logical hash, or local series
  appears in the A9c access ledger or source manifest.
- No production crate or vendored Fortran path changed.

## Findings and dispositions

| ID | Severity | Finding | Disposition | Recheck |
|---|---|---|---|---|
| A9C-REV-001 | P3 | Five fits completed before the availability check interrupted the remaining fit stage. | Report exact partial count and prohibit candidate inference; retain the immutable fits as exposed development evidence. | Report and fit inventory agree; PASS. |
| A9C-REV-002 | P3 | Four pre-ranking tooling defects could otherwise be mistaken for outcome-driven amendments. | Publish the access boundary and correction for each in `pre-ranking-corrections.md`. | Zero candidate development scores existed for every correction; PASS. |

Residual uncertainty: this review does not establish whether another
prospectively selected hot-arid roster or period will meet support, nor whether
either candidate will pass once a complete development matrix exists.

Final verdict: **ACCEPT**

Open P1: 0
Open P2: 0
