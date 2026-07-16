# A9c2 consolidated internal review

Status: `ACCEPTED`
Date: 2026-07-15
Review revision: 2
Report: `docs/reports/a9c2-hot-arid-roster-feasibility-report.md`
Accepted report SHA-256:
`55353e0555af45991792b8d77f9926969e1495053420c8450ac91c5346d6385a`

The accepted revision-1 report and review hashes are retained in
`post-acceptance-operator-disposition.md`: report
`eb83567b06bc65d7261a0bdb44589133c4a6493b90c359cb7f0062a40f9f6051`
and review
`44d50a4356c9830cb6f68f6a8dc915f678b1113e774a470127c8f2a65e8763a5`.

## Scope and protocol

For revision 1, the lead author froze E01--E11 and a claim ledger before
drafting. Three independent read-only roles then reviewed the internal-review
report under the scientific-report authoring protocol:

- accuracy independently recomputed all 113 census rows, displayed table
  cells, hashes, rounding, reason arithmetic, pair distance, hypotheses,
  access flags, and terminal;
- scientific validity checked provenance, population, transformations,
  partition semantics, stop logic, limitations, and conclusion scope; and
- consistency/public safety checked versions, terminology, source commit,
  links, evidence identities, repository alignment, LFS, copyright, and path
  safety.

The original internal-review report hash was
`8531f8c9da47aef921690f8ed588bda597fc6219a8cbd6afc6cca067a5a356a3`.
After finding dispositions, the corrected internal-review hash was
`1d24b8b6affcf51853856eb4bbdda5f41c30b70ea31b58a2df28ca953b82b12a`.
Changing only the status metadata to `ACCEPTED` produced the accepted hash
bound above.

## Review-integrity incident and replacement

The first Phase-4 accuracy reviewer disclosed that a broad local search had
traversed exposed A9c fit JSON and printed matching access-metadata lines. It
reported no daily/subdaily values or confirmation series, and none of those
matches informed a finding, but the command exceeded that review assignment's
explicit file boundary. The lead discarded the entire review, interrupted the
role, and commissioned a new independent accuracy reviewer limited to explicit
E01--E11 paths. Only the replacement accuracy review contributes to the
verdict. This incident did not access an A9c2 candidate output or any locked
confirmation target series.

## Lens results

### Accuracy

Verdict before correction: `ACCEPT WITH CORRECTIONS`.

The replacement reviewer independently reproduced 255 listing rows, 113
metadata-base sites, 2,765 descriptor stations, 18 locked confirmation sites
with 17 in the base, three descriptor matches, two accepted sites, the 17 + 94
+ 2 = 113 reason arithmetic, the 2-of-5 deficit, every displayed rounded
number, the 498.859 km accepted-pair distance, and the registered hold. All
E01--E11 and report hashes reproduced.

### Scientific validity

Verdict before correction: `ACCEPT WITH CORRECTIONS`.

The population, inclusive A8a bounds, nearest-descriptor procedure, haversine
method, confirmation partition, filter precedence, retrospective hypothesis
mapping, first-hold stop, and scope limits were supported. The report does not
interpret the roster result as a grouped-estimator or candidate-model failure.

### Consistency and public safety

Verdict before correction: `ACCEPT WITH CORRECTIONS`.

The internal-review verifier passed. Source commit, E01--E11 identities,
sections, hypothesis outcomes, links, access states, and study facts agreed.
No operator-specific path, credential, copyrighted reading-copy link, or new
oversized artifact appeared in the report or manifest. No new LFS object is
needed.

## Findings and dispositions

| ID | Severity | Finding | Disposition | Recheck |
|---|---|---|---|---|
| SCI-001 | P2 | The draft said the locked confirmation roster was not consumed, although its metadata were read to enforce the ID/distance partition. | Corrected the access-boundary text to distinguish permitted station-ID/coordinate metadata from prohibited daily/subdaily target series; no roster replacement is claimed. | Independent bounded recheck `ACCEPTED`; Abstract, Methods, Access boundary, Conclusions, and manifest now agree. |
| ACC-R-001 | P2 | Replacement accuracy review independently found the same metadata-versus-series contradiction. | Resolved by the SCI-001 correction. | Covered by the same independent bounded recheck. |
| CON-001 | P3 | `pre-2010` did not state the inclusive 2010-01-01 cutoff exactly. | Replaced with `commissioned by the 2010-01-01 cutoff`. | Exact match to E03 confirmed. |
| CON-002 | P3 | `arbitrary count` exceeded E09's support. | Replaced with `uncalibrated design count`. | Claim scope confirmed. |
| ACC-R-002 | P3 | Replacement accuracy review corroborated CON-002. | Resolved by the CON-002 correction. | Text search and evidence comparison pass. |
| ACC-R-003 | P3 | Replacement accuracy review corroborated CON-001. | Resolved by the CON-001 correction. | Text search and evidence comparison pass. |
| ACC-R-004 | P3 | `did not write the grouped objective amendment` was ambiguous because E01 contains a high-level section with that name. | Specified that the complete A9c2 registry and versioned SPEC-A9 grouped-evaluation amendment were not written. | Boundary agrees with the first-hold stop. |

