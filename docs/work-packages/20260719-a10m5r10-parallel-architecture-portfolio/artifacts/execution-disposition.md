# Execution disposition

Terminal: `HOLD-A10M5R10-JOB-LOCAL-CAPACITY`

Run `a10m5r10-parallel-architecture-portfolio-r0` executed the exact frozen
control and ten-role matrix. Job `1014028` reconstructed all six P1/P2
controls exactly. Jobs `1014039` and `1014040` completed the two physics
capacities, all three seeds, all-240 evaluation, physical-support checks, and
job-local cleanup. The other eight candidate jobs failed during environment
bootstrap before their science processes published candidate evidence.

The failure was aggregate node-local storage pressure. Each concurrent setup
needed at least 10,531,009,701 bytes while retaining a 3,865,978,880-byte
wheelhouse and an installed environment of at least 6,665,030,821 bytes. Two
successive four-job batches failed after roughly 130–140 seconds; the shared
temporary filesystem reached 98 percent use during diagnosis. The supervisor
then correctly removed each job-local root. Because setup logs were inside
those roots, the corresponding Slurm streams were empty. This is an
observability defect and a deterministic capacity failure, not candidate
science evidence.

The matrix is incomplete, so the selector was not run. In particular, the two
successful physics rows cannot support eligibility, Pareto, retention, or a
cross-family conclusion by themselves. Planned `portfolio-summary.json` and
`portfolio-decision.json` are deliberately absent.

Toolkit accounting settled at 103 charged GPU-minutes. Sanitized evidence was
collected, all job-local roots were verified absent, the exact durable remote
root was removed, the unused recovery reserve was released, and the authority
closed. A10M5R10R1 is the bounded corrective successor: it preserves the
scientific contract and reruns the full coherent matrix with at most two live
candidate jobs and one authenticated bootstrap at a time.
