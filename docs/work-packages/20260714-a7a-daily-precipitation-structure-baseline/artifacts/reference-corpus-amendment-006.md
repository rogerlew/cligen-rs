# A7a Reference-Corpus Amendment 006

Status: accepted during internal consistency/public-safety review
Date: 2026-07-14
Prior reference record: `claim-evidence-ledger.md`

## Trigger

The read-only reference audit found that the frozen phase-1 ledger used R04
for the Menne et al. GHCN-Daily overview article while the first internal
report draft reassigned R04 to the GHCN dataset. The draft also introduced the
official Daymet guide without recording the reference-corpus expansion.

The audit additionally found that the GHCN provider requests both the dataset
citation and the overview article, and that the official Daymet calendar guide
is needed to support the project's calendar-transform limitation.

## Bounded amendment

The frozen ledger is not rewritten. Its R01--R04 identities remain stable:

- R01 — Richardson (1981), DOI `10.1029/WR017i001p00182`;
- R02 — Katz and Parlange (1998), DOI
  `10.1175/1520-0442(1998)011<0591:OPISMO>2.0.CO;2`;
- R03 — Thornton et al. (2022), Daymet V4 R1 dataset, DOI
  `10.3334/ORNLDAAC/2129`; and
- R04 — Menne et al. (2012), GHCN-Daily overview article, DOI
  `10.1175/JTECH-D-11-00103.1`.

The public report corpus adds:

- R05 — Menne et al. (2012), GHCN-Daily Version 3 dataset, DOI
  `10.7289/V5D21VHZ`, used for the archived eight-station U.S. Cooperative
  Network subset identity; and
- R06 — ORNL DAAC, Daymet Daily V4 R1 guide, no DOI,
  `https://daac.ornl.gov/DAYMET/guides/Daymet_Daily_V4R1.html`, used for the
  native ordinal-calendar limitation.

This correction changes citation identity and completeness only. It changes
no A7a metric, comparison, rank, qualifier, hypothesis outcome, or terminal
decision.
