# A9c development comparison handoff

Status: freeze-ready; A9c remains unscaffolded and unauthorized
Required predecessor terminal: `HARNESS-READY-A9C`

## Objective

Implement and fit the two A9 candidate probability laws on authorized
coefficient-fit evidence, compare them on development evidence across all six
climate regimes, calibrate candidate-blind statistical gates, and freeze at
most one candidate for a later one-shot A9d confirmation. A9c is still climate-
generator research. It does not add a production Rust profile or inspect the
18-site confirmation targets.

## Exact predecessor inputs

A9c must bind byte hashes from, rather than paraphrase from memory:

- the A9a specification, model-family envelope, objective registry, role/data
  plan, exposure manifest, and metadata-only confirmation roster recorded in
  A9b's `predecessor-manifest-v1.json`;
- A9b's `source-manifest-v1.json`, including all research tool and dependency
  versions;
- all seven files in A9b's `artifacts/generated/`, especially recovery,
  Philox/canonical/numerical goldens, firewall mutations, command evidence,
  and the byte-identical replay;
- `requirement-coverage.md`, `review.md`, and `gate-results.md`; and
- the dispatch commit on which this A9b package is eventually committed.

A mismatch is a predecessor-integrity hold. A9c may fix a harness defect only
through a prospectively versioned amendment before candidate comparison output
is inspected; it may not silently regenerate A9b goldens or tolerances.

## Evidence acquisition boundary

Before acquiring any series, A9c must freeze exact metadata selections and
logical-record rules for:

1. Daymet V4 R1 1980--2009 coefficient-fit objects;
2. a development set covering hot-arid, arid-boundary, monsoonal-transition,
   non-monsoonal semi-arid, humid, and cold strata;
3. a separately selected USCRN event-development set;
4. a candidate-blind gate-calibration set or synthetic same-model/null corpus;
   and
5. the complete exposure union, including all A5--A8 evidence.

The sets must be disjoint by path, bytes, object hash, logical hash, normalized
station/period/source key, and station where the frozen plan requires it. A9c
must not acquire or read the A9a 18-site USCRN 2010--2025 confirmation series.
The confirmation roster remains `metadata_only`; no replacement, preview,
summary, or quality query against target years is permitted.

## Candidate implementations

A9c replaces the A9b mocks with research candidate plugins, not production
enums:

- `alternating_renewal_marked_v1` retains observable alternating wet/dry
  semi-Markov spell state, nongeometric seasonal duration laws, wet-amount
  body/tail/memory, joint event marks, and no hidden regime;
- `latent_regime_marked_v1` retains hidden semi-Markov states, strictly
  interior wet probability and joint marked emissions in every state, and
  observed spells that may cross state boundaries.

Both must fit occurrence/spells, wet amount, event descriptors, and declared
daily context jointly. Both use the frozen `wet0` and `r1mm` semantics,
hierarchical station-within-stratum-within-global pooling, no runtime climate
classifier, no runtime fallback, no year-level state, no realized-month
repair, and no horizon-dependent parameter. A9c must rerun cross-fit recovery,
factorization review, and degenerate-intersection tests on the actual
implementations. Structural collapse returns `MODEL-CLASS-EQUIVALENCE` and no
ranking.

## Required execution order

1. Verify A9a/A9b hashes and rerun the complete synthetic harness.
2. Freeze and hash role manifests, station metadata, source URLs/versions,
   calendar/unit/QC/normalization rules, pooling groups, optimizer bounds,
   resource stages, fit/member/simulation identities, and amendment policy.
3. Acquire only authorized fit/development/calibration objects and append every
   access record; validate source completeness without touching confirmation.
4. Implement each real candidate, fit-artifact producer, hard constraints,
   monthly analytic/quadrature reconciliation, and all class-specific tests.
5. Generate 500 paired same-model/null replicates per objective family and
   horizon before candidate ranking; freeze numeric thresholds and hash them.
