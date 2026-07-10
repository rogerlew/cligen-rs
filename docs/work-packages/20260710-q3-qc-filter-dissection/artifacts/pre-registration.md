# Q3 Dissection Pre-Registration

Status: **RATIFIED** — operator, 2026-07-10 ("yes to ratifying.
scaffold and execute"): corpus and observed-reference design
confirmed as proposed. Numeric bounds (§Bounds) were pinned by the
executor under the same direction **before any dissection run**; no
matrix output existed when they were fixed. Amendments after this
point are findings, not edits.
Date: 2026-07-10 (ratified)
Authors: Claude Code (proposal); corpus derivation Ran from the
synced us-2015 collection (operator direction: use the 2015 database).

## Question under test

ADR-0002's cumulative-QC prediction: the Meyer conditioner
(`qc_filter: faithful`) purchases 30-year convergence-to-par by
clipping interannual variability, biting hardest in early decades.
The dissection quantifies, per horizon, what conditioning costs
(group B interannual dispersion vs observed climate) and buys
(group A convergence-to-par), plus the group-P counterfactual
rejection rate.

## Matrix

{`qc_filter: faithful`, `qc_filter: off`} × {30, 100 years} ×
{17-station corpus} = **68 runs**, `generation_profile:
faithful_5_32_3`, `rng.burn: 0`, `interpolation: none`,
`begin_year: 1`, continuous mode. Identity: every run's
`.cli.quality.json` is the measurement; `.cli` bytes archived by
hash only.

## Corpus (ratified)

Drawn from `us-2015` (operator direction), all stations with 40-year
fitting records; regime statistics derived from the pars themselves
(stationary-Markov expected monthly precipitation, day-weighted mean
temperature, July–September precipitation fraction). Selection
favored recognizable stations, geographic spread inside each class,
and Daymet coverage (CONUS/AK; the humid class deliberately avoids
the otherwise-wettest Pacific-Island stations, which Daymet does not
cover).

| Class | Station | par | Annual P (mm) | JAS frac | T mean (°C) | DJF Tmin (°C) |
|---|---|---|---:|---:|---:|---:|
| arid | Death Valley CA | ca042319 | 61 | 0.21 | 25.0 | 5.2 |
| arid | Yuma Test Stn AZ | az029654 | 91 | 0.33 | 23.6 | 7.1 |
| arid | Wendover AP UT (cold Great Basin) | ut429382 | 99 | 0.23 | 11.3 | −6.0 |
| arid | Daggett AP CA (Mojave) | ca042257 | 102 | 0.25 | 20.1 | 3.2 |
| monsoonal | Douglas B D AP AZ | az022664 | 317 | 0.58 | 17.1 | −0.8 |
| monsoonal | Tombstone AZ | az028619 | 339 | 0.56 | 17.8 | 2.8 |
| monsoonal | Jornada Exp Range NM (USDA LTER) | nm294426 | 254 | 0.56 | 14.6 | −5.5 |
| monsoonal | El Paso WB AP TX | tx412797 | 237 | 0.55 | 18.1 | 0.7 |
| humid | Mobile WB Airport AL | al015478 | 1688 | 0.30 | 19.6 | 5.5 |
| humid | Saucier Exp Forest MS (USFS) | ms227840 | 1731 | 0.30 | 19.8 | 5.9 |
| humid | Pensacola AP FL | fl086997 | 1657 | 0.32 | 20.1 | 6.8 |
| humid | Hialeah FL (subtropical) | fl083909 | 1673 | 0.39 | 24.8 | 15.8 |
| cold | Climax CO (alpine, 3,400 m) | co051660 | 592 | 0.27 | −0.4 | −16.7 |
| cold | Lake Yellowstone WY | wy485345 | 487 | 0.23 | 0.2 | −17.7 |
| cold | Int Falls WP AP MN (boreal) | mn214026 | 619 | 0.39 | 3.1 | −19.1 |
| cold | McGrath WSO AP AK (subarctic) | ak505769 | 448 | 0.43 | −2.7 | −25.1 |
| fixture | New Meadows RS ID (golden cross-link) | id106388 | 498 | 0.12 | 5.1 | −12.5 |

Classification notes on the record: a pure JAS-fraction rule
mislabels arctic summer-maximum stations (Barrow) as monsoonal — the
monsoonal class therefore also requires T mean ≥ 12 °C (the NAM
signature); the CONUS-cold class excludes Mount Washington (summit
observatory vs 1-km grid mismatch would poison the observed
comparison).

## Observed reference (ratified)

Group B's authority is observed climate, external to the report
(ADR-0002 ruling 1; SPEC-QUALITY-REPORT). The `.par` does not encode
interannual variation, so it must be acquired:

- **Primary: Daymet v4 (single-pixel API)** at each corpus station's
  catalog coordinates — daily prcp/tmax/tmin, 1980 through the latest
  complete year (~45 years), uniform and gap-free across
  CONUS/AK/HI/PR. Acquisition is python campaign tooling (committed,
  with download date, Daymet version, and raw-CSV SHA-256 pinned);
  derived per-station yearly statistics are committed as artifacts.
- **Secondary (sensitivity): GHCN-Daily** for the same stations
  (COOP mapping `idNNNNNN` → `USC00NNNNNN` where available) — the
  actual fitting lineage, subject to a completeness screen
  (≥ 30 years with ≥ 95% daily completeness). Point-vs-grid
  disagreement between the two references is reported, not
  adjudicated away.

Pinned conventions (drafted to neutralize known Daymet biases):

1. **Wet-day threshold: ≥ 1.0 mm** (ETCCDI R1mm) applied identically
   to the observed series and to generated `.cli` rows wherever
   wet-day counts or spell statistics are compared — interpolated
   products inflate trace-precipitation day counts (drizzle effect),
   and the generator's own 0.01-inch floor sits just below 1 mm.
   Group A/B report values (which use the `.cli` > 0 convention) are
   not redefined; the ≥ 1 mm join is computed in the adjudication
   from the same reports plus the archived `.cli` hashes.
2. **Daily extremes are directional evidence only** from Daymet
   (interpolation damps maxima); the GHCN-Daily secondary carries the
   extreme-value comparison where its record passes the screen.
3. **Daymet's 365-day calendar** (Dec 31 dropped in leap years) is
   accepted as-is for annual and monthly statistics.
4. **No detrending** of the 1980–present reference; a
   detrended-variance sensitivity column is reported alongside so the
   trend contribution to observed SD is visible rather than silently
   included or removed.

## Measurements and decision surfaces

- Convergence (what conditioning buys): group A absolute/relative
  errors at 30 vs 100 years, faithful vs off, per class.
- Variability (what conditioning costs): group B interannual SD/CV
  (annual totals, wet-day counts, monthly totals) per decade block,
  compared to the observed-reference dispersion; the early-decade
  prediction is confirmed iff faithful's decade-0 group-B dispersion
  is systematically below both `off` and observed.
- Price tag: group P counterfactual would-have-been-rejected rate
  (off runs) and retry/cap costs (faithful runs); wall-clock
  re-baseline of faithful vs off on this corpus.
- **No promotion decision here**: outputs are the frontier
  quantification + ADR-0003 exposure adjudication (is `qc_filter`
  user-facing; opt-in vs opt-out per use class).

## Bounds (pinned pre-run, 2026-07-10)

"Material" is defined before the data exists:

- **B1 — convergence buy.** Conditioning materially buys convergence
  at a horizon iff the corpus-median group A |rel_err| for the
  QC-targeted precipitation parameters (wet-day mean and SD) under
  `off` is ≥ 1.2× the value under `faithful`.
- **B2 — variability cost.** Conditioning materially costs
  variability at a horizon iff the corpus-median ratio
  SD_faithful/SD_off of annual precipitation totals is < 0.9, or
  faithful's annual-total CV is farther from the observed-reference
  CV than off's on ≥ 2/3 of the corpus.
- **B3 — early-decade prediction.** Confirmed iff the decade-0
  SD_faithful/SD_off ratio is below the whole-run ratio for a
  majority of the corpus at the 100-year horizon.
- **B4 — counterfactual price.** Descriptive (no bound): the
  would-have-been-rejected batch rate under `off`, and retry/cap
  costs under `faithful`.
- **B5 — performance.** Descriptive: corpus wall-clock, faithful vs
  off (the Q4 fast-batch case is judged against the off baseline).
- **Q4 promotion gate (pre-pinned here for the follow-on
  comparison).** A fast-batch promotion is recommendable only if, on
  this corpus at both horizons, the batch line's (a) group A
  corpus-median |rel_err| for precipitation wet-day mean/SD/skew and
  wet-day fraction is ≤ 1.1× the `qc_filter: off` baseline, (b)
  group B annual-total SD ratio to `off` lies in [0.9, 1.15], and
  (c) measured refill-path performance gain over `off` is ≥ 1.5× —
  all three, else retire-with-record per the ROADMAP row.
