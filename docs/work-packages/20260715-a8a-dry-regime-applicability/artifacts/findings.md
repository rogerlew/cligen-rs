# A8a findings

Terminal: `CONTINUE-A8B-DRY-PARTITION`

A8a selected stations before new daily-data access and generated no candidate climate.

| Stratum | Integrated daily | Legacy daily fallback |
|---|---:|---:|
| cold_arid | 4 | 0 |
| hot_arid | 1 | 3 |
| monsoonal_transition | 3 | 1 |
| negative_control | 4 | 0 |
| non_monsoonal_semi_arid | 3 | 1 |

Shortened-window agreement: 0.850
Monsoonal instability: 0.188
Other-dry instability: 0.188

The classification is a compiler-time evidence disposition, not a runtime aridity inference or output-selected fallback.
