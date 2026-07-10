# CREDITS.md — Lineage and Attribution Documentation

Status: `EXECUTED-COMPLETE`
Date: 2026-07-09
Evidence mode: documentary — every attribution traced to a named
source; no claims beyond the cited record.
Execution model: single-executor doc package (Claude Code;
documentation is Claude's domain per AGENTS/CLAUDE role split).

## Objective

Author a root-level `CREDITS.md` recording the full credit surface of
the port: the CLIGEN authorship lineage (~4 decades), the numerical
libraries embedded in the Fortran and adopted by the Rust port, the
station/climate data lineage, key publications, and the port's own
execution credits. Refresh the stale README Status section (written at
scaffold time, superseded by the completed faithful-mode port).

## Sources consulted (Ran: fetched/read this session)

- USDA-ARS CLIGEN page (version lineage, contributor history, downloads,
  publication list).
- C. R. Meyer, "General Description of the CLIGEN Model and its
  History" (CLIGENDescription.pdf) — the canonical history notes:
  Nicks/Gander origin, Hall/Scheele recovery, Yu corrections, Meyer
  recode + RNG quality control.
- `reference/cligen532/cligen.f` — the in-source changelog (5.1 →
  5.323) and attribution comments: Richardson's `fouri1`/`fouri2`
  ("Code received 01/21/99 from Clarence Richardson"), the "ACM
  Chi-square code from Anderson Cancer Center in Texas" block, Alfred
  H. Morris Jr. / NSWC headers, Bus & Dekker, Fox-Hall-Schryer
  `I1MACH`, Abramowitz & Stegun, Kottegoda, and the Numerical-Recipes-
  replaced-for-licensing note.
- Srivastava, Flanagan, Frankenberger & Engel 2019 (JSWC 74(4):334-349,
  PDF read) — exact author list + the 2015 database update context.
- github.com/jfrankenberger/cligen5 (hosting/maintenance).
- Repo work-package record: libm-pinned + atanf provenance artifacts,
  golden-fixture manifest (DAYMET/gridMET observed series provenance).

Not verifiable this session (milford.nserl.purdue.edu returns 401):
full author lists of the 2002 Applied Climatology and 2003
precipitation-parameter papers — cited by title "as listed on the ARS
CLIGEN page" without invented author lists. The 2007 authors come from
the ARS-linked filename (Meyer-Renschler-Vining2007.pdf).

## Deliverables

- `CREDITS.md` (root).
- README: Status section updated (faithful-mode port complete); Credits
  linked from Provenance and licensing.

## Exit

Single commit to main.
