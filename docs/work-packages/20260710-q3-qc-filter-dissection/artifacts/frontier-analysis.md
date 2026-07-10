# Q3 Frontier Analysis — Conditioning vs Variability

Date: 2026-07-10
Evidence mode: **Ran** — 102 matrix runs (`run-matrix.py`,
`runs.json`), analysis strictly over the pre-registered surfaces
(`analyze-matrix.py` → `matrix-analysis.json`), observed reference
`observed/observed-stats.json` (Daymet v4, 46 yr × 17 stations).
Supplemental generation-only timing (`timing-no-sidecar.json`,
`output.quality: false`, best-of-3, 100 yr).

## Verdicts against the pre-registered bounds

| Bound | 30 yr | 100 yr |
|---|---|---|
| **B1 — convergence buy** (off/faithful median group A error ≥ 1.2 = material) | **1.25 — MATERIAL.** Conditioning buys real convergence at the design horizon (median QC-target error 8.0% vs 10.0%). | **1.12 — NOT material.** The buy fades: 5.5% vs 6.2%. |
| **B2 — variability cost** (SD ratio < 0.9 or CV farther from observed on ≥ 2/3) | **MATERIAL on both prongs**: median SD_faithful/SD_off = 0.81; faithful CV farther from observed on 14/17. | **MATERIAL on both prongs**: SD ratio 0.89; farther on 15/17. |
| **B3 — early-decade prediction** (majority at 100 yr) | — | **CONFIRMED, narrowly: 10/17.** The cumulative-QC "bites hardest early" effect is present but not uniform across regimes. |
| **B4 — counterfactual price** | would-reject 52.2% median | would-reject 52.7% median; **range 50.5–54.4% across every regime class** |
| **B5 — performance** | faithful 0.146 s / off 0.100 s median (with sidecar) | faithful 0.468 s / off 0.311 s; generation-only: **faithful/off = 1.70× median**, corpus total 33.2 s → 3.8 s (**8.8×** — retry-storm stations dominate) |

## The headline findings

1. **The conditioner rejects half of everything, everywhere.** The
   would-have-been-rejected rate is 50.5–54.4% across arid, humid,
   cold, and monsoonal stations alike — the filter is not an
   occasional guardrail; it is a persistent resampling layer that
   discards every second batch regardless of climate regime.
2. **What that buys is a 30-year effect.** At the agricultural design
   horizon the convergence gain is material (B1 = 1.25, exactly the
   Baffaut-motivated purpose). At 100 years the gain is 1.12 — below
   the materiality bound; time does what the filter was doing.
3. **What it costs is real at both horizons and points the wrong way
   vs observed climate.** Conditioned interannual dispersion is
   clipped ~19% (30 yr) / ~11% (100 yr), and the unconditioned runs
   are **closer to the Daymet observed CV on 15/17 stations**.
   Concretely (100 yr annual-total CV): New Meadows observed 0.202 —
   faithful 0.183, off 0.209; Death Valley observed 0.606 — faithful
   0.405, off 0.469 (everything underdisperses in the driest cells,
   but conditioning makes it worse); Mobile AL observed 0.164 —
   faithful 0.179, off 0.176 (humid cells barely care).
4. **The conditioner is the performance pathology.** Yuma's 100-year
   faithful run spent 2,538,348 rejected batch attempts and hit the
   10,000-redo give-up cap 299 times (9.5 s vs 0.2 s unconditioned);
   corpus-wide, faithful burned 7.7M rejected attempts and 908 cap
   give-ups at 100 yr. Turning the filter off is a 1.70× median /
   8.8× corpus-total generation speedup with zero RNG changes.
5. **Cap give-ups mean "faithful" is not uniformly conditioned
   anyway.** 908 give-up events at 100 yr are batches that failed QC
   and shipped regardless — heaviest exactly in the arid/monsoonal
   cells WEPP rangeland work cares about.

## Sensitivities on the record

- The observed CV comparison inherits Daymet's grid-vs-point and
  1980–2025-period character; the pre-registered no-detrend choice
  inflates observed CV slightly. Both effects are shared by every
  config, and the GHCN-Daily secondary (8/17 stations) does not
  change the direction on any of its stations.
- B3's 10/17 is a bare majority: the early-decade mechanism is
  visible but regime-dependent, weaker than the ADR-0002 prose
  predicted.
