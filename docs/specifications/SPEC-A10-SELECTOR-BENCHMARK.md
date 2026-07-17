# A10 Candidate Selector and Generation Benchmark

Status: research-only

Revision: 1 (A10M3, 2026-07-17)

## Surface and authority

This specification freezes A10 development scoring, applicability, runtime
classification, and selection before a neural candidate exists. Producers are
the A10M5 evaluators; the A10M6 selector is the consumer. A selector result may
nominate at most one exact candidate for A10M7 sealing. It does not itself
seal or promote a runtime.

The normative evidence envelope is
[`a10-selector-evidence-v1.schema.json`](a10-selector-evidence-v1.schema.json).

## Comparator and objective identities

`B0` is faithful CLIGEN `faithful_5_32_3`. `B1` is the accepted A9d renewal
comparator `renewal-p010-q090` on inherited common cells only. Missing B1 cells
are unavailable and can never count as improvement. An expanded-panel refit is
a new comparator identity and cannot silently replace B1.

The primary score uses the mandatory non-engineering objectives in the A9
objective registry. Each objective is standardized by its frozen paired-null
family/horizon scale; objectives are averaged within family and the seven
families receive equal weight. Missing required cells fail the regime rather
than receiving a favorable value.

For comparator `b`, `D_b = score(candidate) - score(b)`. A regime is applicable
only when both 30- and 100-year evidence has `D_B0 <= -0.10` and
`D_B1 <= -0.10`, each paired 95% upper confidence bound is at most zero, and
all four guard groups are noninferior to both baselines. The guards are
occurrence/spells, aggregate/extreme precipitation, compound context, and
winter proxies. Unavailable guard evidence fails applicability.

At least four of six regimes must pass, including at least one of the four dry
regimes and at least one of humid or cold. Unsupported regimes remain explicit
faithful fallback cells and cannot increase breadth.

## Generation benchmark

The representative workload contains one frozen inherited development station
per regime and nested 30/100-year streams. The normative host is a Lemhi
`gpu-icrews` allocated L40 compute node with the GPU hidden for CPU timing;
`rmm` (macOS arm64, Apple M1, 16 GB) is the untimed controller. Candidate
portable CPU export and release faithful Rust run in the same allocation on one
physical core, fixed affinity, and identical thread environment. The exact
node, CPU, OS, runtime, and affinity are captured per run. Model load,
conditioning, and state initialization complete before the warm timer; no RNG
draw, state transition, or requested output may occur before it.

There are at least two warmups followed by nine alternating timed samples per
station, horizon, and implementation. A timed sample repeats the workload
without changing its logical streams until at least one second has elapsed.
Contaminated trials are discarded with a reason; more than two discarded
trials fail the benchmark. Excess dispersion (MAD/median above 0.10) triggers
exactly one deterministic rerun; a second failure is terminal.

`R_gen` and every regime/horizon ratio use unrounded median warm time. Ratios
below 5 are `PASS`; exactly 5 through below 10 are `WARN`; exactly 10 and above
are `FAIL`. A `FAIL`, GPU requirement, nondeterminism, incomplete output, CPU
export absence, 30-year warm time above 10 seconds/station, 100-year warm time
above 30 seconds/station, peak RSS above 2 GiB, or export above 250 MiB rejects
the candidate. Cold start is separately reported and fails its own 15-second
absolute safeguard; it never receives the 5x/10x label.

## Selection order and fail-closed behavior

Reject hard engineering, provenance, firewall, completeness, or runtime
failures first. Then reject insufficient applicability. Survivors order by:
applicable breadth descending; primary score ascending; `PASS` before `WARN`;
training-seed standard deviation ascending; exact runtime ratio ascending;
model bytes ascending; stable candidate ID ascending. No evidence or tie-break
may be invented after scored output.

The executable reference arithmetic is
[`research/a10/m3_contract.py`](../../research/a10/m3_contract.py). Unknown
keys, identities, horizons, regimes, comparator sets, non-finite numbers, and
missing values are errors unless this specification explicitly defines the
value as an applicability failure.
