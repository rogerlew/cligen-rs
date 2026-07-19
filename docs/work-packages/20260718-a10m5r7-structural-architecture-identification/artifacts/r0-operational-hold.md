# R0 operational hold

- run: `a10m5r7-architecture-r0`
- Slurm job: `1014016`
- node: `node03`
- state/exit: `FAILED`, `1:0`
- elapsed/GPU accounting: 172 seconds, three charged GPU-minutes
- job-local cleanup: true
- protected roles opened: none
- scientific products: none
- failure: `FileNotFoundError` for the incorrectly rooted first observation
  shard after successful P1 seed-147031 training/reconstruction
- toolkit collection: failed closed as `EVIDENCE_INCOMPLETE` because the
  success-shaped product allowlist had no prospective absence records
- durable cleanup: exact owner marker verified, toolkit `clean.sh` executed,
  and remote root independently verified absent
- successor: A10M5R7R1, same authority/budget, corrected path and satisfiable
  failure evidence; no scientific threshold changed

Restricted raw evidence is retained at
`/Users/roger/.cache/cligen-rs/a10m5r7-architecture/private/failure-evidence-r0/`.
