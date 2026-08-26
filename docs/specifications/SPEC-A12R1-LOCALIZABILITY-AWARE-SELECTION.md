# SPEC-A12R1-LOCALIZABILITY-AWARE-SELECTION — Feasible Donor Evaluation

Status: revision 2; explicit repair implementation authorized; no default change or confirmation authority

## Purpose

A12R1 corrects the prerequisite exposed by A12: a geographically or
climatologically preferred donor can contain monthly occurrence parameters
that the ordinary production PRISM localizer cannot transform. Revision 2 adds
one operator-authorized, explicit repair profile and retains the feasibility
filter as its comparator. It does not silently repair station parameters or
reinterpret A12's HOLD.

## Explicit repair profile

CLI selection is
`--degenerate-occurrence-repair independent-prism-v1`. Absence of the flag
retains `stochastic_prism_localized_par_v1` byte behavior and fail-closed
semantics. Selection activates profile
`stochastic_prism_localized_par_degenerate_occurrence_independent_v1`, even
when no month ultimately requires repair.

Repair is eligible only when source `P(W/W)` and `P(W/D)` are both exactly
zero, source mean wet-day precipitation is finite and positive, and the PRISM
monthly target is finite and strictly positive. Let `D` be the registered
month length and `m` the source mean wet-day amount. Define the continuous
limit `count* = clamp(target / (2m), 0.1, D-0.25)` and `q*=count*/D`. Snap
`q*` through the same Rust `F6.2` formatter used by the `.par` writer (including
its exact half-grid tie behavior), clamp the parsed result to `[0.01, 0.99]`,
call that encoded-grid value `q`, and set `P(W/W)=P(W/D)=q`. This is the continuous
zero-count limit of the existing halfway frequency adjustment, reconciled to
the fixed-width representation, plus an explicit independent-day persistence
assumption. It is not a PRISM-derived transition estimate. Set the new wet-day
mean to `target/(Dq)` and scale source intensity by 2.0, then use the unchanged
F6.2 render, f32 reparse, and encoded validation path. Snapping before the mean
calculation prevents the serialized probability from changing the intended
PRISM monthly expectation.

Each repaired month emits a stderr warning and a structured receipt containing
method ID, month, original values, PRISM target, continuous limit, snapped
count and `q`, the independence assumption, and encoded mean/PWW/PWD/intensity.
The revision-2 `precipitation_ratio` array contains JSON `null` for a repaired
month because its positive-target/zero-source-total ratio is undefined; the
repair entry gives the explicit reason. Other degenerate
or invalid states remain errors. Receipt and artifact profiles, source `.par`
SHA-256, and executable SHA-256 are mandatory.

## Corpus and firewall

Use the same authenticated 240-point A10 `fit_validation` roster, Daymet
calendar/masks, PRISM runtime, `us-2015@2026.07` archive, descriptor families,
build provenance, and confirmation prohibition frozen by SPEC-A12. A new
published source commit, build receipt, execution identifier, and evidence set
are mandatory; A12 artifacts remain immutable.

The immutable predecessor identities are A12 source commit
`d94f6eab53c9103c797b332ae51aea3a87341bcb` and failure-receipt file SHA-256
`ba103ab7d50fbc510910f980181aec9f3a8c188a05cdbee2b7780f7ce567fa7f`.

## Feasibility predicate

For every site and each of its exact nearest ten candidates, run the complete
production six-row localization algebra, F6.2 rendering, f32 reparse, and
encoded constraint validation against that site's PRISM normals. A candidate
is eligible only if every month succeeds under the ordinary profile. No
flooring, imputation, repair, or fallback outside the nearest ten is allowed in
that comparator arm.

Publish the full 240 × 10 eligibility matrix with source `.par` SHA-256,
failure month/reason where applicable, eligible count, raw-policy selection,
and displacement caused by filtering. If any site has zero eligible candidates,
close on `HOLD-NO-ELIGIBLE-TEN` before quality scoring; pool expansion requires
a separately frozen revision.

## Policies and inference

When every site has at least one eligible donor, compare:

- `closest_localizable_v1`: nearest eligible candidate;
- `cligen_prism_rank_sum_localizable_v1`: the current rank-sum score and tie
  breaks computed over all ten candidates, then the lowest-scoring eligible
  candidate;
- `elevation_prism_reference_localizable_v1`: the A12 elevation/PRISM score
  over all ten candidates, then the lowest-scoring eligible candidate.
- `selected_donor_independent_repair_v1`: retain each raw policy's selected
  donor and apply the explicit repair profile when necessary.

The all-ten ranks remain fixed so filtering cannot improve a candidate's score
by renumbering competitors. Use the exact A12 post-localization descriptors,
site pairing, domain-separated 10,000-replicate bootstrap, family safeguard,
and closest-preferred simplicity rule, under a new domain string and seed.
Report feasibility independently from quality; a supported quality policy is
not evidence that a runtime fallback should be automatic.

## Product boundary

The result may recommend a selector candidate for later runtime design. This
revision implements only the explicit degenerate-occurrence repair knob. It
does not implement user-defined, closest, fallback, or heuristic station modes;
it does not change the current default; and it does not authorize confirmation.

## Provenance and review

Cryptographically bind the exact source commit, locked toolchain build,
executable, registered station archive and extracted tree, PRISM files, all
candidate source `.par` files, calendar objects/shards, preflight, evidence,
decision, and replay. Independent review must reproduce feasibility, selector
choices, metrics, inference, and disposition with no unresolved P0/P1.
