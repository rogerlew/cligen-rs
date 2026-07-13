# Handoff — Independent Claude Review

Date: 2026-07-12
Target reviewer: Claude
Review mode: review-only, evidence-backed; one review artifact permitted
Review target: commits `ae58c1c` and `315c4e9`
Expected output:
`docs/work-packages/20260712-sota-climate-generator-review/artifacts/review-claude.md`

## Mission

Independently review the state-of-the-art climate-generator investigation for
scientific accuracy, evidentiary discipline, completeness, public-repository
safety, and implementation realism for `cligen-rs` and WEPPcloud.

Do not edit any review target or silently resolve findings. The sole permitted
repository write is
`docs/work-packages/20260712-sota-climate-generator-review/artifacts/review-claude.md`;
if the operator asks for a chat-only review, return the same report without
writing it. Do not commit or push unless the operator separately requests that
action. If a claim cannot be verified from the available evidence, mark the
evidence limit instead of guessing.

## Dispatch environment

- Repository: `https://github.com/rogerlew/cligen-rs`
- Checkout: `/Users/roger/src/cligen-rs`, or another checkout at repository
  root with the same ignored local-source corpus available
- Start branch: current `origin/main`; do not create or adopt a side branch
- Scientific review target: frozen at `315c4e9` with baseline parent
  `4b3ef1a`; the later handoff-only commit is not a scientific target
- Push target, only if the operator separately authorizes publication of the
  review artifact: `origin main`

## Repository posture

Read `AGENTS.md` first. For every claim about faithful CLIGEN behavior, the
authority order is:

1. `reference/cligen532/cligen.f` — executable faithful-mode specification;
2. `docs/specifications/SPEC-FAITHFUL-GENERATION.md` and its traceability
   package;
3. historical CLIGEN literature only as corroborating context.

Do not use intuition or external CLIGEN descriptions to overrule the vendored
Fortran. Treat every proposed extension as profile-owned behavior that must
declare itself in output provenance. This review is informational and does not
authorize a generation-profile or roadmap decision.

## Primary review set

Read these files completely:

1. `docs/lit-reviews/sota-climate-generator-gap-analysis.md`
2. `docs/lit-reviews/sota-climate-generator-annotated-bibliography.md`
3. `docs/work-packages/20260712-sota-climate-generator-review/package.md`
4. `docs/work-packages/20260712-sota-climate-generator-review/artifacts/source-evidence.md`
5. `docs/work-packages/20260712-sota-climate-generator-review/artifacts/local-reading-copies.tsv`
6. `docs/work-packages/20260712-sota-climate-generator-review/artifacts/review.md`
7. `docs/work-packages/20260712-sota-climate-generator-review/artifacts/gate-results.md`
8. `references/open-access/README.md` and `manifest.tsv`

Then inspect the supporting authority needed to test central claims:

- `docs/specifications/SPEC-FAITHFUL-GENERATION.md`
- `docs/work-packages/20260712-faithful-generation-spec/artifacts/parameter-to-output-map.md`
- `docs/work-packages/20260710-q3-qc-filter-dissection/artifacts/frontier-analysis.md`
- `docs/work-packages/20260710-q3-qc-filter-dissection/artifacts/monthly-sd-addendum.md`
- `docs/specifications/SPEC-QUALITY-REPORT.md`
- `docs/ROADMAP.md`

The dispatch artifact itself is outside the scientific review target.

## Source-access rules

- `references/open-access/` contains redistributable copies. Check article
  identity, license, version, source URL, and SHA-256 against `manifest.tsv`.
- `references/copyrighted/` is Git-ignored. If it exists locally, only the
  canonical files named in `local-reading-copies.tsv` may support scientific
  annotations; do not copy, move, stage, or quote them extensively.
- Alternate and RNG PDFs may be listed, hashed, and have first-page metadata
  inspected solely to verify duplicate classification, scope, and acquisition-
  queue reconciliation. Do not count them as independent scientific evidence.
- Alternate Katz and Wilks PDF wrappers are duplicate content, not independent
  evidence.
- If local copyrighted files are unavailable, review their annotations against
  DOI/publisher records and explicitly mark the full-text verification gap.
- Use primary sources for technical claims. Do not treat a review article as
  sole support when the cited model paper is available.

## Questions the review must answer

### 1. Faithful CLIGEN baseline

- Does every baseline statement agree with the Fortran/spec, including
  fixed-climatology seasonality, observed-mode substitution, cross-variable
  coupling, random-stream QC, and storm-output boundaries?
- Is the historical USDA note AB-39 kept subordinate to the faithful source?
- Does any recommendation risk silent divergence, faithful RNG consumption,
  precision changes, or inferred defaults?

### 2. Scientific synthesis

