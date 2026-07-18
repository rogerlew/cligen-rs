# Architecture review brief

Review `package.md`, `lessons-register.md`, and `design-freeze.md` as an
independent toolkit architect. Inspect the current toolkit specification,
implementation, provider records, canonical-configuration policy, A10M4
execution evidence, roadmap, and AGENTS.md.

Focus on:

- whether the toolkit/application ownership boundary is coherent;
- whether `derive-run`, job wrapping, toolchain provider, sanitization,
  transfer reuse, and provider/record versioning are minimal and implementable;
- whether any remedy duplicates existing behavior or silently changes
  historical semantics;
- whether the canonical `v1` to candidate-successor/smoke sequence is correct;
- whether the package is bounded enough to execute before A10M5; and
- missing positive/adverse fixtures or compatibility obligations.

Return findings as `AR-01`, `AR-02`, ... with severity P1/P2/P3, evidence,
required disposition, and a final `ACCEPT`, `ACCEPT-WITH-CHANGES`, or `HOLD`
verdict. Do not edit repository files.
