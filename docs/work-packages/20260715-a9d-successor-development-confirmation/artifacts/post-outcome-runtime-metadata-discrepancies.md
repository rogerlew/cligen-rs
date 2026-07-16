# A9d post-outcome runtime metadata discrepancies

Date: 2026-07-15
Access boundary: after development evaluation and its terminal were recorded

Independent closeout inspection found stale inherited contract fields in
`development-runtime-v1.json`, which was derived by adapting the A9c3 runtime
record. The A9d design freeze is the authority for A9d grid, stage caps,
resource caps, and terminals; the runtime record is the authority for the
inherited evaluator mechanics that the design did not override. The canonical
fit and evaluation artifacts are the authority for what executed.

The stale or ambiguous runtime fields are:

- `candidate_fit_rule` says "all eight frozen configurations"; the A9d design
  freeze registers 18 configurations, and `fit-execution-v1.json` records 18
  fresh valid fits.
- the `fit_and_structural` and `short_screen` stage rows each retain an A9c3
  `configuration_limit_per_class` of four; the A9d design freeze registers nine
  per class, and the evaluation records all 18 configurations in the short
  screen.
- `candidate_configuration_source` names the inherited A9c campaign grid rather
  than the overriding A9d design grid.
- `candidate_fit_side_amendment.pooling_and_shrinkage` names the inherited
  A9c 50/150 pooling values; the A9d design and all fit records use 10/25/50.
- `terminals` retains A9c3 names. A9d's design freeze and compact result govern
  the A9d terminal vocabulary.
- `resource_limits` retains the evaluator's broad A9c3 search caps. A9d's
  72-hour campaign, 48-hour development, 24-hour confirmation, 12-GiB memory,
  50-GiB retained, and eight-worker caps govern; execution remained within both
  records.
- the generic top-level `design_freeze_sha256` in the fit and evaluation files
  points to this inherited runtime record (`684897...`), while
  `a9d_design_freeze_sha256` in the evaluation and
  `parent_identities.design_freeze_sha256` in every fit point to the actual A9d
  design (`65b7d6...`). The field names are ambiguous but both content
  identities are retained and checkable.

The canonical runtime file is retained byte-for-byte because the fits and
evaluation hash-bind it. The following precedence therefore closes the record
without rewriting outcome-time evidence:

1. `design-freeze-v1.json` plus `pre-output-fit-amendment.md` govern A9d's
   candidate grid, fit amendment, caps, terminal vocabulary, and confirmation
   boundary.
2. `development-runtime-v1.json` governs inherited evaluator definitions,
   burns, prefix reuse, objective calculations, thresholds, promotion ordering,
   and selector implementation where the A9d design did not override them.
3. `fit-execution-v1.json`, `structural-audit-v1.json`,
   `development-evaluation-v1.json`, and `development-result-v1.json` govern
   executed identities and results.

These are contract-label defects, not executed limits: the configuration
identities, stage results, attempt inventory, and selector inputs establish the
executed 18/4/2 funnel. The discrepancies do not change a score, threshold,
promotion, candidate identity, terminal, or confirmation-access boundary.
Public reporting cites this disclosure whenever it uses overridden fields.
