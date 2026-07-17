# A10M1 prospective design freeze

Frozen before new A10M1 station-series access on 2026-07-17.

## Source and time surface

- Primary gridded fit source: Daymet V4 R1 single-pixel daily, 1980--2009,
  variables `prcp`, `tmax`, `tmin`, `srad`, `vp`, `swe`, and `dayl`.
- Primary point source: USCRN. The current official station table is fully
  inventoried. Eligible non-development/nonconfirmation USCRN stations enter
  the Daily01 surface for 2010--2025 according to actual availability.
- Subhourly01 is acquired for a deterministic, station-disjoint event subset
  of up to four stations per primary regime, 2010--2025, subject to source
  availability. Selection uses only station metadata and the frozen regime
  frames; it does not use target values or an event-count floor.
- Existing A9 Daymet/USCRN development objects and synthetic/adverse fixtures
  are inherited by hash. They are not reacquired, relabeled, or promoted into
  fit roles.
- PRISM AN81 daily and gridMET are inventoried optional
  `source_sensitivity` products. Neither is acquired or fed to the optimizer
  in M1. A10M3 may only add one through a prospectively recorded need that the
  committed availability evidence exposes.

## Daymet sampling and role partition

The six regime names are sampling strata for corpus balance, not a deployed
climate classifier or an applicability decision. Each stratum has a frozen
inland CONUS sampling frame in `a10m1-freeze-v1.json`. Candidate coordinates
form a 0.25-degree lattice. A coordinate is accepted only when Daymet returns
the complete requested identity; unavailable/ocean pixels remain recorded
rejections.

Each coordinate maps to a 1-degree tile before role assignment. Tiles are
ordered by SHA-256 over the freeze ID, regime, and tile. Entire tiles are
assigned until each regime has 200 `candidate_fit` and 40 `fit_validation`
locations. Surplus accepted locations are not retained. A location within
100 km of any inherited A9 development or confirmation-metadata site is
ineligible. No tile appears in both roles. Sampling stops rather than
densifying or changing a stratum if its frozen frame cannot meet the target.

Every location receives inverse-location and inverse-regime balancing
metadata. Dense pixels never become independent votes merely because they
contain more windows.

## USCRN eligibility and roles

An eligible row is US, network `USCRN`, commissioned/operational, and not
closed before 2010. The exact A9 development and confirmation station names
are excluded before constructing any data URL. Remaining stations are mapped
to one regime by the frozen geographic frame order; rows outside all frames
are inventoried as `outside_primary_frames` rather than silently forced into
a regime.

Within each regime, SHA-256 orders station identities. The validation count is
the lesser of four and one fifth of the eligible roster (rounded down); a
single-station roster stays fit-only. All other eligible in-frame stations are
`candidate_fit`. The first four fit stations in the independent hash order
form the Subhourly01 event subset. A station keeps one role for all products,
years, and derived windows. HTTP absence, QC missingness, incomplete days,
and zero-event periods remain explicit and do not trigger replacement.

## Calendar and missingness

`daymet_official_365_v1` maps Daymet `yday` from January 1 in civil order.
Leap years retain February 29 and omit December 31. Normalized training
objects expose every Gregorian civil date; the absent leap December 31 row is
masked with every source field null and `source_observed=false`. It is not an
imputed observation and does not enter fit-only normalization statistics.
Generation later emits every Gregorian date under a distinct generated-row
identity.

USCRN uses the source's local-standard-time day fields with no daylight-saving
shift. Daily01 is retained with documented product fields and flags.
Subhourly intervals ending at 0000 belong to the preceding local-standard
civil day. An event is separated only by 72 consecutive valid zero five-minute
precipitation intervals; missing intervals invalidate separation and an
active event. No event-count floor exists.

## Resource and interruption ceiling

- Daymet requests: at most 2,400; retained locations: exactly 1,440.
- USCRN Daily01: at most 2,500 station-year requests.
- USCRN Subhourly01: at most 384 station-year requests.
- downloaded logical bytes: 40 GiB; retained normalized/shard bytes: 10 GiB;
  local execution wall: 8 hours; concurrency: 12 Daymet or 6 USCRN requests.
- All raw and normalized objects are written under ignored `raw/`; manifests
  append identities durably. A rerun resumes only a matching frozen identity.
- Any ceiling breach stops acquisition and yields corpus evidence; it does not
  expand the ceiling, alter roles, or touch confirmation data.

## Amendment rule

After the first permitted series request, changing a source, frame, location,
station role, period, variable, transform, QC rule, event definition, or
ceiling cannot support `A10M1-CORPUS-READY`. It requires an explicit package
hold or a separately authorized future corpus version.
