# Kickoff Prompt — Golden Fixture Harness

Paste-ready dispatch prompt for the executing agent. Authored by Claude
Code, 2026-07-09.

---

Execute the work package at
`docs/work-packages/20260709-golden-fixture-harness/package.md` in the
cligen-rs repository.

Read first, in this order:

1. `AGENTS.md` — conventions, hard rules, gates (including the CRAP ≤ 30
   gate; the differ you build is the first code it measures).
2. `docs/decisions/0001-source-code-authority-port.md` — the posture; §4
   (fixture provenance) is binding on everything you produce.
3. `docs/work-packages/20260709-golden-fixture-harness/package.md` — the
   package. Note the Phase A warning: the vendored
   `reference/cligen532/makefile` optimized target is disqualified for
   golden generation (`-fno-protect-parens` + fast-math family). Define a
   deterministic fixture-build profile instead and record every flag.
4. `fixtures/README.md` — the four-station cohort, what each case
   exercises, and why the vendored production `wepp.cli` files are
   cross-references, not goldens.
5. `docs/port/fortran-decomposition.md` §1 and §5 — the QC-coupled
   trajectory behavior (fixture seeds must exercise the QC regeneration
   path) and the hazards your differ must localize.
6. `docs/standards/rust-scientific-coding-standard.md` — before writing
   the differ.

Execution constraints beyond the package text:

- `reference/cligen532/` is read-only. If interior taps are chosen in
  Phase A, they live as a recorded patch file under this package's
  `artifacts/`, applied to a build tree outside `reference/` — never to
  the vendored source.
- Reproduce each fixture case's invocation from its vendored
  `cligen_wepp.log` / `wepp.inp` before adding seed variants; record the
  exact reproduced command lines in the fixture manifest.
- The `.prn` end-of-record mechanics are already adjudicated in
  `fixtures/README.md` — the hard-truncated variant you craft pins the
  post-5.323 clean-EOF partial-year behavior; do not "fix" or pad it.
- Every claim in your artifacts follows the evidence discipline: Ran vs
  Static, commands recorded, no "verified" without execution.
- Close honestly: `EXECUTED-COMPLETE` only if every gate in the package
  passes; otherwise `EXECUTED-HOLD-<reason>` with the exact blocker and
  first follow-on action.

Deliverables are the package's artifact list; update the work-package
catalog row and `docs/ROADMAP.md` item 1 on close.
