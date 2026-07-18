# Amendment 010 — include the faithful trailing footer

Status: prospective before run 11

Run 10 (`d225056`, Slurm `1013776`) again passed every gate except
`benchmark_complete` and settled `FAILED (1)` after 634 seconds. Amendment 009
correctly localized the failure to the faithful line-count predicate but
incorrectly attributed it to a 365-day calendar. The sanitized evidence
archive was collected normally at 40,960 bytes with SHA-256
`71ae8a5acbfbf5f3c42c3183313ca9d51fb17492954a37b1373bc176ef66be76`,
and exact remote cleanup/close passed.

The byte-pinned faithful fixture proves the actual contract: 15 header lines,
Gregorian daily rows, and one trailing blank footer line. Its 31-year fixture
has 11,338 `splitlines()` entries: `15 + 11,322 + 1`. Restore the Gregorian
day calculation and require both `16 + days_for_years(years)` total lines and
an empty final line. The candidate retains its separately frozen Gregorian
stream contract. This corrects only the faithful completeness assertion; it
does not alter either generated stream or any timed workload.

No scientific, model, optimizer, corpus, dependency, timing, allocation,
threshold, gate, or selector contract changes. Run 11 receives a new
120-GPU-minute intent, bringing cumulative requested use to 1,205 GPU-minutes
including the five-minute recovery allocation, below the 2,400-minute ceiling.
