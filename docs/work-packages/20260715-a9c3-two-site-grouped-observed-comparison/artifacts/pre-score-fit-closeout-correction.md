# A9c3 pre-score fit-closeout correction

Status: prospective-to-scoring execution correction
Date: 2026-07-15

The first A9c3 fit process completed and wrote all eight detail files and all
eight compact fit records. It then stopped before writing either
`structural-audit-v1.json` or `fit-execution-v1.json`. At that point no
faithful baseline, development score, evaluation, Pareto result, selection
result, or confirmation target series had been accessed or written.

The stop exposed two inherited research-only defects in the hash-bound A9c
helpers:

- `research/a9c/models.py::structural_audit` uses the JSON spelling `false`
  in Python and raises `NameError` before returning evidence.
- `research/a9c/run.py::synthetic_recovery` passes generated rows containing
  `precip_mm` to legacy recovery helpers that require `prcp_mm`, causing a
  `KeyError` before recovery evidence is returned.
- The first closeout attempt then exposed that the immutable compact record
  stores `configuration_id` inside `configuration`; the aggregate builder had
  looked for an unpersisted duplicate top-level key. That attempt also stopped
  before writing either aggregate artifact. The resumed inventory adds the
  duplicate ID only to the parent fit-execution record and leaves each compact
  file and its hash unchanged.
- The first faithful-baseline attempt used different output filenames for the
  primary and replay run. Parsed climate rows were identical, but CLIGEN's
  header embeds invocation/output context, so whole-file hashes differed and
  the engineering gate failed before the baseline artifact was written. The
  corrected replay executes the identical frozen run spec and output path
  twice, hashing bytes before and after removal and recreation of the temporary
  output. CLIGEN's fail-closed no-overwrite guard requires that explicit
  removal. This restores the registered same-run byte-replay test without
  changing a burn or climate value.
- The next faithful-baseline attempt completed the byte replay but stopped
  while constructing the in-memory feature cache. The frozen A9c family
  helper expects the predecessor field name `prcp_mm`; the canonical A9c3
  parser emits `precip_mm`. A package-local, value-preserving adapter now
  supplies both names only at that helper boundary. No baseline or score
  artifact was written by the failed attempt.

A9c3 does not modify either historical, predecessor-bound file. The package-
local closeout uses the same structural predicates with valid Python booleans
and adapts only the recovery helper's input field name. It does not change a
fit, refit a configuration, change a monthly result, alter a random stream, or
access a candidate score. The `fit-closeout` command fails closed unless the
exact eight configuration IDs are present in both fit directories, every
detail self-hash reproduces, every detail hash matches its compact record, and
every already-recorded monthly check passed. The closeout output records
`execution_mode=pre_score_closeout_resume` so this incident cannot be mistaken
for a single uninterrupted process.
