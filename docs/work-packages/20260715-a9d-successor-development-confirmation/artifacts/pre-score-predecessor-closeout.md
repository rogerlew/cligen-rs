# A9d pre-score predecessor closeout

Date: 2026-07-15
Access boundary: after fresh fitting; before faithful baseline or candidate
evaluation output

The first evaluation invocation built the isolated faithful binary and then
stopped before running a baseline or candidate score because the A9d
predecessor manifest omitted the A8a parameter archive row required by the
inherited A9c3 baseline verifier. The runtime design already named the exact
archive, and neither its path nor bytes changed.

The closeout appends that archive's repository path, byte count, and SHA-256
to `predecessor-manifest-v1.json`, then reruns predecessor verification. It
does not change a fit, model, mask, threshold, station, burn, comparator,
selection rule, or confirmation boundary. No faithful or candidate evaluation
output existed when the row was added.
