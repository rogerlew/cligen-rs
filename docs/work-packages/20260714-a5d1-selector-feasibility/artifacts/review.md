# A5d1 Selector Feasibility Consolidated Review

Status: `ACCEPTED`
Review date: 2026-07-14 (America/Los_Angeles)
Controlling freeze: `dd38484dca7da633ed30854c16074fa66b2a7a7fdd53b05253277125cdd99d22`
Corrected internal-review report SHA-256: `2b23c2bd921299394241a2c05b911b3d25e072fd0adf4a53c70f5517163af397`
Accepted report SHA-256: `c2ec3dab82b091e41e942f937b1f3e9e7853129023aeb8a3ba5c408f19d05e03`
Reviewer edits: none; all changes were applied by the lead

## Review construction

The package used one consolidated review phase with independent read-only
accuracy/numerical, scientific-validity, and consistency/exposure lenses. The
lead alone edited contracts, tools, results, report, and closure records.

Review began against v3 and deliberately continued across corrections. A
finding that affected optimization or a registered scientific vector
invalidated the corresponding development execution; it was not repaired by
post-hoc relabeling. V2, v3, and v4 completed results were invalidated. V5 was
stopped after 65/306 path records and issued no aggregate or decision. V6 was
then prospectively frozen before its own outcomes.

## Independent checks

The final reviewers independently established that:

- the v6 canonical freeze identity, input/tool hashes, four prior-outcome
  disclosures, and zero-outcome-at-freeze boundary reconcile;
- all 17 station, parameter, Daymet, Fourier/EOF, library, and feature
  identities match their manifests;
- the 34 marginal programs reconstruct as 30 passes, including 17/17 at pool
  256, with the same failure classifications and centered metrics;
- all 306 paths reconstruct with zero complete passes and first-failure counts
  36 stationary, 265 finite-prefix, three boundary, and two dependence;
- aggregate January replay has zero mismatches and passes 290/306 cells at 30
  years and 293/306 at 100 years;
- the 340-record detailed archive is ordered, complete, and hash-consistent;
- independent physical rendering passes 306/306 with zero intervention and an
  exact 30-year prefix;
- the terminal hold is limited to the registered algorithms, tolerances,
  stations, seeds, iteration bound, and single burn-0 library;
- the report's counts, provenance, transition language, limitations, and A5d1b
  recommendation match v6; and
- no confirmation object, public candidate, production/specification change,
  secret, absolute operator path, or copyrighted reading copy entered the
  public evidence.

## Findings and dispositions

| Finding | Severity | Lead disposition | Bounded recheck |
|---|---|---|---|
| A5D1-001 — v2 unparameterized wet-day bin/descriptor references used `max(mean wet days, 1)` instead of the actual uniform wet-day denominator | P1 | Invalidated v2; corrected the denominator and issued a new freeze | Accepted before v3 |
| A5D1-002 — v3 optimized raw moments without establishing centered variance/covariance improvement | P1 | Invalidated v3; fixed annual means and targeted centered detrended variance/covariance in v4+ | Accepted in v4/v6 |
| A5D1-003 — v3 detrended the Daymet target but not candidate and baseline path series | P1 | Invalidated v3; applied identical OLS detrending to all three | Accepted in v4/v6 |
| A5D1-004 — v3 inherited stationary preservation flags rather than replaying empirical constraints at 30/100 years | P1 | Invalidated v3; finite-prefix replay now covers both horizons inside the optimizer and decision | Accepted in v4/v6 |
| A5D1-005 — v3 could select zero-weight blocks and lacked complete tie/numerical evidence | P2 | Forbade weights ≤`1e-12`, capped weights, fixed leap mass, and recorded bounded tie solves/residuals | Accepted in v4/v6 |
| A5D1-006 — the v3 endpoint proxy collapsed boundary direction and omitted spell continuation | P2 | Replaced it with DD/DW/WD/WW and wet/dry continuation contributions at both horizons | Accepted in v4/v6 |
| A5D1-007 — v3 physical proof reused producer logic and did not independently render both horizons | P2 | Added separate 30-/100-year destination-date rendering and a 306-cell independent audit | Accepted in v4/v6 |
| A5D1-008 — v3 evidence lacked strict nested schema rejection, deterministic detailed archive, and sufficient verifier checks | P2 | Added strict schema, mutation tests, 340-record archive, and progressively strengthened verification | Accepted with final closure supplement |
| A5D1-009 — v4 omitted Dec 31→Jan 1 pairs from the fitted January transition replay | P1 | Invalidated v4 despite unchanged diagnostic 0/306 full-pass count; v6 adds realized pairs to within-block January counts in the optimized finite vector | Accuracy and science accepted v6 |
| A5D1-010 — v4 verifier authenticated reported flags without reconstructing numerical solves, paths, and aggregates | P2 | Frozen v6 verifier re-solves 34 LPs and recomputes all 306 path decisions and summaries | Accuracy/consistency accepted |
| A5D1-011 — generated report described centered targets as raw moments and under-scoped methods/hold | P2 | Replaced it with the full scientific report, amended provenance, exact methods, limitations, and algorithm-scoped hold | Scientific report recheck accepted |
| A5D1-012 — retained detailed archive lacked required LFS management | P2 | Added a package-specific LFS rule for current/invalidated detailed archives and replay archive | Consistency accepted; pointer gate pending final staging |
| A5D1-013 — partial v5 independently gated a small boundary-only January subset, risking a false hold | P2 | Stopped v5 before matrix closure; v6 gates the aggregate within-block + realized-boundary January probability and leaves boundary-only ratios diagnostic | Scientific review accepted |
| ACC-V6-001 — resource ceilings were not machine-bound by the frozen verifier | P2 | Added post-result `resource-evidence-v1.json` and a closure supplement that numerically checks all four ceilings | Accepted; supplement independently executed and passed |
| ACC-V6-002 — frozen verifier did not rehash every manifest-listed target library/feature before numerical replay | P2 | Added a post-result closure supplement that rehashes 17 canonical/repeat library records and all 17 features | Accepted; 17 + 17 library records and 17 features rehashed |
| ACC-V6-003 — frozen verifier compared reconstructed flags but not every detailed metric/first-failure/top-level field | P3 | Closure supplement compares full finite/dependence/boundary dictionaries and terminal aggregates within a declared tight numeric tolerance | Accepted; 0 structural/numeric mismatches |
| SCI-V6-001 — report attributed a nonexistent combined-path claim to invariant-only H3 | P2 | Marked H3 supported 306/306 and confined complete-contract failure to H2/H4 | Accepted |

## Residual uncertainty

- The development rules are amended and feasibility-only; they are not
  calibrated promotion gates or confirmation evidence.
- One exposed burn-0 library is evaluated. Registered seeds are required
  sensitivity cells, not independent climate replicates.
- The bounded path search cannot establish that no other complete-block
  construction exists.
- Repeat-library evidence proves the retained final bytes match both recorded
  identities; it does not retain two independent 113 MB library copies.

## Lens dispositions

Accuracy/numerical lens: **ACCEPT**
Scientific-validity lens: **ACCEPT**
Consistency/exposure lens: **ACCEPT**

Final verdict: **ACCEPT**
Unresolved P1: 0
Unresolved P2: 0
Unresolved P3: 0
