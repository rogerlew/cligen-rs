# cligen-rs Roadmap

Status: living — forward-only queue. Completed items move to the
[work-package record](work-packages/README.md).

Ordering principles: **fixtures before port, faithful before native,
port before augmentation** (the port arc, complete) — and now, under
[ADR-0002](decisions/0002-quality-metrics-authority.md):
**instrument before adjudication, adjudication before promotion.**
No generation-behavior change is recommended before the quality
instrument has measured it at both the 30- and 100-year horizons.

The station-file schema version, station-model identifier, generation
profile, and typed-output schema version are independent compatibility
axes. A revision of one does not imply a revision of another.

## Active queue

**Operator direction 2026-07-15: continue stochastic climate-generator
development, retire the stopped A8c runtime first, and replace incremental
candidate rescue with a calibration-first successor family.** File/I/O,
openWEPP, WEPPcloud, PyO3, and other consumer-integration work remains deferred;
it is not a prerequisite for this research sequence.

**Operator direction 2026-07-16: execute A10 as one cohesive package per
planned milestone, `A10M0` through `A10M9`.** Ordinary iteration remains inside
its owning milestone package; a failed gate does not automatically create an
ad hoc suffixed rescue package. This supersedes the reviewed plan's original
single-package topology without changing milestone order, scientific rules,
or confirmation access.

The required A10M0 predecessor freeze completed on 2026-07-16 with
`A10M0-PREDECESSORS-FROZEN`. It hashed 20 governing authorities, hydrated and
replayed the A9d LFS evidence without changing its hold, preserved the
confirmation firewall, and froze A10M2's one-GPU-hour ceiling. Its accepted
record is the
[A10M0 work package](work-packages/20260716-a10m0-dispatch-predecessor-freeze/package.md).

A10M1 completed on 2026-07-17 with `A10M1-CORPUS-READY`. Its accepted v2
surface freezes 1,200 Daymet fit plus 240 tile-held validation locations across
six regimes and 351 nonleaking tiles, 24 eligible USCRN daily plus 14 event
stations, 32 inherited development objects, exact calendar/missingness and
fit-only normalization surfaces, and a 98-object / 223,799,545-byte offline
transfer manifest. The first Daymet selection remains explicit failed evidence:
its leakage audit found cross-frame role disagreement in boundary tiles, so v2
excluded all four ambiguous tiles and restored quotas from prepublished,
role-labeled surplus without reading values or reacquiring data. Confirmation
target access remained false. The accepted record and downstream restrictions
are in the
[A10M1 work package](work-packages/20260717-a10m1-corpus-role-freeze/package.md).
A10M1 and the later A10M2 completion now satisfy both A10M3 entry conditions.

The
[A10M2 Lemhi GPU integration and restartability readiness](work-packages/20260716-a10m2-lemhi-gpu-integration/package.md)
executed on 2026-07-16 and closed at `EXECUTED-HOLD-CUDA-ENVIRONMENT`.
It proved the supervised SSH path, I-CREWS-priority `gpu-icrews`
authorization, typed L40 allocation, driver/toolkit identity, and Ceph/XFS
storage split. Its first J1 exposed a login/compute module-registry mismatch;
after a published amendment, CUDA 12.8 `nvcc` reached but crashed its host
`gcc` by `SIGILL` and reported an unsupported host OS. The two attempts used
20 requested GPU-minutes and one second of actual allocation. The fail-closed
ladder correctly left J2--J4b unsubmitted and cleaned the exact remote run.

At that terminal, A10M3 was not authorized. The operator explicitly
authorized the
[A10M2D1 Lemhi CUDA drift diagnostic](work-packages/20260716-a10m2d1-lemhi-cuda-drift-diagnostic/package.md)
on 2026-07-16; it completed at `A10M2D1-ROOT-CAUSE-LOCALIZED`. One six-second
L40 job proved that `node03` is AMD EPYC without the tested AVX-512 features,
while the Intel login host defaults to a `linux-skylake_avx512` Spack GCC and
runtime. That ambient compiler and its login-built RPATH-bearing binary die by
`SIGILL` on `node03`; explicit OS GCC 8.5 and advertised GCC 11.2 both compile
and pass the unchanged CUDA 12.8 smoke from either build side. Compute-node
Lmod also still cannot resolve the login-visible CUDA module. The simplest
observed correction is direct CUDA 12.8 plus explicit `/usr/bin/g++`, pending
administrator support. A10M2 remains immutable; its corrective continuation
is recorded separately.

