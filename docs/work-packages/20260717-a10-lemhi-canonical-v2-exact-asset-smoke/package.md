# A10 Lemhi canonical v2 exact-asset smoke

Status: `EXECUTED-COMPLETE`
Date: 2026-07-17
Evidence mode: Live
Starting branch and push target: current `origin/main`, push `main`

## Objective

Validate the unchanged semantic candidate at
`5addee9c5db3592ee247eab2b5266ed5567fd9aaf24ed78dcb321ecbb001e22d`
after adding a configuration-level asset firewall that compares every frozen
runtime/framework/toolchain byte identity before staging. Reuse the proven
environment-closure and compute protocol under a new package/run/authority.

## Authority and resources

The operator-authorized corrective successor permits one `gpu:l40:1` primary
job on `gpu-icrews` (4 CPUs, 16,384 MiB, 15 minutes) and one conditional
exact-node recovery (2 CPUs, 1,024 MiB, 5 minutes), with a 20 L40-GPU-minute
ceiling, no retry/requeue, and one allocation at a time. It does not authorize
A10M5, confirmation targets, direct node SSH, or candidate mutation.

Agents have authoring authority for the package, exact local artifact
reconstruction, toolkit inputs, evidence closeout, and attestation if and only
if every frozen candidate identity and live gate passes.

## Plan

1. Verify the candidate semantic hash, profile/provider hashes, and exact
   runtime, requirements, wheel manifest, wheelhouse, Rust, and Cargo-vendor
   byte identities before any remote mutation.
2. Publish the source authority, build its exact source archive, initialize a
   fresh immutable 20-minute authority, and bind executable intent.
3. Stage and remotely verify all hashes, sizes, and required modes.
4. Run the proven typed-presence/clear/reconstruct environment protocol and
   full one-L40 Python/CUDA/Rust/supervisor smoke.
5. Collect, sanitize, settle, clean, close, and repeat the configuration-level
   identity firewall against the executed plan.
6. Emit `lemhi-canonical-smoke-attestation-1` only if all gates pass.

## Gates and exit

All repository/toolkit gates from the predecessor remain required. The new
`verify-live-inputs.py` is a pre-allocation and pre-attestation firewall.
Success is `A10-LEMHI-CANONICAL-V2-SMOKE-READY`; any mismatch or operational
uncertainty holds without attestation or designation.

## Result

Terminal: `A10-LEMHI-CANONICAL-V2-SMOKE-READY`

The pre-allocation and pre-attestation firewalls both matched all frozen
candidate assets. Job `1013866` completed all 27 gates in 236 seconds on
`node03`; the recovery allocation was not used, and exact job-local/durable
cleanup passed. Immutable attestation
`lemhi-a10-py311-l40-v2-candidate-smoke-20260717` binds the candidate. The
candidate is attested but not yet current; designation remains the next
local-only package.
