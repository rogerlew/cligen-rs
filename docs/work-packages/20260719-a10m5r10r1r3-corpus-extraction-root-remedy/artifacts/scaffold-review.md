# Independent scaffold review

- Package: `20260719-a10m5r10r1r3-corpus-extraction-root-remedy`
- Reviewer: independent `portable_bootstrap_review` subagent
- Disposition: `ACCEPT`
- Review date: 2026-07-19

The first review identified one fail-closed gap: the archive layout pin was
semantically validated but its own bytes were not authenticated before
authority issuance. The package now freezes
`artifacts/corpus-layout-pin.json` at 859 bytes and SHA-256
`30058e8cbe2b420f899bcc67b5d90042e39c921ba1e75ea107d81c624437b51e`
before semantic use in the standalone verifier, asset preparer, and
authority/plan builder. A real authority-path regression proves that a
coordinated altered pin, archive, and asset manifest is rejected before
issuance.

The reviewer independently reran the freeze verifier, all 24 package tests,
and shell syntax checks. The reviewer also confirmed the R1R2 evidence
bindings, fresh package/run/authority/budget/token identifiers, exact
two-wrapper extraction delta, unchanged portable bootstrap and admission
contracts, unchanged two-role waves and 935 GPU-minute ceiling, the miniature
old-versus-fixed extraction regression, and the absence of predecessor science
results. No concrete findings remain.

Disposition: the scaffold is accepted for operator-controlled execution.
