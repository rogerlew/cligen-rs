# HPC safety review brief

Review `package.md`, `lessons-register.md`, and `design-freeze.md` as an
independent HPC operations and safety reviewer. Inspect the current toolkit
specification/remote scripts, Lemhi guide, storage/scheduler providers,
canonical configuration, A10M4 failures/cleanup evidence, roadmap, and
AGENTS.md.

Focus on:

- exact target ownership and recovery after catchable/uncatchable exits;
- the safety and resource accounting of an exact-node recovery allocation;
- job-local capacity admission and the removal of the scheduler-purge claim;
- sanitization versus evidence integrity and leakage behavior;
- authority/budget continuity, transfer timeout/reuse, MFA, and prohibited
  compute-node access;
- whether any remedy can delete foreign/shared state or hide an operational
  failure; and
- missing failure-injection fixtures or stop rules.

Return findings as `HS-01`, `HS-02`, ... with severity P1/P2/P3, evidence,
required disposition, and a final `ACCEPT`, `ACCEPT-WITH-CHANGES`, or `HOLD`
verdict. Do not edit repository files.
