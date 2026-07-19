# Gate results

Evidence mode: live on Lemhi from `rmm`, 2026-07-19.

- Published live source: `0caae8e462dd82cdc382e0d425a0553872c648d1`.
- Canonical configuration: CPython 3.11.15, NumPy 2.2.6, PyTorch
  2.7.1+cu128, CUDA 12.8, NCCL 2.26.2: PASS.
- Admission: four fresh snapshots showed node03 idle with all four L40s; no
  observed allocation was displaced.
- Job `1014018`, one L40: PASS, exit 0, 94 seconds, 94 GPU-seconds.
- Job `1014019`, two L40s: PASS, exit 0, 64 seconds, 128 GPU-seconds.
- Job `1014020`, four L40s: PASS, exit 0, 76 seconds, 304 GPU-seconds.
- Job `1014021`, two-L40 controlled rank failure: PASS, expected exit 1,
  bounded peer teardown, 62 seconds, 124 GPU-seconds.
- Every success role passed all 16 identity, topology, NCCL, DDP, checkpoint,
  and cleanup gates. The controlled failure passed all 10 failure gates.
- Ledger: PASS; 82 primary requested GPU-minutes, 650 actual GPU-seconds, 14
  per-job-ceiling-rounded actual GPU-minutes, and unused five-minute recovery
  reserve released under the 90-minute ceiling.
- Collection: PASS after A10M5O1R1 escaped one PyTorch
  `<NO_OTHER_FAILURES>` placeholder; no raw evidence, job, or gate changed.
  The resumed collection's adapter metadata retained the older revision-3
  label, while its per-file transformation receipt authenticated revision 4
  and the escaped-token count. A10M5O1R1 now sources the adapter label from the
  projector constant so subsequent receipts cannot repeat that label drift.
- Cleanup: PASS; toolkit reported durable root and job-local state absent,
  closed the run, and an independent SSH check confirmed the remote root
  absent and no matrix job queued.
- Strong-scaling recommendation: FAIL as an advisory performance gate;
  two/one was 0.3999x and four/two was 0.0462x. Operational readiness is not
  affected; classification is `SINGLE-GPU-PREFERRED`.
- Toolkit tests: PASS, 56 tests; remote shell syntax and package verifiers:
  PASS; `git diff --check`, `cargo fmt --check`,
  `cargo clippy --all-targets -- -D warnings`, and `cargo test`: PASS.

Coverage/CRAP was not required because no production function under `crates/`
changed.
