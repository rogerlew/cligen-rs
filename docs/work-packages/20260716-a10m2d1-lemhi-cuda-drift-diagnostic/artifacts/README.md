# A10M2D1 artifact registry

Scaffolded evidence:

- `investigation.md` — facts already observed and documentation comparison;
- `hypotheses.md` — ranked explanations, tests, and falsifiers;
- `test-matrix.md` — exact comparison matrix and interpretation rules; and
- `jobs/` — self-contained diagnostic sources.

Execution adds:

- dispatch and source manifests;
- sanitized login and D1 inventory/probe/compile/run logs;
- binary hashes and configuration status table;
- Slurm/accounting and resource ledgers;
- documentation-drift and root-cause reports;
- cleanup receipt, review, gate results, terminal, and A10M2 handoff.

Never retain credentials, usernames, control sockets, absolute user paths,
unrestricted environments, core files, large caches, or confirmation data.
