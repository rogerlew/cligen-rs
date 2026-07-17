# A10M2D1 artifact registry

Scaffolded evidence:

- `investigation.md` — facts already observed and documentation comparison;
- `hypotheses.md` — ranked explanations, tests, and falsifiers;
- `test-matrix.md` — exact comparison matrix and interpretation rules; and
- `jobs/` — self-contained diagnostic sources.

Executed evidence:

- `dispatch.md` and `logs/source-manifest.sha256` freeze the dispatch and
  staged source identity;
- `logs/` retains sanitized login and D1 inventory/probe/compile/run evidence
  plus source and binary manifests;
- `configuration-results.md` and `root-cause.md` interpret the comparison;
- `documentation-drift.md` classifies the published claims;
- `resource-ledger.md` and `cleanup.md` retain accounting and cleanup;
- `review.md` and `gates.md` record acceptance checks; and
- `terminal.md` and `a10m2-handoff.md` close the package and bound the next
  correction.

Never retain credentials, usernames, control sockets, absolute user paths,
unrestricted environments, core files, large caches, or confirmation data.
