# A5b Post-Climate WEPP Amendment v3

Date: 2026-07-13
Status: **FROZEN BEFORE PUBLIC WEPP RESPONSE OUTPUT**

## Boundary and disclosure

The v6 runner, campaign, analyzer, and post-climate freeze remain immutable.
Their freeze SHA-256 is
`75e0278df8b09af0e6a8e10e1fa5aa462ddbc02908a5b4ad135778307df5f410`.
The candidate climate manifest remained at pre-WEPP SHA-256
`b52d20b6e472995491ae3d81433f54a709a2a53c65c8b4753957c0ecb0193b50`
with all 1,904 transient candidate climates present.

The v6 campaign passed both accepted-input verifiers, executed all 2,176 WEPP
coordinates, validated each response/execution pair during private staging,
and built its canonical private archives. Its final archive revalidation then
failed closed on the known faithful-off dry coordinate before publication.
The complete private publication tree was removed; no archive, campaign
index, analysis output, manifest transition, lifecycle quarantine, or
candidate deletion survived.

No raw stream or response value was inspected after the v6 freeze. The error
identified only the existing closed PeakRO audit for the faithful-off
zero-event coordinate already documented by amendment v1. The prior
candidate-response inspection disclosure remains in force, so downstream
results remain exploratory for model-selection purposes.

## Failed validation

The exact coordinate was station `ca042319`, profile `faithful_off`, 30 years,
replicate 3 (legacy burn 503). The final validator reported:

`runs/a5b-wepp-ca042319-faithful_off-30yr-rep3/execution.json: element PeakRO recovery: PeakRO recovery counts differ`

The per-run production parser had already accepted this source-defined dry
case under the frozen v5/v6 zero-event contract: the exact 48-line preamble is
followed immediately by `ANNUAL AVERAGE SUMMARIES`, there are no event blocks,
and the complete companion element output has zero Runoff and PeakRO. Its
execution audit therefore correctly records zero event records, zero event
keys, zero event duplicates, zero cross-checked keys, zero recoveries, and an
empty recovery observation.

The duplicate final validator in v6 instead required `records > 0` and
`keys >= 1` for every execution record. That predicate contradicted the
registered zero-event contract and the independent v6 analyzer, both of which
allow the exact all-zero closed count vector. The failure occurred while
revalidating archived JSON, not while executing or parsing Fortran output.

## v7 disposition

Extractor `a5b_wepp_p326_response_extractor_v7` changes only the final
PeakRO-audit count predicate. Positive element row/key counts remain required.
Event record and key counts may be zero; keys must remain between zero and the
smaller of event records and element keys, duplicate rows must equal records
minus keys, and cross-checked keys must equal event keys. Any nonempty recovery
observation with zero events remains impossible because its count must be at
least one and no greater than the event-record count.

The v7 self-test constructs the exact zero-event seam, parses its complete
zero-valued companion element stream, builds the production PeakRO audit,
requires final revalidation to return zero recoveries, and rejects a mutated
nonzero cross-check count. Existing positive-event, recovery, overflow,
aggregation, raw-role, archive, and lifecycle mutation tests remain unchanged.
The independent v7 analyzer retains and exercises its existing zero-event
acceptance vector while binding the v7 contract and runner identities.

This correction changes no Fortran input, execution, output parsing,
response value, metric, aggregation, candidate, threshold, or promotion rule.
Production must restart from an absent WEPP evidence directory, repeat both
accepted-input verifiers, rebuild the pinned WEPP executable, and regenerate
the complete 2,176-run campaign under v7.
