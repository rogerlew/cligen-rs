# Review — Performance Arc (Benchmark, Profile, Fast-Batch Spike)

Date: 2026-07-10
Reviewer: Claude Code
Scope: `20260710-cli-runtime-benchmark`, `20260710-cli-runtime-profile`,
and `20260710-fast-batch-rng-spike` — packages, artifacts, and the new
code (`fast_batch.rs`, `profile.rs`, the `clgen`/`ranset` seam,
`SPEC-GENERATION-PROFILES.md`, the three `scripts/*.py` runners).
Evidence mode: **static** — read of the committed record and source;
no commands run by the reviewer. Numeric claims below cite the
packages' own Ran evidence.

Per the review convention: findings and evidence, disposition left to
the executor. Findings are ordered by severity. §Guidance at the end
is strategic direction requested by the operator, not a finding.

## What holds up

- Golden-SHA-256 preflight on **every** timed and profiled execution
  (24 profiled, 192 benchmarked on wepp1, 96+96 in the spike) —
  eliminates the benchmarked-divergent-work failure class outright.
  This should be standing policy for all future perf work.
- Measured-vs-inference labeling is disciplined throughout; the spike
  explicitly refuses bit/trajectory/stochastic-parity claims.
- The wepp1 cross-host run was a genuine falsification attempt and
  materially changed the picture (4.17× → 1.74× composite).
- Profile-boundary hygiene: default faithful, unknown values fail
  closed at parse, no implicit selection, mandatory
  `--generation-profile` header marker, faithful goldens still gated
  byte-identical.

## Findings

### F1 (High, strategic) — the spike attacks the wrong layer first

The profile package's own evidence: 60.15% + 5.86% of Rust seed-17
self time is `compiler_builtins::…::fma_fallback` — **software-emulated
FMA** inside the pinned `logf`/`cosf`, reached through `ranset`'s QC
loop (`profile-report.md` §Sampled call-graph). The same artifact's
legacy profile shows the reference binary executing `__logf_sse2` /
`__cosf_sse2` — glibc's **non-FMA** ifunc variants, because the host
CPU (Xeon E5-2697 v2, Ivy Bridge) has no FMA hardware.

There is therefore a cheap, faithful-preserving remedy candidate that
was neither attempted nor queued: **re-adjudicate plain-ops
(non-`mul_add`) variants of the pinned transcendentals against the
existing tap corpus** — the 26.4M-record logf/cosf capture and the 12
goldens already exist; the adjudication machinery already exists
(standard §1.3). Two outcomes, both decision-critical:

- **Pass** (bit-identical over the corpus + goldens): the seed-17
  pathology largely dies *inside faithful mode*. Bit-identity is the
  acceptance contract; the implementation beneath it is free.
  `fast_batch_v0`'s motivation shrinks accordingly.
- **Fail**: `mul_add` is load-bearing for fidelity on some inputs, the
  faithful cost on non-FMA hosts is the price of correctness, and the
  case for a fast profile strengthens — now with evidence.

Estimated cost: an afternoon. The spike, by contrast, now owes a
stochastic-parity campaign before it can be recommended for anything.

### F2 (High) — the 12.0× headline is host-confounded and conflates three effects

The spike's 12.0× composite (`benchmark-report.md`) was measured only
on the non-FMA host where the F1 pathology dominates. It bundles:
(a) avoided software-FMA work — possibly recoverable faithfully per
F1; (b) QC/retry avoidance — the actual behavioral change being
priced; (c) batch layout. The report says it does not isolate effects,
which is honest — but the decomposition it skips is exactly the
decision-relevant one. On wepp1 the *faithful* gap was already only
1.74× composite; the fast-batch matrix was never run there. The number
that should drive a go/no-go on the parity campaign — what QC-bypass
buys on FMA-capable production hardware against an F1-fixed baseline —
is unmeasured and plausibly nearer 2× than 12×.

### F3 (Medium) — the seam swap changes more than "no QC"; the spec understates it

Faithful `ranset` columns 5 and 9 are not i.i.d. uniform columns:

- Column 5 (precip amount, `j = 4`, `rng.rs:161-170`): zero on days the
  refill-time Markov chain calls dry, a fresh k5 uniform otherwise —
  driven by `RansetState.ell`, a **persistent** two-state chain that is
  coupled to, but can desynchronize from, `clgen`'s consuming chain
  (`bk7.l`). The source carries a band-aid for exactly that desync
  (`cligen.f:1253`, the `v7 == 0.0` redraw; `daily.rs:165-168`
  documents it).
- Column 9 (tpeak, `j = 8`, `rng.rs:174-183`): zero on dry days keyed
  off `ranary[4][i] > 0`, and **all zeros by construction under
  `iopt = 6`** (observed).