The operator authorized the
[A10M2D2 rmm-to-Lemhi SCP characterization](work-packages/20260716-a10m2d2-rmm-lemhi-scp-characterization/package.md),
which completed on 2026-07-16 at `A10M2D2-SCP-EXPECTATIONS-FROZEN`. All 27
registered integrity verdicts passed across 4.849 GiB of logical traffic with
exact cleanup and no Slurm/GPU use. Sustained warm-path rates were 10.054
MiB/s upload and 4.727 MiB/s download. A 1,024-file tree was 40.16 times slower
to upload and 14.14 times slower to download than its tar archive; A10 should
bundle small immutable objects. Interrupted SCP exposed an incomplete object
at its requested name, while the installed rsync pair resumed and verified it.
Routine single archives up to about 10 GiB are reasonable in the observed
window; about 50 GiB or larger warrants resumable or administrator-supported
managed transport investigation. The Globus CLI was absent and per-account
quota remained unproven, so neither finding may be inferred from shared Ceph
capacity. Later time-window replication and real artifact sizes remain
explicit follow-up rather than assumptions.

Stage 2 was the required forward M2 readiness gate: verify Ceph-to-job-local
staging, representative shard layout, bounded local read, durable-class
checkpoint copy-back, cache fallback, and exact local cleanup. The A10M2
completion satisfied it inside C1-02 using A10M1's full accepted manifest.
Every staged and copied-back object was hash verified. Its measured rates are
warm-cache diagnostics because the required durable hash pass preceded timed
copies; they are not cold-path or training-throughput claims.

The operator scaffolded and executed the bounded
[A10M2 completion package](work-packages/20260717-a10m2-completion/package.md)
on 2026-07-17. It closed at `A10M2-COMPUTE-READY` while preserving the
original A10M2 hold and D1/D2 evidence. It proved direct CUDA 12.8 with OS
GCC, hashed offline Python 3.8.11 / PyTorch 2.4.1+cu124 reconstruction,
one-L40 framework behavior, the full 98-object stage-2 path, two-L40
NCCL/DDP, and Slurm signal/checkpoint/manual-resume equivalence. Seven
allocations used 53 requested and 2.0167 actual GPU-minutes; the exact remote
run was removed after verified evidence retrieval. With A10M1 already ready,
the original A10M3 entry conditions were satisfied; the later operator
direction below adds two operational prerequisites. Confirmation access
remains prohibited.

**Operator direction 2026-07-17: insert an extensible Lemhi workflow toolkit
and a CPython 3.11 smoke gate before A10M3.** The required forward sequence is
now:

1. **Complete (2026-07-17):** execute the
   [A10 Lemhi toolkit foundation](work-packages/20260717-a10-lemhi-toolkit-foundation/package.md)
   against the authoritative
   [toolkit specification](specifications/SPEC-LEMHI-AGENT-TOOLKIT.md);
2. **Complete (2026-07-17):** the
   [CPython 3.11 Lemhi smoke package](work-packages/20260717-a10-lemhi-python311-smoke/package.md)
   uses the toolkit, a pinned Linux x86-64 runtime, offline dependency
   reconstruction including NumPy, and a bounded one-L40 validation, and
   reached `A10-LEMHI-PY311-SMOKE-READY`; and
3. **Complete (2026-07-17):** A10M3 reached `A10M3-DESIGN-FROZEN` after
   binding
   canonical configuration `lemhi-a10-py311-l40-v1` and semantic SHA-256
   `0b1115a6801259c62d9550c877a3c49a897319348ba1c2027be0d9c4f77c1179`
   under
   [SPEC-LEMHI-CANONICAL-CONFIGURATION](specifications/SPEC-LEMHI-CANONICAL-CONFIGURATION.md).

