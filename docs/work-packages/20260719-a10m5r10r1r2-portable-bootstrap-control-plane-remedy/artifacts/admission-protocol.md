# Submission admission and portable-bootstrap protocol

This protocol is mandatory for
`a10m5r10r1r2-portable-bootstrap-control-plane-remedy-r0`.

## Login-host admission

For each role, immediately before `lemhi-toolkit submit`:

1. While no other controller is submitting this authority, copy the current
   private toolkit `state.json` to
   `$RUN_ROOT/admission-input/state.json` and copy current
   `publication/job-*.json` records to
   `$RUN_ROOT/admission-input/publication/`. Replace this owner-only,
   non-evidence snapshot for every admission.
2. Invoke the staged checker on the Lemhi login host:

   ```text
   /usr/bin/python3.11 ./admission_checker.py \
     --remote-run-root "$RUN_ROOT" \
     --contract "$RUN_ROOT/job-local-capacity-contract.json" \
     --asset-manifest "$RUN_ROOT/asset-manifest.json" \
     --toolkit-state "$RUN_ROOT/admission-input/state.json" \
     --publication-dir "$RUN_ROOT/admission-input/publication" \
     --role "$ROLE" \
     --output "$RUN_ROOT/admissions/$ROLE.json"
   ```

   For the second member of a wave, also pass exactly:

   ```text
   --setup "$FIRST_ROLE=$RUN_ROOT/results/$FIRST_ROLE/setup.json"
   ```

   No setup argument is allowed for control or a wave's first member. The
   second-member setup is required even if the first role is already terminal.
3. Require checker exit zero and authenticate the printed SHA-256 against the
   immutable receipt. The login receipt records `/usr/bin/python3.11`, resolved
   path, version, byte count, and SHA-256. A failed check publishes no
   allowlisted receipt.
4. Immediately submit that exact role at attempt zero. Do not admit another
   role between checking and submission.

Control admission requires toolkit state `VERIFIED` with no attempts.
Candidate admission requires `MATRIX_ACTIVE`, passed and observed control, and
the frozen wave order. The checker counts every registered, reserved,
submitted, or unvalidated candidate conservatively as live. The second role
requires the first role's self-hashed ready setup; a new wave requires both
prior roles' authenticated terminal job receipts and cleanup.
Any candidate attempt observed as `RESULT_VALIDATED` with `passed: false`
closes all later admission gates. Because every role has exactly one attempt,
the operator must invoke whole-matrix stop rather than continue the wave.

## Compute-side portable bootstrap

The compute image is not required to provide `/usr/bin/python3.11`.
`bootstrap_environment.sh` performs this strict sequence:

1. use POSIX shell utilities to create job-local directories;
2. extract the already toolkit-hash-verified `runtime.tar.gz` into
   `$runtime_root` without invoking Python;
3. invoke only `$runtime_root/bin/python3 --version` and require the pinned
   `Python 3.11.15` result;
4. invoke `setup_diagnostics.py` and all setup inline checks explicitly with
   `$runtime_root/bin/python3`;
5. create the environment with that same runtime, install the hash-locked
   wheelhouse, verify it, delete wheel and pip caches, and publish ready setup;
6. run controls or candidate science only from the isolated environment.

The ready setup records the portable compute interpreter as
`[JOB_LOCAL]/runtime/cpython/bin/python3`, its exact bytes and SHA-256, source,
asset manifest, admission, job, node, role, and owner-marker identities.

## Pre-runtime failure closure

If the portable archive is absent, unreadable, unextractable, or does not
contain the pinned Python runtime, the supervised command exits before any
Python diagnostic. After supervised cleanup, the outer wrapper invokes the
known compute `/usr/bin/python3` only to publish terminal failure evidence.
Those heredocs are frozen to Python 3.6 syntax, contain no future annotations,
and cannot produce a passing result: `portable_runtime_available` and setup
authentication remain false. The gate still binds the Slurm job, node, role,
run, admission, manifest, cleanup outcome, and exact gate bytes observed by
the toolkit.

Observe the exhausted failed role. Then invoke A10M5O1R2 `stop-matrix` for the
whole unsubmitted remainder; issue no further admission or submission. Sparse
collection must include each submitted attempt's authenticated failed gate and
Slurm stdout/stderr. Complete collection, exact-root cleanup, closure, review,
and disposition under this fresh package identity.
