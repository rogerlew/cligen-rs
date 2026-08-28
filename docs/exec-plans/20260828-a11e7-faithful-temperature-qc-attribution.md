# A11E7 Faithful Temperature QC Attribution ExecPlan

Status: executing

## Purpose

Coordinate the source-bound scaffold, 1,280-stream execution, deterministic
replay, and closure. The package and specification retain scientific authority.

## Progress

- [x] Freeze the QC-on/off attribution question and decision semantics.
- [x] Publish prospective execution source.
- [ ] Correct the independently nullable correlation validator exposed by the
      first exact-source attempt and publish a new execution source.
- [ ] Execute and replay the frozen grid.
- [ ] Review, run gates, and close.

## Decisions

- A11E7 is the QC attribution recommended by A11E6S; the temperature overlay
  moves to the following identifier.
- Observed data are target; QC-on faithful is operational control; QC-off is an
  attribution ablation, not an automatic replacement.
- Thirty-two members reduce the eight-member stochastic ambiguity without
  adding a model family or tuning dimension.
- The first attempt exposed a report-only validation defect rather than a
  generation failure: nullable Pearson and Spearman estimators cannot be
  required to share definedness because they operate on different variates
  and have independent finite-result gates. Correct that bounded contract and
  restart from a new exact source commit; do not retain partial evidence.