This ordering does not revoke `A10M1-CORPUS-READY` or
`A10M2-COMPUTE-READY`; it adds operational prerequisites before the scientific
milestone. Foundation execution reached `LEMHI-TOOLKIT-FOUNDATION-READY` using
deterministic local fixtures and a recording command adapter; it performed no
remote write or allocation. The smoke package subsequently authenticated 19
CPython, standard-library, native-linkage, NumPy, PyTorch, CUDA, one-L40,
offline-install, and cleanup gates under the toolkit. Its three single-attempt
runs used 60 requested and 4.75 actual GPU-minutes; the first two are retained
harness failures, and the final run passed in 100 seconds. All exact remote
roots were removed. A10M3 subsequently froze the research model, fit,
generation, benchmark, selector, and 560-L40-GPU-hour ceiling without a cluster
allocation or candidate/confirmation access. The accepted stack is the current
canonical A10 Lemhi single-L40 Python configuration; A10M2's Python 3.8 stack
is legacy explicit-only and cannot be selected automatically.

**Complete (2026-07-17):** A10M4 reached
`A10M4-QUALIFICATION-READY` after a bounded one-L40 qualification of the real
A10M1 loader, the smallest frozen N0 configuration, exact checkpoint/restart,
stateless nested generation, portable CPU export, the full 12-row benchmark,
and cleanup. The successful job passed all 20 structured gates in 628 seconds.
Ten qualification allocations plus one recovery allocation used 1,205
requested GPU-minutes and 48.62 elapsed single-GPU minutes, within the
40-GPU-hour ceiling. All failed implementation hypotheses and prospective
amendments remain in the
[A10M4 package](work-packages/20260717-a10m4-one-l40-qualification/package.md).
No development or confirmation target series was read, no fitted weights were
retained, and the diagnostic timing ratios received no selector classification.

**Complete (2026-07-17):**
[A10M4O1 operational hardening](work-packages/20260717-a10m4o1-lemhi-operational-hardening/package.md)
reached `A10M4O1-TOOLKIT-HARDENED` through local injected fixtures with no
remote action or allocation. Toolkit revision 2 now freezes an all-v2
provider/record stack, complete native toolchain closure, `--export=NONE`
deterministic environments, toolkit-recoverable job-local supervision and
reserved recovery, raw-before-projection evidence, immutable authority
revisions with ledger checkpoints and pre-spend accounting reconciliation,
integer transfer telemetry, and append-only within-run asset manifests. All 23
historical foundation tests and 21 hardening tests pass. Canonical v1 remains
byte-immutable status-at-issuance history.

The package published immutable successor semantics
`lemhi-a10-py311-l40-v2-candidate` at SHA-256
`5addee9c5db3592ee247eab2b5266ed5567fd9aaf24ed78dcb321ecbb001e22d`.
It created no smoke attestation or designation. The frozen 5x/10x runtime
criteria remain unchanged and require a separate prospective scientific
decision.

**Hold (2026-07-17):** the bounded
[canonical-v2 smoke package](work-packages/20260717-a10-lemhi-canonical-v2-smoke/package.md)
reached `HOLD-A10-CANONICAL-V2-SMOKE-ENVIRONMENT-CLOSURE`. Its one authorized
primary allocation failed before job-local root creation or Python import:
Slurm `--export=NONE` still presented at least one prohibited ambient
Python/loader variable, so the entry guard failed closed. A separately
reserved exact-node recovery allocation proved `JOB_LOCAL_ABSENT`; both jobs
settled and the marker-bound durable root was removed. The candidate remained
immutable and no smoke attestation or designation was created.

**Active (2026-07-17):** the
[environment-closure successor smoke](work-packages/20260717-a10-lemhi-canonical-v2-environment-closure-smoke/package.md)
uses a new identity with the unchanged candidate. It records typed ambient
presence flags, clears prohibited state, reconstructs the registered
environment, and asserts closure before import. It also closes the demonstrated
executable-mode, terminal-failure-receipt, and pre-submission-abort protocol
gaps. The required sequence remains candidate smoke, immutable smoke
attestation, local canonical-designation-index revision, then A10M5.

