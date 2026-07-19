# Resource ledger

The authority ceiling was 935 GPU-minutes. The run charged 11 GPU-minutes:
one minute for control job `1014042` and one minute each for candidate jobs
`1014043` through `1014052`. Every job was single-GPU, single-attempt, terminal,
and toolkit-observed exactly once. The private ledger head after settlement is
`19f90bce480b3e5295bbceb99d10a3275893c134d478dce7f8d5e097962507d2`;
the complete private ledger file SHA-256 is
`b2a2c607e8f41fa5e544932573672cb45b723344f3611d6aa317c963dec246bb`.

No recovery job ran. Because toolkit collection could not represent absent
PASS-only admission files, its reserved five-minute recovery token could not
be released through normal close. This is a controller-record limitation, not
unaccounted scheduler use; scheduler accounting contains only the eleven
one-minute jobs above.
