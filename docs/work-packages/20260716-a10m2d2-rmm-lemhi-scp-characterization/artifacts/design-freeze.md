# Stage-1 design freeze

## Measurement boundary

The measured path is one warm agent workflow:

```text
rmm (Apple M1/macOS) -> UI VPN -> login-ui control master ->
lemhi control master -> durable Ceph home
```

Cold password/Duo authentication is a human prerequisite and is not timed.
The results bind only to the observed host, VPN route, warm masters, Lemhi
endpoint, storage, and time window.

## Fixture contract

- Primary fixtures are random/incompressible byte streams.
- The compression control is a zero-filled byte stream of the same 64-MiB
  logical size as its random comparator.
- The 1,024-file fixture is split from the random 64-MiB fixture into exact
  65,536-byte members. Its tar comparison contains exactly that directory.
- Large fixtures are streamed to disk and never accumulated in memory.
- Fixtures live only under a validated `mktemp` directory and the unique
  commit-derived remote run.
- Fixtures are evidence inputs, not repository artifacts.

## Transport contract

- Every SSH/SCP command uses `BatchMode=yes` and `ConnectTimeout=10`.
- SCP uses the installed default protocol; legacy `scp -O` is forbidden.
- Individual commands time out after 1,800 seconds.
- Commands run sequentially; no concurrency or bandwidth saturation load test
  is authorized.
- One 256-MiB upload is rate-limited to 8,192 Kbit/s and terminated after ten
  seconds to characterize SCP partial-file behavior. A conditional rsync
  resume counts the full 256 MiB conservatively even though only a suffix may
  cross the wire.
- Default cipher, compression, and SSH configuration remain unchanged except
  for the two registered `-C` comparisons.
- The wrapper records monotonic nanoseconds, process status, logical bytes,
  seconds, and effective MiB/s.

## Safety contract

- The script requires clean Git state before it creates execution artifacts.
- It refuses a pre-existing remote run name or output directory.
- It hashes after every upload and download.
- Recursive deletion is limited to validated agent-created local and remote
  names; `$HOME`, `~`, repository roots, and shared directories are forbidden.
- A command failure is evidence and aborts subsequent transfer cells; there is
  no invisible retry. The registered intentional interruption is the sole
  expected nonzero command and must return timeout status 124 with a partial
  size strictly between zero and the source size.
- The script attempts exact cleanup on failure, but a cleanup failure must be
  reported rather than concealed.