After a successor canonical smoke pass, A10M5 may scaffold the
frozen 12-configuration, one-seed development screen and bounded promotions
under the unchanged A10M3 scientific contracts. It remains development-only,
may use at most two concurrent one-L40 jobs and the frozen 160 + 280
L40-GPU-hour M5 envelopes, and may not access confirmation targets.

A9d completed on 2026-07-15 with
`HOLD-A9D-NO-SELECTABLE-CANDIDATE` in one successor-development/conditional-
confirmation package. Eighteen fresh configurations entered an 18/4/2 staged
development funnel on the prospectively accepted 92-cell surface. Both model
classes fit and remained structurally distinct; all 720 strict short-prefix
context audits passed. The renewal and latent replay finalists nevertheless
retained three and 17 material-degradation rows, respectively, so the unchanged
selector sealed no candidate. No confirmation target series was accessed and
the conditional confirmation was not run. The accepted record is in the
[A9d work package](work-packages/20260715-a9d-successor-development-confirmation/package.md)
and [public report](reports/a9d-successor-development-confirmation-report.md).

A9a completed on 2026-07-15 with `FOUNDATION-READY-A9B`. It froze a joint
occurrence/amount/event/context family envelope, two structurally distinct
research class slots, optimizer-neutral fit and tuning contracts, a
31-objective registry, six-regime applicability, an exact metadata-only
18-site USCRN confirmation roster, a development/confirmation firewall, and 20
synthetic/adverse fixture groups. It selected no candidate, accessed no
confirmation target, and changed no production runtime. The accepted record is
in the [A9a work package](work-packages/20260715-a9a-successor-family-foundation/package.md).

A9c completed on 2026-07-15 with
`HOLD-A9C-GATE-CALIBRATION`. It materialized 64 normalized observed role
objects, 180 exact USCRN station-year identities, and 7,000 candidate-blind
null replicates without confirmation access. Its hot-arid development sites
had 136 and 97 events, leaving 0/2 available stations for mandatory storm
time-to-peak, peak-ratio, and joint-dependence objectives. Five fits completed,
but no development score or candidate ranking was accessed. The accepted
record is in the
[A9c work package](work-packages/20260715-a9c-observed-development/package.md).

Post-acceptance operator disposition retains that terminal and arithmetic but
corrects the follow-on interpretation: the 150/200 station floors were
prospective design choices, not empirically calibrated minimum sample sizes
for sparse hot-arid sites. The A9c report is revised to revision 2. This does
not retroactively pass a cell, rank a candidate, or alter A9a/A9b history.

A9b completed on 2026-07-15 with
`HARNESS-READY-A9C`. Its
[accepted package](work-packages/20260715-a9b-calibration-harness/package.md)
implements and independently replays the synthetic-only research harness:
strict schemas/canonical hashes, immutable fits, the data-role firewall,
hash-chained one-shot access, Philox random fields, two structurally distinct
mock plugins, monthly/objective/null/Pareto machinery, bounded append-only
optimization, and FX-001--FX-020. It accessed no observed target, ranked no
candidate, and changed no production runtime.

Its context-complete boundary is frozen in the
[A9c handoff](work-packages/20260715-a9b-calibration-harness/artifacts/a9c-handoff.md).

The [A9c2 grouped hot-arid re-entry](work-packages/20260715-a9c2-grouped-hot-arid-reentry/package.md)
completed on 2026-07-15 with `HOLD-A9C2-HOT-ARID-ROSTER`. Its prospectively
frozen metadata census reduced 255 station-listing rows to 113 active,
operational, cutoff-eligible USCRN sites. Only Yuma, Stovepipe Wells, and
Mercury matched the exact A8a hot-arid descriptor screen; Mercury is a locked
confirmation station, leaving two accepted development sites against five
required. No station series, candidate output, or confirmation target series
was accessed, so grouped calibration and the fresh model comparison were not
reached. The accepted result is also documented in the
[A9c2 public report](reports/a9c2-hot-arid-roster-feasibility-report.md).

