# A10M1 normalized field glossary

Null means unavailable under the named source/QC rule. It is never zero,
inferred from another product, or a permission to drop the record.

## Identity and masks

| Field | Meaning | Units / domain |
|---|---|---|
| `source_id` | exact product surface | registered string |
| `role` | immutable permitted use | A10 role registry |
| `regime` | corpus-balancing sampling stratum | six-regime registry |
| `tile_id` / `station_id` | nonleaking partition identity | string |
| `calendar_transform_id` | date/day-boundary contract | registered string |
| `source_observed` | Daymet source row exists for date | boolean |
| `date` / `dates` | proleptic-Gregorian civil label | ISO 8601 date |

## Daymet V4 R1

| Field | Meaning | Units |
|---|---|---|
| `prcp` | daily total precipitation | mm/day |
| `tmax`, `tmin` | daily maximum/minimum 2 m air temperature | degrees C |
| `srad` | daylight-period incident shortwave radiation average | W/m² |
| `vp` | daily average vapor pressure | Pa |
| `swe` | snow water equivalent | kg/m² |
| `dayl` | daylight duration | s/day |

## USCRN Daily01

The normalized lowercase names preserve the official Daily01 names:
`t_daily_max`, `t_daily_min`, `t_daily_mean`, `t_daily_avg` (degrees C),
`p_daily_calc` (mm/day), `solarad_daily` (MJ/m²/day),
`sur_temp_daily_{max,min,avg}` (degrees C), `rh_daily_{max,min,avg}`
(percent), `soil_moisture_{5,10,20,50,100}_daily` (m³/m³), and
`soil_temp_{5,10,20,50,100}_daily` (degrees C). Negative documented missing
sentinels normalize to null. `surface_temperature_type` preserves the source
type flag.

## USCRN Subhourly01 derived events

| Field | Meaning | Units |
|---|---|---|
| `depth_mm` | sum of valid positive five-minute precipitation | mm |
| `duration_min` | first interval lower bound through last positive interval end | min |
| `time_to_peak_fraction` | earliest peak midpoint relative to event duration | fraction |
| `peak_ratio` | peak interval depth divided by event mean interval depth | ratio |
| `air_temperature_c` | complete positive-interval context mean | degrees C |
| `solar_radiation_w_m2` | complete positive-interval context mean | W/m² |
| `relative_humidity_pct` | complete positive-interval context mean | percent |
| `wind_speed_1_5m_m_s` | complete positive-interval 1.5 m wind mean | m/s |
