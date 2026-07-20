# Scaffold review

Disposition: `ACCEPT`

## Review basis

R14R1's failure is operational: each independent candidate job expands the
same multi-gigabyte canonical environment on node-local storage. A single
four-GPU allocation with one shared immutable environment removes that
duplication without changing the scientific computation performed by any
candidate.

The portfolio is not a multi-rank model. It uses no DDP, NCCL, collectives,
gradient sharing, parameter sharing, or cross-candidate state. The only shared
objects after bootstrap are read-only program, environment, control, and corpus
files. Candidate output and caches are disjoint.

## Independent review

Independent re-review confirmed the exact inherited science hashes, plan
resource arithmetic, one-role four-GPU provider shape, strict device mapping,
per-child failure propagation, setup/corpus immutability, evidence roster,
terminal semantics, predecessor authentication, and exact cleanup behavior.

The review identified and dispositioned three blocking interface defects before
acceptance:

- the admission wrapper now consumes the inherited materializer's exact
  `--role` argument, with a composed CLI test;
- inherited admission-checker bytes are authenticated before staged code is
  executed, including an explicit tamper-before-exec test; and
- each frozen plain `training.json` publication is promoted without semantic
  content changes to a self-authenticated record whose hash is bound into both
  child process and evidence records. Replay independently cross-checks those
  bindings and the exact adapter-only and total parameter counts.

All five package tests, Python compilation, shell syntax, JSON parsing, and
`git diff --check` pass. Generated Python cache files are absent.