The predecessor completeness package is the
[A9c4 completeness correction](work-packages/20260715-a9c4-context-support-completeness/package.md)
completed on 2026-07-15 with `HOLD-A9C4-COMPLETENESS-SURFACE`. Its pre-output
audit retained 92 of 111 originally applicable mandatory 30-year cells: 68
non-storm cells through observed/faithful common support and 24 storm cells
through the inherited grouped policy. The other 19 lacked the required two
observed contributors. Wet amount and compound context consequently failed
the frozen breadth guard in arid-boundary, hot-arid, and monsoonal-transition
regimes. No corrected fit, output, evaluation, or candidate freeze occurred.
The accepted result is documented in the
[A9c4 public report](reports/a9c4-context-support-completeness-report.md).

A9d prospectively chose to accept A9c4's 92-cell surface with its explicit
limits and tested the already specified bounded context laws without adding a
selector or model class. This preserves A9c4's terminal and H1 while resolving
its successor choice. The earlier prerequisite-only A9d draft was an
uncommitted administrative detour and was superseded by the operator's direct
one-package dispatch; it is not an immutable package record or catalog item.

A9c3 completed on 2026-07-15 with
`HOLD-A9C3-NO-SELECTABLE-CANDIDATE`. Its equal-weight Yuma/Stovepipe estimator
was finite at the actual 136/97 event frequencies, and four renewal plus two
latent configurations entered the short screen. Every one of 240 candidate
site/burn prefixes violated physical support, so zero configurations advanced
to full development or Pareto replay and no candidate was sealed. The accepted
record is in the
[A9c3 work package](work-packages/20260715-a9c3-two-site-grouped-observed-comparison/package.md)
and [public report](reports/a9c3-two-site-grouped-observed-comparison-report.md).

A9e Rust runtime work remains unscaffolded because no successor candidate was
selected or sealed. A9 does
not inherit an A8c candidate, coefficient, threshold, station classification,
or confirmation claim. ADR-0002 requires separately roadmapped downstream
evidence for any future extension-quality or production decision. ADR-0004
continues to prohibit promotion or post-hoc rescue of the evaluated A5b
candidates; it does not govern every successor. The present sequence neither
performs nor waives openWEPP/WEPPcloud integration.

**Operator correction 2026-07-14: stop the selector/count-construction
escalation and return to the model question left open by A5c.** The A5d0-A5d1b
complete-year selector branch is closed as exploratory evidence rather than a
production prerequisite. A5d1c and the unscaffolded A5d2-A5d5 roadmap items are
cancelled, and their identifiers will not be reused. Useful evaluation and
corpus concepts may be proposed afresh only after a development candidate earns
continuation. The immutable A5d0-A5d1b records retain their evidence and
outcome-time recommendations, but this operator direction supersedes those
recommendations.

There is no active A7 item. A7b completed the prospective analytic comparison
and returned `STOP-PRECIPITATION-LINE`. Review showed that its second-order and
two-phase semi-Markov candidates are two parameterizations of the same
four-state binary process, not independent model classes. Both registered
parameterizations cleared the 184-cell corpus-breadth floor with 192/204
feasible cells, but each reached only 31/36 mandatory dry/cold/wet development
cells rather than the required 36/36. Death Valley supplied all five
development failures: its JJA season lacked the registered adjacent-wet-pair
and long-wet-state exposure, and its April and December cells exceeded the
frozen normalized-tail-error bound. No mechanism was selected.

The conditional A7c integrated pilot and A7d corpus confirmation are removed
from the queue, remain unscaffolded, and are not authorized. Relaxing A7b's
prospective gates or choosing the higher-ranked near miss would convert a stop
rule into outcome-time selection, so this roadmap does neither. Any future
precipitation proposal requires a new operator roadmap and package identifier;
it must explain how the arid-station identifiability boundary is handled
without post-generation repair, fixed-count search, or unregistered data
pooling. The accepted A7 record is retained in the
[A7a work package](work-packages/20260714-a7a-daily-precipitation-structure-baseline/package.md),
[A7a public report](reports/a7a-daily-precipitation-structure-report.md), and
[A7b work package](work-packages/20260714-a7b-analytic-precipitation-feasibility/package.md).

