# Execution disposition

Terminal: `HOLD-A10M5R12-NO-TEMPORALLY-ELIGIBLE-CANDIDATE`

R2 recovered and projected all 51 exact parent evidence members, including the
45.7 MB retained stream archives, without rerunning a model or consuming a GPU
minute. Two isolated executions of the frozen selector produced the same
16,531-byte result at SHA-256
`7b60081173948351b398d1eefabbfe06a8fe1cb2ad3f9430b56909be24c081b0`.
Solar and confirmation evidence remained sealed.

Neither continuous process was temporally eligible. The inherited gates were
an upper 90% bound on the bootstrap median regime ratio no greater than 1.25
and a maximum regime ratio no greater than 1.5:

| Candidate | Bootstrap upper bound | Maximum ratio | Eligible |
| --- | ---: | ---: | --- |
| Hierarchical medium-plus-slow | 2.49825 | 3.63158 | no |
| Medium-only | 2.51729 | 3.67678 | no |

The slow hierarchy is directionally but not materially better in the overall
comparison. Its median relative-error advantage over medium-only is about
0.31%, and the probability that medium-only is lower-error is 0.095. The
hierarchy materially improves annual dispersion and annual lag, which is the
first evidence that the slow daily process is doing useful work, but annual
cross-field dependence remains the dominant error family. Calendar
quantization is not the demonstrated failure: both models evolve continuously
through boundaries, and the selector observes aggregate statistics only.

Cleanup used the authenticated intent and source-87d marker-bound cleaner.
The remote archive, marker, and run root are independently absent. Parent state
and ledger retain their exact pre-recovery hashes; the parent remains honestly
toolkit-unclosed with 99 settled GPU-minutes and its unused five-minute
recovery reservation stranded.

The smallest scientific successor is a matched selector-alignment comparison:
retain the continuous daily hierarchy, extend training windows so the learned
366--1,266 day states are identifiable, add the missing annual-lag and complete
cross-field families to the aggregate loss, and compare a shared slow climate
state against the existing separate-state mapping. This tests objective/horizon
alignment and explicit joint dependence before adding solar.
