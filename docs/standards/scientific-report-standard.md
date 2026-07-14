# Scientific Experiment Report Standard

Status: active (version 1)
Applies to: public experiment reports under `docs/reports/`

## Purpose

This standard separates a scientific result from the work package that produced
it. A report is a durable, public-facing account of an experiment. It must be
traceable to canonical evidence, explicit about the status of its hypotheses,
and reviewable without relying on the author's memory or unpublished files.

The standard governs report structure and claim discipline. The companion
[authoring protocol](scientific-report-authoring-protocol.md) governs the
multi-agent workflow, review lenses, and acceptance gates.

## Required metadata

Every report begins with one H1 title followed by these fields:

```text
Report ID: `<stable-id>`
Status: `DRAFT` | `INTERNAL-REVIEW` | `ACCEPTED` | `SUPERSEDED`
Date: YYYY-MM-DD
Revision: <positive integer>
Authors: <person or role>
Evidence mode: Ran | Static | Derived | Mixed
Experiment record: <repository-relative link>
Evidence snapshot: <repository-relative link>
Review record: <repository-relative link>
```

The filename is `<report-id>-report.md`. `ACCEPTED` means the report manifest
and all review gates pass. `SUPERSEDED` reports remain in the catalog and link
to their replacement. A post-acceptance change increments `Revision`, records
its evidence and dispositions, refreshes every affected hash, and passes the
acceptance gates again; accepted prose is never changed silently.

## Required sections

The following H2 headings appear exactly once and in this order:

1. `Abstract`
2. `Introduction`
3. `Hypotheses`
4. `Methods`
5. `Analysis`
6. `Results`
7. `Limitations and validity`
8. `Conclusions`
9. `Reproducibility and data availability`
10. `References`

Subsections may be added. Methods state what was done; Analysis states how
measurements and decisions were derived; Results state observations;
Conclusions interpret only results already reported. Limitations and validity
must identify threats to internal, construct, and external validity that are
material to the conclusions.

## Hypothesis registry

Hypotheses have stable IDs (`H1`, `H2`, and so on) and one of these provenance
classes:

- `preregistered`: stated as a hypothesis before outcome access;
- `amended`: changed prospectively, with the amendment and access boundary
  identified;
- `retrospective mapping`: reconstructed after execution from a frozen gate or
  decision rule; or
- `exploratory`: proposed or evaluated after relevant outcome access.

Each registry row states the scope, metric or comparison, decision rule,
provenance, outcome, and result location. An amended, retrospectively mapped,
or exploratory hypothesis cannot be described as confirmatory. A report must
distinguish failure to pass a bound from evidence that a model family is
impossible or generally inferior.

## Claims and evidence

Each consequential claim belongs to one of four classes:

- `Ran`: directly produced by a recorded execution;
- `Static`: established by inspecting an authoritative source;
- `Derived`: recomputed from canonical evidence; or
- `Interpretation`: an inference bounded by the preceding evidence.

Every quantitative result cites a stable repository evidence ID (`E01`,
`E02`, ...). Every material literature claim cites a primary-source reference
ID (`R01`, `R02`, ...). Repository evidence and external references are listed
separately under References. Each declared evidence and reference ID must be
cited in the report body before its References definition. A DOI is preferred;
sources without a DOI must say `No DOI` and provide an authoritative URL where
available.

The report may summarize machine evidence but does not become its authority.
Exact counts, thresholds, identities, hashes, and status come from the cited
specification, manifest, or canonical analysis. Faithful CLIGEN behavior is
governed by the vendored source and the repository's source-authority decision,
not by external descriptions of other CLIGEN versions.

## Quantitative presentation

Tables identify units, aggregation level, comparator, rounding, and treatment
of unavailable or baseline-zero values. The text must not imply more precision
than the evidence. Reported ratios state their numerator and denominator.
Uncertainty intervals state the resampling unit, replicate count, interval
rule, and whether they affect a decision.

Methods include a `Study identity` table whose fact/value rows are duplicated
in the strict report manifest. The verifier checks those rows and registered
matrix arithmetic so a report cannot pass with contradictory dimensions.

Negative and null findings are reported with the same granularity as positive
findings. Descriptive downstream responses cannot be converted into pass/fail
claims without a registered bound.

## Reproducibility and public safety

The report links the experiment record, specifications, canonical analyses,
evidence-identity manifest, review, and exact source commit. It states whether
large files use Git LFS and how their content identities are checked.

Public reports may cite copyrighted literature but must not link to untracked
or nonredistributable local reading copies. Third-party datasets retain their
own notices and citations. Secrets, local credentials, and operator-specific
absolute paths are prohibited.

## Acceptance

A report becomes `ACCEPTED` only when:

- its manifest passes `docs/reports/verify-report.py`;
- every registered hypothesis has an outcome and a Results cross-reference;
- every measured and published claim has the required evidence class;
- independent accuracy and consistency lenses have verdict `ACCEPT`;
- the hash-bound consolidated review has one terminal `ACCEPT` verdict and
  exactly one zero count for open P1 and P2 findings;
- no P1 or P2 review finding remains open; and
- the repository and package-specific gates recorded by the authoring protocol
  pass.
