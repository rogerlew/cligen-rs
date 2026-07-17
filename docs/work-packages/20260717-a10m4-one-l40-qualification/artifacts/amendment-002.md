# Amendment 002 — complete offline Rust toolchain

Status: prospective before run 2

Run 1 (`dfcc523`, Slurm `1013761`) settled `FAILED (101)` after 105
seconds. Its authenticated stderr is exactly Cargo's failure to execute
`rustc -vV` because no `rustc` executable existed. The asset builder had
published the standalone Cargo component and vendored crates, but not the
compiler or standard library. The failure occurred before source compilation,
corpus parsing, model construction, training, generation, or scoring.

Replace the standalone 10,788,340-byte Cargo component with the complete
official Rust 1.92.0 x86-64 Linux distribution, whose published identity is
192,171,372 bytes and SHA-256
`d2ccef59dd9f7439f2c694948069f789a044dc1addcc0803613232af8f88ee0c`.
Install it only into job-local storage and assert the exact `rustc` and Cargo
versions before the unchanged locked, offline release build.

No scientific contract, model, corpus, runtime, dependency lock, allocation
shape, evidence gate, or selector boundary changes. Run 2 receives a new run
identity and one new 120-GPU-minute intent. Cumulative requested use would be
240 GPU-minutes against the package's 2,400-GPU-minute ceiling.
