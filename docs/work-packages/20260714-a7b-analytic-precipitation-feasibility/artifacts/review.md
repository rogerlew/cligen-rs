# A7b consolidated internal review

Status: `ACCEPTED-WITH-SCOPE-CORRECTION`
Date: 2026-07-14
Canonical analysis SHA-256:
`f460055a7978932747ed0bb969d89917c00067af7500f3d0fd833d7af1321d3b`
Canonical decision SHA-256:
`263a0e6788afcc7a49b07be9879ddabbc58adbe3188a73145c2f06b861a778a8`

## Review method and coverage

The calculation lens used a separately authored verifier to check the frozen
source and parent-input identities, source ancestry, unchanged production
crates, 17 stations, 68 amount fits, 136 occurrence fits, 408 candidate-month
cells, and 34 station-level likelihood records. For every feasible cell it
independently solved the stationary distribution, reconstructed finite-month
endpoint and uninterrupted-wet probabilities, recomputed the baseline and
candidate wet-count variance, repeated the 96-point Gauss--Legendre and
20-point Gauss--Hermite amount quadrature, and checked dispersion, tail,
variance-retention, and monthly-budget invariants. It recomputed summaries,
qualification, ranking, and the terminal, then reproduced analysis, decision,
and findings artifacts byte-for-byte in a temporary directory.

The scientific-validity lens checked candidate state meaning, stationary wet-
fraction recentering, legacy first-order/independent-amount targets, variance
reallocation rather than addition, fixed RNG ownership, fit identifiability,
selection restraint, and the no-generator-output interpretation boundary. It
also compared the two occurrence transition systems under state permutation,
which exposed the parameterization equivalence recorded separately.

The consistency lens checked the A7a authorization terminal, A5a station and
Daymet identities, 1980--2025 no-leap window, exact f32-widened legacy rows,
development-station membership, output hashes, roadmap/catalog closure, public
paths, and ordinary Git treatment of the diffable 1.1 MB canonical JSON.

## Findings and dispositions

| ID | Severity | Finding and consequence | Disposition | Recheck |
|---|---|---|---|---|
| A7B-PRE-001 | P2 | The first invocation queried parent key `terminal`, while A7a stores `terminal_decision`. It stopped before loading candidate data. | Amendment 001 changed only that key lookup, recorded the original/amended hashes and absence of outcome artifacts, and re-froze the analyzer identity. | Freeze, parent identity, and reproduction checks pass; no fit, threshold, numeric, or decision rule changed. |
| A7B-SV-001 | P2 | The second-order and registered two-phase semi-Markov kernels are isomorphic four-state processes, so A7b did not test two independent model classes. | The equivalence note proves the mapping and narrows the conclusion to one unique mechanism in two parameterizations. The conservative stop remains because both have the same 12 infeasible cells and neither qualifies. | Transition-permutation and paired-cell checks reproduce; A7c remains unauthorized. |
| A7B-SV-002 | P3 | The stored likelihood tie-break compares 16,788 O2 days with 16,789 semi-Markov days per station because their fit histories start one day apart. | The ranking is not interpreted: neither candidate qualified, so the tie-break selected nothing. A future comparison must align support. | Qualification and terminal are unchanged when ranking is ignored. |
| A7B-SV-003 | P3 | The arid development failure could be made to disappear only by changing the frozen exposure/tail bounds, pooling data, or replacing Death Valley after outcome access. | No rescue was attempted. The 36/36 prospective rule is applied as written. | Five Death Valley failures remain explicit in canonical cells and the roadmap. |

## Result and interpretation

Both parameterizations meet the corpus floor with 192/204 feasible cells but
miss the mandatory development surface at 31/36. Death Valley April and
December exceed the maximum tail-log-error threshold. Death Valley JJA has 14
adjacent wet pairs and 14 WW/W2+ exposures, below the frozen minimum of 25;
June, July, and August therefore fail identifiability. All cold and wet
development cells are feasible.

The terminal `STOP-PRECIPITATION-LINE` closes this registered campaign and
does not claim that every possible precipitation generator is infeasible.
A7b generated no candidate climate, changed no production or public interface,
and authorizes neither A7c nor A7d.

## Residual uncertainty

- Daymet grid-cell precipitation at the registered 1 mm wet threshold is the
  sole fit source; no GHCN sensitivity was part of analytic feasibility.
- Seasonal shapes are applied to monthly legacy targets. Stationarity is
  certified for each monthly kernel in isolation, not for month-boundary
  transients; no integrated pilot was authorized to evaluate those transients.
- The log-quantile spline and Gaussian copula are one bounded amount family;
  rejection here does not compare alternative positive marginals, regional
  pooling, or longer spell-age structures.
- In-sample likelihood was only a registered deterministic tie-break, not
  confirmation evidence, and is not interpreted after the equivalence finding.

Final verdict: **ACCEPT WITH SCOPE CORRECTION**

Open P1: 0  
Open P2: 0
