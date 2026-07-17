# Analysis contract

## Primary quantities

For each successful command:

```text
elapsed_seconds = elapsed_monotonic_ns / 1e9
effective_MiB_per_second = logical_bytes / 1048576 / elapsed_seconds
```

Report upload and download separately. For S16 and S256, report median,
minimum, maximum, and all three trials. S1024 is the sustained planning
reference. L0 reports command latency only. F1024 and TAR compare total elapsed
time for identical logical content. CR64/CZ64 compare `-C` with default only
within the same content class.

## Planning projections

Use the direction-specific S1024 rate to calculate linear 1/10/50/100-GiB
transfer-time projections. Show seconds and a human-readable duration. Label
them planning estimates: VPN contention, Ceph caching/load, local storage,
encryption, and time of day can violate linear scaling.

If S1024 fails or times out, do not substitute a favorable smaller-file rate
without an explicit hold. If a later time-window replication is desired, it
requires a new execution identity rather than overwriting this record.

## Decisions

The terminal report must state:

- the size range practical for routine operator-supervised SCP in the observed
  window;
- whether small-file sets should be archived before transfer;
- whether `-C` should be avoided for already compressed/incompressible assets;
- what partial name/size SCP leaves after interruption and whether the observed
  rsync pair can safely resume and verify it;
- the projected point at which transfer time warrants investigating rsync
  resume, Globus, or another administrator-supported transport;
- whether integrity and stability support stage 2; and
- limitations that prevent the result from being treated as an SLA.

Integrity is categorical: every hash must match. Throughput has no prospective
pass threshold because this package establishes the baseline rather than
gaming an invented target.

Three within-session repeats do not characterize time-of-day variability. The
terminal must recommend whether a separately identified later-window replay is
worth its additional network traffic; it must not silently merge such a replay
into this execution.
