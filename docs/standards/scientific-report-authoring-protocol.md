# Scientific Report Authoring Protocol

Status: active (version 1)
Companion standard: [Scientific Experiment Report Standard](scientific-report-standard.md)

## Purpose and roles

This protocol produces one coherent report while using independent agents to
reduce transcription, confirmation, and citation errors. The lead author is
the sole editor of the report. Subagents are read-only investigators and
reviewers: they return findings with exact evidence locations and do not edit,
commit, or push.

The package retains one consolidated review phase, consistent with the work-
package convention. Multiple lenses are recorded inside that phase rather than
treated as serial approval ceremonies.

## Phase 1: scope and evidence freeze

Before drafting results or conclusions, the lead records:

- report ID, question, scope, source commit, and experiment package;
- authoritative specifications and amendment history;
- canonical machine analyses and their content hashes;
- the external literature corpus and source-access limits;
- a claim-evidence ledger with stable evidence IDs; and
- the hypothesis provenance vocabulary that applies to the experiment.

The freeze identifies any outcome access that changes confirmatory work into
exploratory work. Later corrections are appended as amendments; they do not
rewrite the access history.

## Phase 2: independent extraction

Dispatch at least these read-only roles, in parallel where practical:

1. **Evidence analyst** — independently recomputes counts, tables, ratios,
   rounding, gate outcomes, null handling, and artifact hashes.
2. **Methods analyst** — reconstructs design, candidate identities, frozen and
   amended rules, population, transformations, uncertainty, and limitations.
3. **Reference analyst** — verifies primary-source metadata, DOI/URL identity,
   claim support, version scope, license-safe linking, and authority boundaries.

Agents return a claim ledger, disagreements, and residual uncertainty. An
unsupported claim is omitted or explicitly weakened. The lead resolves
disagreements against authoritative artifacts before drafting.

## Phase 3: synthesis

The lead first builds the hypothesis/outcome crosswalk, then writes from the
accepted ledger using the report template. The report uses one voice and keeps
measurement, interpretation, and decision statements distinct. Exact numeric
claims point to repository evidence; literature supplies scientific context,
not project result values.

The draft and manifest enter `INTERNAL-REVIEW` together. After this boundary,
changes that affect a result, hypothesis outcome, or conclusion require a
review finding and bounded recheck.

## Phase 4: consolidated internal review

Read-only reviewers apply independent lenses:

- **Accuracy:** recompute every published table and key narrative number;
  verify hashes, sample dimensions, gate logic, rounding, and null rules.
- **Scientific validity:** verify hypothesis provenance, design-to-claim fit,
  amendments, uncertainty language, limitations, and conclusion scope.
- **Consistency and public safety:** compare names, versions, periods,
  candidate status, citations, links, source authority, terminology, LFS
  identities, and data notices across the report and repository records.

Each finding has a stable ID, severity, evidence, consequence, required
correction, disposition, and recheck. Severities are:

- `P1`: invalidates or reverses a central result, or creates a serious safety
  or provenance problem;
- `P2`: materially weakens accuracy, reproducibility, or claim scope; and
- `P3`: localized clarity, metadata, or maintenance defect.

The lead alone applies corrections. A reviewer or a newly dispatched bounded
review checks each P1/P2 disposition. Acceptance requires zero open P1/P2
findings; open P3 findings must be enumerated as residual uncertainty.

## Mechanical gates

Run the following from the repository root:

```sh
python3 docs/reports/verify-report.py --internal-review <report-manifest>
python3 docs/reports/verify-report.py <report-manifest>
python3 docs/reports/verify-report.py --self-test
git diff --check
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
```

The report verifier enforces strict JSON, file/hash identities, filename and
catalog identity, required metadata and section order, hypothesis/reference/
evidence membership, study-identity rows and registered matrix arithmetic,
body citations, local link existence, hash-bound accepted review records, and
the absence of drafting placeholders. Strict JSON includes duplicate-key and
nonfinite-number rejection. Run the coverage and CRAP gates from `AGENTS.md`
when production functions in `crates/` changed.

## Scientific and consistency gates

The consolidated review records PASS or FAIL for every item:

- all numeric tables independently reproduce from canonical evidence;
- design dimensions multiply to every reported matrix total;
- rounding, missing-value, unavailable-field, and baseline-zero policies match
  the frozen analysis;
- every conclusion follows from a reported result and does not generalize
  beyond the evaluated versions, stations, periods, and gates;
- every quantitative claim has a repository pointer and every literature
  claim has a primary citation within that source's scope;
- candidate names, versions, horizons, stations, replicates, gates, and status
  agree with the experiment package, specifications, analyses, and roadmap;
- faithful-mode claims follow the repository source-authority hierarchy;
- prospective, amended, and exploratory language agrees across all artifacts;
- machine-evidence hashes and any LFS pointers validate; and
- copyrighted reading copies remain untracked and third-party notices remain
  accurate.

## Closure record

The work package stores the frozen claim ledger, consolidated review with lens
coverage and dispositions, and exact gate commands/results. On closure, set
the report and manifest to `ACCEPTED`, add the report and package to their
catalogs, and retain residual uncertainty. A later scientific correction
increments the report revision, retains the prior accepted hash and new review
or advisory disposition, refreshes affected manifest hashes, and reruns the
acceptance gates. A materially changed question or conclusion requires a
superseding report; it does not silently alter an accepted conclusion.
