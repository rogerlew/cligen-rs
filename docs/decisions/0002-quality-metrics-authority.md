# ADR-0002: Quality Metrics Are the Extension Authority; Faithful Mode Is Scaffolding

Status: Accepted
Date: 2026-07-10
Deciders: Roger Lew (operator); drafted by Claude Code

## Context

The faithful-mode port is complete: `cligen run` reproduces the pinned
CLIGEN 5.32.3 build byte-for-byte across the golden matrix, on top of
~46M bit-identical interior records (METHODOLOGY.md). Bit parity was
the acceptance that **proved the machinery** — it established that the
Rust transcription is the Fortran, and that role is discharged and
recorded.

The performance arc (`20260710-*` packages) then exposed a question
bit parity cannot answer: when an extension profile changes generation
behavior, what makes it *good*? The first answer — "stochastic parity
to faithful mode" — is circular. A literature review
(`docs/lit-reviews/legacy-randn-generator-review.md`) grounds why:

- Faithful output is the `.par` contract *as filtered through* a
  statistically defective RNG (`RANDN`, an uncited decimal LCG —
  exactly N' = 100003·N mod 10^10, a ≈ √m, the textbook bad-lattice
  zone) and a quality-control conditioner (Meyer,
  Renschler & Vining 2008) that regenerates monthly batches until
  they look typical.
- The QC was motivated by 30-year convergence — WEPP agricultural
  planning runs (Baffaut et al.: 30 years insufficient for stable
  soil-loss averages). Conditioning purchases that convergence by
  clipping sampling variability, on top of the WGEN-family's known
  structural underdispersion of interannual variance (Katz & Parlange
  1998; Wilks & Wilby 1999).
- Native stochastic practice (forest / rangeland hydrology,
  WEPPcloud) canonically runs 100 years and *needs* year-to-year
  variability. A filter tuned for the 30-year agricultural horizon
  baked invisibly into universal machinery is a symptom-shaped
  partition — the same defect class openWEPP's charter names.
- Meyer's own posture supports generator replacement: his QC treats
  the RNG as a commodity behind a distributional contract. What he
  never made explicit is the filter as a *user-facing policy*.

Measured against faithful output, a profile that produced more
realistic variability would be graded **wrong**. The measuring stick
must therefore change.

## Decision

1. **Authority for extensions = the quality-metric vector.** For every
   non-faithful configuration, correctness authority is
   [SPEC-QUALITY-REPORT](../specifications/SPEC-QUALITY-REPORT.md)
   metrics measured against (a) the `.par` contract — the fitted
   monthly statistics every profile must reproduce — and (b) observed
   climate, the only authority for what `.par` does not encode
   (interannual variance, covariation structure). Distance to
   faithful-mode output is *compatibility information*: reported,
   never gated.

2. **Every generated climate file emits a machine-readable quality
   report by default.** Adjudication is an instrument, not a campaign:
   runs self-report; comparing profiles or horizons means comparing
   reports. The instrument consumes the `.cli` surface, so it applies
   identically to legacy-Fortran output — legacy is measurable with
   the same stick.

3. **Generation policy decomposes into orthogonal, declared knobs.**
   The RNG backend (`generation_profile`) and the QC conditioning
   policy (`qc_filter`) are separate runspec surfaces, each versioned,
   each declared in output provenance. `qc_filter: off` on the
   faithful backend is a first-class configuration: source RNG, source
   column semantics, no conditioning — the ablation that isolates what
   the filter costs and buys. Conditioning becomes a use-case choice
   (convergence-priority for 30-year agricultural runs,
   variance-priority for 100-year native runs), not a baked-in
   behavior.

4. **Faithful mode is retained as scaffolding with enumerated jobs and
   a retirement condition — not carried indefinitely.** Its remaining
   jobs: (a) the **ablation platform** — the legacy binary can
   reproduce faithful behavior but cannot run counterfactuals
   (`qc_filter: off` on `RANDN` is impossible in Fortran-as-shipped);
   only identical machinery with one toggled seam isolates the QC's
   effect; (b) regression gate on shared machinery while extension
   architecture builds out; (c) migration bridge for a
   zero-behavior-change production swap. Faithful mode is
   feature-frozen: gates keep running, no new faithful capabilities.
   **Retirement condition**: when the QC/RNG dissection campaign is
   closed and production runs on declared profiles, faithful mode may
   drop to a tagged release. `reference/cligen532/` remains the
   permanent authority for legacy behavior under ADR-0001, which this
   ADR scopes but does not weaken: the Fortran defines what CLIGEN
   *is*; it no longer defines what a generator *should produce*.

## Consequences

- SPEC-FAST-BATCH-V1's assessment re-anchors on the quality vector;
  its "stochastic parity" framing and internal QC-policy fork are
  superseded (QC policy is the orthogonal `qc_filter`; QC diagnostics
  become standing quality-report metrics).
- The adjudication design is fixed: 30- **and** 100-year runs across
  `{faithful, faithful + qc_filter: off, batch backends}`, with
  per-decade convergence-to-par and per-decade interannual variance —
  the convergence-versus-variability frontier at both horizons. The
  cumulative-QC design predicts conditioning bites hardest in early
  decades; if confirmed, the 30-year horizon is the most distorted
  slice, and the number lands on the record.
- Improving the metrics (radiation–wetness covariation, interannual
  variance) will require **model augmentation**, not RNG work — those
  are tier-2 A-series profiles, and the report is what prices them.
- "Stochastic parity" leaves the project vocabulary as an acceptance
  concept.