- Are the 39 annotations bibliographically correct and faithful to the cited
  model, especially AB-02/03/09/12/21–23 and AB-34–38?
- Does the report correctly distinguish a measured aggregate-variance deficit
  from its possible causes? Challenge both the annual-state hypothesis and the
  daily precipitation-structure counterfactual.
- Are monthly SDs consistently treated as output targets, while Fourier/EOF
  coefficients are treated as a representation requiring stochastic
  coefficient, covariance, constraint, and persistence semantics?
- Are daily occurrence, amount dependence, tails, spell persistence, and later
  subdaily generation coordinated without double counting or incompatible
  production profiles?
- Are ML forecast/emulator/downscaling systems correctly kept outside the
  direct CLIGEN peer class and native Rust implementation path?

### 3. Ranking and feasibility

- Is enabling schema/provenance/I/O work correctly separated from model
  improvements?
- Does each ranked gap have an evidence class, WEPP value, concrete Rust seam,
  data requirement, validation gate, main risk, and credible feasibility?
- Do implementation seams match the current Rust code and preserve the active
  rendered-`.cli` quality path?
- Is the recommended sequence internally consistent, including the narrowly
  scoped precipitation counterfactual in the interannual spike and the broader
  later precipitation-structure study?
- Is the sequence clearly pending operator ratification rather than silently
  modifying `docs/ROADMAP.md`?
- Is deprecated single-storm behavior appropriately deferred without
  weakening faithful-mode compatibility?

### 4. Evidence and public-repository safety

- Can every measured claim be traced to repository evidence and every
  published claim to a primary citation?
- Do access labels accurately distinguish archived, link-only, acquisition-
  required, and local-reading-copy sources?
- Does every archived PDF have independently supportable redistribution terms?
  Pay particular attention to noncommercial/no-derivatives terms and whether
  the repository wording overstates what they permit.
- Are local reading identities reproducible without tracking copyrighted
  files? Are duplicate PDFs and the RNG papers correctly excluded?
- Are preprints, software licenses, data licenses, and article licenses kept
  distinct?
- Does the remaining eight-paper acquisition queue actually remain
  unfulfilled by the current local files?
- Is the package's `EXECUTED-COMPLETE` state still honest after the acquisition
  addendum, and does `gate-results.md` distinguish original and addendum runs
  accurately?

### 5. Missing SOTA or WEPP-relevant gaps

- Identify any major generator family or capability whose absence would change
  the top-eight ordering or the first two studies.
- Distinguish “interesting omission” from an omission that materially changes
  the decision.
- Check whether erosion-relevant validation covers runoff, soil loss, event
  intensity, antecedent state, and aggregation-scale behavior adequately.

## Reproducible checks

Start with:

```text
git status --short --ignored
git log --oneline --decorate -5
git diff 4b3ef1a..315c4e9 --stat
git diff 4b3ef1a..315c4e9 --check
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
```

Also verify that:

- `manifest.tsv` has exactly one row per archived PDF and every SHA-256 matches;
- all canonical rows in `local-reading-copies.tsv` match any available local
  file;
- no path under `references/copyrighted/` is tracked;
- all relative Markdown links in the review package resolve;
- AB identifiers are unique and sequential and every entry has a DOI or an
  explicit no-DOI note.

Do not run coverage/CRAP gates: the review commits change no production
function. Do not modify or normalize any PDF while checking it.

## Finding standard

Use these priorities:

- **P1:** central conclusion is false or materially unsupported; faithful-mode
  authority is violated; a public-source/license problem makes the repository
  unsafe; or the recommended first study is invalidated.
- **P2:** material scientific, attribution, traceability, feasibility, or
  sequencing defect that should be corrected before relying on the review.
- **P3:** useful precision, clarity, or coverage improvement that does not
  change the main decision.

Give every finding a stable identifier such as `CLAUDE-001`. Every finding
must include:

1. priority and short title;
2. exact file and tight line range;
3. the claim or omission;
4. primary evidence supporting the finding;
5. concrete correction or disposition recommendation.

Avoid preference-only findings, broad literature wish lists, or criticism
without a falsifiable correction.

## Required report shape

Write the expected output path above with:

1. **Verdict** — `ACCEPT`, `ACCEPT WITH CORRECTIONS`, or `HOLD`;
2. **P1/P2 findings** — ordered by priority, or “none”;
3. **P3 observations** — optional;
4. **Coverage ledger** — files, papers/records, local PDFs, and commands
   actually inspected or run;
5. **Residual uncertainty** — unavailable sources, unverifiable licenses, or
   claims checked only at abstract/record level;
6. **Recommended disposition order** — smallest safe correction sequence.

If no P1/P2 finding exists, say so explicitly and still provide the coverage
ledger and residual uncertainty. Do not mark findings resolved; only the
operator/package executor can disposition them.
