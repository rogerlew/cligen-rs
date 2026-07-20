# Execution note

## Published attempt 1 — failed before selector

Source commit: `72b6513f46f1f06292c7672b90593679d5f8cbae`

The first published R13R2 replay authenticated its committed script/input
bindings and reached local science-asset loading, then stopped on the
legitimate JSON number `1289.0` in authenticated `sites.json`:

```text
RuntimeError: floating JSON number prohibited: 1289.0
```

The strict integer-only I-JSON parser was correct for toolkit records and the
semantic plan, but its use for float-valued science JSON was an interface
error. The selector did not start, no replay result or identity was emitted,
and toolkit cleanup was not invoked. The R13R1 collection and remote cleanup
firewall therefore remain unchanged. The local output root
`/Users/roger/.cache/cligen-rs/a10m5r13r1-admission-controller-materialization-remedy/r13r2-replay`
was observed empty after the exception and was removed only after this failure
was recorded.

The correction retains strict integer-only parsing for the committed input
pin, raw semantic plan, toolkit plan receipt, collection receipt, predecessor
pin, and asset manifest. Byte-authenticated science assets and generated
selector results use a separate object parser that permits finite JSON floats
while still rejecting duplicate keys, constants such as `NaN`, unpaired
surrogates, unsafe integers, and non-object roots.
