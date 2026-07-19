# Design freeze

The plan's positive integer `gpus` field is the resource-ledger multiplier.
The typed Slurm GRES is the scheduler reservation. They must describe the same
resource, model, and count before any remote mutation:

    gpu:l40:1  <-> gpus = 1
    gpu:l40:2  <-> gpus = 2
    gpu:l40:4  <-> gpus = 4

This package accepts only one homogeneous node03 allocation and counts one
through four. It rejects generic `gpu:N`, other models, other resources, zero,
counts above four, and any mismatch. Existing immutable provider and canonical
configuration records are not edited; the optional capability is additive.
