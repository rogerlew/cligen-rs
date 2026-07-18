# A10M5 handoff

A10M5 is authorized only from terminal `A10M4-QUALIFICATION-READY`. It must
consume the exact A10M3 machine contracts and canonical configuration
`lemhi-a10-py311-l40-v1` at semantic SHA-256
`0b1115a6801259c62d9550c877a3c49a897319348ba1c2027be0d9c4f77c1179`.
The accepted A10M1 v2 manifests remain the only corpus authority.

The qualified operational pattern is:

1. use the `rmm` MFA-bootstrap/keepalive control path and the Lemhi toolkit;
2. reconstruct the pinned CPython 3.11/PyTorch CUDA environment and complete
   Rust toolchain from content-addressed assets without ambient modules;
3. request typed `gpu:l40:1` jobs on `gpu-icrews`, use job-local storage, set
   `CUBLAS_WORKSPACE_CONFIG=:4096:8`, and clean exact roots on every exit;
4. exclude A10M1's intentional masked Daymet rows without imputation, preserve
   the selected window cursor in checkpoints, deserialize restart state on CPU,
   and then load model/optimizer state onto the GPU;
5. sanitize all returned errors, collect only allowlisted evidence, and require
   structured gate receipts plus terminal accounting and exact cleanup.

A10M5 may execute only the frozen 12-configuration, seed-147031 screen and at
most two full-development promotions per pooling class. The frozen M5 resource
envelopes are 160 L40 GPU-hours for screening and 280 L40 GPU-hours for
finalist development, with at most two concurrent jobs. It must use the A10M3
training, checkpoint, generation, evaluation, benchmark, comparator, and
missingness contracts unchanged.

M4 evidence is qualification-only. Do not reuse its weights, checkpoint,
export, two-step cost projection, or raw runtime ratios as candidate evidence.
A10M5 creates new candidate identities and scored development records. It may
read only the frozen development surface needed by its evaluator; confirmation
targets remain prohibited until the later selector gate explicitly permits
them. Grid expansion, role changes, threshold changes, Python 3.8 fallback, or
post-output rescue require a new prospective scientific decision.

A10M5 should stop with an exact development disposition and a complete handoff
to A10M6; it must not silently promote or seal a public runtime.
