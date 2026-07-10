# Output Writer, Orchestration, and the `cligen` CLI

Status: `STAGE-S-COMPLETE` — spine executed and gated; 12/12 golden
`.cli` byte parity from typed run inputs; format adjudication closed
(57.3M fields, 0 mismatches). Awaiting Codex Stage C dispatch
(`artifacts/kickoff-codex.md`).
Date: 2026-07-09
Evidence mode: Stage S **executional** (`artifacts/gate-results.md`)
Execution model: staged, two executors (the item-3..7 pattern) —
Claude Code writes the design-setting spine; Codex completes and runs
gates; each reviews the other; Claude closes with Stage R2.

## Objective

Close the faithful-mode port — ROADMAP item 8: the `.cli` output
surface (`wxr_gen` headers, formats 642/778/644/500/520/555/648 +
the day_gen daily-row format 2000, including the header argv echo per
SPEC-RUNSPEC rev 2 §Header echo and the run-end blank line), the
`wxr_gen` year-loop orchestration (leap rules incl. the quirky
iopt-4/7 `nt` test, per-year ccl1 zeroing, the `opt_calc` seam —
characterized: a no-op for `iopt ≥ 4`), the observed `initial_year`
intake (`usr_opt:3572-3574` → `PrnReader::initial_year` per
SPEC-OBSERVED-INPUT rev 2), and the `cligen` binary consuming
SPEC-RUNSPEC `inp.yaml` documents.

**The named hazard**: Fortran FORMAT output rounding. Every formatted
REAL field goes through a `fortran_format` module adjudicated
empirically against the reference runtime (probe-driven sweeps per
descriptor — the §1.3 discipline applied to output), before the
byte-parity gate ever runs.

## Acceptance (whole package)

- **The endgame gate**: `cligen run` on the 12 golden runspecs
  (SPEC-RUNSPEC §Golden equivalence, `command_echo` pinned verbatim)
  reproduces the 12 golden `.cli` files **byte-identically** — the
  new interface proves the old bytes.
- `fortran_format` descriptor sweeps: bit-exact text equality against
  reference-runtime formatted output for every descriptor on the
  `.cli` surface (F5.1, F5.2, F4.2, F6.2, F4.0, F4.1, F9.2, F7.5,
  F8.5, I-widths), across swept value ranges + every value in the
  goldens.
- `cligen validate` fail-closed vectors per SPEC-RUNSPEC §Field
  invariants; schema/orchestration vectors for the
  fixture-unreachable branches (design_storm, linear/mmp
  interpolation, overwrite, canonical echo rendering), labeled.

## Stages

### Stage S — Spine (Claude Code)
1. FORMAT-rounding adjudication: Fortran probe (copied tree, additive
   or standalone driver) sweeping each descriptor; `fortran_format.rs`
   matched bit-for-bit on text.
2. `output.rs`: header + daily-row writers over `DailyRow`/station
   state. `wxr_gen` year-loop port (+ `opt_calc` iopt≥4 no-op with
   typed deferrals for 1-3) and library-level run orchestration.
   `PrnReader::initial_year`.
3. Library byte-parity: all 12 goldens reproduced via typed run
   config (pre-CLI), asserted in a `#[ignore]`-able but fast gate.
4. Handoff + kickoff.

### Stage C — Completion + gates (Codex)
The serde runspec (schema structs, JSON Schema, validation per
SPEC-RUNSPEC §Field invariants), the `cligen` binary
(`run`/`validate`, path resolution as the `(document, base_dir)`
boundary, canonical echo renderer, overwrite policy), the 12 golden
runspec fixtures, validate vectors, all gates.

### Stage R1 — Cross-review (Codex)
Format fidelity (rounding adjudication evidence, header field
provenance), orchestration fidelity (year plan vs wxr_gen:3758-3800,
stop protocol consumption), SPEC-RUNSPEC conformance, test/evidence
alignment.

### Stage R2 — Final sanity review (Claude Code)
Gates re-run; targeted reads (the header writer vs formats
642/778/644; one descriptor adjudication re-verified); R1
disposition; close or bounce — and with it, the faithful-mode port.

## Execution & dispatch

Both executors on **`main`**; start from current `origin/main`, push
to `main`. No side branches.

## Scope exclusions

`iopt` 1-3 surfaces (opt_calc branches, clmout, CREAMS unit 8) —
typed deferrals, ratified excluded per SPEC-RUNSPEC. `.cli.parquet`
(A1/SPEC-CLI-PARQUET). PyO3 (A6).

## Authority

`cligen.f`: `wxr_gen` 3589-3816 (headers + year loop), day_gen format
2000 (3055-3056), `opt_calc` 3196-3324, `usr_opt` 3560-3575 (ioyr),
main 963-973 (run-end blank line + close); SPEC-RUNSPEC rev 2;
SPEC-OBSERVED-INPUT rev 2; the 12 goldens as the byte oracle.

## Gates

Stage S: descriptor adjudication + library byte parity before Stage C.
Stage C: full suite + the golden-runspec CLI gate. Reviews
dispositioned; close by R2.

## Exit criteria

`EXECUTED-COMPLETE`: 12/12 golden byte parity through `cligen run`;
descriptor sweeps clean; validate vectors green; both reviews
dispositioned. Holds: a FORMAT rounding behavior that cannot be
pinned platform-independently (stop and characterize — §1.3
escalation).

## Artifacts

- `artifacts/format-rounding-adjudication.md`
- `artifacts/orchestration-characterization.md` (folded into this
  file's Objective/Authority if small)
- `artifacts/spine-handoff.md`, `artifacts/kickoff-codex.md`
- `artifacts/review-codex.md`, `artifacts/final-review-claude.md`
- `artifacts/gate-results.md`
