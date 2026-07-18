# A10M5R2 prospective execution

Run identity: `a10m5r2-screen-r1`

Authority identity: `a10m5r2-screen-r1-authority`

Budget identity: `a10m5r2-screen-budget`

The authority ceiling is 365 GPU-minutes: twelve single-attempt, one-L40,
30-minute jobs plus one separate five-minute exact-node recovery reserve. Jobs
run sequentially on the only observed typed L40 node. No retry or amendment is
authorized by this record.

The local canonical cache supplies eight already attested large assets. The
package asset constructor adds only committed R2 entry points, the byte-exact
A10M5 trainer core, twelve wrappers, toolkit recovery/supervision scripts, and
an expected-predecessor manifest constructed from committed A10M5 evidence.
The toolkit hashes and remotely revalidates every staged asset.

Each job reconstructs the pinned CPython 3.11/PyTorch/CUDA and Rust closures in
its supervised job-local root. The trainer fits and persists its export, then
exits. The shell launches the fresh CPU worker under external measurement.
The wrapper publishes the scientific receipt only after exact job-local
cleanup. A failure stops subsequent submission unless the package's ordinary
forward execution can close honestly without broadening the frozen question.

## Execution lessons

Toolkit `observe` is a terminal-settlement operation, not a blocking monitor.
Calling it while a job is still running fails closed with
`JOB_TERMINAL_MISMATCH`; monitor with `squeue`, wait for settled `sacct`, and
then call `observe` once.

Revision-2 recovery paths are mandatory members of the evidence allowlist even
when recovery is not used. A successful run must prospectively materialize an
explicit `invoked=false` recovery record and non-invocation streams. Also,
external `/usr/bin/time -v` echoes its complete command line. Any plan that
collects that file must freeze an exact durable-root replacement before the
last role settles, or produce a non-reserved pre-redacted command token.
