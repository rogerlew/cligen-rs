# Interannual Candidate Experiment 001 Consolidated Review

Status: accepted
Initial review date: 2026-07-14 (America/Los_Angeles)
Initial report SHA-256: `381c6a842dd15e7388acc224f1f95c9f320815d72b8310d9ead54dee5684505f`
Corrected internal-review SHA-256: `eea00fed2c1feb99804514916ce93be57649482ab1dfbedc097d426ee6265d4d`
Accepted revision-1 report SHA-256: `8f6b4b18e8e1761ab3a5ae9651f201060fc0c9ebebe801e98c4ed9909f7f83e4`
Accepted revision-2 report SHA-256: `b1b7f0af0a1f8980183b5e4fa00222c5ae1ccfd29c4bd2b7f43c916652789f5b`
Post-acceptance advisory SHA-256: `b85c5cb775b4356c587399a182c900ee49a477e8c6abb5e5e0aee6b3a4e689af`
Reviewer edits: none; all corrections applied by the lead author

## Review construction

The package used one consolidated review phase with three independent,
read-only lenses:

- accuracy recomputed the published climate and WEPP results from canonical
  analyses;
- scientific validity checked hypothesis provenance, access history,
  uncertainty, construct validity, and conclusion scope; and
- consistency/public safety checked governance, specifications, report,
  manifest, catalogs, citations, hashes, links, LFS, source notices, and the
  verifier's failure behavior.

Before drafting, separate read-only evidence, reference, and standards agents
constructed the claim ledger and citation boundaries. The lead author was the
only file editor. Initial lens verdicts were `ACCEPT WITH CORRECTIONS` with no
P1 finding.

## Independent checks that passed

The reviewers independently established that:

- all 14 gate rows and all 14 detailed climate rows match the canonical
  analysis, including three-decimal rounding, Gate 3 range 1.900–3.243, Gate 4
  range 1.393–2.841, and denominator 408 for every Gate 5 row;
- Gates 1–6 recompute from their numerator, denominator, station, and regime
  fields, and all 14 integrated Gate 7 records pass;
- `7 × 17 × 2 × 8 = 1,904` climate records and
  `8 × 17 × 2 × 8 = 2,176` WEPP records are unique and complete;
- all 448 WEPP corpus medians recompute from paired station/replicate records,
  and all 14 reported two-decimal rows match;
- all 8,092 station-level baseline-zero ratios are null rather than zero,
  infinity, or NaN;
- cold-domain annual-mean ranges recompute to 1.060–1.170 for maximum snow-
  water state and 0.981–1.031 for snowmelt;
- diagnostics reproduce 119 successful fits, zero warnings, two HMM
  relabelings, 24,486 precipitation clips, 59,033 temperature repairs,
  15,565,742 dewpoint caps, and the complete WEPP parser audit;
- the 2,000-replicate, five-year-block target bootstrap and corpus availability
  counts 221, 8, and 2,000 for Gates 1, 4, and 6 match the machine analysis;
- the report, governance, and 12 evidence objects matched their initial
  manifest hashes; the two canonical analyses are LFS-managed and
  `git lfs fsck` passed;
- candidate identities, periods, horizons, replicate qualification, gate
  status, faithful source authority, exploratory boundary, and no-promotion
  status agree across the specifications and experiment record;
- DOI/title/author metadata agrees with the repository corpus, including the
  Daymet/GHCN lineage and Anurag Srivastava attribution; and
- no public artifact links copyrighted local reading copies, exposes a secret
  or operator path, or implies that repository licensing relicenses source
  data.

## Findings and dispositions

