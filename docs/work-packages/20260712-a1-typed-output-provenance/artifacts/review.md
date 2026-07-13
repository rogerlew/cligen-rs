# A1 Adversarial Review and Disposition

Review: delegated read-only code/API audit plus independent schema adversary
Final verdict: **ACCEPT**
Date: 2026-07-12

## P1/P2 disposition

No P1 or P2 finding remained and no blocking disposition was required. The
review independently found no faithful-generator, typed projection,
provenance, path/publication, or schema regression. The final code audit
confirmed that f32/f64 widths, expression order, RNG/state sequencing, row
order, header timing, early-stop behavior, and run-end rendering remain
unchanged in faithful mode.

Schema review used strict duplicate-key parsing and a fully offline Draft
2020-12 registry. Seven changed/published schemas passed `check_schema`,
versioned/latest reference resolution passed, 23 negative mutations were
rejected, and the current artifact corpus validated. A clean isolated replay
of the 10-case A1 golden/Parquet test also passed.

## P3 disposition

| Finding | Disposition |
|---|---|
| **A1-P3-001 — transitive canonical-formatter pin.** `serde_json` is exact-pinned, while its active `zmij` backend is exact only through `Cargo.lock`. | Accepted. Workspace output is fixed by the lockfile and literal canonical-hash vectors. Reassess a direct exact pin or owned canonical writer before changing provenance schema/canonicalization. |
| **A1-P3-002 — publicly mutable DTO validation breadth.** Runtime provenance validation is slightly looser than JSON Schema for a control-character edge, and quality serialization validates nested provenance but not every mutable public envelope field. | Accepted for the 0.1.0 surface. Trusted run/post-hoc constructors emit conforming artifacts and both Rust/schema gates cover them. Add complete DTO validation or construction-restricted fields before API stabilization; A5a must account for this when it revises the quality envelope. |
| **A1-P3-003 — lock operational edges.** Distinct hardlink names can acquire different locks for one inode during concurrent overwrite; a crash can leave a lock file. | Partly remediated and otherwise accepted. Sequential hardlink replacement is tested safe, and the spec now documents stale-lock recovery after confirming no active writer. Inode-aware cross-name locking is deferred until that operator concurrency case enters scope. |
| **A1-P3-004 — test isolation and foreign-writer coverage.** Fixed `target/` paths make separate concurrent Cargo invocations contend, and no focused fixture proves acceptance of an older/foreign logical-schema-v1 writer. | Accepted as test hardening. The lock correctly prevents corruption and all normal single-invocation gates pass. Use temp-unique package paths and add a foreign/older writer fixture in a later reader-compatibility package. |

The separate final code audit also noted the intentional Rust API changes.
They are accepted for the unreleased 0.1.0 interface: A1 introduces its typed
and provenance surfaces together, and no legacy `.cli` or runspec format is
silently reinterpreted.

## Specific review rulings

- Storm text remains supported but deprecated and is not admitted to typed
  output v1. A source-calendar requested storm date is not asserted equal to
  the emitted Gregorian date because the faithful source can normalize a
  requested non-Gregorian leap day (for example, year 100 February 29) to the
  next emitted date.
- JSON Schema is structural authority; Rust validation remains normative for
  canonical-hash recomputation, cross-axis equality, inclusive day spans, and
  calendar/mode semantics.
- Publication is intentionally per artifact. The canonical lock and staged
  companions define safe cooperating-writer behavior, but the four-file
  bundle is not misrepresented as one filesystem transaction.
- Path-only station selection truthfully leaves collection release identity
  unreported instead of inferring it from cache layout.

## Conclusion

The package meets its exit criteria: independent readers can identify and
validate the versioned typed artifact, every text artifact is cryptographically
bound to mandatory provenance, faithful `.cli` bytes are unchanged, and all
final repository and complexity gates pass. The four P3 items do not change
A1 behavior or block closure.
