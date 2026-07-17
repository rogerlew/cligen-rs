# Additional investigations

## Included in stage 1

- live Ceph filesystem capacity and sanitized quota-command visibility;
- local and remote rsync version/availability;
- local and remote Globus CLI visibility, explicitly not treated as proof that
  a managed Globus endpoint does or does not exist;
- intentional SCP interruption, partial-file name and size, exact cleanup;
- conditional rsync `--partial --append-verify` recovery and final SHA-256;
- direct-many-file versus archive behavior;
- default versus SSH compression for incompressible/compressible content; and
- within-session repeat variation at 16 and 256 MiB.

## Routed to stage 2

- Ceph-to-job-local and job-local-to-Ceph throughput;
- actual filesystem type/capacity and `${SLURM_TMPDIR:-${TMPDIR:-/tmp}}`
  resolution;
- representative shard staging and archive layout after A10M1 freezes real
  objects;
- durable checkpoint-style copy-back and preemption timing;
- missing-local-cache fallback to verified durable objects; and
- exact job-local cleanup after normal and later interrupted execution.

## Deferred until inputs or authority exist

- A later time-of-day/VPN replication uses a new execution identity and byte
  ledger if the initial variability or operational stakes justify it.
- Actual wheelhouse, environment, shard, checkpoint, and model sizes are
  inventoried when A10M1 and framework selection create them; synthetic sizes
  are not substituted as facts.
- Managed Globus endpoint discovery and administrator-supported transfer
  recommendations may require C3+3 documentation, UI access, or administrator
  confirmation. CLI absence alone is not a negative finding.
- Concurrent-transfer saturation is excluded unless a later demonstrated need
  justifies load on shared infrastructure.
