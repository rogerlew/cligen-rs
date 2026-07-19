# Execution disposition

Terminal: `A10M5O1-MULTI-L40-TOOLKIT-READY`

The original defect is closed. Slurm reservation count and toolkit accounting
count can no longer diverge in a valid plan. Existing single-L40 consumers do
not gain multi-GPU authority because their immutable provider declares a
maximum of one. A10M5O2 may use the additive provider after this exact source
is committed and published.
