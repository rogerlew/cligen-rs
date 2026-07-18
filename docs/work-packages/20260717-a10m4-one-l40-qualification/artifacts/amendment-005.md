# Amendment 005 — failure-path job-local cleanup

Status: prospective before run 6

Run 5 (`8d87f71`, Slurm `1013770`) settled `FAILED (2)` after 24 seconds
while extracting the wheelhouse: node03's `/tmp` reported no space. Earlier
failed attempts created package-owned directories named exactly
`/tmp/a10m4-qualification-<job-id>`, but the harness removed job-local state
only on its success path. The no-space condition also prevented the shell from
materializing the failure-receipt here-document, so normal collection was not
possible. The stderr identity was 1,461 bytes with SHA-256
`87b893f90bfc38570d404803e2544c9d1edddff38612c9ecd61946c3c031d7a5`;
stdout was empty.

One explicit recovery allocation, Slurm `1013771`, requested one L40 for five
minutes on node03 and completed in 10 seconds. It removed only the four known
package-owned paths for jobs `1013761`, `1013766`, `1013769`, and `1013770`,
then asserted all four were absent. Its stdout and stderr were empty.

Move exact, nonsymlink job-local cleanup into the EXIT trap before failure
receipt construction. The success path retains its existing cleanup and
absence check. This prevents failed attempts from exhausting node-local
storage and makes receipt construction possible after cleanup.

No scientific, model, corpus, dependency, allocation-shape, gate, or selector
contract changes. Run 6 receives a new 120-GPU-minute intent. Including the
five-minute recovery intent, cumulative requested use becomes 605 GPU-minutes
against the 2,400-minute package ceiling.
