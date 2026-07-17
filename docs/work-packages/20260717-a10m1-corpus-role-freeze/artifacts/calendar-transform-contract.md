# A10M1 calendar-transform contract

## `daymet_official_365_v1`

For source year `Y` and `yday` in `1..365`, the source civil date is
`date(Y, 1, 1) + (yday - 1 days)`. Thus in a leap year, source day 60 is
February 29, day 61 is March 1, and day 365 is December 30. December 31 has no
Daymet observation.

Normalization exposes a complete proleptic-Gregorian date axis. Every source
record has `source_observed=true`. Leap-year December 31 is appended with
`source_observed=false`, all Daymet values null, and
`missing_reason=source_calendar_absence`. Monthly/annual aggregations ignore
masked values and report observed/expected counts. No value is shifted across
months and no absent day is filled for fitting.

Generated model output later uses `proleptic_gregorian_generated_v1` and must
emit all civil dates. A generated December 31 is model output, never described
as a Daymet observation. The inherited A5 relabeling is not used by this
corpus.

## `uscrn_daily01_lst_v1`

Daily01 source dates and aggregates are retained on the documented local-
standard-time boundary. No daylight-saving shift is applied. Missing
sentinels and quality flags become null values plus masks; records are not
dropped merely because one variable is unavailable.

## `uscrn_subhourly01_lst_v1`

Subhourly01 local date/time is an interval end. The `0000` interval belongs
to the preceding civil day. A civil day is complete for a field only when all
288 expected five-minute interval ends exist and that field is valid. The
event transform is `a10_uscrn_event_6h_v1`, identical to the accepted A9
six-hour separator: 72 consecutive valid zero-precipitation intervals are
required; missing intervals invalidate separation and active events.

## Frozen test vectors

| Source identity | Expected normalized result |
|---|---|
| Daymet 1999 yday 60 | 1999-03-01, observed |
| Daymet 2000 yday 60 | 2000-02-29, observed |
| Daymet 2000 yday 61 | 2000-03-01, observed |
| Daymet 2000 yday 365 | 2000-12-30, observed |
| Daymet 2000-12-31 axis row | all fields null, not observed, source-calendar absence |
| Daymet 2001 yday 365 | 2001-12-31, observed |
| USCRN interval end 20190102 0000 | local-standard civil day 2019-01-01 |
| 71 valid zero intervals between positive intervals | one event |
| 72 valid zero intervals between positive intervals | two events |
| missing interval inside a zero run | cannot establish separation |
