# A12 independent review

Reviewer: delegated subagent `a11_scaffold_review`

## Prospective review — 2026-08-26

Disposition: **GO for source publication**. No unresolved P0, P1, or
publication-blocking P2 findings.

The initial HOLD identified raw rather than localized occurrence scoring,
mutable-cache provenance, f64/f32 selector drift, incomplete calendar
preflight, incomplete paired-family inference, an unbound build, a failing
CRAP gate, insufficient focused tests, and a public API break. Closure review
verified their correction: all 240 sites use and agree with the exact Rust
selector receipt; the current policy uses the Rust-localized file; the other
policies perform the complete six-row render/reparse constraints; registered
station bytes and private copies of the exact binary and PRISM runtime are
verified before and after use; the preflight is complete and published before
scoring; the inference and domain-separated bootstrap are frozen; the build
receipt binds source hashes, Cargo.lock, toolchain, command, and binary; the
public two-argument API remains intact; and the selector orchestration is below
the CRAP threshold.

Reviewer-reproduced gates: evaluator tests 16/16 PASS; manifest validation PASS
at canonical SHA-256
`1e18770b05dd1a7ab11896308807c685806f1367c812b148e8f1a879cab37250`;
`git diff --check` PASS; regenerated llvm-cov PASS; CRAP PASS with 0/830
functions above 30. No observed execution or confirmation target series was
accessed during prospective review.

## Completed failure-evidence review — 2026-08-26

Disposition: **GO for `EXECUTED-HOLD-UNLOCALIZABLE-DONOR` closure**. No
unresolved P0/P1; no material P2 remains.

The reviewer independently reproduced the build/source/binary identities,
240-site and 40-per-regime calendar preflight, PRISM file-set identity,
station archive/tree/catalog identities, failure-receipt self-hash, sorted site
index 49, all-three-policy winner and scores, donor hash, June source values,
June PRISM normals, and production fail-closed error. No selector-quality
evidence or decision artifact exists, so scientific replay is not applicable.
Confirmation access remained false.

A12R1 was reviewed as the least-complex non-retroactive successor. It must
retain the immutable A12 source/failure identities and prospectively evaluate
full-localization eligibility before policy quality.
