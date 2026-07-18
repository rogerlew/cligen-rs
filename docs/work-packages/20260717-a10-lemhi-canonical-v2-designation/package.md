# A10 Lemhi canonical v2 designation

Status: `EXECUTED-COMPLETE`
Date: 2026-07-17
Evidence mode: Static
Starting branch and push target: current `origin/main`, push `main`

## Objective

Advance the local canonical designation pointer to the smoke-attested v2
candidate without mutating the v1 record, v2 semantic candidate, or immutable
attestation.

## Authority and scope

The exact-asset smoke reached `A10-LEMHI-CANONICAL-V2-SMOKE-READY` and emitted
attestation SHA-256
`5caf106a84797b1d068be5693478f74b5368752bcfb78fa5eba186bdc21db350`.
The established roadmap authorizes this local-only successor. It performs no
VPN action, remote write, scheduler query, allocation, target-data access, or
A10M5 scientific execution.

## Execution and gates

Created designation revision 1 under schema
`lemhi-canonical-designation-index-1`. Its `current` entry binds the v2
candidate and attestation; its `superseded` entry binds canonical v1's
immutable semantic hash. Verification checks every hash and confirms that the
historical v1 embedded status remains unedited status-at-issuance text.

## Result

Terminal: `A10-LEMHI-CANONICAL-V2-DESIGNATED`

Designation SHA-256:
`f2ea307d0c3e87a82554c3438f6d5378bba16df4b5d1e29a64ef763fb31d5690`.

New A10 single-L40 consumers resolve the current configuration through the
designation index. A10M5 is the next scientific stage.
