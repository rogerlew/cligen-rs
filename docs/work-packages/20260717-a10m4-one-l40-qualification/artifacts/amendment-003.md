# Amendment 003 — correct Cargo vendor resolution

Status: prospective before run 4

Run 3 (`c6446c2`, Slurm `1013766`) settled `FAILED (101)` after 122
seconds. The complete Rust 1.92.0 distribution installed and Cargo started,
but Cargo resolved the configured `../../vendor` directory relative to the
extracted workspace root. That produced `/tmp/vendor`, one directory above the
actual job-local `vendor/` tree. The failure occurred before compilation,
corpus parsing, model construction, training, generation, or scoring.

Change only the Cargo source replacement from `../../vendor` to `../vendor`.
For the frozen layout `JOB_LOCAL/source/.cargo/config.toml` plus
`JOB_LOCAL/vendor/`, Cargo resolves the corrected value to the existing vendor
root. The locked dependency set, vendor bytes, scientific contract, model,
corpus, runtime, allocation shape, evidence gates, and selector boundary do
not change.

Run 4 receives a new run identity and one new 120-GPU-minute intent.
Cumulative requested use would be 360 GPU-minutes against the package's
2,400-GPU-minute ceiling. The run-2 staged-only administrative abort requested
no scheduler resources and is not charged.
