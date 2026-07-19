# Authority initialization hold

Terminal: `HOLD-A10M5R8-AUTHORITY-SOURCE-IDENTITY`

The scaffold source was published as
`56a7d421769d6c6c1dc8abf57eba76922c3f6d6b`, but the private asset manifest
and authority input mistakenly recorded
`56a7d42dc8690c1ba69b572a5ebc3649996f8e20`. The latter is not the published
Git object. This was detected immediately after authority initialization and
before doctor, probe, plan, prepare, stage, any remote mutation, any resource
reservation, or any Slurm submission.

The invalid genesis and its ledger remain preserved beneath the package's
private cache. The ledger contains only genesis and has zero requested or
actual GPU-minutes. It will not be reset, edited, derived, or used. The source
and scientific contract passed local verification and all repository gates;
the defect is solely the private source-identity expansion.

Corrective successor A10M5R8R1 reuses the unchanged experiment and receives a
new package-scoped authority. Its asset and authority generation consume the
exact output of `git rev-parse HEAD`; no abbreviated or manually expanded SHA
is accepted.
