# A10M1 coverage and availability analysis

Evidence mode: Ran

## Daymet v2

| Regime | Fit locations / tiles | Validation locations / tiles |
|---|---:|---:|
| hot-arid | 200 / 44 | 40 / 8 |
| arid-boundary | 200 / 45 | 40 / 6 |
| monsoonal-transition | 200 / 32 | 40 / 11 |
| non-monsoonal semi-arid | 200 / 33 | 40 / 12 |
| humid | 200 / 68 | 40 / 17 |
| cold | 200 / 67 | 40 / 14 |

All 1,440 locations contain 10,950 Daymet source rows for 1980--2009 and
10,958 normalized Gregorian axis rows. Across the corpus, every one of the
seven variables has 15,768,000 observed values. Each also has 11,520 explicit
`source_calendar_absence` masks: eight leap-year December 31 rows per
location. No masked row contributes to fit-only normalization statistics.

The fit surface spans 351 unique one-degree tiles after the v2 boundary repair.
Per-location and per-regime weighting metadata, not the number of windows,
defines downstream balance.

## USCRN

The official table yielded 24 eligible, in-frame, nondevelopment,
nonconfirmation stations. All have complete 2010--2025 Daily01 file presence
(5,844 civil rows per station). Metadata-only exclusions leave no eligible
hot-arid station; this absence remains visible and is not repaired by accessing
the two A9 development or three confirmation hot-arid stations. Six-regime fit
coverage is supplied by Daymet; USCRN contributes point evidence according to
actual availability.

Daily roles by regime are: arid-boundary 4 fit; cold 6 fit plus 1 validation;
humid 9 fit plus 2 validation; monsoonal-transition 1 fit; non-monsoonal
semi-arid 1 fit; hot-arid 0. Fourteen metadata-selected fit stations carry
Subhourly01 event objects. Their unfiltered actual event totals are:

| Regime | Event stations | Events |
|---|---:|---:|
| arid-boundary | 4 | 6,130 |
| cold | 4 | 6,031 |
| humid | 4 | 7,245 |
| monsoonal-transition | 1 | 1,010 |
| non-monsoonal semi-arid | 1 | 1,079 |
| hot-arid | 0 | 0 |

The retained event objects contain 21,495 events total; individual stations
range from 1,010 to 2,260. No event floor, station substitution, zero-event
removal, or post-access regime reassignment was applied.

Daily01 missingness remains field-specific. Of 140,256 station-days,
precipitation has 137,971 available values, the four air-temperature summaries
each have 139,397--139,450, solar radiation has 139,606, and RH summaries each
have 136,525. Soil fields retain substantially larger documented gaps rather
than being inferred from another depth or product. Exact source/regime/role/
field/year/month/state counts are in `availability-cube-v1.json`; 152
candidate-fit-only normalization rows are in
`normalization-statistics-v1.json`.

## Optional-source disposition

The measured primary corpus provides seven broad daily Daymet variables plus
USCRN point precipitation, temperature, radiation, humidity, soil, wind-event,
and storm-shape evidence. M1 therefore found no scientific need to acquire
PRISM or gridMET. They remain explicitly named `source_sensitivity` options;
neither may silently fill a primary missing value or enter the optimizer.
