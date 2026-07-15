# A7a Frozen Claim-Evidence Ledger

Status: frozen before new A7a-derived output
Date: 2026-07-14
Report ID: `a7a-daily-precipitation-structure`
Source commit: `d27a008e91a4853044aed5207d02a3aeb631ac8c`

## Hypothesis crosswalk

| Hypothesis | Prospective A7a claim | Authority before outcome |
|---|---|---|
| H1 | Amended by analysis amendment 003: the frozen breadth rule either measures a daily-structure priority or closes the A7 line; unavailable cells are conservatively non-material. | E01, E02 |
| H2 | Amended by analysis amendment 003: core daily families can be ranked by one fixed lexicographic rule; unavailable cells cannot improve rank. | E01 |
| H3 | Amended by analysis amendment 003: daily-family distance may co-localize with dispersion distance using available components; no causal claim is permitted. | E01 |
| H4 | Amended by analysis amendment 003: the two QC arms may differ in observed distance; unavailable pairs are counted separately. | E01, E03 |

## Evidence IDs

- **E01 — A7a measurement contract.** Exact metrics, null, thresholds,
  ranking, rounding, and terminal rule.
- **E02 — A7a canonical analysis.** To be produced after freeze; authoritative
  for stream counts, overlap checks, station cells, QC comparison, and
  propagation diagnostics.
- **E03 — A5a retained baseline.** Hash-pinned 544 quality reports, exact
  station parameters, manifests, and fixed burn/horizon membership.
- **E04 — A5a observed corpus.** Hash-pinned Daymet/GHCN raw sources,
  fixed-period logical records, target document, and third-party notice.
- **E05 — A7a terminal decision.** To be produced after freeze by applying E01
  to E02.
- **E06 — A7a consolidated review.** To be produced after report synthesis;
  authoritative for independent recomputation and open-finding counts.
- **E07 — A7a gate record.** To be produced at closure; authoritative for
  executed commands and terminal package status.

## External reference corpus

- **R01 — Richardson (1981).** Foundational first-order daily
  precipitation/temperature/radiation weather-generator structure. DOI
  `10.1029/WR017i001p00182`.
- **R02 — Katz and Parlange (1998).** Precipitation overdispersion as a
  stochastic-model diagnostic. DOI
  `10.1175/1520-0442(1998)011<0591:OPISMO>2.0.CO;2`.
- **R03 — Thornton et al. (2022).** Daymet V4 R1 dataset identity and scope.
  DOI `10.3334/ORNLDAAC/2129`.
- **R04 — Menne et al. (2012).** GHCN-Daily dataset identity and quality
  assurance. DOI `10.1175/JTECH-D-11-00103.1`.

Literature supplies context and dataset identity only. It does not supply A7a
numeric outcomes or override the repository's faithful source authority.
Copyrighted local reading copies, if any, are not public report links.

## Permitted result claims

- exact stream, station, horizon, QC-arm, burn, overlap-check, and material-gap
  counts from E02;
- the terminal decision and qualifying families from E05;
- ranked family breadth and severity under E01's rule;
- noncausal QC and propagation diagnostics; and
- limitations bounded to the exposed stations, sources, periods, rendered
  R1mm precipitation, and deterministic burn spread.

## Prohibited claim upgrades

- IID uncertainty, population significance, or confidence-interval language;
- causal transmission from a daily-family miss to monthly/annual dispersion;
- proof that first-order Markov structure alone caused a residual;
- independent confirmation by GHCN, which shares observing-system lineage and
  is incomplete at several stations;
- general rejection of CLIGEN, all station climates, or all weather-generator
  families; and
- authorization or expected success of any particular A7b/A7c mechanism.