The scientific A8 generation line remains closed: A8c completed with
`STOP-A8-ROUTED-DAILY`, A7b's whole-domain stop remains final, and no A8d
confirmation is authorized.

A8c1 completed the unshipped-runtime retirement on 2026-07-15. It removed the
`a8c_routed_daily_v1` profile, revision-2 routed station input, model-specific
generation, provenance, quality, schema, and test surfaces while restoring the
shared runtime to its pre-A8c shape. The exact A7/A8 scientific record, A8c LFS
archive, and historical implementation commit remain verifiable. This was
retirement hygiene, not scientific continuation or reinterpretation of the A8c
stop.

A8a completed on 2026-07-15 with `CONTINUE-A8B-DRY-PARTITION`. Its prospective
20-station confirmation found 15 `integrated_daily` and five
`legacy_daily_fallback` classifications, reproduced all eight development
dispositions, integrated all four negative controls, reached 0.850
shortened-window agreement, and passed all analytic and terminal guards.
Monsoonal and other-dry instability were both 0.1875, so A8a does not justify a
separate monsoonal campaign. The accepted record is retained in the
[A8a work package](work-packages/20260715-a8a-dry-regime-applicability/package.md).

A8b completed on 2026-07-15 with `USE-LEGACY-DAILY-FALLBACK`. Its exact pooled
two-EOF/AR(1) candidate failed before coefficients because the frozen
1980--2009 El Centro June-total scale is exactly zero; A8b did not drop or
repair the cell and opened no replacement search. The explicit null certified,
so boundary stations retain legacy daily behavior with no secondary year state
or additional RNG. The accepted record is retained in the
[A8b work package](work-packages/20260715-a8b-secondary-year-fallback/package.md).

A8c's explicit six-station routed pilot completed on 2026-07-15. All replay,
nested-horizon, fallback, provenance, and faithful-regression checks passed,
and both registered daily target families improved at both horizons. The
candidate stopped because wet-amount means missed the monthly budget broadly,
integrated time-to-peak medians collapsed to zero, and changing precipitation
occurrence propagated through CLIGEN's wet/dry-conditioned Boise dew-point and
Alamosa wind-speed paths. These are model-structure results, not a fallback or
runtime hold. The exact record is retained in the
[A8c work package](work-packages/20260715-a8c-routed-daily-pilot/package.md).

No A8d confirmation, WEPP response study, threshold relaxation, coefficient
retuning, or public-default change follows. A9 is the separately roadmapped
new family: before implementation it must jointly specify wet-amount
calibration, precipitation-conditioned downstream variables, and storm
time-to-peak semantics rather than treating them as post-generation guards.

Monsoonal climates were a mandatory stratum in A8c. Their
annual precipitation alone is not a safe routing variable: seasonal
concentration can leave dry-season occurrence states weakly identified even
when annual totals appear adequate. A8a found no excess monsoonal instability,
so a separate sequence would duplicate corpus, routing, and fallback work and
is not roadmapped.

A5f0 supplied the pivot into this queue. Its derived-only attribution returned
`RETIRE-SCALAR-IID-MECHANISM` for the exact
`a5e0_direct_annual_state_v1` mechanism and
`a5e0_direct_monthly_loading_fit_v1` recipe. Cross-month dependence supplied
70.6% and 67.9% of positive H1-family degradation at 30 and 100 years, one
component represented only 11.9–16.5% of fit-period annual-feature variance,
and all 96 active loadings responded with the expected sign (global median
realized/expected slope ratio 0.994). No one parameter seam met the frozen
five-of-six localization rule. The disposition is descriptive on the exposed
three-station development surface; it is not causal proof and does not reject
annual-state models generally.

A5f1 then retired the unshipped A5e0 runtime from current `main`: crates.io has
no `cligen` crate, repository releases predate A5e0, and the exact historical
implementation remains reachable at `1ca40bb`. The closed specification,
schemas, report, and work-package evidence remain in place; no accepted public
interface or faithful behavior changed.

