# Submission admission protocol

This protocol is mandatory for `a10m5r10r1r1-python311-control-plane-remedy-r0`.
The checker runs on the Lemhi login host from the already verified remote run;
a receipt created only on the controller is not sufficient.

For each role, immediately before `lemhi-toolkit submit`:

1. While no other controller is submitting this authority, copy the current
   toolkit private `state.json` to
   `$RUN_ROOT/admission-input/state.json` and copy the current toolkit
   `publication/job-*.json` records to
   `$RUN_ROOT/admission-input/publication/`. The destination is owner-only and
   is not evidence-allowlisted. Replace the snapshot for every admission.
2. On the login host, invoke the staged checker with the exact staged paths:

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

   No setup argument is allowed for the control or the first member of a
   wave. The second-member setup argument is required whether the first member
   is still submitted or has already been terminally observed.
3. Require checker exit zero and authenticate the printed record SHA against
   `$RUN_ROOT/admissions/$ROLE.json`. A failed check publishes no allowlisted
   receipt. An existing role receipt is immutable and the checker refuses to
   replace it.
   The receipt must record `/usr/bin/python3.11`, its resolved path, version,
   byte count, and SHA-256; the `control_plane_python311` gate must pass.
4. Immediately submit that exact role at attempt zero with the toolkit. Do not
   admit another role between checking and submission.

The control check requires toolkit state `VERIFIED` with no attempts. Candidate
checks require `MATRIX_ACTIVE`, a passed and terminally observed control, and
the exact frozen wave order. The checker counts every registered, reserved,
submitted, or terminal-but-not-validated candidate conservatively as live.
It admits a second live candidate only after the first candidate's self-hashed
setup receipt authenticates all readiness, execution, admission, and asset
identities. A new wave requires both prior roles' authenticated toolkit job
receipts with terminal state and successful job-local cleanup.

Each submitted job independently opens its exact plural-path admission receipt
inside supervised execution. `bootstrap_environment.sh` stops before runtime
extraction unless that receipt and all asset identities authenticate. Final
job evidence repeats the authentication and binds the admission and setup
record hashes to the Slurm job, node, and owner marker.

If a submitted upstream role exhausts with a failed validated result, stop the
whole remaining matrix with the A10M5O1R2 `stop-matrix` operation. Do not issue
further admissions or submit known-doomed roles. Sparse collection must still
include each submitted attempt's authenticated gate and Slurm streams.
