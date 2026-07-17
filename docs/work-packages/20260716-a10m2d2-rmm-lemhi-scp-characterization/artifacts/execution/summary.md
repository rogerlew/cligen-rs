# A10M2D2 transfer characterization summary

Terminal: `A10M2D2-SCP-EXPECTATIONS-FROZEN`

## Boundary and disposition

The one-pass matrix ran on 2026-07-16 from published `main` at
`5d8abbe61df810d4a11dc4ab92fa686214be25a1`. It measured the warm path from
the `rmm` Apple M1/macOS host through the operator's active UI VPN and existing
SSH control masters to Lemhi Ceph home. Cold MFA was neither automated nor
timed. No Slurm allocation, compute node, GPU, scientific data, or LFS object
was used.

All 27 registered transfer-integrity verdicts passed. The only nonzero command
status was the prospectively required I256 timeout status 124. Exact remote
and local cleanup passed.

## Warm latency and single-file throughput

Rates are effective logical MiB/s. Repeat rows show median and observed
minimum--maximum.

| Cell | Direction | Median seconds | Median MiB/s | Observed MiB/s range |
|---|---|---:|---:|---:|
| L0, 10 repeats | control | 0.348783 | n/a | n/a |
| S16, 3 repeats | upload | 2.162680 | 7.398 | 5.272--7.518 |
| S16, 3 repeats | download | 3.839203 | 4.168 | 3.515--4.371 |
| S256, 3 repeats | upload | 23.002628 | 11.129 | 10.959--11.339 |
| S256, 3 repeats | download | 52.462190 | 4.880 | 4.676--5.106 |
| S1024 | upload | 101.851860 | 10.054 | single observation |
| S1024 | download | 216.619707 | 4.727 | single observation |

Warm no-payload command latency ranged from 0.342668 to 0.352710 seconds. The
S256 rate range was 3.4% of its median for uploads and 8.8% for downloads.
That is sufficient for a first operational baseline but not an SLA or a
time-of-day characterization.

## Small files and archives

The direct fixture contained 1,024 files of 64 KiB each, or 64 MiB total. Its
BSD tar representation was 66.503 MiB including archive padding.

| Form | Upload seconds | Download seconds | Upload MiB/s | Download MiB/s |
|---|---:|---:|---:|---:|
| 1,024 files | 218.468606 | 175.663238 | 0.293 | 0.364 |
| tar archive | 5.439977 | 12.422678 | 12.225 | 5.353 |

The archive was 40.16 times faster to upload and 14.14 times faster to
download despite its padding. A10 should bundle directories containing many
small immutable objects before crossing the WAN path, then verify the archive
hash before extraction.

## SSH compression

| Content | Direction | Default seconds | `-C` seconds | `-C` elapsed change |
|---|---|---:|---:|---:|
| random 64 MiB | upload | 6.098381 | 6.147469 | 0.8% slower |
| random 64 MiB | download | 13.471063 | 13.549090 | 0.6% slower |
| zero 64 MiB | upload | 5.644600 | 5.834409 | 3.4% slower |
| zero 64 MiB | download | 17.489214 | 13.614170 | 22.2% faster |

Compression did not help incompressible content and was not a reliable win
even for the small compressible control. Do not enable `scp -C` by default for
wheelhouses, archives, Parquet, model weights, or other already compressed or
incompressible A10 artifacts. The isolated compressible-download benefit is a
candidate for a larger controlled test only if A10 later has a genuinely
compressible large object.

## Interruption and alternatives

The intentional ten-second, rate-limited SCP upload returned status 124 and
left one destination named `interrupted-256m.bin` with 9,011,200 bytes (8.594
MiB). SCP therefore exposed the incomplete object at the requested destination
name in this run; consumers must not treat existence as completion.

Local rsync 3.4.1/protocol 32 and remote rsync 3.1.3/protocol 31 successfully
used `--partial --append-verify` to finish that object in 22.876509 seconds,
after which its SHA-256 matched. The R256 ledger conservatively uses the full
256-MiB logical source as its denominator and is not a measurement of suffix
wire bytes. Rsync is the observed resumable option for large transfers.

The Globus CLI was absent on both endpoints. That does not establish whether
administrators expose a managed Globus endpoint. Administrator documentation
or confirmation remains necessary before making a Globus claim.

## Capacity and traffic

The Ceph filesystem reported 659,806,879,744 KiB (614.49 TiB) available at the
measurement instant. This is shared-filesystem capacity, not evidence of the
account's quota. The available `quota -s` probe emitted no usable quota record,
so retention limits remain administrator-dependent.

Logical transferred payload was 5,206,187,008 bytes (4,965.007 MiB, 4.849
GiB), leaving 162,522,112 bytes (154.993 MiB) below the hard 5-GiB ceiling.
Peak retained remote fixture content was approximately 1,938.503 MiB, below
the 2-GiB bound. Command-level measured time summed to 1,094.337 seconds;
local fixture generation, hashing, and orchestration are not included in that
sum.

## Operational recommendation

For this observed warm VPN window, SCP is reasonable for hash-verified single
files or archives up to roughly 10 GiB: the sustained rates project about 17
minutes to upload and 36 minutes to download 10 GiB. At 50 GiB, projections
rise to about 1 hour 25 minutes upload and 3 hours download; use resumable
rsync or investigate an administrator-supported managed transport rather than
depending on one SCP session. Use the same resumable rule earlier whenever an
interruption would be expensive.

Do not transfer unbundled small-file trees. Do not use destination existence
as an integrity signal. Always publish and verify a SHA-256 manifest. A later
time-window replay is not justified immediately by the modest S256 variation;
give it a new execution identity if a route change or a planned transfer of 50
GiB or more makes scheduling accuracy material.

Integrity, bounded stability, and cleanup support proceeding to the roadmapped
Stage 2 Ceph/job-local staging gate inside the next authorized GPU-bearing
A10M2 allocation.
