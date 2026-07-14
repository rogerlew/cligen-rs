# A5c Interannual Profile Adjudication

Status: `NO-PROMOTION`
Decision date: 2026-07-14
Evidence mode: Static adjudication of frozen A5b evidence

## Question

Does any A5b interannual candidate satisfy the accepted A5 evaluation
contract strongly enough to enter a public station-model or generation-profile
surface?

## Finding

No. The frozen A5b table contains 14 candidate/horizon rows: seven candidate
versions at 30 and 100 years. Every row is ineligible because it fails one or
more of climate Gates 1–6. No candidate passes the complete climate vector at
both horizons. Gate 7 passes for all rows and establishes evidence
completeness; it is not a substitute for a failed climate gate.

The result is especially clear on preservation guards. Every candidate/horizon
row fails Gate 3 (monthly contract), Gate 4 (daily precipitation structure),
and Gate 5 (storm descriptors). The accepted report and its advisory review
show that these are substantive or structurally expected failures, not a case
where a single marginal threshold blocks an otherwise eligible candidate.

## Evidence boundary

The final A5b model-selection evidence is exploratory. Candidate metric and
response access occurred while successor executable contracts were repaired.
That prevents a confirmatory promotion or post-hoc selection among near misses.
It does not weaken the conservative conclusion: a candidate that demonstrably
failed registered gates cannot become eligible because the evidence boundary
is stricter.

Accordingly, this package uses the A5b evidence only to reject promotion of the
evaluated versions and to form prospective design requirements. It does not
rank the seven versions for deployment, revise the frozen gates, or claim that
interannual modeling itself failed.

## Interface disposition

No compatibility surface changes:

- generation-profile enum: unchanged;
- station document and station-model contracts: unchanged;
- runspec and provenance schemas: unchanged;
- typed-output schema: unchanged;
- legacy `.par` format: unchanged;
- default generation profile: `faithful_5_32_3`;
- default QC policy: `faithful`.

The A5b identifiers remain research-only identifiers in experimental schemas
and evidence. Version axes remain independent; a decision record does not
force any file-format or output-schema revision.

## Renewal condition

Any renewed candidate must enter a new prospectively registered study. The
successor should first prove that its candidate class can preserve the monthly
variance budget, then test variance reallocation or structure-preserving
conditioning/resampling with integrated daily precipitation behavior. Before
freezing that study, it should incorporate the advisory's prospective
calibrations: observation-scaled preservation distances, a faithful-clone null
candidate, a measurable uncertainty surface, an explicit WEPP response rule,
and bounded intervention rates. Both 30- and 100-year horizons and the complete
downstream campaign remain required.

The machine-readable disposition is
[`a5c-decision-v1.json`](a5c-decision-v1.json); its immutable inputs are listed
in [`evidence-lock-v1.json`](evidence-lock-v1.json).
