# A5c Closure Review

Verdict: `ACCEPT`
Review date: 2026-07-14
Reviewer: Codex (package closure review)
Evidence mode: Static review plus executed verifier and repository gates

## Scope

This review checks whether A5c faithfully applies the already accepted A5b
evaluation contract and closes with a conservative disposition. It does not
recompute the A5b climate or WEPP analyses, rank candidates, or independently
validate the underlying observational products. Those questions were covered
by the A5b package review and the accepted experiment-report review, both of
which are immutable inputs in the A5c evidence lock.

## Traceability review

The machine decision contains exactly seven candidate IDs and binds each to
the independent generation-profile and station-model identifier registered in
SPEC-A5B-CANDIDATES. Each candidate has exactly the 30- and 100-year rows. The
verifier extracts the 14 source rows from the accepted A5b results table and
requires every recorded row to remain ineligible.

The decision follows SPEC-A5-EVALUATION's monotonic rule: passing the complete
evidence gate does not overcome a climate-gate failure, and eligibility would
still not compel promotion. No candidate passed all climate gates, so an empty
eligible set and empty promoted-profile set are the only contract-consistent
outcome.

## Evidence-boundary review

The package labels the final evidence exploratory for model selection and
states why: candidate metric and response access occurred during successor
contract repairs. It uses that evidence only for conservative rejection of
versions that failed registered gates. It does not select a near miss, weaken
a gate, or claim confirmatory comparative superiority. The renewal condition
requires a new prospectively registered study, preventing reuse of the A5b
response surface as a hidden selection phase.

## Advisory-finding disposition

The post-acceptance advisory review concurs that no defensible recalibration
would rescue the seven evaluated versions. A5c correctly treats its findings
as prospective:

- analytic variance-budget feasibility is required before another campaign;
- variance reallocation or structure-preserving conditioning/resampling
  replaces unconstrained multiplicative variance addition;
- daily precipitation behavior is integrated or preserved by construction;
- observation-scaled guards and a faithful-clone null calibrate false failure;
- uncertainty availability, downstream WEPP criteria, and intervention-rate
  guards are registered before response access.

None of those recommendations is applied retroactively to alter an A5b gate.

## Compatibility and version review

The evidence lock snapshots the accepted runspec, generation-profile,
provenance, station-document, and typed-output specifications and schemas. The
verifier requires the public generation-profile enum to remain exactly
`faithful_5_32_3` and `fast_batch_v0`, with `faithful_5_32_3` as default, and
rejects the presence of any A5b profile ID in those public surfaces. All seven
surface-change flags are false. No production source or schema was changed.

This is consistent with the operator's independent-version rule: a research
adjudication changes none of the station-schema, station-model,
generation-profile, provenance, or output-schema compatibility axes.

## Verification review

`verify-a5c-decision.py` passes after checking 24 SHA-256 identities, 14 gate
rows, the accepted report manifest, all candidate identity mappings, public
defaults, and roadmap/catalog/ADR closure. It rejects synthetic mutations for
duplicate JSON keys, non-finite JSON, a bad evidence hash, fabricated candidate
eligibility, a promoted profile, a public-surface change, and a changed
default. Repository format, lint, and test gates pass.

## Findings

No P1, P2, or P3 findings. The package is internally consistent, conservative
under its evidence boundary, and complete against the ratified A5c acceptance
criteria.
