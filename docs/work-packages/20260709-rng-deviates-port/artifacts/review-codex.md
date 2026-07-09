# Stage R1 Independent Review — Codex

Reviewer: OpenAI Codex, 2026-07-09.

Evidence mode: Static source/transcription review + Ran targeted and package
gates. Stage R2 remains assigned to Claude Code; this review does not close
the package.

## Outcome

Six findings were accepted and fixed: two High, three Medium, and one Low.
No R1 finding remains open, no tolerance was introduced or widened, and no
reference file was modified.

## Findings

1. **High — `jlt` rejected the source's valid single-storm `ntd` shape.**
   Before review, the Rust function required `ntd` to equal 365 or 366.
   Static evidence: `cligen.f:3064` assigns `ntd=ntd1` for options 4/7 and
   calls `jlt` at line 3088; `jlt` itself only distinguishes `ntd == 366`
   from every other value at lines 1876-1881. Ran evidence also captured
   `ntd=166` in both single-storm `ranset` entries. **Fixed:**
   `calendar.rs:34-60` now treats only 366 as leap while validating the
   selected calendar, and the copied-Fortran fixture contains exact
   `JLT 166 166` evidence (`calendar_vectors.rs:9-37`).

2. **High — `ranset` transcribed the February predicate too narrowly.**
   Before review, Rust selected 29 days only for `ntd == 366`. Static source
   lines 4091-4095 select 29 days whenever `mox == 2` and `ntd != 365`, which
   includes the ordinal values passed by single-storm mode. **Fixed:**
   `rng.rs:104-113,314-316` now preserves the exact predicate; the focused
   source-rule test at `rng.rs:352-362` covers 365, 366, a February ordinal,
   and the captured June ordinal.

3. **Medium — replay evidence omitted first-call common-block writes.**
   The ranset tap asserted seeds, `last_r`, `ell`, `ranary`, and QC state but
   did not independently assert the `vv/v1/v3/v5/v7/fx/v9/v11/z` assignments
   at source lines 4099-4117. **Fixed:** the replay derives the one-draw values
   from each captured entry seed and the already bit-anchored `randn`, then
   asserts all nine common fields at their sole ranset-owned write point
   (`tap_identity.rs:234-242,303-365`). Later external writers remain outside
   ranset replay scope.

4. **Medium — `libm_pinned` licensing/provenance was ambiguous and its
   numeric note became stale when ACM added binary64 `exp`.** The Stage S
   header said “MIT via glibc” while flagging an LGPL-carrier concern, and
   standard §1.3 still said all f64 `exp` stayed on `libm`. **Fixed:** direct
   ARM-upstream attribution, copyright, and SPDX expression now appear at
   `libm_pinned.rs:1-35`; exact commit/file hashes and adjudication are in
   `libm-pinned-provenance.md:1-49`; the complete upstream dual license is
   committed as `arm-optimized-routines-LICENSE.txt`; standard §1.3 records
   the empirically required ACM exception at lines 18-30. No glibc source was
   copied.

5. **Medium — specification and tap evidence described only the Stage S
   state/evidence surface.** The active core spec still called `Cbk7Seeds`
   seed-only and omitted `Cbk4State`, ranset SAVE state, and ACM ENTRY state;
   the tap schema/manifest omitted Stage C provenance and stream semantics.
   **Fixed:** SPEC-GENERATOR-CORE rev 2 lines 15-30 documents every current
   owner; `tap-schema.md:105-140` defines both Stage C streams; and the
   manifest records the copied build, hashes, all 2,584 full calls, committed
   sample policy, and final non-invasiveness run.

6. **Low — `jdt` claimed fail-closed day validation but accepted impossible
   month days.** The source assumes valid caller input, while repository rule
   §1.7 requires malformed new interface inputs to fail closed. **Fixed:**
   `calendar.rs:23-33` derives the month bound from the supplied `nc` table
   and leap selector; direct Fortran vectors now include every month-end, and
   `calendar_vectors.rs:40-44` pins rejection of non-leap February 29.

## Review coverage

- **Transcription fidelity (Static):** read the Rust units against
  `cligen.f:1651-1903`, `1980-2019`, `4002-4700`, and `4705-7165`, including
  `dinvr`/`dzror` continuation labels and every ranset retry/update block.
  Stage S `randn`, `dstn1`, `dstg`, and `ks_tst` had no functional
  transcription finding. Stage C ACM direct vectors cover all public units,
  both inverse-search directions, and all `gratio` accuracy selectors.
- **Precision map (Static + Ran):** audited casts and transcendental sites;
  no REAL*4 faithful value was widened except the source-declared
  `dble()`/DOUBLE PRECISION sites. No standard float method, fast-math flag,
  reassociation, or tolerance comparison was introduced. The ACM `exp`
  decision is direct-vector adjudicated.
- **State translation (Static):** checked `/random/`, `/bk7/`, and `/bk4/`
  ownership, block-data defaults, `DstgState`/`RansetState`, ACM SAVE state,
  ENTRY sharing, and EQUIVALENCE accessors. No global or duplicated state was
  found.
- **Test/evidence alignment (Static + Ran):** verified patch-on-copy hygiene,
  bit-format schemas, committed sample completeness, per-record ranset state
  assertions, direct-vector provenance, and ignored full-stream paths. The
  named `mox=0` hazard is separately characterized and dispositioned in
  `ranset-mox0-characterization.md`.
- **Reference hygiene (Static):** `git diff -- reference/cligen532` is empty;
  the committed Stage C patch targets only the ignored copied build tree.

Final acceptance command results are recorded in `gate-results.md` after the
post-review rerun.
