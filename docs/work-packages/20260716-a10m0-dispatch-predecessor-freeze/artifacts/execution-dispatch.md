# Execution dispatch

- Repository: `cligen-rs`
- Starting branch: `main`
- Push target: `main`
- Frozen predecessor source: `f831d54c2f5c37eb69b27acaa99a3a228a32f7c7`
- Executor host: `rmm`, Apple M1, 16 GB, on the University of Idaho VPN
- A10M0 terminal: `A10M0-PREDECESSORS-FROZEN`
- A10M2 resource authority: frozen J1--J4b matrix, maximum one GPU-hour

After this package commit reaches `origin/main`, the operator's instruction
`Execute A10M2` authorizes ordinary reversible remote staging, the five frozen
Slurm submissions, evidence retrieval, exact-package cleanup, closure, commit,
and push. It does not authorize credentials handling, deliberate preemption,
confirmation access, or a resource-envelope expansion.