A5e0 remains immutably retained with status
`EXECUTED-HOLD-PROSPECTIVE-BOUNDARY`: its specification, implementation, and
analyzer were not bound at the claimed prospective boundary, so A5f0 does not
retroactively ratify its climate decision. No default or public interface
changed.

The conditional A5e1 expansion is removed from the queue and remains
unscaffolded and unauthorized. A5f0 found no basis for a bounded seam ablation,
so no repair or clean-reproduction chain follows. A7a measured the published
competing explanation that daily precipitation structure contributes to the
aggregate deficit; A7b then found no registered mechanism feasible across the
complete development surface. A7 was not an A5 repair and did not inherit an
A5 candidate.

Exact per-output gates are limited to engineering invariants: faithful-mode
identity, deterministic replay and provenance, fail-closed inputs, valid
calendars and values, and the same-seed 30-year output being the prefix of its
100-year output. Climate moments, dependence, storm descriptors, and winter
behavior are ensemble evaluation targets. Exact finite-path marginal replay,
nested optimized counts, path annealing, and all-station/all-seed climate gates
are not production requirements.

A7c and A7d are closed, unscaffolded conditional concepts rather than active
roadmap items because A7b did not select a mechanism. Wet/dry-conditioned
radiation, full subdaily forcing, external storm benchmarking, and
multisite/spatial generation remain later studies.
Single-storm generation remains deprecated.

The closed selector exploration remains in the work-package catalog:
[A5d0](work-packages/20260714-a5d0-successor-feasibility-calibration/package.md),
[A5d1](work-packages/20260714-a5d1-selector-feasibility/package.md), and
[A5d1b](work-packages/20260714-a5d1b-finite-path-realization/package.md), and
[A5e0](work-packages/20260714-a5e0-direct-annual-state-pilot/package.md), with
the derived disposition in
[A5f0](work-packages/20260714-a5f0-annual-state-failure-attribution/package.md).
The selector branch's stationary-weight result and finite-path failures remain
useful evidence, but its count-search holds do not govern the A5e0
evidence-boundary disposition or A5f0's mechanism-specific retirement.

The A5a–A5c sequence is complete. **A5c executed** (2026-07-14,
[`20260714-a5c-interannual-profile-adjudication`](work-packages/20260714-a5c-interannual-profile-adjudication/package.md))
and accepted [ADR-0004](decisions/0004-a5b-interannual-no-promotion.md): none
of the seven independently versioned A5b candidates passed all climate gates
at both horizons, so no public station model or generation profile was
promoted. The evidence is exploratory for model selection and may support the
conservative rejection only. `faithful_5_32_3` remains the default; station
schema, station model, generation profile, provenance, and output versions
remain independent and unchanged. Any successor considered for promotion
requires a new prospective study with analytic feasibility, monthly variance
reallocation, integrated daily precipitation structure, prospectively
calibrated guards, and complete downstream evidence.

The preceding quality arc (ADR-0002, Q1-Q4) is complete. Both closing
adjudications were ratified by the operator on 2026-07-10 on the R1-amended
record: **ADR-0003 Accepted** (`qc_filter` user-facing, default `faithful`,
`off` a considered opt-in for 100-year variance-priority runs) and **the
fast-batch line retired** (SPEC-FAST-BATCH-V1 → RETIRED; reopening condition
pinned).

The closed arc:

- **Q3 executed** (2026-07-10,
  [`20260710-q3-qc-filter-dissection`](work-packages/20260710-q3-qc-filter-dissection/package.md)):
  `qc_filter: faithful | off` implemented (SPEC-RUNSPEC rev 5;
  metrics_version 2 counterfactuals); the ratified 102-run dissection
  quantified the frontier — ~52% of unconditioned batches fail the
  QC verdicts in every regime (faithful's actual discard cost is far
  larger where it retries), the convergence buy is real with an
  estimator-sensitive horizon profile (R1-corrected), the
  interannual-variability cost is material at both horizons and
  farther from observed climate on 15/17 stations (single-burn Daymet;
  detrended 14/17, GHCN 6/8), and conditioning is the dominant
  generation cost (1.70× median / 8.8× corpus total).
  **ADR-0003 Accepted** (operator, 2026-07-10, on the R1-amended
  draft: user-facing, default `faithful`, `off` a considered opt-in
  for 100-yr variance-priority runs).
