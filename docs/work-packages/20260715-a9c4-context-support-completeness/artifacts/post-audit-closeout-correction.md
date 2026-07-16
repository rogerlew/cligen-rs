# Post-audit mask closeout correction

Date: 2026-07-15
Access boundary: after `availability-audit-v1.json` was written; before any
A9c4 fit or corrected candidate output

The first `python -m research.a9c4.audit` execution completed the expensive
source-specific audit and wrote the canonical audit artifact, then stopped
while constructing the mask because the Python object used the JSON token
`false` instead of Python's `False`. No mask existed and no A9c4 candidate had
been fit or generated.

The lead corrected that one token and added a deterministic closeout path that
loads the already written audit, applies the already frozen mask and breadth
rules, and writes `evidence-mask-v1.json`. The audit artifact was neither
deleted nor regenerated. The closeout found 111 mandatory cells, retained 92,
classified 19 as report-only, and returned a failed breadth guard. This
correction changes no measurement, threshold, mask rule, or terminal.
