# A10M2 Artifact Registry

This directory retains the auditable evidence for the Lemhi GPU integration
package. Scaffolding commits only this registry and `preflight.md`; execution
adds artifacts under the following stable groups:

- `dispatch-*` and `design-freeze-*` — source identity, authorization, frozen
  resources, pass/fail rules, and attempt policy;
- `inventory-*` — sanitized SSH/Slurm/partition/node/module/storage receipts;
- `environment-*` — lock, Linux x86-64 asset manifest, hashes, licenses, and
  offline reconstruction receipt;
- `jobs/` — committed CUDA/Python sources and exact Slurm scripts;
- `logs/` — sanitized stdout/stderr and scheduler/accounting receipts;
- `checkpoints/` — compact synthetic checkpoint identities and comparisons,
  not large binary caches;
- `attempt-ledger-*` and `resource-ledger-*` — every submission, rerun,
  terminal state, and GPU-minute calculation;
- `cleanup-*` — retained/deleted remote object identities without operator
  paths;
- `review.md`, `gate-results.md`, `terminal.md`, and `a10m3-handoff.md` —
  closure evidence.

Credentials, usernames, absolute operator paths, SSH/VPN/Keychain material,
unrestricted environment dumps, large wheel/image caches, and confirmation
data are never committed.