- **Q4 executed** (2026-07-10,
  [`20260710-q4-fast-batch-adjudication`](work-packages/20260710-q4-fast-batch-adjudication/package.md)):
  same-instrument comparison against the qc_off re-baseline: quality
  legs pass (the batch line is equivalent, not better); the
  performance leg was not evaluable as pre-registered (R1 finding 2;
  observed end-to-end gain 1.32× on this host). **Retirement
  ratified** (operator, 2026-07-10) as a portfolio decision with a
  pinned reopening condition.

Dependencies are real, not ceremonial: Q1 (complete) is the
instrument every later item reports through; Q2 (complete) supplies
the regime corpus (and the packaging substrate) Q3/Q4 adjudicate
over; Q3's qc_off re-baseline is the denominator of Q4's performance
case.

**Q2 (station databases + deployability) is complete** (2026-07-10,
[`20260710-q2-station-db`](work-packages/20260710-q2-station-db/package.md)):
the five production collections (us-legacy, us-2015, ghcn-intl, au,
chile) ship as hash-pinned GitHub-release payloads outside the crate
(SPEC-STATION-DB rev 1); `cligen stations sync` is the only
network-touching operation; `nearest` reproduces an independent
oracle across all collections; a fresh install → sync → run
round-trip reproduces the goldens byte-identically through the
cache; `cargo publish --dry-run` is clean at 163.5 KiB. The repo went
public same-day: tokenless `sync` verified for all five collections
(`CLIGEN_SYNC_TOKEN` remains supported but is no longer required).
Addendum: au payload revised to 2026.07.1 — longitudes corrected to
east-positive at the source (pars + catalog, jimf-cligen532
`ddfa671d`), operator-directed
([addendum](work-packages/20260710-q2-station-db/artifacts/au-longitude-correction.md)).

**Q1 (quality-report instrument) is complete** (2026-07-10,
[`20260710-q1-quality-report`](work-packages/20260710-q1-quality-report/package.md)):
every `cligen run` emits a `*.cli.quality.json` sidecar (groups A-D +
group P process metrics, per-decade blocks, byte-deterministic;
SPEC-QUALITY-REPORT active rev 4 with published JSON Schema), and
`cligen quality <file.cli> --par <file.par>` measures any WEPP-format
`.cli` post hoc — legacy-Fortran output included. Faithful golden
byte identity was untouched throughout.

## Other deferred augmentations

These remain outside the active A7 precipitation sequence and may reorder on
operator direction. Each lands behind a versioned profile or specification.

| # | Item | Mechanism | Acceptance |
|---|---|---|---|
| A2 | **Native f64 mode** | Uniform-f64 engine; measured faithful↔native divergence characterization; the idiomatic destination architecture (faithful modules graduate to executable spec) | Divergence documented per variable; profile `native-f64-v1`; quality report ≥ faithful on groups A/B |
| A3 | **Observed parquet input + single-pass substitution + leap-year imputation** (SPEC-OBSERVED-INPUT) | f64 parquet observed series; variable replacement in one pass; leap-day handling | Spec + fixtures; kills the flatfile→wepppyo3→flatfile round-trip |
| A4b | **Station mutation and localization utilities** | Provenance-stamped PRISM localization, future-climate deltas, and mean/CV scaling against the modern station schema; no mutation operation selects generation behavior. | Every mutation is explicit and deterministic, carries complete lineage into output provenance, and produces a schema-valid declared station model. |
| A6 | **PyO3 surface** (SPEC-PYO3) | Python bindings, Arrow zero-copy hand-off | wepppy consumes without flatfiles |

**The faithful-mode port (items 1-8) is complete** (2026-07-09,
`20260709-output-cli-port`): `cligen run` on the 12 golden runspecs
reproduces the golden `.cli` files byte-identically. Faithful mode is
now ADR-0002 scaffolding: frozen, gated, carrying the ablation
platform for Q3 and the compatibility bridge — with its retirement
condition on record.
