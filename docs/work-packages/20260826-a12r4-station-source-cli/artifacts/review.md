# A12R4 independent review

Status: FINAL CLOSURE GO

The initial review found three P1 gaps: elevation source/unit/rank provenance,
schema-3 null and method-ID semantics, and exact-source resolution/snapshot
identity. Revision 1 now freezes `.par` feet to metres, elevation-mode-only
nullable fields, five exact method IDs and receipt shapes, exact unique catalog
ID matching, symlink lexical/canonical paths, and one immutable byte snapshot.
It also freezes ordinary-only automatic eligibility independent of repair.

Implementation review initially found two P1 defects: semantically corrupt
station data could be classified as merely unlocalizable, and exact-ID lookup
could truncate a duplicate under catalog drift. Re-review then found incomplete
finite validation for source fields preserved by localization. The implementation
now performs complete `StationDocumentV1` validation plus scientific domain
checks before feasibility classification, resolves exact IDs with an untruncated
bytewise catalog query, and tests corruption in both localized and untouched
fields for automatic and exact sources. Focused tests, format, and strict clippy
passed. Independent disposition: GO with no remaining P0/P1 code findings.

Final closure review independently verified all five method identities, ten
successful release runs, five atomic failures, default/replay identity, dry-site
repair invariance, source commit agreement with `origin/main`, release binary
and LCOV hashes, the runtime-evidence file hash, and terminal roadmap/catalog/
package/ExecPlan consistency. Final disposition: GO with no remaining P0/P1.
