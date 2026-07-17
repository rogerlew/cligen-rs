# A10 Neural Candidate Research Interfaces

Status: research-only

Revision: 1 (A10M3, 2026-07-17)

## Surface and authority

This specification freezes the A10 model, fit/checkpoint, and generated-stream
records before candidate fitting. It introduces no public generation profile
and does not change faithful CLIGEN. The A10 study plan, A10M1 corpus terminal,
A10M2 compute terminal, and A10M3 design freeze are the authorities.

Producers are the A10M4+ research trainer and generator. Consumers are the
restart harness, evaluators, selector, and audit packages. All consumers fail
closed on missing or additional fields, invalid hashes, unknown identities,
role violations, or non-finite values.

## Model record

The normative machine surface is
[`a10-model-v1.schema.json`](a10-model-v1.schema.json). A record identifies one
exact `neural_point_weather_state_space_v1` configuration, pooling class,
parameter count, corpus and normalization identities, and the canonical Lemhi
configuration. The parameter count cannot exceed 50,000,000. Only the frozen
grid values are admissible.

`N0_complete` uses transferable station/grid descriptors and regime-level
complete pooling. `N1_partial` adds learned station/tile deviations with a
zero-centered hierarchical shrinkage prior; it may not use development or
confirmation identity as a feature.

## Fit and checkpoint record

The normative surface is
[`a10-fit-checkpoint-v1.schema.json`](a10-fit-checkpoint-v1.schema.json).
Checkpoints contain model, optimizer, scheduler, mixed-precision scaler, all
training RNGs, sampler state, and the exact corpus cursor. Publication is
temporary-write, fsync, SHA-256 verification, atomic rename. A trainer retains
the newest two verified checkpoints and writes at least once per epoch, every
15 minutes, and on the registered Slurm signal.

Only `candidate_fit` rows contribute gradients or normalization. The
`fit_validation` role supplies early stopping and diagnostics only.
Development rows never enter fit state. Confirmation target bytes remain
inaccessible.

## Generated-stream record

The normative surface is
[`a10-generated-stream-v1.schema.json`](a10-generated-stream-v1.schema.json).
Each record describes a complete 100-year Gregorian stream and its exact
30-year prefix. Generation uses `random123_philox4x32_10` with counter layout
`station,burn,member,date,draw`; training RNG, batch order, worker count, and
evaluation order cannot affect the bytes. The record binds exact model,
station, burn, member, stream, and prefix identities.

Generated values are finite and in declared physical support. No clipping,
repair, date insertion, or post-generation balancing is permitted. NaN/Inf,
support failure, date drift, non-nested prefix, state collapse/explosion,
nontermination, or provenance mismatch is a hard failure.

## Provenance and failure behavior

Every record uses lowercase SHA-256 identities. The exact canonical runtime is
`lemhi-a10-py311-l40-v1` with semantic SHA-256
`0b1115a6801259c62d9550c877a3c49a897319348ba1c2027be0d9c4f77c1179`.
Python 3.8 evidence is legacy explicit-only and cannot be selected by fallback.
Malformed or unknown records are rejected; they are never coerced.
