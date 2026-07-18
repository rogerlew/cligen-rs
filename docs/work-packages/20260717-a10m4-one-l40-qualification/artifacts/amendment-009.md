# Amendment 009 — respect the faithful 365-day calendar

Status: prospective before run 10

Run 9 (`be94000`, Slurm `1013775`) reached every qualification phase and
settled `FAILED (1)` after 618 seconds. All gates passed except
`benchmark_complete`: every candidate stream was complete and supported, all
12 benchmark rows had low dispersion, the fresh restart was exact, and CPU
export safeguards passed. The sanitized evidence archive was collected
normally at 40,960 bytes with SHA-256
`ce5287339e74ebf8a15379f678372e59441b5fe89015b0c37d8f039e67343f6a`,
and exact remote cleanup/close passed.

The completeness predicate incorrectly compared faithful CLIGEN output with
the neural candidate's Gregorian day count. The faithful byte contract emits
exactly 365 daily rows per simulated year; the neural candidate separately
retains its frozen Gregorian stream contract. Validate each implementation
against its own calendar: `15 + years * 365` total faithful `.cli` lines and
the existing Gregorian candidate count. This corrects only the comparator
completeness assertion; it does not alter either generated stream or any timed
workload.

No scientific, model, optimizer, corpus, dependency, timing, allocation,
threshold, gate, or selector contract changes. Run 10 receives a new
120-GPU-minute intent, bringing cumulative requested use to 1,085 GPU-minutes
including the five-minute recovery allocation, below the 2,400-minute ceiling.
