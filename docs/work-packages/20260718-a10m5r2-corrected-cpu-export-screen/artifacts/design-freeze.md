# A10M5R2 prospective correction freeze

The only correction relative to A10M5 is process lineage for CPU memory
measurement. The trainer writes and closes the export, then exits. The job
shell directly execs a separate one-core inference worker under external
`/usr/bin/time -v`; the worker reports `/proc/self/status` `VmHWM` and
`VmRSS`. Those two independent fresh-address-space values gate 2 GiB.

The twelve architecture/pooling/tail configurations, seed, corpus roles,
training schedule, identities, benchmark stations and horizons, timing
protocol, promotion rule, and every numerical threshold remain frozen at
A10M5. No protected role is opened.
