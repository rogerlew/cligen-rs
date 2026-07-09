# Stage R2 Final Review — Claude Code

Reviewer: Claude Code (Stage S executor; R2 closes the package).
Date: 2026-07-09.
Evidence mode: Ran (all gates re-executed in this review session) +
Static (targeted source-vs-port reads).

## Verdict: CLOSE — `EXECUTED-COMPLETE`

## Gates re-run independently (Ran, this session)

| Gate | Result |
|---|---|
| `cargo fmt --check` | exit 0 |
| `cargo clippy --all-targets -- -D warnings` | exit 0 (verified directly) |
| `cargo test` | 8 suites ok |
| Full-stream release taps (`--ignored`) | 2 tests ok — Stage S streams (randn=19,784,955, dstn1=26,402,148, dstg=30,268) + the ranset full replay, 13.97 s |
| `cargo llvm-cov` | exit 0 |
| `cargo crap --fail-above` | 98 functions analyzed, none exceed 30, exit 0 |
| `reference/cligen532/` hygiene | `git diff 93567d1..d5c5b9f -- reference/` empty |

## Targeted verifications (Static, this session)

- **Spine integrity**: `deviates.rs` and `crandom3.rs` have zero diff
  across Codex's commits; `rng.rs` deletions are module-header doc
  lines only (header now covers `randn` + `ranset`), `randn`'s body
  untouched.
- **`ranset` February predicate** (R1 finding 2): port
  `mox == 2 && ntd != 365 → 29` verified as the exact De Morgan of
  `cligen.f:4091-4095` (`mox.ne.2 .or. ntd.eq.365 → dim(mox)`).
- **ENTRY translation** (`dinvr`/`dstinv`, `acm.rs`): the
  reverse-communication ASSIGN/GOTO machinery is an explicit
  `InvrStage` enum on `DinvrState` with `dstinv` as a separate
  initializer function sharing the host state — precisely the coding
  standard §5 prescription; `dzror`'s state rides alongside. Covered by
  the 919-vector direct fixture in both search directions.
- **`ranset(mox=0)` characterization**: reachability closed (single
  live call site immediately after `mox = mo`; all 2,584 captured
  entries in 1..=12), the common-layout aliasing worked out to the word,
  and the fail-closed decision correctly reasoned — replicating the
  under-run would require inventing storage-layout semantics outside
  the source authority.
- **License provenance** (R1 finding 4): `libm_pinned` now attributes
  the ARM optimized-routines upstream at a pinned commit with per-file
  SHA-256s; upstream grant is `MIT OR Apache-2.0 WITH LLVM-exception`
  (compatible; full text committed). The Stage S "via glibc" ambiguity
  is resolved — glibc was the reference *runtime*, not a code source.
  The ACM-driven f64 `exp_pinned` addition followed §1.3's
  empirical-adjudication rule as designed.

## R1 disposition review

All six findings verified fixed with evidence; the two High findings
(single-storm `ntd` ordinals in `jlt`/`ranset`) were genuine
transcription errors of exactly the class this staged process exists to
catch — the reviewer read the source predicate, not the port's
assumption. No tolerance was introduced anywhere; every fix tightened
fidelity or evidence.

## Package outcome

ROADMAP item 3 is complete: the generator core (RNG, deviates, QC, ACM,
calendar, ranset) is ported with bit-identity against ~46.2M captured
Fortran values plus 2,584 stateful ranset replays and 919 direct
vectors. Patterns, spec, and tap infrastructure are established for
items 4–8.
