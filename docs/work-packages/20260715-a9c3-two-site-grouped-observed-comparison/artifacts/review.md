# A9c3 consolidated internal review

Status: `ACCEPTED`
Date: 2026-07-15
Report: `docs/reports/a9c3-two-site-grouped-observed-comparison-report.md`
Accepted report SHA-256:
`8e58f0109ea61915277bce92a2c8aff9a30202ac0c9f9aef060c737894015f53`

## Scope and protocol

The lead author froze E01--E14 after canonical evaluation, then appended E15
when independent methods extraction identified the short-stage engineering-
horizon deviation. Three read-only roles independently extracted numeric
evidence, methods, and reference/data authority before report drafting. The
report and manifest then entered one consolidated internal-review phase under
the scientific-report authoring protocol.

The first internal-review report hash was
`376e59172dcf412affe6364552c397cdb8c3681f3a7d926e2fca5a8a3ac33f11`.
After SCI-001 it was
`1cea6d887b3c84520b7b8136b94249ee22e8ea069bff2f1ccc70d2b29aa422d4`;
after CON-001 it was
`bcb9729b8b1227438ba781ee789c7a35b4c089fbaf87b5f95a52cc03ba6da14b`;
and after ACC-001--ACC-004 it was
`bd683f6ec6b15e5ecc44491c6883a3e642af5b7eeabe55bac77e484cdc122745`.
All three lenses accepted that corrected internal-review hash. Changing only
the report status to `ACCEPTED` produced the accepted hash above.

## Pre-draft extraction and deviation disposition

Independent methods extraction found that the implementation computed the
short-stage climate objectives on 30-year prefixes but validated physical
support over their 100-year parent streams. The lead recorded the discrepancy
in E15 before drafting. Every one of 240 attempts retains a first violation at
index 0--111, so every 30-year prefix also fails. The terminal is unchanged,
while the 609,654 total is explicitly labeled a parent-stream diagnostic and
not a 30-year violation total.

Extraction also found that monthly-reconciliation summaries omit their per-
month-length moments, Monte Carlo standard errors, and applied tolerances. The
report discloses that independent numeric audit requires deterministic re-
execution and describes the recorded result as uncertainty-adjusted Monte
Carlo agreement, not agreement within 0.5 percent.

## Lens results

### Accuracy

Final verdict: `ACCEPT` after corrections.

The reviewer reproduced all E01--E15 and governance hashes, study facts,
hypothesis outcomes, source roles, configuration identities, stage and
objective dimensions, table cells, violation arithmetic, resource arithmetic,
rounding, and the final report hash. In particular:

- 14 thresholds × 500 replicates = 7,000 threshold identities;
- 6 configurations × 20 sites × 2 burns = 240 attempts;
- each configuration has 156 objective rows = 95 available + 60 unavailable
  + 1 failed across 31 unique objective IDs;
- the six parent-stream violation totals sum to 609,654;
- all 240 first retained failure indices are 0--111;
- 36 of 36 screened storm-descriptor family rows materially improve; and
- calibration, fit, and evaluation wall times sum to
  2,531.4380139559507 seconds.

### Scientific validity

Final verdict: `ACCEPT` after correction.

The reviewer accepted hypothesis provenance, the amended grouped construct,
candidate-blind calibration, fit/class boundary, staged promotion logic,
short/parent-stream distinction, monthly uncertainty wording, bounded causal
language, limitations, and the hold terminal. The report does not infer that
either model class is impossible or that faithful CLIGEN is superior. It
states that no 100-year full-development climate-objective or Pareto comparison
occurred.

### Consistency and public safety

Final verdict: `ACCEPT` after correction.

The reviewer verified the source commit, Daymet and USCRN product versions and
role periods, DOI/URL identities, access dates, lowercase Subhourly01 README,
confirmation target-series wording, faithful Rust versus Fortran authority,
LFS integrity, third-party/non-relicense language, local links, and package/
catalog status transitions. No operator-specific absolute path, secret,
private-key material, copyrighted local reading-copy path, or local-file URI
appears in the public report or manifest.

## Findings and dispositions

| ID | Severity | Finding | Disposition | Recheck |
|---|---|---|---|---|
| SCI-001 | P2 | The initial next-step recommendation proposed fixing context support and rerunning without addressing 19 unavailable mandatory rows or 8--18 degradation rows. | Required observed/faithful/candidate cause decomposition, completeness confirmation or prospective amendment before new output, and framed unchanged mechanisms only as diagnostic controls. | Bounded scientific recheck `ACCEPTED`; no remaining P1/P2. |
| CON-001 | P3 | R02 omitted NOAA's requested subset access date. | Added `Accessed 2026-07-15` to R01--R03 and matching manifest citations. | Bounded consistency recheck `ACCEPTED`; no remaining P1/P2/P3. |
| ACC-001 | P2 | The methods described all eight configurations as a full pooling-by-tail cross, although the latent grid used paired settings. | Distinguished the renewal 2×2 pool/tail grid from latent k3/k4 at paired (50, 0.95)/(150, 0.90) settings. | Bounded accuracy recheck `ACCEPTED`. |
| ACC-002 | P2 | The report attributed `ca042713` fit ineligibility to development data rather than the coefficient-fit role. | Identified it as a Daymet coefficient-fit station series. | Bounded accuracy recheck `ACCEPTED`. |
| ACC-003 | P3 | `No 100-year candidate development` conflicted with generated and support-validated 100-year parent streams. | Specified that no 100-year full-development climate-objective stage occurred. | Bounded accuracy recheck `ACCEPTED`. |
| ACC-004 | P3 | `Station-count blocker` mislabeled A9c's per-station event-count support floor. | Replaced it with `per-station event-count blocker`. | Bounded accuracy recheck `ACCEPTED`. |

## Scientific and consistency gates

- PASS — all published numeric facts and tables reproduce from E05--E09 and
  E15.
- PASS — hypothesis provenance and outcomes match the prospective design and
  amended construct.
- PASS — the 30-year scientific/100-year parent-stream deviation is explicit
  and cannot be mistaken for a corrected or overwritten execution artifact.
- PASS — no candidate advanced to full development, Pareto replay, selection,
  or candidate freeze.
- PASS — zero locked confirmation target-series access is distinct from
  permitted confirmation metadata access.
- PASS — faithful comparator claims are limited to the fresh Rust profile;
  vendored Fortran remains the semantic authority.
- PASS — normalized observed data and fit-detail artifacts use Git LFS where
  appropriate; raw USCRN annual bytes are not redistributed.
- PASS — strict internal-review verification passed at every corrected report
  hash before acceptance.

## Residual uncertainty

- Exact field totals for 609,654 support violations cannot be reconstructed
  because only the first 100 labels per attempt were retained.
- Monthly-reconciliation component moments and Monte Carlo tolerances require
  deterministic re-execution for independent audit.
- The causes of 19 unavailable mandatory rows remain to be decomposed before
  any new candidate outcome.
- The 8--18 short-stage degradation rows remain unresolved.
- No 100-year full-development, eight-burn replay, confirmation, production
  runtime, or consumer-integration inference is supported.
- Two-site hot-arid inference remains limited to Yuma and Stovepipe Wells.

Final verdict: **ACCEPT**

Open P1: 0
Open P2: 0
