# Frozen stage-1 transfer matrix

Binary units are used throughout: 1 MiB = 1,048,576 bytes and 1 GiB =
1,073,741,824 bytes.

| ID | Content | Direction/options | Repetitions | Logical payload budget |
|---|---|---|---:|---:|
| L0 | zero-payload `ssh ... true` | warm command | 10 | 0 |
| S16 | 16-MiB random file | upload + download | 3 each | 96 MiB |
| S256 | 256-MiB random file | upload + download | 3 each | 1,536 MiB |
| S1024 | 1-GiB random file | upload + download | 1 each | 2,048 MiB |
| F1024 | 1,024 × 64-KiB random files | recursive upload + download | 1 each | 128 MiB |
| TAR | tar of F1024 | upload + download | 1 each | at most 132 MiB |
| CR64 | 64-MiB random file | default and `-C`, both directions | 1 each | 256 MiB |
| CZ64 | 64-MiB zero file | default and `-C`, both directions | 1 each | 256 MiB |
| I256 | 256-MiB random file | rate-limited SCP upload, intentional 10-second timeout | 1 | 256 MiB conservative |
| R256 | I256 partial | conditional rsync `--partial --append-verify` | 1 if available | 256 MiB conservative |

Expected maximum when conditional R256 runs is 4,964 MiB (about 4.85 GiB).
The absolute logical-byte ceiling is 5 GiB, leaving at least 156 MiB for tar
headers and accounting conservatism. Wire-level SSH framing is not measured as
payload and is outside this logical ceiling.

Every nonzero cell records source size/hash, command status/time, destination
size/hash, and integrity verdict. Repetition reuses the same agent-created
remote filename; peak retained remote fixture data remains below 2 GiB.

I256 is not an integrity failure: it must leave a partial file larger than zero
and smaller than 256 MiB. R256 records local/remote rsync versions and either
verifies the completed source hash or proves that compatible resume support is
unavailable. Its absence does not invalidate the SCP baseline.
