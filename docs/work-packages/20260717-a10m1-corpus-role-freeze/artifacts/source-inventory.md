# A10M1 source inventory

Access checked 2026-07-17. Product identities and downloaded documents are
hashed in the execution manifest.

| Source | Intended role | Calendar / boundary | M1 disposition |
|---|---|---|---|
| Daymet V4 R1 single pixel | broad daily candidate fit and tile-held fit validation | official 365 records/year; Feb 29 retained and leap Dec 31 absent | acquire seven fields for 1980--2009 |
| USCRN Daily01 | point daily candidate fit and station-held fit validation | local-standard civil day | inventory all eligible stations; acquire 2010--2025 according to availability |
| USCRN Subhourly01 | storm shape and multivariate event context | five-minute local-standard intervals | deterministic subset, no event-count selection |
| Existing A9 observed objects | development only | accepted A9 transforms | inherit exact hashes; no role change |
| Existing A9 synthetic/adverse objects | synthetic fixture only | fixture-specific | inherit exact hashes |
| PRISM AN81 daily | source sensitivity only | Gregorian product calendar | do not acquire: Daymet supplies primary P/T and no M1 evidence establishes necessity |
| gridMET | wind/sequencing source sensitivity only | product calendar | do not acquire: USCRN supplies point wind and gridMET is not independent monthly P/T authority |

Daymet is a gridded estimate, not independent point truth. USCRN has a shorter
and field-dependent record. Those limitations remain in downstream source
identity and cannot be erased by concatenation. No mixed-product target is
constructed in A10M1.

Official source entry points:

- Daymet V4 R1 guide and DOI: <https://daac.ornl.gov/DAYMET/guides/Daymet_Daily_V4R1.html>
- Daymet single-pixel service: <https://daymet.ornl.gov/web_services>
- USCRN quality-controlled products: <https://www.ncei.noaa.gov/access/crn/qcdatasets.html>
- USCRN bulk products: <https://www.ncei.noaa.gov/pub/data/uscrn/products/>
