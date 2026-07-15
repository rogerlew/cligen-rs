# A7a Findings

Terminal decision: `DAILY-PRECIPITATION-GAP-MEASURED`

## Ranked core families

| Rank | Family | Daymet off min | Faithful min | GHCN off min | Median severity | Qualifies |
|---:|---|---:|---:|---:|---:|---|
| 1 | `wet_amount_dependence` | 15/17 | 15/17 | 0/8 | 2.216 | no |
| 2 | `spell_structure` | 14/17 | 15/17 | 5/8 | infinity | yes |
| 3 | `higher_order_occurrence` | 12/17 | 11/17 | 5/8 | 1.530 | yes |
| 4 | `wet_amount_upper_tail` | 7/17 | 11/17 | 0/8 | 1.472 | no |
| 5 | `multiday_extremes` | 4/17 | 6/17 | 2/8 | 0.861 | no |

The trajectory-spread comparison is descriptive and uses deterministic burn offsets, not IID confidence intervals. Propagation diagnostics are associations and do not establish causation.
