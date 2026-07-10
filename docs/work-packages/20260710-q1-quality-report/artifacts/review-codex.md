# R1 Cross-Review — Stage S Quality-Report Spine

Reviewer: Codex (openai gpt-5.6-sol)
Date: 2026-07-10
Evidence: **Static** source/spec review plus cited **Ran** Stage C gates.
Disposition owner: Claude in Stage R2.

## Findings

### C-R1-001 — MEDIUM — Intake overclaims calendar-date validation

**Finding (verbatim):** `quality::intake::parse_row` describes and reports
an `InvalidDate`, but validates only `month in 1..=12` and `day in
1..=31`. Impossible dates such as February 31 are accepted. This weakens
the spine's fail-closed claim and can make date-keyed top events and
transition/decade statistics describe a non-calendar stream.

Evidence: Static, `quality/intake.rs::parse_row`; the Stage S
`fail_closed_errors_render_their_diagnostics` date vector uses month 13
and does not exercise month-specific day bounds.

Disposition to Claude: **accept and remediate in R2**, preferably by
reusing the crate's calendar authority with year-aware month length and a
direct February/leap-year vector. If WEPP `.cli` intentionally permits a
looser date surface, narrow the error/docs claim explicitly instead.

### C-R1-002 — MEDIUM — Skew byte determinism relies on platform `powf`

**Finding (verbatim):** adjusted Fisher–Pearson skew computes
`m2.powf(1.5)`. Rust `f64::powf` is not the repository's pinned math
surface, so repeated local byte identity does not establish the spec's
platform-independent “given inputs → byte-reproducible report” claim.
The Stage S adjudication compared one vector within tolerance, not exact
cross-platform report bytes.

Evidence: Static, `quality/estimators.rs::adjusted_skew`; Ran evidence
proves local repeatability only.

Disposition to Claude: **accept for contract/implementation
adjudication in R2**. Pin an exact implementation (for example an
explicitly adjudicated square-root formulation or pinned libm operation),
then regenerate/report any quality-sidecar byte changes. Do not alter the
faithful `.cli` byte surface.

### C-R1-003 — HIGH — Active spec contradicts the dispatched fast-v0 scope

**Finding (verbatim):** SPEC-QUALITY-REPORT group P says
`fast_batch_v0` reports carry `qc_filter: null` **and off-style
counterfactuals**. The package exclusion and Stage C kickoff explicitly
assign those counterfactuals to Q3 and instruct Stage C to “carry the
null.” The metrics-version-1 Rust type and published schema therefore
have no field for the active spec's stated fast-v0 counterfactual output.

Evidence: Static, active rev 3 group P versus `package.md` Excluded and
`artifacts/kickoff-codex.md` deliverable 1.

Disposition to Claude: **accept as a contract conflict and adjudicate
before package closure**. Recommended: amend the active spec to state
that fast-v0 counterfactuals begin in Q3 and are absent in Q1, with the
required metrics-version consequence decided there. Do not invent the Q3
diagnostic in this package.

### C-R1-004 — LOW — Documented ignored-gate command is not reproducible

**Finding (verbatim):** Stage S `gate-results.md` records
`CLIGEN_FMT_SWEEP=target/stage-c-fmt/fmt_pairs.txt cargo test ...` as a
successful command. In Stage C the same root invocation passed the daily
ignored suites and then failed because `format_identity` interpreted the
relative environment path from the crate test working directory. The
absolute capture path passed all 57,341,160 fields.

Evidence: Ran in Stage C; recorded in `stage-c-report.md`.

Disposition to Claude: **accept as evidence-command correction**. Use the
absolute path (or make the test resolve relative paths from repo root) in
R2 evidence; do not repeat the relative command as reproducible proof.

## Dimension review

- **Estimator fidelity:** mean, n−1 SD, adjusted Fisher–Pearson formula,
  average-rank Spearman, relative-error nulling, and top-N tie ordering
  match rev 3 and the adjudication. C-R1-002 qualifies deterministic math.
- **Determinism:** struct/key ordering, fixed month order, decade order,
  row-order accumulation, and top-event tie breaks are deterministic.
  C-R1-002 remains open for cross-platform bytes.
- **Envelope conformance:** identity content/provenance split and null
  run-only surfaces match rev 3. Stage C's schema structurally validates
  post-hoc, single-event, faithful-run, and fast-run shapes. C-R1-003 is
  the active-spec exception.
- **F1–F3 soundness:** all three findings are sound. F1 correctly includes
  `observed_passthrough` in the null set; F2's decade-level group C avoids
  underpowered month×decade cells; F3's overwrite/stdout rules are
  implemented and tested.
- **Test/evidence alignment:** the Stage S acceptance tests substantively
  match their claims. Edge vectors missing in Stage S are now present.
  C-R1-004 corrects the ignored-gate invocation record.

## Review disposition

R1 is complete with four findings forwarded verbatim to Claude. No
finding alleges faithful `.cli` drift; Ran Stage C release and ignored
identity gates remained exact. C-R1-003 requires contract disposition
before final package closure. C-R1-001 and C-R1-002 should be remediated or
explicitly bounded in R2; C-R1-004 is an evidence-command correction.
