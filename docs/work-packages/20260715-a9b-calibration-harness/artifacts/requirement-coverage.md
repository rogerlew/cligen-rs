# A9b requirement coverage

Status: complete
Specification: `SPEC-A9-RESEARCH-FOUNDATION`, revision 1

## Normative MUST/MUST NOT map

| ID | Specification requirement | Implementation | Executable/static evidence |
|---|---|---|---|
| A9-MUST-001 | Station, class, fit, profile, optimizer, dataset, member, RNG, and output identities must not be inferred from one another. | `artifacts.py`, `candidates.py`, `rng.py`, strict candidate configuration schemas | FX-013 immutable fit/hash mutation; FX-014 domain separation; FX-015 schema-matched validated fit; production-token scan |
| A9-MUST-002 | Logical records in different data roles must be disjoint. | `artifacts.validate_role_manifest_semantics` compares source/version/site/variable/calendar/day-boundary/period keys plus object and logical hashes. | FX-013 role/schema mutations; FX-016 exact identity firewall |
| A9-MUST-003 | Fit, optimize, development-evaluate, and gate-calibrate must reject confirmation paths, object hashes, logical hashes, and station-period keys. | `roles.RoleFirewall`; all four CLI commands invoke it before computation. | FX-016 path, symlink, copy, rename, bytes, object-hash, logical-hash, and normalized-key mutations; two-entry append-only access chain |
| A9-MUST-004 | Candidate plugins must not receive observed targets, thresholds, ranks, strata, or other candidates' output. | Plugins receive only strict class configuration, `ValidatedFit`, candidate-neutral campaign/site/burn/date identities, and the random field. A9b command inputs additionally require `synthetic_only: true`. | FX-003 structural audit; FX-013 unknown-field rejection; FX-015 validated-fit and horizon mutation; static interface-signature review |
| A9-MUST-005 | Occurrence/amount/covariance monthly contributions must reconcile to total mean and variance. | `moments.monthly_moments` and `reconcile_moments`, fixed Simpson quadrature | FX-008 analytic independent/dependent vectors for 28/29/30/31 days and deliberate covariance omission failure |

All five capitalized normative occurrences in the revision-1 specification are
covered. Schema validation is not used as a substitute for the cross-file,
state-transition, RNG, or numerical semantic tests above.

## Handoff implementation units

| Unit | Code | Fixture/golden evidence |
|---|---|---|
| canonical JSON, schema, hashes | `canonical.py`, `artifacts.py` | FX-013; canonicalization golden vector |
| roles and one-shot confirmation | `roles.py` | FX-016; role-firewall mutation artifact |
| immutable fit artifacts | `artifacts.py` | FX-013 and FX-015 |
| two mock candidate protocols | `candidates.py` | FX-001--FX-004, FX-015 |
| deterministic optimizer protocol | `optimizer.py` | FX-019 |
| Philox and exact encoding | `rng.py` | FX-014 golden vectors |
| calendar, nested horizon, context, event | `calendar.py`, `context.py`, `events.py`, `candidates.py` | FX-009--FX-012, FX-015 |
| hard constraints, moments, quadrature | `moments.py`, plugin validators | FX-005--FX-008 |
| objectives, availability, nulls, Pareto, selector | `objectives.py` | FX-017--FX-018 golden vectors |
| append-only attempts, restart, resource/storage | `log.py`, `optimizer.py` | FX-019--FX-020 |
| all registered fixtures | `fixtures.py` | canonical `fixture-results-v1.json`, 20/20 PASS |

## Research-only boundary

No A9 identifier is added to production enums or station schemas. The tool is
outside `crates/`; its mock class IDs remain research values. The source and
fixture manifests record `observed_target_access: false`, and the verifier
rejects production/reference diffs or network-client imports. A9b does not
authorize an observed fit, class ranking, climate claim, or runtime pilot.

