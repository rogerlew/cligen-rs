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
firewall therefore remain unchanged. The cache-local R13R2 replay output root
was observed empty after the exception and was removed only after this failure
was recorded.

The correction retains strict integer-only parsing for the committed input
pin, raw semantic plan, toolkit plan receipt, collection receipt, predecessor
pin, and asset manifest. Byte-authenticated science assets and generated
selector results use a separate object parser that permits finite JSON floats
while still rejecting duplicate keys, constants such as `NaN`, unpaired
surrogates, unsafe integers, and non-object roots.

## Published attempt 2 — successful authenticated replay and close

Source commit: `009d87b2438768c46509eeb901bf96e73f4d4005`

The corrected replay authenticated every pinned input, reconstructed semantic
plan ID `2dfc598e9767f4492afb99449fd3de1c2d320624de4213d3fcf993881f0ee91b`,
and executed two isolated selector passes. Their temporal-result bytes were
identical at SHA-256
`2213ce79ef3cf9bf2a91562983824307c7fbd7cc26f85159b24cbbf176079cbb`.
Replay record SHA-256 is
`1f08ab7df52ba51709e16878cf23135e85f7dbdce7a5be75558562e7b326f810`.

The selector returned
`HOLD-A10M5R13-NO-TEMPORALLY-ELIGIBLE-CANDIDATE`; both candidate eligibility
flags were false and `protected_roles_opened` remained empty. Only after that
authenticated replay identity existed was cleanup invoked. Cleanup receipt
`d4de26d813327793ba834037d0317ca4db7359e6aae12049bfa3b8d00094949d`
proved remote absence and verified job-local absence. Terminal receipt
`886657cb32a8185d7d97fa86d3e411e17fd2f0f1ab40b98398e8d68f89abda0b`
then closed the three-attempt toolkit run.
