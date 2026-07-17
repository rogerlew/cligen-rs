# A10M2D2 execution kickoff template

Execute
`docs/work-packages/20260716-a10m2d2-rmm-lemhi-scp-characterization/package.md`
end to end.

- Repository: `cligen-rs`.
- Start from clean current `origin/main` at `<DISPATCH_COMMIT>`.
- Remain on `main`; push only to `main`.
- Predecessors: A10M2 `EXECUTED-HOLD-CUDA-ENVIRONMENT` and A10M2D1
  `A10M2D1-ROOT-CAUSE-LOCALIZED` remain immutable.
- Authority: stage-1 warm SCP characterization only, maximum 5 GiB logical
  transferred payload, zero Slurm/GPU use.

Before remote write, require the operator's UI VPN and verify the `login-ui`
and `lemhi` masters with `ssh -O check`. Stop for human bootstrap if either is
absent. Run the frozen matrix once through `BatchMode=yes`, enforce the byte
and timeout ceilings, verify every transfer hash, retain sanitized evidence,
remove only the exact local/remote fixture directories, review, run gates,
reconcile roadmap/catalog state, and push the terminal record.

From the clean repository root, execute the frozen driver with:

```sh
bash docs/work-packages/20260716-a10m2d2-rmm-lemhi-scp-characterization/artifacts/jobs/run_stage1.sh
```

Do not automate MFA, use scientific/LFS data, submit Slurm work, access a
compute node, install software, expand the transfer matrix, retain fixtures,
or execute the roadmapped stage-2 Ceph/local-storage test.
