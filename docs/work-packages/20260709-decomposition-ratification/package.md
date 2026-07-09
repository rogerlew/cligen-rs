# Decomposition Ratification

Status: `EXECUTED-COMPLETE`
Date: 2026-07-09
Evidence mode: Static + Ran (mechanical extraction script executed;
targeted source reads; close gates run).
Executor: Claude Code (operator-directed); independent review by Codex —
6 confirmations (1 corrected a census figure), 3 findings, all accepted
and applied (`artifacts/review-codex.md`).

Outcome: `docs/port/fortran-decomposition.md` ratified at rev 3 —
50-unit inventory with per-unit includes/callees, complete common-block
ownership table, live call-graph spine (ENTRY edges included), full
precision census (391 sites in `cligen.f`; 388 in the QC/ACM cluster;
generation-path islands = `dstg` locals + `g_dsum`/`g_ssum`
accumulators), complete aliasing census (two sites), and four ratified
dead units (`nrmd`, `chitst`, `alph`, `r5mon` — ~330 lines out of port
scope, confirmed against EXTERNAL/procedure-argument mechanisms).

## Objective

Take `docs/port/fortran-decomposition.md` from reviewed-first-pass to
ratified: complete the unit inventory with per-unit common-block usage and
a call graph, enumerate every double-precision site (the full precision
map), confirm or refute the dead-code candidates, and re-verify the module
boundaries and port order against the measured call graph. ROADMAP item 2;
the RNG/deviates port (item 3) builds on this.

## Scope

Included:

- Mechanical extraction over `reference/cligen532/cligen.f`: unit
  boundaries, per-unit `include` usage, per-unit callees (subroutine calls
  and function references).
- Common-block ownership map: for each live `.inc`, the including units
  and the block's variables; aliasing sites enumerated.
- Precision-map audit: every `double precision`, `real*8`, `dble(`, and
  `D`-exponent literal site, by owning unit.
- Dead-code adjudication: `nrmd`, `chitst`, and any unit unreachable from
  the live call graph (including whether `alph`/`r5mon` originals are
  reachable now that the live path uses the Yu variants).
- Role verification for every unit still carrying a name-inferred
  description.
- Rewrite of the decomposition doc to its ratified revision; module map
  and port order corrected as the evidence requires.

Excluded:

- Any Rust port code; any `reference/` modification; tap design (RNG
  package); spec authoring beyond what the doc rewrite itself needs.

## Plan

1. Mechanical extraction (script over the source; committed as artifacts).
2. Targeted reads for role verification and aliasing enumeration
   (delegated read-only agents where efficient; conclusions re-verified).
3. Doc rewrite to ratified revision.
4. Codex independent review (read-only); findings dispositioned.
5. Gates, catalog/roadmap updates, close.

## Gates

- `cargo fmt --check`; `cargo clippy --all-targets -- -D warnings`;
  `cargo test` (unchanged code — regression only).
- Every inventory row carries source-line evidence; no `unread` markers
  remain on load-bearing units.
- Dead-code verdicts state their call-graph evidence.
- Codex review findings dispositioned before close.

## Exit criteria

`EXECUTED-COMPLETE`: decomposition doc ratified (rev 3) with complete
common-block map, precision map, call graph, dead-code dispositions;
review dispositioned. Hold: a structural discovery that invalidates the
module map (name it and stop rather than papering over).

## Artifacts

- `artifacts/unit-extraction.md` (mechanical inventory: units, includes,
  callees)
- `artifacts/precision-sites.md`
- `artifacts/deadcode-adjudication.md`
- `artifacts/review-codex.md`
- `artifacts/gate-results.md`
