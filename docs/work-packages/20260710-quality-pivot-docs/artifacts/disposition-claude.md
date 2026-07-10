# R1 Dispositions — Claude Code

Date: 2026-07-10
Evidence mode: labeled per item. All seven findings **ACCEPTED** and
applied same-day (this commit).

| # | Sev | Disposition | Applied fix |
|---|---|---|---|
| 1 | High | **ACCEPTED — verified independently.** Ran: 10,000 random-state simulation of the Fortran digit-group update confirms `N' = 100003·N mod 10^10` exactly. My "~3 multiplier / 3× serial correlation" mechanism claim was wrong; the conclusion (textbook-poor LCG) survives on corrected grounds: a = 100003 ≈ √m is the classic bad-lattice zone; composite modulus caps period at λ(10^10) = 5·10^8. | Lit review §1 rewritten (LCG identity + verification note + corrected Knuth argument); ADR-0002 context line corrected. |
| 2 | High | **ACCEPTED.** A bare `.cli` cannot recover runspec-only fields; the command echo is verbatim-arbitrary and must never be parsed as authority. | SPEC-QUALITY-REPORT rev 2: identity split into `content` (recoverable) / `provenance` (run-only, null post-hoc); acceptance now nulls group P **and** `identity.provenance`; envelope sketch updated. |
| 3 | Medium | **ACCEPTED.** Spec status mismatch. | SPEC-GENERATION-PROFILES `qc_filter` section now opens with a declared-contract/schema-rejected-until-Q3 status block, mirroring the `fast_batch_v1` discipline. |
| 4 | Medium | **ACCEPTED.** Group P must key on the knob, not the backend. | Group P re-keyed on `qc_filter` alone; `fast_batch_v0` explicitly carried as pre-knob (`qc_filter: null`, off-style counterfactuals). |
| 5 | Medium | **ACCEPTED.** Determinism requires pinned estimators. | Rev 2 pins: adjusted Fisher–Pearson skew g1·√(n(n−1))/(n−2) with n≥3 else null; top-N tie-break (earlier date, then row index); `observed_passthrough` placed as `par_convergence.observed_passthrough` (null post-hoc). |
| 6 | Low | **ACCEPTED.** The 10,000-redo give-up path makes "0 by construction" not universally true. | Lit review §5 qualified (cap-hit caveat, cligen.f:4302-4332); SPEC-QUALITY-REPORT group P adds retry-cap give-up events as a reported metric. review-claude.md is a closed, dispositioned artifact and is left as-authored; this row is its correction of record. |
| 7 | Low | **ACCEPTED.** | Lit review prose standardized to "2008 — online 2007". |

Also fixed while applying: `metrics_version` placement inconsistency
introduced by the finding-2 edit (top-level, not in `identity.content`)
— caught on self-review, not by R1.

Net: SPEC-QUALITY-REPORT → draft rev 2; SPEC-GENERATION-PROFILES
qc_filter section status-aligned; lit review + ADR-0002 factually
corrected. The pivot's direction and all four ADR-0002 rulings are
unaffected by the findings.
