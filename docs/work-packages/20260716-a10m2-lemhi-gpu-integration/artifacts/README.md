# A10M2 Artifact Registry

This directory retains the auditable evidence for the Lemhi GPU integration
package. Execution closed at J1 with `EXECUTED-HOLD-CUDA-ENVIRONMENT`.

Retained evidence:

- `dispatch.md` and `design-freeze.md` — source identity, authorization, frozen
  resources, pass/fail rules, and attempt policy;
- `amendment-01-compute-module-registry.md` — prospective correction after the
  first failure;
- `inventory-live.md` — sanitized SSH/Slurm/node/module/storage receipts;
- `jobs/` — committed CUDA/Python sources and exact Slurm scripts;
- `logs/` — exact sanitized J1 stdout/stderr and both source manifests;
- `j1-result.md` — CUDA gate evidence and failure classification;
- `attempt-ledger.md` and `resource-ledger.md` — every submission, rerun,
  terminal state, and GPU-minute calculation;
- `cleanup.md` — retained/deleted remote object identities without operator
  paths;
- `retention-manifest.sha256` — hashes of every other retained artifact;
- `review.md`, `gate-results.md`, `terminal.md`, and `a10m3-handoff.md` —
  closure evidence.

`environment-selection.md` records why framework selection and wheel staging
were not reached. No checkpoint was created. J2, J3, J4a, and J4b have no logs
because the fail-closed ladder prohibited their submission.

Credentials, usernames, absolute operator paths, SSH/VPN/Keychain material,
unrestricted environment dumps, large wheel/image caches, and confirmation
data are never committed.
