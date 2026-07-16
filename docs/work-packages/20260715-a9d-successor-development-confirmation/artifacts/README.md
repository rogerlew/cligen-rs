# A9d artifacts

The prospective design and dispatch files predate corrected A9d candidate
output. Generated JSON uses canonical sorted-key serialization. Large raw and
normalized confirmation objects live under `artifacts/large/` and are tracked
with Git LFS when the confirmation stage is reached.

The package has one lifecycle: development, optional candidate seal, optional
sealed confirmation acquisition, one confirmation consumption, and one final
terminal. No intermediate work-package identifier is used.

Development completed at `HOLD-A9D-NO-SELECTABLE-CANDIDATE`. The package
therefore contains 18 fresh fits, the staged development evaluation, compact
terminal, accepted public report, and review, but correctly contains no
candidate freeze, confirmation target-series object, consumed-confirmation
manifest, confirmation fit, or confirmation evaluation. The 18 fit-detail JSON
files use Git LFS; the compact fits and machine summaries remain regular Git
content.
