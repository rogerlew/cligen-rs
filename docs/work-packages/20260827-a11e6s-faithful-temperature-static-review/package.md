# A11E6S — Faithful Temperature Static Review

Status: `EXECUTED-COMPLETE — DESIGN_CONSISTENT_UNDERDISPERSION_EXPECTED`

Date: 2026-08-27

Evidence mode: static source-authority review plus authenticated prior evidence

Starting branch and push target: current `origin/main`, push `main`

## Objective

Determine whether A11E6's faithful annual-temperature underdispersion is best
explained by a cligen-rs implementation defect, the source design, or the
comparison/aggregation path.

## Authority

- ADR-0001 source-code authority
- vendored `reference/cligen532/cligen.f` and `crandom3.inc`
- Rust faithful temperature, RNG/QC, parameter, mode, and output paths
- completed bit-identity port evidence
- ADR-0002, Q3 QC dissection, and A11E6 authenticated evidence

## Scope

Included: static equation and state trace, Fortran/Rust correspondence,
precision and test evidence, design-level variance implications, A11E6 scorer
audit, competing explanations, confidence grading, and recommended ablation.

Excluded: new generation, parameter changes, generator implementation,
confirmation, promotion, and a numerical attribution claim not supported by
the static evidence.

## Gates

Exact source inventory, line-local source trace, distinction between verified
fact and inference, existing identity evidence, comparison-path audit, review
without unresolved P0/P1, standard Cargo gates, `git diff --check`, and link
validation. No production function changes occur, so coverage/CRAP is not
triggered.

## Outcome

The review found no evidence of a Rust implementation defect. The generated
temperature and `RANSET` paths reproduce the Fortran source shape and are
covered by bit-identical interior and full-output evidence. A11E6's parser and
annual aggregation use the intended daily Tmax/Tmin fields and canonical
observed weighting.

Underdispersion is expected from the source model. Temperature is generated
from fixed calendar-month daily means and daily standard deviations. Tmax and
Tmin are coupled to preserve daily marginal moments, but there is no annual
temperature state, interannual parameter variation, or cross-month climate
factor. Averaging largely daily-scale noise into monthly and annual means
therefore removes variance that observed climate carries through persistent
and year-scale processes.

The faithful QC conditioner deepens that structural limitation. `RANSET`
tracks cumulative standard-normal sums, squared sums, and distribution bins
separately by parameter and calendar month, rejecting new monthly batches at a
50% threshold until the cumulative sequence looks typical. For temperature
columns this creates feedback against sustained monthly anomalies and hence
against low-frequency and annual variability. The cumulative rather than
per-batch design mitigates but does not remove this effect.

Static review cannot quantify the split between missing annual state and QC
conditioning. The next bounded package should therefore run the already
implemented `qc_filter: faithful` versus `qc_filter: off` ablation on the exact
A11E6 temperature corpus. Any deficit remaining with QC off is the
source-shaped fixed-parameter structural component; the on/off difference is
the conditioner's net contribution on this corpus.
