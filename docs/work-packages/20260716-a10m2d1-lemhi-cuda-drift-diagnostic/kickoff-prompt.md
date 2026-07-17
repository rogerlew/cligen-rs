# A10M2D1 execution kickoff template

Execute
`docs/work-packages/20260716-a10m2d1-lemhi-cuda-drift-diagnostic/package.md`
end to end.

- Repository: `cligen-rs`.
- Start from clean current `origin/main` at `<DISPATCH_COMMIT>`.
- Remain on `main`; push only to `main`.
- Predecessor: A10M2 terminal `EXECUTED-HOLD-CUDA-ENVIRONMENT`.
- Authority: diagnostic comparison only, maximum 10 requested GPU-minutes.

Before any remote write, verify `login-ui` and `lemhi` control masters with
`ssh -O check`; stop for human MFA bootstrap if either is absent. Freeze exact
source hashes and confirm no user job is present. Run login prestaging, then D1
once. Continue through all registered probes after an individual configuration
failure, while failing closed for allocation/device/safety failures. An exact
rerun is allowed only for a documented infrastructure transient.

Retrieve sanitized evidence, classify every hypothesis and documentation
claim, account resources, remove only the exact remote run directory, review,
run gates, reconcile roadmap/catalog state, and push the terminal record. Do
not install software, use unsupported-compiler overrides, access confirmation
data, or proceed to PyTorch/NCCL/restart testing.