| Finding | Severity | Disposition | Bounded recheck |
|---|---|---|---|
| ACC-001 — Gate 4 was incorrectly described as having station conditions | P2 | Corrected to the sole corpus ≤1.10 rule and positive-trace compatibility note | ACCEPT |
| VALID-001 / CONS-004 — acceptance and lens verdicts were declared before review existed | P2 | Report, manifest, and catalog returned to `INTERNAL-REVIEW`; final acceptance occurred only after all rechecks | ACCEPT |
| VALID-002 — abstract omitted exploratory outcome access and used overly strong rejection language | P2 | Abstract now discloses access, says evidence is exploratory, and limits inference to no promotion of exact versions | ACCEPT |
| VALID-003 — 30-year coefficient-fit uncertainty was omitted | P2 | Limitations now distinguish 30 vectors/36 features, runtime parameters from degrees of freedom, and target-only bootstrap from fit uncertainty | ACCEPT |
| VALID-004 / CONS-001 — Gate 1 wording implied every low-frequency component failed | P3/P2 | Abstract now says every row failed the joint primary Gate 1 | ACCEPT |
| VALID-005 — downstream preservation question appeared adjudicated despite no bound | P3 | Introduction now says WEPP responses were documented and preservation was not adjudicated | ACCEPT |
| VALID-006 — bootstrap endpoint rule was incomplete | P3 | Analysis now states nearest-rank p2.5/p97.5 over available aggregates | ACCEPT |
| CONS-002 — strict verifier accepted nonfinite JSON and contradictory review counts; reviews lacked hashes | P2 | Verifier rejects constants/overflowed nonfinite values, hash-binds reviews, requires one terminal verdict/count block, and adds mutation tests | ACCEPT |
| CONS-003 — manifest/report semantic checks were presence-only | P2 | Verifier now checks metadata enums, one H1, exact hypothesis provenance/outcomes, body citations, checked study-fact rows, and matrix arithmetic | ACCEPT |
| CONS-005 — copied template links resolved from the wrong directory | P3 | Template links are destination-relative | ACCEPT |
| CONS-006 — angle-bracket DOI was not canonically encoded | P3 | Manifest uses percent-encoded DOI resolver form and verifier compares canonical encoding | ACCEPT |

## Residual uncertainty

- The accuracy reviewer independently covered published matrices, identities,
  calculations, null semantics, and LFS integrity but stopped a redundant full
  archive verifier after about 100 seconds. The accepted A5b gate record retains
  the prior completed archive-verifier result.
- No A5b production campaign was rerun; this report is a synthesis of accepted,
  hash-bound evidence.
- DOI metadata was cross-checked against the local curated corpus; no live-
  network resolution sweep was required.
- Legacy station files can encode years of record without calendar bounds; the
  report's held-out statement applies to Daymet extension coefficients and
  target periods, not necessarily every historical observation underlying a
  legacy station parameter file.

## Bounded rechecks

- Accuracy independently matched corrected Gate 4 wording to the specification
  and evaluator, then recomputed all 14 gate, 14 climate, and 14 WEPP rows with
  no changed value.
- Scientific validity accepted all six dispositions and independently verified
  the corrected internal-review report SHA-256.
- Consistency/public safety reran the self-test and internal-review verifier,
  attacked nonfinite JSON and semantic contradictions, checked phase state,
  DOI encoding, template links, citations, study arithmetic, and review
  terminal logic, and accepted all six dispositions.

The final transition from `INTERNAL-REVIEW` to `ACCEPTED` changes report status
metadata only; the lead records and hash-binds the accepted report and this
review in the final manifest.

## Post-acceptance advisory incorporation

At the operator's request, revision 2 incorporates
`post-acceptance-advisory-review.md` without rescoring the experiment. The lead
checked the advisory against `SPEC-A5-EVALUATION`, `SPEC-A5B-CANDIDATES`, the
canonical climate diagnostics, and exact run dimensions.

| Advisory | Disposition |
|---|---|
| ADV-001 — Gate 3/4 residual-ratio scaling | Accepted with qualification: revision 2 recommends uncertainty-scaled absolute distance prospectively but preserves every registered outcome |
| ADV-002 — uncalibrated Gate 5 zero-excursion rule | Accepted: revision 2 recommends a faithful-clone null candidate or paired cell test |
| ADV-003 — sparse Gate 1/4 bootstrap surfaces | Accepted: revision 2 requires eligibility-cell diagnosis and informative uncertainty availability |
| ADV-004 — no numeric WEPP bound | Accepted: revision 2 requires a bound or explicit justified no-gate decision before successor output |
| ADV-005 — no intervention-rate guard | Accepted with correction: exact candidate row counts make the dewpoint-cap rate 34.4%, not the advisory's approximate one fifth |

The advisory's stronger causal explanations were bounded. The independent-
multiplier variance identity is reported as an idealized mechanism and future
feasibility screen, not proof that all A5b gates had to fail. The advisory's
analytical Gate 5 null probability and spectral-extrapolation explanation were
not independently established and were not elevated to report findings.

Revision 2 changes no quantitative table, gate or hypothesis outcome,
exploratory boundary, or no-promotion decision. The lead reran strict report
verification, manifest/evidence/review hash checks, repository gates, exact
station-day arithmetic, and LFS integrity after incorporation.

## Final disposition

Accuracy lens: **ACCEPT**
Scientific-validity lens: **ACCEPT**
Consistency/public-safety lens: **ACCEPT**

Final verdict: **ACCEPT**
Open P1: 0
Open P2: 0
Open P3: 0
