# SPEC-GENERATION-PROFILES — Declared Generator Behavior Profiles

Status: active (rev 3; adds the `qc_filter` policy knob under
ADR-0002; v1 design draft linked below)
Surface: the `generation_profile` and `qc_filter` selectors in a rev-1
runspec and their required declaration in generated `.cli` header
provenance.

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

## `qc_filter` — the conditioning policy knob (ADR-0002)

**Status: accepted and implemented** (Q3 package
`20260710-q3-qc-filter-dissection`, 2026-07-10; SPEC-RUNSPEC rev 5 and
the JSON Schema revved in the same change). `qc_filter` is rejected in
combination with `generation_profile: fast_batch_v0` — the pre-knob
profile is always unconditioned.

Generation policy decomposes into orthogonal declared knobs: the RNG
backend (`generation_profile`) and the quality-control conditioning
policy (`qc_filter`). `qc_filter` is an optional top-level runspec
string:

| Value | Meaning | Output declaration |
|---|---|---|
| `faithful` | Default. The source acceptance/retry protocol (K-S + normal mean/variance CI, cumulative, regeneration; `cligen.f:4002-4340`) applies to the active backend. On the faithful backend this preserves golden byte identity. | none (faithful default) |
| `off` | No conditioning: every produced batch is accepted. On the faithful backend, `RANDN`, the per-parameter streams, the column-5/9 zero masks, and the `ell` chain remain source-shaped; only the accept/retry loop and its QC accumulation are skipped. Trajectories diverge from faithful exactly where faithful rejected a batch. | The writer appends `--qc-filter off` to the CLI header command line. |

Unknown values fail closed. `qc_filter: off` is the ablation
configuration ADR-0002 names: it isolates what the Meyer conditioner
costs (interannual variability) and buys (30-year convergence),
measured by SPEC-QUALITY-REPORT groups A/B and priced by the group-P
counterfactual verdicts, which are evaluated diagnostically whenever
conditioning is off. Conditioning is a use-case choice —
convergence-priority (30-year agricultural horizons) versus
variance-priority (100-year native stochastic horizons) — never an
implicit behavior.

The combination `generation_profile: faithful_5_32_3` +
`qc_filter: faithful` is the byte-identity surface; every other
combination is a declared extension measured under ADR-0002.

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
