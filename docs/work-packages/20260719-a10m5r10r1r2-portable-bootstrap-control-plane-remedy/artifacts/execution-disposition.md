# Execution disposition

Terminal: `HOLD-A10M5R10R1R2-CORPUS-ROOT-NESTING`

The portable-bootstrap hypothesis passed. On compute node03, control job
`1014054` extracted the frozen runtime with POSIX tools, authenticated Python
3.11.15, installed and checked the frozen wheelhouse, deleted setup payloads,
and published a valid `ready-for-science` receipt.

The control payload then failed before materializing any of its six controls.
The unchanged corpus archive is rooted at `corpus/`. `run_control.sh` extracted
that archive into `[JOB_LOCAL]/corpus` and also passed `[JOB_LOCAL]/corpus` as
the corpus root, producing `[JOB_LOCAL]/corpus/corpus`. The expected
`artifacts/offline-transfer-manifest-v1.json` was consequently one directory
below the supplied root. The original A10M5R10 wrapper had extracted the same
archive into `[JOB_LOCAL]`, which supplied the correct root.

The authenticated gate failed only `control_evidence_published`; all eight
portable setup, admission, identity, deletion, and cleanup gates passed. The
toolkit observed the one exhausted attempt, classified all ten candidates
`NOT_EXECUTED_UPSTREAM_FAILURE`, collected 13 present and 140 absent allowlisted
files, removed the exact remote root, released the unused recovery reserve,
and closed normally.

No control or candidate result exists and the selector did not run. The package
therefore carries no architecture conclusion. A fresh A10M5R10R1R3 authority
may correct only the two control/candidate extraction destinations to the
already successful A10M5R10 form; science, archive bytes, calendar, resource
bound, roles, capacities, seeds, objective, and selector remain frozen.