6. Execute analytic/support, short screening, full development, and eight-burn
   Pareto replay under A9a's exact evaluation/resource ceilings. Retain every
   infeasible, incomplete, failed, dominated, and complete attempt.
7. Publish the complete 31-objective vector, station/stratum/horizon
   availability and uncertainty, Pareto frontier, and the frozen lexicographic
   selection calculation.
8. Review leakage, source independence, model independence, identifiability,
   numerical replay, monthly reconciliation, arid applicability, monsoonal
   behavior, winter proxies, storm descriptors, and compound context.

Candidate access cannot influence null thresholds, station roles, metrics,
normalization, support floors, resource limits, or the selection rule.

## Selection and freeze boundary

Use `a9_lexicographic_pareto_v1` exactly:

1. reject infeasible, incomplete, or mandatory-stratum-ineligible fits;
2. reject any familywise material degradation in a mandatory family, stratum,
   or horizon;
3. maximize the worst regime-by-mandatory-family standardized improvement;
4. maximize materially improved families;
5. minimize median normalized distance;
6. minimize effective fitted parameter count; and
7. break an exact tie by candidate-class ID.

A selected candidate is an A9d research freeze, not a runtime profile. The
freeze must contain exact source/normalized hashes, candidate source and schema
hashes, fit recipe and artifacts, gates, objective registry, parameters and
members, optimizer evidence, eight development burns, twelve newly derived
confirmation burns, calendar/context/event semantics, selection bytes, and
the A9d terminal rule. No A9d target is read while building it.

## Resource and storage bounds

Retain A9a's ceilings: at most two classes; 4,096 analytic proposals per
class; 256 short-screen configurations; 64 full-development configurations;
eight Pareto replays; eight workers; 12 GiB aggregate RSS; 24 hours per stage;
72 hours per campaign; and 50 GiB retained. One byte-identical infrastructure
retry is permitted. Evidence at or above 10 MiB uses Git LFS. Exhaustion is
`evaluation_incomplete`, never a favorable score or silent prune.

## Required public artifacts

- exact role/source/station/access manifests and exposure union;
- candidate source/config/fit schemas and implementation manifests;
- immutable fit artifacts and fit-ineligible/failed inventories;
- calibrated-null thresholds with all 500-replicate identities;
- complete hash-chained optimizer and resource/restart evidence;
- 31-objective station/stratum/horizon vectors, uncertainty, availability,
  Pareto frontier, and selection trace;
- structural cross-fit/non-isomorphism evidence;
- candidate freeze or named hold;
- report authored under the repository scientific report standard;
- consolidated review with zero open P1/P2 findings; and
- repository/package gate results.

## Terminals

- `CANDIDATE-FROZEN-READY-A9D` — exactly one candidate and complete one-shot
  confirmation freeze are ready for a separately dispatched A9d;
- `HOLD-A9C-DATA-ROLE` — required observed roles cannot be materialized without
  overlap, source failure, or confirmation exposure;
- `HOLD-A9C-MODEL-CLASS-EQUIVALENCE` — implementations are structurally
  isomorphic or enter the excluded degenerate intersection;
- `HOLD-A9C-FIT-APPLICABILITY` — a class cannot fit mandatory strata under the
  frozen pooling and exposure rules;
- `HOLD-A9C-MONTHLY-RECONCILIATION` — analytic/quadrature budgets fail;
- `HOLD-A9C-GATE-CALIBRATION` — candidate-blind thresholds, availability, or
  baseline-zero rules cannot be frozen;
- `HOLD-A9C-NO-SELECTABLE-CANDIDATE` — the frozen rule rejects both classes;
  or
- `HOLD-A9C-RESOURCE-BOUND` — complete evidence cannot be produced under the
  prospective ceiling.

A9d, A9e, production promotion, and downstream integration remain
unauthorized until their respective predecessor terminal and operator
dispatch.

