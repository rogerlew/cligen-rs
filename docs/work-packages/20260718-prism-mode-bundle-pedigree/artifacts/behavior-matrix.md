# Frozen behavior and difference matrix

| Surface | FSWEPP / Rock:Clime | Brooks et al. (2016) | WEPPcloud / `wepppy` reviewed commit | cligen-rs v1 |
|---|---|---|---|---|
| Purpose | Interactive custom CLIGEN climate for FSWEPP | Spatialize measured station weather across Tahoe hillslopes | Automated stochastic point/watershed climate preparation | Reproducible Cargo point mode and research comparator |
| Base climate | User-selected expanded CLIGEN station | Nearby SNOTEL daily/hourly weather | Selected legacy/2015 CLIGEN station | Deterministically selected `us-2015@2026.07` station |
| Station choice | User judgment using location, elevation, and precipitation displays | Study-specific nearby SNOTEL assignment | US: nearest ten plus distance, latitude, elevation, and precipitation ranks | Nearest ten plus distance, latitude, precipitation, Tmax, and Tmin ranks; no elevation service |
| PRISM input | 4 km monthly precipitation and elevation; user edits | 800 m monthly precipitation, Tmax, and Tmin maps | Live metquery monthly precipitation, Tmax, and Tmin | Hash-pinned Norm91m 1991–2020 4 km monthly ppt M4, Tmax/Tmin M5 |
| Grid handling | User can inspect/select neighboring cells | Hillslope and station pixels | Live service response | Containing valid cell; no interpolation or nearest-valid search |
| Precipitation | User substitutes/edits monthly totals and wet days | Daily station precipitation multiplied by monthly PRISM hillslope/station ratio | Replaces `.par` mean wet-day precipitation after bounded wet-day adjustment | Same reviewed bounded concept, strict finite checks and fixed-width reparse |
| Temperature | User edits or lapse-rate adjustment | Add monthly PRISM hillslope/station Tmax/Tmin differences to daily station values | Replaces `.par` monthly Tmax/Tmin means | Replaces `.par` means with requested-cell normals; no lapse-rate correction |
| Occurrence | Wet days manually editable; no documented automated transition formula | Preserves the source daily occurrence sequence | Halfway wet-day response; recomputes P(W/W), P(W/D) while preserving their ratio | Same registered algebra with strict bounds and no silent fallback/floor |
| Half-hour intensity | No source establishing the current clamp | Notes limitations of generated subhourly peaks; does not specify this `.par` rule | Optional `MX .5 P` ratio clamp, default off | Mandatory 0.5–2.0 ratio clamp, explicitly labeled heuristic |
| Network/data identity | Server/CD-era data; version history separate | Study data identity | Live unversioned service responses | Explicit sync only; query/run local; runtime/source archives and internals hash-pinned |
| Output claim | FSWEPP custom climate | Study-specific spatial weather input | WEPPcloud operational climate | Independent corrected descendant, not behavior-identical to any prior layer |

The matrix is a pedigree and compatibility boundary. It is not a quality
ranking and does not transfer validation claims between implementations.
