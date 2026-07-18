# Amendment 006 — exclude masked Daymet rows

Status: prospective before run 7

Run 6 (`cad91ec`, Slurm `1013772`) completed environment reconstruction and
the offline faithful-Rust build, then settled `FAILED (1)` after 190 seconds
at the finite-training gate. Local inspection of the exact accepted corpus
identified the cause: A10M1 intentionally inserts null February 29 rows for
Daymet's no-leap source calendar. The hard-coded offset-zero 730-day window
crossed that masked row, and NumPy preserved it as NaN. No optimizer update or
checkpoint occurred.

Do not impute the missing row or add an unplanned input channel. Select the
first deterministic 732-row span in the same frozen `candidate_fit` object for
which `source_observed` is true and all seven source fields are finite. Use its
first two overlapping 730-day batches. Assert finiteness before device transfer
and add an authenticated `missingness_excluded` gate plus the selected offset
to the training record. This follows A10M1's rule that masked calendar rows do
not enter fitting.

The all-exit cleanup introduced by amendment 005 ran. Normal collection again
refused the unsanitized Python traceback's private path. Before marker-validated
recovery cleanup, `evidence.json` was 156 bytes at SHA-256
`0a90dd82704a9fca36285656324df639b57bde9cc32c0725a716533c7864edae`,
stderr was 6,492 bytes at SHA-256
`4ba2e3c318b67937d3cc6886444495d029d1986b02666aa10b31c12784f6fed7`,
the three unavailable placeholders retained SHA-256
`f2ca24de27c2207528c02c059d8560f0b70a7f429fbd47f477e0d933047546e5`,
and stdout was empty. Future Python stderr is filtered only to replace the
frozen private run-root prefix before it reaches Slurm stderr.

No model, optimizer, role, normalization statistic, dependency, allocation,
or selector contract changes. Run 7 receives a new 120-GPU-minute intent,
bringing cumulative requested use to 725 GPU-minutes including the recovery
allocation, below the 2,400-minute ceiling.
