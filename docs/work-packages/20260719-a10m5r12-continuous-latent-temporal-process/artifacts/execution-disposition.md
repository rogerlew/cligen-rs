# Execution disposition

Date: 2026-07-19
Terminal: `HOLD-A10M5R12-ADMISSION-NOT-MATERIALIZED`
Scientific interpretation: prohibited

The single control attempt, Slurm job `1016048`, exited 1 after 29 seconds.
The job wrapper required
`admissions/control-materialization.json`, but the controller sequence had not
run the staged admission checker before toolkit submission. Setup diagnostics
therefore failed while opening the absent receipt. The authenticated job record
reports `submission_admission_authenticated=false`, every environment/science
gate false, and `job_local_cleanup=true`.

No candidate role was submitted, Torch/CUDA self-tests did not run, the
environment was not bootstrapped, and no climate/model result exists. The
failure is operational and cannot update the architecture hypothesis.

The toolkit charged one GPU-minute, stopped both unstarted candidate roles,
collected the exact failure evidence under sanitizer projection 5, verified
remote and job-local absence, and closed the run. The direct bounded successor
is A10M5R12R1, which materializes and authenticates a fresh state/publication
snapshot and admission receipt before every toolkit `submit` call.

Primary evidence identities:

- job receipt SHA-256:
  `de5c525db9ece3d646afc624ee6fed713b108d0fde31aeb34737c3e07af4a9bd`;
- collection receipt SHA-256:
  `e7c7423f1b9071da47d2d3274058e25b983f8e180b4e344352cf5bed82eac232`;
- cleanup receipt SHA-256:
  `3e179f26f2d0e150d3ce9ed03b08a8294c356f281789f7219517e1278d6a1f07`;
  and
- terminal receipt SHA-256:
  `19cc5b271e323b293a85972cffd28df2692cdfc0f0071593bf6f049f69bdd2dc`.
