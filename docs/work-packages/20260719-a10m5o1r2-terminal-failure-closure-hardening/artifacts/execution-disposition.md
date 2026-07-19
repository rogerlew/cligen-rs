# Execution disposition

Terminal: `A10M5O1R2-TERMINAL-FAILURE-CLOSURE-READY`

The toolkit can now close a provider-v2 matrix after an exact upstream role is
exhausted and failed without submitting never-started dependents or fabricating
their evidence. It atomically classifies all zero-attempt roles, authenticates
the trigger and authority ledger/scheduler state, collects the exact sparse
evidence surface, preserves mandatory evidence for every submitted attempt and
invoked recovery, proves scoped cleanup, and closes accounting.

This is a prospective toolkit disposition. It opened no Slurm allocation and
does not retrofit, reinterpret, or replace the manual exact-root cleanup and
`EXECUTED-HOLD-PYTHON311-CONTROL-PLANE` disposition of A10M5R10R1. A fresh
science-package/run identity may use `stop-matrix` if its own control or
candidate role exhausts.
