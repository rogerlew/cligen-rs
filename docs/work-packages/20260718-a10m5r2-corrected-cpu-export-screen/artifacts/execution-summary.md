# A10M5R2 execution summary

Terminal: `A10M5R2-PROMOTIONS-READY`

All twelve frozen seed-147031 configurations ran once and passed. Candidate
generation and fit identities matched immutable A10M5 evidence exactly; all
98 corpus objects, checkpoint, support, order/prefix, runtime, dispersion,
process-lineage, offline-install, cleanup, and toolkit gates authenticated.
Development-selection and confirmation roles remained unopened.

## Corrected deployment boundary

| Measure | Minimum | Maximum | Gate |
|---|---:|---:|---:|
| parameters | 34,351 | 226,767 | pass |
| export bytes | 152,420 | 927,088 | pass |
| worker `VmHWM` bytes | 559,370,240 | 569,270,272 | pass, at most 2 GiB |
| external maximum RSS bytes | 644,579,328 | 676,618,240 | pass, at most 2 GiB |
| cold load seconds | 0.0111 | 0.0248 | pass, at most 15 seconds |
| worst runtime ratio | 3.6725 | 4.2221 | pass |

The narrow memory range across a 6.6-fold parameter range shows that the
runtime closure dominates these small exports; model size does not approach
the 2 GiB safeguard in this matrix. The corrected boundary therefore resolves
the A10M5 hold without relaxing its threshold.

## Frozen promotions

| Stratum | Rank 1 | Rank 2 |
|---|---|---|
| N0 complete | `N0-l64-w128-d2-lognormal` | `N0-l64-w128-d3-lognormal` |
| N1 partial | `N1-l64-w128-d2-lognormal` | `N1-l64-w128-d3-lognormal` |

All GPD rows were ordered behind all lognormal rows in both strata. These four
promotions are operational anchors for A10M5R3's prospectively frozen family
and capacity-knee work. They are not a final architecture, temporal, spatial,
or confirmation decision.

## Lifecycle

Jobs `1013932`, `1013934`, `1013936`, `1013939`, `1013943`--`1013946`,
`1013948`, `1013949`, `1013951`, and `1013952` all ran on `node03`. They used
6,107 elapsed GPU-seconds and 108 per-job ceiling-rounded GPU-minutes against a
365-minute authority. The five-minute recovery reserve was released unused.
Collection, job-local absence, remote-root absence, and terminal close passed.
