# A8c1 consolidated retirement review

Verdict: `ACCEPT`  
Open P1 findings: 0  
Open P2 findings: 0  
Reviewed: 2026-07-15

## Review scope

This review covers release exposure, removal completeness, faithful and
pre-A8c compatibility, schema consistency, evidence preservation, Git/LFS
reachability, Cargo package exposure, roadmap/catalog state, and the boundary
with the scaffolded A9a package. It does not reassess the A8c scientific stop
or review an A9 model design.

## Findings

No P1 or P2 findings remain.

### Removal correctness

PASS. The 27-file baseline surface is fully accounted for:

- four A8c-only files are absent;
- 22 shared production/specification files equal the pre-A8c comparator blob
  byte-for-byte; and
- the specification registry is the sole custom disposition, returning active
  interfaces to their pre-A8c revisions while retaining a clearly retired
  historical A8c row.

Static token scanning and Cargo metadata/package inspection find no accepted
A8c profile, model, fit, route, extension RNG, station-document-v2 schema, or
runtime/test target. No generic A8c-created seam was retained without a current
consumer.

### Compatibility and faithful behavior

PASS. Exact comparator restoration prevents accidental reinterpretation of
faithful numerical code. `cargo test` passed all executed tests, including
byte-identical `.cli` goldens, end-to-end golden runspecs, revision-1 modern
station parity, provenance/schema checks, observed behavior, and source-vector
tests. No vendored Fortran, legacy fixture, default, precision mapping, or
transcendental implementation changed.

### Historical and scientific-record integrity

PASS. All 148 baseline-preserved files retain their exact sizes and SHA-256
identities. The implementation commit remains an ancestor of current `HEAD`.
The retained-stream archive matches its accepted
`ee50d033c6022f9988fc4734cd892d518866dd7df7a35aba24448399ee47edae`
identity, its Git LFS pointer declares the same object and size, and
`git lfs fsck --objects HEAD` passes. No A7/A8 experiment artifact or A9a scaffold file
was edited.

### Interface and documentation consistency

PASS. Runtime and documentation copies of the provenance and quality schemas
are byte-identical. Current station, generation-profile, provenance, quality,
and runspec specifications no longer describe A8c as accepted. The historical
A8c specification explicitly has no producer or consumer on current `main` and
points to the exact implementation commit. The work-package catalog and
roadmap record A8c1 as complete and leave A9a scaffolded as the next active
package.

### Release and package exposure

PASS. Neither repository release/tag contains A8c; the official sparse crate
index and Cargo search show no published `cligen` crate. `cargo metadata` and
`cargo package --list` expose none of the retired identifiers or files. The
crates.io API's 403 response is recorded but is not relied upon as absence.

### Engineering gates

PASS. Formatting, Clippy, tests, coverage generation, and CRAP gates pass.
Coverage reports 89.71% lines and 80.92% functions. CRAP analyzed 730 functions,
found zero above threshold 30, and reported a maximum of 25.0.

## Residual uncertainty

- The registry conclusion depends on the official sparse index and Cargo
  search because the crates.io API denied the request under its data-access
  policy. Both independent official registry paths agree that no crate exists.
- Git history is the compatibility path for any unknown consumer pinned to an
  untagged `main` commit. The package does not promise source compatibility for
  the unshipped experimental profile.
- A9a may reuse lessons from the A8 evidence, but this review does not approve
  reuse of A8c identifiers, coefficients, thresholds, or runtime structure.

These residuals do not block retirement.

## Conclusion

The package satisfies `EXECUTED-COMPLETE` and returns
`A8C-ROUTED-DAILY-RUNTIME-RETIRED`. A9a execution is now eligible for a
separate operator dispatch; no A9 implementation or candidate is authorized by
this verdict.
