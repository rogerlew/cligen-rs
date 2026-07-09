# Codex Review — Decomposition Ratification

Reviewer: Codex (via MCP, read-only, 2026-07-09;
thread 019f48b2-4a6b-7823-9a13-b6c395cfb342)
Disposition: all three findings ACCEPTED and applied same-day
(extraction script fixed + artifacts regenerated; doc corrected to the
388 figure; `header` assigned to `par/`; block-data ownership note
added; preamble row relabeled).

Verbatim review follows.

---

**Confirmations**

- CONFIRMED: the four dead-code verdicts survive independent search. `nrmd` has only comments/declaration evidence (cligen.f:426, cligen.f:2123); `chitst`, `alph`, and `r5mon` only have commented call sites next to live replacements (cligen.f:1731, cligen.f:3118, cligen.f:877).

- CONFIRMED: no `EXTERNAL` or actual-argument procedure passing falsifies those verdicts. The live `EXTERNAL` declarations name ACM routines, not `nrmd/chitst/alph/r5mon` (cligen.f:4804, cligen.f:4807, cligen.f:6203).

- CONFIRMED: five common-block rows spot-checked against live includes: `cbk1.inc` (cligen.f:473, 1108, 2028, 2687, 3003); `ccl1.inc` (1542, 3024, 3652); `csumr.inc` (1553, 3228); `cinterp.inc` (519, 1051, 1162, 2737, 3031); `crandom3.inc` (515, 1047, 1172, 1684, 4041, 4464).

- CONFIRMED: call-graph spot checks match source: `program→sta_dat` 856, `program→r5monb` 878, `wxr_gen→day_gen` 3788, `day_gen→alphb` 3119, `alphb→dstg` 3882, `cdfchi→dstinv` 4892 with `ENTRY dstinv` 5316, and `dinvr→dstzr` 5293 with `ENTRY dstzr` 5623.

- REFUTED: the "381 inside QC/ACM cluster" precision claim. A non-comment source scan confirms 391 matching lines in `cligen.f`, but 388 are inside §2.7's `ks_tst`/`conflm`/`confls`/ACM range, not 381. See Finding 1.

- CONFIRMED: no other `double precision`/`real*8`/`dble(`/D-literal sites appear in the named generation-path units. Positive sites outside ACM/QC are `dstg`'s locals (cligen.f:1696) and the QC accumulator declarations/initializers (crandom3.inc:15, crandom3.inc:16, cligen.f:1073, cligen.f:1074); `confls` performs the ACM widening (cligen.f:4659, 4662, 4663).

**Findings**

1. **Medium — Precision census prose and artifact are incomplete/inconsistent.** Evidence: `cligen.f` has 391 non-comment precision-site lines, but §2.7's live QC/ACM range contains 388, not 381; the only `cligen.f` sites outside that range are 1073, 1074, and 1696. Also, `precision-sites.md` is generated only from `cligen.f` (extract.py:15, 118) and omits live include declarations crandom3.inc:15-16. Correction needed: change the 381 claim to 388 for the §2.7 cluster, and extend the precision artifact/script to include live `.inc` precision declarations, clearly separating `cligen.f` line-sites from include-file state declarations.

2. **Medium — §3 module map omits live `header` and does not assign `block data` initialization ownership.** Evidence: `sta_dat` calls `header(version)` at cligen.f:2343, and `header` is a live subroutine at 2153-2184, but §3 lists `par/` as only `sta_dat/sta_name/sta_parms` and `output/` as `clmout` summaries. `block data` initializes common state at 1037-1090. Correction needed: add `header` to a module ported no later than `par` step 3, or move/port that dependency explicitly; add a §3 line assigning `block data` initializers to the owning state constructors.

3. **Low — `unit-extraction.md` contains a bogus `(main)` program row for the header preamble.** Evidence: `extract.py` unconditionally inserts `(main)` for lines 1 through the first unit start minus one (extract.py:52-55), but the actual `program cligen` starts at cligen.f:382, and lines 1-381 are comments. Correction needed: label that span as `preamble` or omit it from the unit inventory; do not count it as a program unit.
