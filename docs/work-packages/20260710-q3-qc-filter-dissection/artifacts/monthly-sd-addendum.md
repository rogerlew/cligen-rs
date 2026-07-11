# Addendum — Monthly Interannual Dispersion vs Observed

Date: 2026-07-10 (post-close addendum; operator-directed)
Evidence mode: **Ran** — observed monthly SDs recomputed from the
original hash-verified raw downloads (`observed/augment-monthly-sd.py`;
17/17 Daymet + 8/8 GHCN raws matched their pinned SHA-256s; no
re-acquisition); generated monthly SDs read from the existing 102
matrix sidecars; analysis in `analyze-monthly-sd.py` →
`monthly-sd-analysis.json`.

## Why this exists

The ratified pre-registration's *Measurements* section promised
monthly-total interannual dispersion "compared to the observed-
reference dispersion," but the original acquisition computed only
annual observed statistics, so that comparison was never made — a
record gap the operator identified on 2026-07-10 (missed by R1).
This addendum closes it. It is **descriptive**: no pre-registered
bound attaches to it, B2 (annual, material at both horizons) is
unaffected, and the single-burn caveat (R1 finding 5) carries over.

## Results

**Direction confirmed at monthly grain, but weaker than annual.**
Station-months (17 stations × 12 months = 204) where the
unconditioned run's monthly SD is closer to the Daymet observed SD:

| Horizon | off closer | with ≥2 mm noise floor | GHCN secondary |
|---|---|---|---|
| 30 yr | 115/204 (56%) | 115/202 | 60/96 (63%) |
| 100 yr | 122/204 (60%) | 121/202 | 54/96 (56%) |

Compare the annual result (off closer on 15/17 stations, 88%): the
monthly signal points the same way but is diluted — expected, since
monthly SDs carry ~12× the sampling noise and the `.par` *does*
encode the within-year seasonal structure that dominates at this
grain.

**Both configurations under-disperse against observed climate in
nearly every month.** The corpus-median generated/observed monthly-SD
ratio is below 1 in 12/12 months for faithful and 9/12 (30 yr) –
11/12 (100 yr) months for off. Conditioning deepens a deficit that
exists regardless of the knob — the strongest evidence yet that the
missing interannual variance is **structural** (the ADR-0002 layer-3
gap assigned to A5), not a conditioning artifact alone.

**The clipping is broad, not seasonal.** The faithful/off monthly-SD
ratio dips deepest in May (0.71 at 30 yr, 0.85 at 100 yr), March, and
November, but no single season concentrates the effect; the
conditioner clips across the calendar.

**fast_batch_v0 adds nothing at this grain either**: off is closer to
observed than v0 on ~56–57% of station-months — consistent with the
Q4 quality-equivalence finding.

## Consequence for the standing rulings

None changed. ADR-0003's evidence base gains a month-level
corroboration (weaker but same-signed); the A5 augmentation case
gains its sharpest motivating number: *even unconditioned,
source-shaped generation under-disperses observed monthly totals in
9–11 of 12 months.*
