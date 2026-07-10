# R1 Cross-Review — Codex (gpt-5.6-sol)

Date: 2026-07-10
Reviewer: openai codex gpt-5.6-sol (read-only sandbox, dispatched via
MCP by Claude Code at operator direction)
Scope: commit range fa06129..30fbe4c — the ADR-0002 quality-pivot
documentation arc.
Dimensions: A factual accuracy vs primary record; B cross-document
coherence; C implementability (as presumptive Q1-Q4 executor);
D governance hygiene; E evidence discipline.

Findings reproduced verbatim below.

---

1. **High** — legacy-randn-generator-review.md:34 and
   0002-quality-metrics-authority.md:23: RANDN is mischaracterized as
   an effective "~3" multiplier, which undermines the spectral/serial-
   correlation argument built on "each output is approximately 3x the
   previous."
   Evidence: `cligen.f:1995-2011` multiplies digit chunks by 3 but
   also adds `k(2)` into `k(4)` and `k(1)` into `k(3)`; with output
   integer `N = k4*10^8 + k3*10^5 + k2*10^3 + k1`, the transition is
   `N' = 100003*N mod 10^10`, not `3*N`.
   Disposition direction: correct the RANDN characterization and
   either rework or remove claims that depend on multiplier `~3`.

2. **High** — SPEC-QUALITY-REPORT.md:45: the acceptance claim that
   post-hoc `cligen quality` equals the run-emitted report "minus
   group P" is not implementable as written.
   Evidence: the envelope requires `generation_profile`, `qc_filter`,
   `rng.burn`, mode, years, days, and run-emitted resolved runspec
   fields at lines 45-48 and 108-114, but a bare `.cli` plus `.par`
   cannot reliably recover resolved runspec-only fields; SPEC-RUNSPEC
   also allows arbitrary `output.command_echo`, so header parsing is
   not a complete authority.
   Disposition direction: split identity into recoverable post-hoc
   fields vs run-only provenance, and change acceptance to exclude
   all run-only fields, not just `process`.

3. **Medium** — SPEC-GENERATION-PROFILES.md:29 vs SPEC-RUNSPEC.md:157:
   the active profile spec presents `qc_filter` as an optional
   top-level runspec field while the active runspec spec says the same
   knob is rejected until a later implementation package.
   Evidence: generation profiles lines 29-40 define values and output
   declarations; runspec lines 157-163 explicitly say `qc_filter` and
   `output.quality` are declared contracts rejected by this schema
   revision.
   Disposition direction: mark the `qc_filter` section as future/draft
   until Q3, or rev the runspec/schema in the same package that makes
   it active.

4. **Medium** — SPEC-QUALITY-REPORT.md:96 and SPEC-FAST-BATCH-V1.md:123:
   group P treats "batch backends" as inactive QC cases, contradicting
   the fast-batch v1 composition model.
   Evidence: quality-report lines 96-104 say counterfactuals apply
   when inactive "or batch backends"; fast-batch lines 123-128 require
   `fast_batch_v1` to compose with both `qc_filter: faithful` and
   `off`.
   Disposition direction: key group-P behavior only on `qc_filter`,
   with `fast_batch_v0` called out as the current no-QC spike if
   needed.

5. **Medium** — SPEC-QUALITY-REPORT.md:49: several metric definitions
   are under-specified for byte-deterministic implementation.
   Evidence: line 49 specifies f64 accumulation and n-1 sample stats,
   but group A requires precipitation skew at lines 62-69 without
   defining the skew estimator; group D requires "top five daily
   events" at lines 91-94 without tie-breaking; observed mode flags
   `observed_passthrough` at lines 133-136 without schema placement or
   per-metric semantics.
   Disposition direction: define formulas, tie ordering, null/flag
   placement, and schema-level field names before Q1 implementation.

6. **Low** — legacy-randn-generator-review.md:237 and
   review-claude.md:153: "faithful = 0 by construction" for QC
   rejection metrics ignores the source's 10,000-redo give-up path.
   Evidence: `cligen.f:4302-4332` leaves the failed final attempt in
   place once `iredo` reaches 10000; the docs correctly mention retry
   storms elsewhere, but the zero-rejection shorthand is not
   universally true.
   Disposition direction: qualify as "zero for accepted final batches,
   except capped give-up events," and report cap hits separately.

7. **Low** — legacy-randn-generator-review.md:64: the
   Meyer/Renschler/Vining paper is cited as 2007 in prose while the
   corrected bibliography and CREDITS use 2008.
   Evidence: CREDITS now records *Hydrological Processes*
   22(8):1069-1079, doi `10.1002/hyp.6668`, online 2007 but published
   2008; the lit-review reference row also says 2008.
   Disposition direction: standardize prose citations to 2008 with an
   "online 2007" note if needed.

Clean checks: the column-5/9 zero-mask claims match `rng.rs:161-183`
and `cligen.f:4149-4180`; the ranset cumulative K-S/mean/variance
description matches `cligen.f:4002-4340` and `ks_tst`'s `0.8276`
threshold at `cligen.f:4491-4502`; `dstn1` is deterministic, so
diagnostic QC can be non-mutating if it operates on already produced
batch values. The local copyrighted PDF hash prefixes match the
lit-review table.

Overall verdict: the quality-arc pivot is coherent in direction, and
most source-grounded ranset/fast-batch mechanics check out. The main
blocker is factual: the RANDN multiplier analysis is wrong in a way
that affects the literature review's central RNG critique. The Q1 spec
also needs tightening before execution because its current post-hoc
equality and metric definitions are not precise enough to implement
deterministically.
