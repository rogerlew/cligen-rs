# A12R3 independent review

Status: prospective GO; closure review pending

Independent reviewer must inspect the frozen protocol before source commit and
later reproduce the terminal evidence, decision, replay, and provenance chains.

## Prospective review

The independent review found three P1 blockers: narrow build attribution,
site-by-site quality scoring before the full feasibility pass completed, and
missing post-use authentication of isolated inputs. The scaffold now requires
exact clean HEAD/origin identity for the build and binds the broader source and
production dependency surface; uses distinct complete feasibility and scoring
passes; rechecks the copied PRISM tree, extracted station tree, archive, and
binary before scoring; and records every selected station/source `.par` SHA-256
identity directly in the execution receipt. Targeted disposition, safeguard,
and source-surface tests were added. Re-review confirmed the PRISM distribution
authority is also source-bound and returned GO with no unresolved P0/P1 finding.

The first staged science attempt then exposed two sparse wet-month descriptor
cells before publishing evidence. Independent amendment review required and
confirmed an exact full-corpus descriptor-eligibility replay before scoring,
the exact two-cell diagnostic roster, and 12 finite months for all non-wet-day
families. Final prospective amendment disposition: GO, no unresolved P0/P1.

## First closure review

Status: NO-GO; implementation correction pending re-execution

Independent recomputation matched all 240 sites, 2,400 candidate cells, two
sparse cells, 720 selected station/source identities and metrics, both
bootstrap comparisons, and `CLOSEST_PREFERRED`. It found 582 published
site-policy distances had been overwritten through shared mutable station
dictionaries. The flawed execution and replay are preserved under `attempt1-`
artifact names. The corrected evaluator snapshots each selected arm at the
site boundary and has a regression test for later mutation.
