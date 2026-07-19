# Execution disposition

Terminal: `HOLD-A10M5R10R1R3-CUBLAS-ENVIRONMENT-SCOPE`

The extraction-root hypothesis passed. Control job `1014056` authenticated the
portable runtime and environment, exposed the three corpus manifests at the
correct root, completed the frozen calendar preflight, and launched the first
P1/seed-147031 training subprocess.

Training then failed at the output-head `nn.Linear` in the first batch's
forward pass, before loss evaluation, backward, optimizer step, or checkpoint
publication. Slurm launches the parent wrapper with `--export=NONE`.
`bootstrap_environment.sh` exported
`CUBLAS_WORKSPACE_CONFIG=:4096:8` only in its child shell; process environment
changes cannot propagate back to the parent that subsequently launches
`train.py`. PyTorch deterministic-algorithm enforcement correctly rejected the
missing workspace configuration.

The authenticated result gate failed only `control_evidence_published`; all
eight admission, portable setup, identity, payload-deletion, and cleanup gates
passed. The toolkit observed the exhausted attempt, classified all ten
candidates `NOT_EXECUTED_UPSTREAM_FAILURE`, collected 13 present and 140 absent
allowlisted files, removed the exact remote root, released the unused recovery
reserve, and closed normally.

No control or candidate row completed and no selector ran. No architecture
conclusion is authorized. A fresh A10M5R10R1R4 may restore the required frozen
science-launch environment in both parent wrappers; model code, objective,
archive, calendar, role matrix, seeds, waves, and 935-minute bound remain
unchanged.
