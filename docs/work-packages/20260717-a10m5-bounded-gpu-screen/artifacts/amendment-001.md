# Prospective amendment 001 — marker-bound supervisor

The first staged lineage (`a10m5-screen-r1`) was verified but aborted before
submission and before any fit output or GPU allocation. Review found that its
job shell cleaned normal exits but did not guarantee a durable marker-bound
recovery target if Slurm interrupted the application before the shell trap.

Each configuration wrapper now creates the accepted v2 ownership marker,
invokes `supervise_v2.sh`, records durable application status, lets the
supervisor remove the exact job-local tree on every settled exit, and emits the
authenticated recovery target only if that removal cannot be proven. The
scientific design, assets, jobs, roles, grid, seed, and resource envelope are
unchanged. A new source commit and toolkit lineage are required prospectively.
