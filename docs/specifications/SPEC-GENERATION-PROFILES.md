# SPEC-GENERATION-PROFILES — Declared Generator Behavior Profiles

Status: active (rev 2; v1 design draft linked below)
Surface: the `generation_profile` selector in a rev-1 runspec and its
required declaration in generated `.cli` header provenance.

## Producers / consumers

Producer: the `cligen` runspec resolver and generation orchestrator.
Consumers: CLI-output readers, benchmark tooling, and any future provenance
collector. The selector is an extension surface; the faithful algorithm
remains defined by `reference/cligen532/cligen.f` under ADR-0001.

## Runspec field

`generation_profile` is an optional top-level string. The currently accepted
values are:

| Value | Meaning | Output declaration |
|---|---|---|
| `faithful_5_32_3` | Default source-authority port. | Existing legacy-compatible header behavior is preserved for golden byte identity. |
| `fast_batch_v0` | Experimental, non-faithful four-lane monthly uniform-batch producer. | The writer appends `--generation-profile fast-batch-v0` to the CLI header command line. |

Unknown values fail closed at YAML parsing. A profile can never be selected
implicitly by host, build target, or environment variable.

## Profile evolution

The intended runtime surface remains the `inp.yaml` `generation_profile`
field: faithful `faithful_5_32_3` is the default, and a fast-batch extension
is an explicit alternative. Profile identifiers are versioned behavior
contracts, so the future alternative is named `fast_batch_v1`, not the bare
`fast_batch`. A bare name would not identify its generator, seed derivation,
mask semantics, or parity evidence.

[`SPEC-FAST-BATCH-V1`](SPEC-FAST-BATCH-V1.md) is a draft for that future
profile and its assessment. It is **not** yet an accepted runspec value;
current resolvers and the JSON schema must continue to reject it until an
implementation package updates this specification and the schema together.
`fast_batch_v0` remains an implemented spike and is not a parity candidate.

## fast_batch_v0 semantics

The profile replaces only the month-refill producer that normally calls
`ranset`. It fills all nine parameter columns and up to 31 days of the
existing `Crandom3State.ranary` matrix with deterministic f32 values strictly
inside `(0, 1)`. It does not update `ranset`'s cumulative QC state or execute
the K-S, normal-mean, normal-variance, or retry checks. Daily consumers keep
their existing parameter transforms and wet/dry decisions.

The profile deliberately does **not** preserve `ranset`'s conditional zero
masks. In faithful mode, parameter 5 (precipitation amount) is zero on days
the refill-time `RansetState.ell` chain calls dry, and parameter 9 (time to
peak) is zero on those days and on every observed-mode (`iopt = 6`) day.
`fast_batch_v0` instead supplies an open-interval uniform in every slot.
This removes the source's `bk7.v7 == 0.0` recovery path when the refill and
daily wet/dry chains desynchronize, and makes observed-mode parameter-9
storage nonzero even though the downstream observed path does not consume it.
These are declared distributional changes beyond QC removal and are required
attention cells for any stochastic-parity study.

The profile's master state is deterministically derived from the faithful
post-burn, post-warm seed surface. Its algorithm and seed derivation are
versioned by the `v0` name. It has no bit, trajectory, calibration, or
stochastic-equivalence claim relative to CLIGEN 5.32.3.

## Failure behavior

Malformed runspec values fail closed. A fast-profile output without its
required header marker is a writer error. Faithful runspecs remain on the
existing golden-identity acceptance path.
