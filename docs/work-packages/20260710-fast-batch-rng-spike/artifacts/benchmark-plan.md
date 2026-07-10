# Fast Batch RNG Benchmark Plan

## Question

How much process-level CLI time is attributable to the faithful monthly
`ranset` QC/retry protocol on the existing 12-workload matrix?

## Compared profiles

- `faithful_5_32_3`: the default, golden-checked Rust execution.
- `fast_batch_v0`: a deterministic extension that fills the same 9×31
  monthly uniform matrix with a four-lane batch PRNG and does not execute
  `ranset` QC/retry logic.

This is a profile comparison, not a comparison against legacy output: the
fast profile is intentionally divergent and must declare itself in the CLI
header command line.

## Method

- Build the release `cligen` binary once.
- Use the existing benchmark manifest's 12 runspecs.
- For each case, make an ephemeral fast-profile runspec with an absolute
  target output path; retain the original runspec for faithful samples.
- Run one warm-up and seven alternating samples of each profile.
- Faithful samples must match the named golden SHA-256. Fast samples must
  exist, be nonempty UTF-8 CLI text, carry `--generation-profile
  fast-batch-v0`, contain the expected CLI column header, and have finite
  numeric daily rows.
- Record raw samples, binary/source/manifest hashes, profile outputs, and
  host metadata in JSON and CSV.

## Interpretation guardrail

The result measures the combined effect of the batch PRNG and bypassing
source QC retries. It must not be attributed to hardware SIMD alone, or used
as stochastic-parity evidence.
