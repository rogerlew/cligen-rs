# R1 Dispositions — Claude Code (changelog-history section)

Date: 2026-07-10
Evidence mode: every HIGH/MEDIUM claim re-verified against
`cligen.f` before acceptance (Ran: header reads at lines 253-266,
297-369). All seven findings **ACCEPTED**.

| # | Sev | Disposition | Applied fix |
|---|---|---|---|
| 1 | HIGH | **ACCEPTED — my chronology was backwards.** The QC feedback loop and the 50% cumulative thresholds date to 2000 (the 11/11/99 release "does not include the RNG-QC code"); Meyer himself inserted the 10,000-retry escape in 5.105 (04/2001, Yuma/Wupatki); 5.220 added χ² to an *existing* QC and fixed Meyer's own retry mechanism. My "conditioning as last resort after the 2003 search" and "inherited cap" claims were wrong, as was the asserted analytical→structural→parameter ordering (source order: guard 5.200 → structural 5.212 → analytical 5.213). | Section rewritten: QC-first chronology; 5.105 escape correctly attributed (with the newly surfaced reseeding-rejected detail — "changing the random seed k8(4) from 31 to 41 … not the solution pursued"); reading 1 recast as "the QC was permanent; everything around it evolved"; ordering claim dropped. |
| 2 | HIGH | **ACCEPTED.** Reading 2 overstated a bias argument as a theorem plus a uniqueness result, and understated the paper's own engagement with the circularity objection and the history notes' outliers-beyond-expected-percentage nuance. | Reading 2 rewritten as `[analysis]`: rejection rate at a 50% level cannot by itself diagnose generator defect; the evidence was partly a property of the yardstick; QC was the intervention *selected*, not the only one possible; RANDN's genuine defects stand on independent grounds (Layer 1). |
| 3 | MEDIUM | **ACCEPTED in part per the reviewer's own split.** "Outside every question he was asked" contradicted Layer 3's Johnson et al. year-to-year-variance complaint. | Reading 3 narrowed to "no entry contemplates a mechanism for it," with the Layer 3 cross-reference added; Q3 characterization retained (reviewer confirmed it substantively correct). |
| 4 | MEDIUM | **ACCEPTED.** I conflated the 2004 K-S D-value calibration with the 2000-era `thresh`/`thres2` CI thresholds. | 5.2255 bullet now states the 50% level predates it (2000 design) and 5.2255 extended it to the new test. |
| 5 | MEDIUM | **ACCEPTED — pre-existing Layer 2 error exposed.** The escape hatch was attributed to "v5.2251" (no such entry); source says 5.105, bug-fixed 5.220. | Layer 2 corrected in place. |
| 6 | LOW | **ACCEPTED.** The subsection mixed source, read, analysis, and measured evidence under one `[source]` tag. | Heading retagged; each reading now carries its own tag (`[source]`, `[analysis]`, `[source + measured]`). |
| 7 | LOW | **ACCEPTED.** I silently corrected the source's "interatively" typo inside quotation marks. | Now quoted verbatim with `[sic]`. |

Net: the fossils and most entry-level facts survived review; the
narrative arc did not — the corrected story (conditioning first,
refinement after) is more interesting than the one I wrote, and the
5.105 reseeding-rejected detail surfaced during verification is now
in the record.
