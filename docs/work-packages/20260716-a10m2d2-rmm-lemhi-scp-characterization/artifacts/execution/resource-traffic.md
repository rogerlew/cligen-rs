# Resource and traffic ledger

- Dispatch commit: `5d8abbe61df810d4a11dc4ab92fa686214be25a1`
- Logical payload: 5,206,187,008 bytes (4,965.007 MiB)
- Hard ceiling: 5,368,709,120 bytes (5,120 MiB)
- Headroom: 162,522,112 bytes (154.993 MiB)
- Calculated peak remote fixture content: approximately 1,938.503 MiB
- Per-command timeout: 1,800 seconds; no unexpected timeout occurred
- Expected I256 timeout: status 124 after 10.007922 seconds
- Measured command-time sum: 1,094.337305 seconds
- Slurm jobs/allocations: zero
- GPU time: zero
- Scientific, private, or LFS fixture bytes: zero
- Remote run after cleanup: absent
- Local fixture directory after cleanup: absent

The frozen TAR row estimated at most 132 MiB round trip. The generated BSD tar
was 69,733,888 bytes (66.503 MiB), so the observed round trip was 133.007 MiB,
1.007 MiB above that prospective sub-budget. The driver accounted the actual
bytes and the hard 5-GiB ceiling retained 154.993 MiB of headroom. This is a
P3 estimate defect, not a safety-envelope breach.
