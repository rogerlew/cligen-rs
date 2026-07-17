# Amendment 004 — deterministic CuBLAS process environment

Status: prospective before run 5

Run 4 (`cf17353`, Slurm `1013769`) completed the offline faithful-Rust
release build in 69 seconds, loaded the model and corpus, and reached the first
GPU update. PyTorch then refused the GRUCell CuBLAS operation because
deterministic algorithms were enabled without a pre-process
`CUBLAS_WORKSPACE_CONFIG`. The job settled `FAILED (1)` after 189 seconds.

Export the documented deterministic CuBLAS workspace setting `:4096:8` before
any Python process. Also invoke the harness by its run-root-relative path so a
future traceback does not embed the forbidden private Ceph prefix. This second
change affects failure-log publication only.

The toolkit refused run 4 collection because the traceback contained that
forbidden prefix. Before marker-validated recovery cleanup, the six allowlisted
files were identity-recorded: `evidence.json` was 156 bytes with SHA-256
`0a90dd82704a9fca36285656324df639b57bde9cc32c0725a716533c7864edae`;
stderr was 8,482 bytes with SHA-256
`b398ad326b9eb5817d7f5b9aebcc0a71789b165e47c6f89656b86e5d1f187c28`;
the three unavailable placeholders retained SHA-256
`f2ca24de27c2207528c02c059d8560f0b70a7f429fbd47f477e0d933047546e5`;
and stdout was empty. No private path is reproduced here.

No model, optimizer, corpus, dependency, allocation, gate, or selector
contract changes. Run 5 receives a new 120-GPU-minute intent, bringing
cumulative requested use to 480 GPU-minutes against the 2,400-minute ceiling.
