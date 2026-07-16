# A9d pre-confirmation protocol correction

Date: 2026-07-15
Access boundary: after the final development hold; before any confirmation
target-series acquisition or access

Closeout review found that `design-freeze-v1.json` describes the conditional
Daymet candidate-fit period as ending on 2009-12-30, while the accepted A9a
confirmation roster freezes the coefficient-fit period through 2009-12-31.
The A9a period is authoritative. Any confirmation path would therefore use
1980-01-01 through 2009-12-31 under `daymet_official_365_v1`.

No A9d candidate was sealed, so the conditional confirmation path was not
reached. No confirmation target bytes were acquired, parsed, summarized, or
scored. This correction changes no development fit, score, selector outcome,
or terminal; it prevents the off-by-one description from being inherited by a
future independently authorized confirmation design.
