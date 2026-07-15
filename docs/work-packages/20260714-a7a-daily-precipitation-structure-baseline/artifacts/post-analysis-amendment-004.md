# A7a Post-Analysis Amendment 004

Status: accepted after canonical JSON output and before report drafting
Date: 2026-07-14
Prior freeze: `pre-analysis-freeze-v4.json`

## Trigger

The v4-frozen analyzer completed the scientific matrix and wrote canonical
analysis and decision JSON, then failed while rendering `findings.md` because
the `str.format` call supplied `qualifying` both explicitly and through the
ranking row.

Pre-correction output identities:

- `a7a-analysis-v1.json`:
  `425ce817f0167d3c65df57b8fa6f77d333c94a7fa59bfa7eef771322f99366a0`
- `a7a-decision-v1.json`:
  `4f82ab9b61942bced8ef546018a02e561e443df515cf8a1ba4eeeaab3ab38b15`

The decision was `DAILY-PRECIPITATION-GAP-MEASURED`, with
`spell_structure` and `higher_order_occurrence` qualifying. These outcomes
were accessed before this correction.

## Bounded correction

Rename only the renderer's explicit keyword from `qualifying` to
`qualifying_text`. No JSON calculation, contract, input, metric, null,
threshold, ranking, or decision code changes.

Acceptance requires a complete corrected rerun to reproduce both JSON hashes
above byte-for-byte and produce the Markdown findings. A successor
post-analysis freeze binds the corrected analyzer, verifier, amendment, and all
three output identities.