`fast_batch_v0` fills all nine columns with unconditional nonzero
uniforms (`fast_batch.rs::refill`). Consequences invisible to the
spike's structural checks: the band-aid path never fires; zero
partners never enter the `dstn1` rolling pairs on desynced wet days;
observed-mode column 9 becomes nonzero where faithful guarantees zero.
`SPEC-GENERATION-PROFILES.md` states "daily consumers keep their
existing parameter transforms and wet/dry decisions" — true (wetness
derives from column 1 vs `prw` under `bk7.l`) but incomplete: the
input distribution **on the consumed support** changes through at
least three mechanisms besides QC removal. These belong in the spec
now, and pre-registered as attention cells for any parity campaign —
not left for it to discover.

### F4 (Medium) — every composite is anchored to an uncharacterized workload

The 12-fixture matrix was designed for parity edge coverage, not
workload realism. Two burn-17 cells contribute ~67% of the faithful
composite gap (jeogla-17 alone is 3.79 s of 5.63 s). Uncharacterized:
what `-r` burns production wepppy actually issues, and whether
seed-17's QC-retry storm is a quirk of this burn×station pairing or a
generic tail. A one-hour characterization — wepppy's cligen
invocations, plus a burn sweep (r = 0..~50 per station, retry counts) —
would anchor every headline number in all three packages, and doubles
as the corpus-design input for the parity campaign.

### F5 (Low, batched)

- Single-storm rows (~2 ms) are process-spawn-dominated; they are
  evidence of tie in *process* cost, not generator speed.
- Seven unpinned samples on a shared 48-CPU host is adequate for the
  4-6× claims, marginal for the 1.1-1.4× cells. `taskset` + more
  samples next run costs nothing.
- The Rust seed-0 call graph has 140 samples; quoting "32.88%" FMA
  share at that count is false precision — one decimal is generous.
- `FastBatchState::from_seeds` funnels 40 seed words through a single
  u64 before lane expansion — 64 bits of effective state. Fine for a
  spike; a v1 should widen (e.g., four independent folds).
- Governance: the perf arc jumped the ratified A-series queue (A1 was
  head) with no recorded re-sequencing decision. Presumably
  operator-directed — the record should say so; ROADMAP should place
  this arc relative to A1/A2.

## Guidance — measuring stochastic parity without overthinking it

(Requested strategic direction; disposition still the executor's.)

**Reframe:** this is not validating a weather generator; it is
validating a **swap**. Faithful mode is a perfect oracle, sampled as
cheaply as desired. That makes parity a two-sample *equivalence*
problem over a declared statistics vector — one spec page, one script,
one package.

Refuse three traps: (1) significance testing at scale — the null is
false by construction (the profiles are different processes), so
two-sample p-values reject everything at large N; test equivalence
within declared bounds and report worst-case margins. (2) RNG-theory —
SplitMix64 quality is settled literature; cite and move on. (3) corpus
maximalism — the mechanism is station-independent; regime diversity
beats census coverage.

**Tolerance anchors already on the shelf**, descending authority:

1. **CLIGEN's own QC thresholds** (`cligen.f:4269-4332`): the K-S D
   bound and normal mean/variance CI bounds are the original authors'
   operational definition of an acceptable batch. Run the faithful QC
   tests *as a measurement* over fast-batch months; report the
   would-have-been-rejected rate (faithful = 0 by construction). One
   number, in the model's own currency, quantifying exactly what was
   removed. It also points at the pragmatic endgame: a
   `fast_batch_v1` that **reapplies QC batchwise** (cheap once dstn1
   isn't paying software FMA) gets QC-equivalent semantics and most of
   the parity argument for free.
2. **The .par quantization floor**: perturb one .par field by one
   quantum, measure the output-statistic delta — inter-profile
   differences below that scale are immaterial by construction.
3. **Consumer sensitivity, cited not rerun**: Srivastava et al. 2019
   (JSWC 74:334-349) for WEPP's response to database-scale deltas.

**Design:** corpus = 4 fixture stations + ~4 more .par for regime
spread (arid few-event, humid, cold, monsoonal; wepppy's collection)
× ~100 burns × 100 years × both profiles — embarrassingly parallel,
bounded hours on wepp1. Statistics vector per station×month: wet
fraction, P(W|W), P(W|D), wet-day amount mean/SD/skew,
tmax/tmin/rad/wind/tdew means+SDs, storm dur/tp/ip distributions; plus
per-run tails: annual precip, storm count, annual max daily P.
Pre-registered attention cells from F3: wet-day amounts (band-aid
mechanism), observed-mode tpeak, first-wet-day-of-month, short-month
slots. Gate: every cell inside its anchored bound → the claim is
"stochastically indistinguishable at the declared bounds for the
declared statistics" — never "equivalent" unqualified.

**Order of operations:** (1) F1 plain-ops re-adjudication — may
dissolve the motivation; (2) fast-batch matrix on wepp1 against the
F1-fixed baseline — price the real win; (3) only if it still matters,
build v1-with-batchwise-QC; (4) run the parity package against v1,
which is far easier to pass than v0. Reaching step 4 may never be
necessary — that is the good outcome, not a failure of the spike.
