# A9c claim-evidence ledger

Status: revised for accepted report revision 2

| Claim | Class | Authority | Permitted wording |
|---|---|---|---|
| The observed corpus was materialized without confirmation access | Ran | `observed-source-manifest-v1.json`, `data-role-manifest-v1.json` | 40 Daymet and 24 USCRN normalized objects; 180 USCRN station-years; confirmation remained metadata-only |
| Numeric null calibration completed | Ran | `null-thresholds-v1.json` and its LFS replicate object | seven statistical families, two horizons, 500 identities per cell |
| Mandatory storm availability failed | Ran | `gate-calibration-availability-v1.json` | hot-arid time-to-peak, peak ratio, and joint dependence each had 0/2 available stations |
| Observed hot-arid rates | Derived | `gate-calibration-availability-v1.json` and the frozen 2018--2024 period | Yuma 136/7 = 19.4 and Stovepipe Wells 97/7 = 13.9 events per station-year, rounded to one decimal; do not generalize beyond these sites and event/QC rules |
| A9c selected or rejected a candidate | Prohibited | no development score or selection trace exists | state only that selection was not executed |
| Either model class is unsuitable | Prohibited | availability stopped before comparison | no model-suitability inference |
| A9d is ready | Prohibited | terminal is a hold, not a candidate freeze | A9d remains unauthorized |
| A replacement period/roster would pass | Interpretation only | no replacement target was accessed | describe as a design requirement, not a result |
| The 150/200 station floors establish intrinsic hot-arid data insufficiency | Prohibited | no A9 support-power calibration established those counts | state that the frozen rules caused the hold, not that the observations are deficient |
| A grouped hot-arid design is already adequate | Prohibited | A9c2 is scaffolded but unexecuted | describe grouped evaluation as a prospective design to be calibrated candidate-blind |
| Successor direction | Static operator decision | `post-acceptance-operator-disposition.md` | expand metadata-selected hot-arid locations, use station-balanced grouping, and rerun under a new campaign identity |
