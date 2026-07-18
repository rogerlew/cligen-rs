# A10M5R3 execution summary

## Scientific result

The accepted corrected `r4` matrix ran all 18 frozen roles once at attempt
zero on `node03`. All application and toolkit job gates passed. The frozen
family ordering selected `lognormal_wet_v2`:

| Family | Mean validation NLL | Mean tail score | Mean stability | NLL SD |
|---|---:|---:|---:|---:|
| lognormal wet v2 | 2.771989 | 0.270788 | 0.927987 | 0.003990 |
| lognormal body + GPD excess v2 | 2.835594 | 0.225562 | 0.930141 | 0.006413 |
| gamma wet v2 | 3.727604 | 0.301895 | 0.920904 | 0.004557 |

The splice remained a useful tail diagnostic but did not win the frozen
primary-NLL-first ordering. The prior whole-wet-day GPD is absent from the v2
schema and was not rerun.

## Capacity result

| Point | Parameters | Validation NLL | Max runtime ratio | Peak RSS (MB) | Export bytes |
|---|---:|---:|---:|---:|---:|
| P0 | 34,351 | 3.025619 | 3.817x | 660.5 | 152,420 |
| P1 | 87,295 | 2.666572 | 4.210x | 677.1 | 364,196 |
| P2 | 276,927 | 2.587045 | 6.280x | 671.0 | 1,122,724 |
| P3 | 975,679 | 2.499899 | 12.415x | 681.5 | 3,917,732 |
| P4 | 3,019,695 | 2.203700 | 27.562x | 670.2 | 12,093,796 |

All five points were on the frozen multi-cost frontier. Curvature selected P1
as the knee and P2 as its immediately larger neighbor. P3 and P4 demonstrate
continued fit improvement but cross the frozen 10x runtime failure boundary
and are not retained.

Across all three seeds, P1 mean NLL was 2.663283 with population SD 0.003118;
P2 mean NLL was 2.574190 with SD 0.014351. Every retained row passed all hard
gates. P1 runtime ratios were 4.210x, 4.376x, and 4.209x; P2 ratios were
6.280x, 6.088x, and 6.347x. P2 therefore carries a warning classification but
does not cross the 10x fail boundary.

## Disposition separation

The scientific evidence says `A10M5R3-CAPACITY-PAIR-READY`, but the package
does not. Fresh authority resets in failed correction lineages exceeded the
frozen 18-job count, and the accepted parent run could not toolkit-close after
an invalid projection token. The package terminal is therefore
`HOLD-A10-RESOURCE-BOUND`; A10M5R3R1 owns the bounded evidence-admissibility
decision.