## Revision 2 post-acceptance review

Revision 2 adds E12, the operator's decision to accept the two-site hot-arid
evidence as functionally adequate for research continuation. It changes no
census value, hypothesis outcome, access state, or A9c2 terminal. The first
revision-2 internal-review report hash was
`a239fc370fac3dea6c973b0f77c2fa4df6e203e5c50afa1641eebd5d3869828f`.
After review corrections its internal-review hash was
`10d38cf060195c02f1f19e259b0f5b1fdb785145791fea970a5022f2a4fe073d`.
Changing only the status metadata to `ACCEPTED` produced the accepted hash at
the top of this record.

### Revision 2 lens results

- Accuracy: `ACCEPT`. E01--E11 hashes and all numeric facts, H1--H3 outcomes,
  2-of-5 arithmetic, access states, and terminal remain unchanged. E12 and the
  new study-identity rows reproduce. The prior report/review/gate hashes in E12
  agree with their retained bindings.
- Scientific validity: `ACCEPT`. Functional adequacy is consistently an
  operator risk-acceptance decision, not statistical evidence that two sites
  equal five. Power remains an uncertainty diagnostic, nonfinite estimators
  remain hard failures, and two-site spatial limitations are explicit.
- Consistency/public safety: `ACCEPT WITH CORRECTIONS`, then `ACCEPT` after
  bounded recheck. A9c2 remains a hold; A9c3 remains unscaffolded and
  unauthorized; no corpus-expansion recommendation remains active.

### Revision 2 findings and dispositions

| ID | Severity | Finding | Disposition | Recheck |
|---|---|---|---|---|
| A2-CON-001 | P2 | The retained kickoff template exposed an operator-specific absolute repository path. | Replaced both absolute paths with repository-logical wording. | Bounded consistency/public-safety recheck `ACCEPT`; no operator path remains in the package or report. |
| A2-CON-002 | P3 | The report's `separately scaffolded A9c3` wording conflicted with the roadmap's unscaffolded state. | Changed the report to say the next action is to scaffold A9c3 and the package to say A9c3 is roadmapped and unscaffolded. | Bounded recheck `ACCEPT`; future scaffolding is permitted and execution remains unauthorized. |

Revision-2 internal-review verification passed after both corrections. No
A2-ACC or A2-SCI finding was opened.

## Scientific and consistency gates

- PASS — every numeric table and key narrative number reproduces from E04 and
  E11.
- PASS — reason and roster arithmetic reproduce without an unavailable or
  baseline-zero ambiguity.
- PASS — every conclusion is bounded to the exact frozen USCRN population,
  A8a descriptor screen, partition, and first-hold gate.
- PASS — hypotheses are retrospective mappings to prospective rules and are
  not described as confirmatory.
- PASS — confirmation metadata access is distinct from confirmation target-
  series access.
- PASS — candidate class, fit, grouped calibration, A9d, and runtime claims
  remain explicitly unevaluated or unauthorized.
- PASS — machine-evidence hashes reproduce and no new large artifact requires
  LFS.
- PASS — the report uses the public NOAA citation only for source context and
  the frozen E07 snapshot for exact results.
- PASS — E12 is governance evidence, not a relabeling of the failed H1 result
  or an empirical model-adequacy claim.
- PASS — A9c3 is roadmapped but unscaffolded and unauthorized; A9d, runtime,
  and consumer integrations remain unauthorized.
- PASS — strict internal-review verification passed before acceptance.

## Residual uncertainty

- The nearest legacy CLIGEN descriptor may not represent the exact USCRN
  point, and the A8a screen is not a PET-based physical aridity definition.
- Later, inactive, non-USCRN, and other subhourly networks are outside scope.
- The recorded access history and deterministic program boundary are not an
  operating-system forensic audit.
- A different prospective corpus or regime definition could yield a different
  roster without changing this A9c2 terminal.
- The overwritten revision-1 manifest bytes are not retained as a separate
  file; E12 retains their accepted SHA-256 identity.

Final verdict: **ACCEPT**

Open P1: 0
Open P2: 0
