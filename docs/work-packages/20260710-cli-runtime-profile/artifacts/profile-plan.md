# Profile Method

Evidence mode: Static

## Workloads

The profile deliberately contains the Jeogla pair only:

| Case | Rust benchmark median | Legacy benchmark median | Reason |
|---|---:|---:|---|
| `jeogla-au-seed0` | 0.109595 s | 0.101745 s | same station/mode, near-parity control |
| `jeogla-au-seed17` | 3.791807 s | 0.610949 s | seed-dependent runtime outlier |

Both entries come from the all-golden manifest at
`../20260710-cli-runtime-benchmark/artifacts/benchmark-cases.json` and
must hash to the pre-existing goldens after every profile execution.

## Measurement

- Five independent process runs per implementation/case with `perf stat`
  counters: `task-clock`, `cycles`, `instructions`, `branches`,
  `branch-misses`, `cache-misses`, `context-switches`, `cpu-migrations`,
  and `page-faults`.
- One `perf record -F 999 -g --call-graph dwarf` process per
  implementation/case, rendered to `perf report --stdio` with self-time
  symbol ordering.
- Output deletion/setup and hash verification are outside the timed
  process interval; the process itself includes its normal CLI interface,
  generation, and output write.
- Legacy compilation occurs only under `target/` and uses `-O3
  -ffp-contract=off -fprotect-parens -fno-fast-math`.

The profile is a sampling attribution, not proof of per-line cost. Rust
symbol names require release symbols to survive in the executable; when a
toolchain strips a name, the report records the available mapped symbol.
