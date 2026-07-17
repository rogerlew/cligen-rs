# A10M2 Execution Kickoff Template

Execute the package at
`docs/work-packages/20260716-a10m2-lemhi-gpu-integration/package.md` end to end.

Repository and branch discipline:

- repository: `cligen-rs`;
- start from clean current `origin/main` at `<DISPATCH_COMMIT>`;
- remain on `main`; and
- push only to `main`.

Before any remote write or Slurm submission, record the operator's execution
authorization, the dispatch commit, the accepted A10M0 predecessor terminal,
and confirmation that the frozen maximum of 1 GPU-hour is approved. Verify
both SSH control masters with `ssh -O check`.
If either is absent, stop remote work and request human MFA bootstrap; never
solicit, receive, or automate password/Duo material.

Execute J1--J4b sequentially under their frozen resources and gates. Do not
submit a later job after an earlier hard failure. One exact rerun is permitted
only for a documented infrastructure transient and must not change code,
environment, resources, or pass criteria. Do not deliberately preempt another
job. Monitor every job to a terminal Slurm accounting state, retain sanitized
receipts, account for all GPU-minutes, clean nonretained remote assets, run the
package and repository gates on identified environments, independently review
the evidence, reconcile roadmap/catalog state, and push the complete package
record to `main`.

The package may close only at `A10M2-COMPUTE-READY` or one of its named holds.
It must not train an A10 candidate, access confirmation data, change production
Rust, or create a suffixed rescue package.
