# A10M1 verification

Evidence mode: Ran

## Independent corpus checks

- Parsed the v2 selection independently: 1,440 unique point IDs, exactly
  200 `candidate_fit` and 40 `fit_validation` per regime.
- Recomputed tile roles: 351 tiles, zero role splits.
- Recomputed protected-coordinate distances: minimum 100.005749 km.
- Opened a v2 Daymet tar member: seven exact fields, 10,958 Gregorian dates,
  10,950 observed masks, observed 1980-02-29, and null/nonobserved leap-year
  December 31 rows.
- Parsed all USCRN object identities: 24 Daily01 objects with 5,844 records
  each and 14 Subhourly01 objects with 21,495 actual events.
- Rehashed all 60 invalidated v1 and all 60 accepted v2 Daymet archives at
  their distinct paths: 120/120 match their manifests.
- Rehashed all 98 accepted transfer objects through the package verifier.
- Rehashed 32 inherited development objects: 20 Daymet and 12 USCRN objects
  match the accepted A9 manifest.
- Verified the source manifest states
  `confirmation_target_series_accessed=false` and the leakage overlap is empty.

## Executable verifier

Command:

```text
python3 docs/work-packages/20260717-a10m1-corpus-role-freeze/artifacts/jobs/a10m1_corpus.py verify
```

Result:

```text
PASS self-test: calendar, 0000 boundary, and 72-zero event separator
PASS verify: six regimes, 98 transfer objects, zero confirmation access
```

The verifier fails closed on a freeze mismatch, missing or changed object,
quota/tile failure, nonempty leakage list, transfer hash mismatch, or a true
confirmation-access flag.
