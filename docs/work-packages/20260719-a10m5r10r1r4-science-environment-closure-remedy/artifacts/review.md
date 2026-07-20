# Independent execution review

Disposition: `ACCEPT`.

The reviewer independently authenticated authority revision `0b9bc396…`, plan
`cdce8b81…`, all 20 publication receipts, and all 11 Slurm attempts. Every job
completed with exit `0:0`; every registered gate is true. The reviewer traced
all 11 admission and setup hash chains and all 30 seed records. Every
fit-validation score remained gradient-free, no protected role was opened,
and no result was spliced or retried.

The 36-entry ledger validates through head `f8a2ee09…`. It records 930 requested
primary GPU-minutes submitted and 396 actual GPU-minutes settled from 23,436
elapsed seconds under per-job ceiling. The unused five-minute recovery reserve
was released. Live scheduler accounting independently reproduced every job's
terminal state and elapsed time.

Collection authenticated a 6,952,960-byte archive at `aa83f2d…`, with all 153
allowlisted files present and none absent. Every projected file matches its
manifest byte count and SHA-256. Cleanup and terminal record self-hashes pass;
all 11 attempts are closed, no role was stopped, recovery was not invoked, and
a fresh remote check proves the exact durable run root is absent.

The four selector artifacts have the recorded `09451e…`, `12b216…`,
`08d3df…`, and `ae50cc…` hashes. The decision is
`A10M5R10-PORTFOLIO-READY`: four configurations are eligible and nondominated,
and annual/monthly residual K1, monthly residual K2, and annual/monthly
residual K2 are retained. Hierarchical joint-factor K2 was eligible and lost
only the frozen 2% equivalence/parsimony tie-break on the third retention axis.
State-space K1/K2 correctly fail daily-NLL and combined-dispersion gates. The
physics K1/K2 arms improve solar family and dependence aggregates but fail
solar per-block non-degradation and core combined dispersion; K1 also fails
the median-each-block guard.

The reviewer confirmed that publication redaction intentionally changes the
control-summary identities and therefore cannot be fed back into the exact
selector. Two raw-result replays before cleanup were byte-identical, and their
output hashes match the committed selector artifacts. The package,
disposition, accounting, toolkit, roadmap, and ExecPlan records describe this
boundary accurately. The result verifier passes. No findings remain.
