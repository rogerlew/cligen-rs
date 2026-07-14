# A5b Pre-Output Amendments

Candidate output did not exist when the amendments below were made. These
changes are part of the prospective freeze and cannot be applied to an
already-inspected candidate matrix.

## 2026-07-13 -- offline schema registry

The first production matrix attempt was interrupted during its read-only
952-plan preflight, before target creation, after `jsonschema` warned that the
augmented-station schema's relative base-schema reference could be retrieved
automatically from its mutable public URL. The fitter and independent evidence
verifier already used the frozen local base schema, but the matrix runner did
not. No plan, trajectory, report, archive, or manifest from that attempt was
retained; the earlier freeze and fit directory were removed before correction.

The runner now registers every root schema by its frozen `$id`, registers the
local fixed-monthly station schema under both its declared `$id` and the exact
URI obtained by resolving the augmented schema's relative reference, registers
the local provenance-v1 schema at the exact URI obtained by resolving the
quality schema's relative reference, and performs no automatic remote
retrieval. The base-station schema is a separate run-record/evidence contract
and prospective-freeze input rather than an implicit dependency. Both local
dependencies are prospective-freeze inputs. Self-tests make URL access fatal
and traverse each external reference to prove the registry is closed before
the replacement freeze and fit are produced.

The first replacement production matrix completed all 272 shared faithful
bases, then failed closed before publishing any candidate output when its first
quality-report validation traversed the still-unregistered relative
`provenance-v1.schema.json` reference. Transactional rollback removed the
target and no climate, report, plan, archive, or manifest from that execution
was retained. The replacement freeze and fit directory were removed again;
the already-frozen local provenance schema registration and missing self-test
traversal will be admitted only through the next prospective freeze.

## 2026-07-13 -- experimental lineage boundary

The public A1 provenance, station, runspec, and typed-output vocabularies are
closed to the fixed-monthly model and cannot truthfully encode seven A5b
spikes. SPEC-A5-EVALUATION revision 3 therefore uses unchanged post-hoc
envelope-2/metrics-3 reports plus the separately versioned A5b run record.
A5c, not A5b, owns public integration of a selected model.

## 2026-07-13 -- HMM EM roundoff tolerance

The first production-fit attempt stopped before writing its output directory
when one station's scaled forward/backward EM likelihood changed by
`-6.8128144903312204e-08`. This is numerical jitter at roughly the requested
convergence scale, not evidence of a substantive downhill EM step. The
prospective contract now records changes in `[-1e-7,0)` as a roundoff
intervention and treats them as zero improvement; changes below `-1e-7`
remain fatal. The failed temporary fit was removed by the fitter and no
coefficient bundle, climate trajectory, report, or candidate statistic from
it was retained.

The next fit attempt also stopped without output when a different station's
raw likelihood decreased by `-0.00019884054273688889`. Review identified a
contract error: the frozen add-0.5 transition smoothing is a penalized EM
step, so raw likelihood is not its monotone objective. The contract now tests
`raw_log_likelihood + 0.5*sum(log(transition_probability))`, reports raw
likelihood separately, and applies the same roundoff/fatal thresholds to the
matching penalized objective. No bytes from the failed attempt were retained.

A subsequent pre-freeze fit process reported a repeated-fit byte mismatch for
the first station while the fitter contract was still being revised. It
published no output. With the current script identity held fixed, twenty
complete fits of that real station produced one unique bundle/details hash.
The production fitter now snapshots and rechecks its own bytes, both station
schemas, the frozen A5a configuration/manifests, and the release generator
after every station and immediately before publication. A mutable fit process
therefore fails closed instead of being attributed to numerical behavior.

## 2026-07-13 -- pinned spectral DFT

A later independent pre-freeze audit ran the production fitter only into a
temporary directory under `target/`. It stopped and removed that directory
when the two repeated fits of `az029654` differed. Twenty focused repetitions
produced two exact bundle outcomes, thirteen and seven times respectively.
The only coefficient differences were one-ULP changes in the
`spectral_random_phase` amplitudes produced by repeated `numpy.fft.rfft`
calls; the largest absolute difference was
`1.7763568394002505e-15`. The differing amplitudes changed their payload and
fit-identity hashes, so tolerating the difference would have violated the
byte-repeat gate.

The spectral fit now uses a frozen explicit 30-point real DFT: chronological
`fsum` reductions for real and imaginary terms at frequencies 1--14, an
exactly specified alternating real sum at the Nyquist frequency, and no DFT
normalization. The fitter self-test pins the resulting coefficient bytes,
rejects a wrong year count and zero training variance, verifies the Nyquist
normalization, and repeats the explicit transform 65 times. No coefficient
bundle or candidate trajectory from the failed temporary attempt was
retained.

## 2026-07-13 -- accepted corpus regime vocabulary

Independent runner and verifier implementation found that the accepted A5a
corpus labels `id106388` with regime `fixture`, while the draft A5b run and
evidence schemas omitted that existing label. Both schemas now admit
`fixture` and the runner preserves the exact corpus value. The five-site WEPP
snow/cold domain remains selected by its frozen station-ID list, so this
vocabulary repair changes no grouping, metric, threshold, or downstream
domain assignment.

## 2026-07-13 -- shared-plan and HMM diagnostic compatibility

The matrix tooling now requires exactly one 128-year plan for each
station/candidate/replicate tuple and binds the same member from its 30- and
100-year run records. It also admits the HMM's finite
`em_penalized_objective` diagnostic added with the corrected convergence
contract. These are conformance repairs made before any coefficient bundle or
candidate trajectory was published.

## 2026-07-13 -- candidate-neutral faithful base identity

Runner/verifier integration found that placing candidate metadata in the
faithful runspec made its nominal base runspec, CLI header, and run identity
candidate-dependent. The matrix now generates one neutral faithful base for
each station/horizon/replicate (272 total) and all seven candidates bind it.
The overlay replaces only the neutral command-echo suffix from its strict
plan; it independently regenerates and hash-checks the common faithful CLI
before applying annual states. Candidate output remains explicitly labeled,
while base trajectories and identities are now comparable by exact bytes.

## 2026-07-13 -- independent pre-freeze audit dispositions

An independent readiness audit found that the analysis omitted the accepted
`fixture` regime from both deterministic and bootstrap regime summaries. The
frozen regime order is now exactly `arid`, `monsoonal`, `humid`, `cold`,
`fixture`; this retains `id106388` in every applicable regime result without
changing its separately frozen WEPP cold/snow-domain assignment.

The analyzer now resolves the candidate-bound pre-candidate freeze before it
imports executable analysis helpers. It requires the supplied baseline
manifest and archive to be the exact accepted A5a paths and hashes recorded by
that freeze. It also requires its own frozen source plus the complete A5a
`build_targets.py`, `corpus_common.py`, corpus configuration, and established
Rust estimator-source identity. The bootstrap helper is release-only: the
freeze builds it with locked, offline Cargo, pins its executable bytes and
compiler/build metadata, and the analyzer rechecks and records the entire
identity. A debug-binary fallback is no longer admissible.

The no-output guard now recognizes the production archive names
`candidate-evidence-*-v1.tar.gz`, `shared-base-evidence-v1.tar.gz`, and recursively nested
`wepp-response-*-v1.tar.gz`, the intended `artifacts/wepp/evidence-v1/`
directory, the campaign index, and downstream analysis output. This closes a
path-pattern seam that could otherwise have admitted prior output into the
prospective freeze.

The independent evidence verifier now cross-checks each manifest-bound
contract against the freeze inventory, with a mutation proving that an
individually self-consistent but post-freeze contract is rejected. In the
sealed post-WEPP lifecycle state it derives the single repository-relative CLI
root from the 1,904 run records and proves every canonical raw CLI path absent
even when no CLI-directory argument is supplied; a retained-file mutation is
part of its self-test.

Finally, the source-calendar wording now makes clear that a civil-calendar
Daymet sensitivity is an optional, report-only, non-gate follow-on. Revision 1
does not promise that additional report and continues to score only the
prospectively registered `noleap_365_v1` interpretation.

## 2026-07-13 -- bounded precipitation and atomic evidence closure

Real-plan preflight exposed that a clip-once-then-renormalize rule could move
precipitation factors back outside their declared bounds. Plan generation now
uses a deterministic active-set proportional box projection of all 128 annual
factors into `[0.05,20]`, assigns the exact `fsum == 128` residual
deterministically, and defines `precipitation_clip_count` as the number of
final bound-valued factors.

The overlay separately derives one effective precipitation factor for every
consumed year/month as the lesser of the requested factor and the exact f64
widening of `f32(999.9) / faithful_typed_monthly_max`. A dry faithful month
retains its requested factor. It never applies a per-day precipitation cap and
records the complete `12 * horizon` adjustment table and count. Every rendered
row, including Tmax, Tmin, and dewpoint F5.1 fields, is checked for asterisks
before diagnostics publication; no new temperature cap is introduced.

Evidence now includes one canonical 544-member shared-base archive containing
the 272 neutral runspecs and 272 provenance companions cross-bound by all
candidate run records. The runner performs a read-only preflight of all 952
plans before target creation, then stages and verifies all seven candidate
archives plus the shared-base archive before atomic publication and manifest
sealing. Any pre-seal failure rolls back the staged publication.

## 2026-07-13 -- downstream WEPP comparison closure

The prospective WEPP campaign now includes frozen analyzer
`analyze-wepp.py`. It independently validates the exact 2,176 response and
execution records, canonical archive membership and hashes, and the response
schema plus semantic verifier. Candidate responses are paired with
`faithful_off` by station, horizon, and replicate before the registered
station/domain/corpus equal-station hierarchy is evaluated. Signed difference,
zero-baseline-null ratio, unavailable-family handling, and ordering are fixed
by `a5b-wepp-paired-hierarchical-median-v1`.

The analyzer emits canonical `artifacts/wepp/a5b-wepp-analysis-v1.json`, copies
climate Gates 1--6 unchanged, and closes Gate 7 only on complete valid WEPP
evidence. It registers no downstream numeric pass bound and cannot promote a
candidate.

A final independent readiness audit found that the downstream analyzer pinned
the climate-analyzer implementation but did not prove that the supplied
climate analysis described the same lifecycle instance as the WEPP campaign.
Before candidate output, the analyzer and campaign contract now require the
climate analysis to bind the campaign's exact post-WEPP candidate-manifest
SHA-256 and to report complete climate evidence. Self-tests reject both a
different manifest binding and `climate_evidence_complete: false`. The
post-WEPP ordering keeps the climate analysis bound to the canonical manifest
that remains after the raw candidate CLI lifecycle closes.

## 2026-07-13 -- WEPP linker selection and evidence lifecycle

The first executable self-test correctly stopped before candidate output when
the frozen object set linked to 839,648 bytes rather than its prospective
818,952-byte pin. Object-by-object comparison proved all 238 compiled objects
were identical. GNU `collect2` had selected Conda's PATH-prepended ld64-530;
the prospective pin had used Apple's `/usr/bin/ld` 1266.8. The WEPP contract
and runner now pin `/usr/bin/ld` by content hash and select it with the exact
system-only link PATH. Re-linking the identical objects then reproduced the
original 818,952-byte executable byte-for-byte. No candidate climate or WEPP
response output existed during this reconciliation.

The same pre-output review made campaign publication rollback-safe and
license/size proportionate. Public WEPP archives retain only validated
response and execution records; execution records hash-bind raw streams with
`retained: false`. The complete campaign is staged and validated before the
candidate CLI root is reversibly quarantined and the manifest boolean is
flipped. Candidate and campaign evidence are revalidated, the campaign is
atomically published, and only then is quarantine deleted. A pre-publication
failure restores both the original manifest and CLI root. The accepted A5a
baseline manifest/archive are additionally cross-checked against their fixed
pins in the pre-candidate freeze.

## 2026-07-13 -- accepted A5a verifier extension boundary

The accepted A5a verifier binds the complete historical `crates/**/*.rs`
inventory and the then-current A5 evaluation specification. A5b necessarily
adds the declared overlay executable and revises that specification as its
prospective successor, so invoking the unchanged verifier directly against
the extended checkout would reject those two expected changes before it
could validate the accepted archive.

Frozen wrapper `verify-accepted-a5a-baseline.py` preserves the accepted
verifier unchanged and pins its bytes and accepted manifest. It reconstructs
the historical implementation and evaluation-contract identities, proves
every historical source byte against the accepted inventory, proves every
historical evaluation artifact from Git snapshot
`10df134607fcf9c22d27aa38a0e27b457f7c176c`, admits only the exact frozen
A5b overlay source and exact successor evaluation-specification bytes, then
injects only those historical identities while running the complete original
archive, schema, and semantic verification. Its mandatory self-test rejects
an unregistered source extension, a changed historical source binding, and a
changed historical evaluation binding. It does not alter or regenerate any
accepted A5a evidence.

## 2026-07-13 -- WEPP ancillary fixed-width overflow

The first production WEPP launch stopped before building or simulating because
an empty `target/a5a-baseline-v1` directory from an earlier accepted-baseline
verification occupied the campaign's fail-closed regeneration target. Removing
that empty generated directory changed no contract or evidence byte. WEPP
output remained absent, all 1,904 candidate climates remained present, and the
candidate manifest continued to record that no climate byte had been removed.

The retry passed the complete A5a and candidate-evidence preflight, then failed
closed while parsing faithful baseline run `ak505769`, 30 years, replicate 2.
The pinned WEPP executable exited zero with its exact success banner and empty
stderr, but its element stream contained eleven `*******` tokens in `Sm`. An
exact disposable reproduction matched the canonical climate SHA-256 and
located every token in that same ancillary column; all registered response
fields remained finite numeric values.

Pinned WEPP source establishes the cause. `sedout.for` and `contin.for` sum
unfrozen per-layer `soilw` into `watcon`, convert it to millimetres, and render
it as the element stream's `Sm` field with `F7.3`. The reviewed p326 fixture has
a 1.8 m soil profile whose physically plausible liquid storage can round to
1,000 mm, above the format's largest positive representation of 999.999 mm.
Fortran therefore emits seven asterisks without a floating-point exception.
`Sm` is not used by runoff, peak runoff, soil loss, winter response, or
rain-on-snow extraction, and its hidden value is neither imputed nor treated as
an unavailable registered response.

The extraction adapter is prospectively versioned. It accepts exactly seven
asterisks only in the explicitly identified non-response `Sm` column, records
the raw element-stream hash, count, and first mapped key in each execution
record, and reports the aggregate intervention count in campaign evidence.
Every structural check remains in force; asterisks in `Runoff`, `PeakRO`,
`SedLeave`, `QRain`, any other column, or any key are fatal. Self-tests cover
the admitted presentation overflow and the response-bearing mutations, and
the independent analyzer cross-checks the per-run and campaign totals.

Frozen campaign-v1 semantics correctly rejected the observed token. Before
admitting the versioned adapter, the failed WEPP staging tree, prospective
freeze, fit directory, all climate archives and manifest, and the candidate
target were removed. No WEPP response artifact was retained. The replacement
freeze, fit, climate matrix, and WEPP campaign must therefore execute again
from an output-absent state under this amendment.

The fresh replacement-freeze audit then forced four additional mutations
before any output was regenerated. The element parser accepted a same-width
header swap and skipped arbitrary later records beginning with `na`; response
schema validation did not cross-bind the response's extraction-adapter ID to
the execution parser and campaign adapter; and the freeze absence guard did
not reject two stale WEPP workspaces or dangling canonical-output symlinks.
These were evidence-boundary defects, not candidate results, and the audit
remained on hold.

The v2 contract now checks the complete exact 26-field element header and its
one exact units row before accepting data, so a changed field order, missing or
repeated units row, or any later `na` line is fatal. Every response record's
extraction adapter is cross-bound to the execution parser, frozen runner
SHA-256, and campaign adapter identity in both staged validation and
independent analysis. The pre-candidate guard additionally rejects the exact
A5a regeneration target, the whole-target WEPP quarantine path, and dangling
symlinks at every canonical output path. Mutation tests cover each seam. These
corrections remain prospective because freeze, fit, climate, candidate target,
WEPP campaign, and downstream analysis output are all absent.

## 2026-07-13 -- WEPP execution-record construction closure

The next replacement run produced and independently validated the complete
1,904-climate evidence matrix under pre-candidate freeze SHA-256
`1ae43a885ab20401482272a2f44917701e2de82a5bbec83d77e971f37ffc6823`.
The downstream WEPP runner then completed its prerequisite verification and
reached the first substantive WEPP job. The pinned WEPP executable ran without
a reported Fortran failure, but the Python runner stopped before writing even
that job's response/execution pair: its execution-record constructor referred
to `element_artifact`, a local that existed only inside the separately tested
response constructor. No WEPP archive, campaign index, analysis output, A5a
regeneration target, or lifecycle quarantine was retained. The climate
manifest remained in its exact pre-WEPP state with
`candidate_cli_bytes_removed_after_wepp: false`.

The defect is an evidence-construction bug, not a climate or WEPP result. The
execution-record construction now lives in `compose_execution_record`, obtains
the element artifact from its explicit `output_artifacts` input, and is
exercised directly by the runner self-test. That self-test checks that the
production constructor carries the exact closed `Sm` overflow audit. A static
undefined-name pass over every A5b Python pipeline source reported the original
single fault before correction and zero faults afterward.

The frozen runner hash changed, so the already generated climate evidence
cannot remain in a package that promises a complete prospective freeze before
candidate output. The freeze, fit evidence, all climate archives and manifest,
and the candidate target were therefore removed along with any failed staging.
The replacement freeze, fit, climate matrix, and WEPP campaign must execute
again from the output-absent state under this amendment.

## 2026-07-13 -- WEPP same-day element-event aggregation

The next replacement freeze had SHA-256
`ccd11ed4c4f114b7d3ed9600c275db03f7229285fba7eba21118643a30253563`,
and the replacement climate manifest had SHA-256
`2432ac0e875934af489dfe4c85f6656dab3b77de3035f7c6030fadb9ac1b8a20`.
The corrected execution-record constructor crossed its former first-job
failure. A later faithful 100-year job then stopped on the parser's assumption
that element output has at most one row for a mapped day/OFE.

The exact failed coordinate was `ms227840`, faithful-off, 100 years, replicate
7. A disposable exact reproduction captured element stream SHA-256
`c67d50fdcf30de04e51fb78eedc6d96776962f385ff7dd1434b36c4af5d80077`
before deleting the raw workspace. The stream had 3,516 valid rows and 3,515
unique mapped date/OFE keys. Its two records at synthetic year 100, legacy
ordinal 357, OFE 1 were not identical: their runoff values were 2.548 and
5.014 mm, peak runoff 11.954 and 18.967 mm/h, sediment leaving 0.005 and
0.015 kg/m, and explicit `QRain` 2.548 and 5.014 mm. The source climate had
one 47.0 mm record for 22 December 100, so the repeated mapped key is a WEPP
element event/output surface, not a duplicate climate row or year-label
collision.

Extractor v3 admits same-day event records through the closed policy
`a5b_wepp_element_same_day_aggregation_v1`: sum runoff, sediment leaving, and
`QRain`; take the maximum peak runoff; and join the already summed daily
`QRain` once to hourly rain/snow eligibility. It records raw rows, unique keys,
duplicate rows, the first duplicate key, exact aggregation rules, and source
element hash per execution, plus the campaign-wide duplicate-row sum. The
independent analyzer re-derives every count and rejects changed keys, rules,
hashes, or aggregates. Synthetic tests exercise a distinct same-day event pair
and prove the sum/max and rain-on-snow behavior.

No WEPP response archive, campaign index, downstream analysis, lifecycle
transition, A5a regeneration target, or quarantine was retained. Because the
runner, analyzer, and campaign contract hashes changed, the freeze, fit
evidence, all climate archives and manifest, and candidate target were removed
again. The replacement freeze, fit, climate matrix, and WEPP campaign must
execute from an output-absent state under extractor v3.

The focused independent pre-output review initially held extractor v3 on two
P2 provenance bindings. The invocation and public response metadata still used
an unqualified duplicate-record rejection even though valid same-day element
events are reduced by the versioned policy, and the runner-side campaign
validator trusted the runner path/hash declared by its own index. Before the
replacement freeze, the metadata was corrected to distinguish fatal duplicate
hourly records from admitted same-day element events. The publication validator
now requires the exact repository-relative runner path and the SHA-256 of the
currently executing runner; self-test mutations change the adapter ID, runner
path, and runner hash independently and must all fail closed.

## 2026-07-13 -- WEPP PeakRO fixed-width companion recovery

The next replacement freeze had SHA-256
`c29e5b19baab1c695194186c79d840ecc6fa7204ff291ba8c16434564b32f995`;
its fit aggregate had SHA-256
`d9eaf56a63c8fe201c486aa8525c6090b24d7fcb6373d4386b16b0cfa5ca8c58`,
and its climate manifest had SHA-256
`8aacf657f0eb4088ecec2c6749bd5413e0ad00081376587cd8e16df6907d0de8`.
An initial WEPP invocation passed a byte-identical checkout build rather than
the exact sealed snapshot pathname required by the manifest. The runner
rejected that operator invocation before any WEPP execution. Reinvocation with
the snapshot binary passed the complete preflight and baseline regeneration,
then failed closed in the first production batch on a second fixed-width
presentation overflow.

The exact coordinate was station `al015478`, candidate
`rank_one_monthly_sd`, 30 years, replicate 1/burn 17, synthetic year 10,
legacy ordinal 279 (October 6), OFE 1. The 217,141-byte element stream had
SHA-256
`726217f6e5f3f3736103097650c39338bf9889620b6f01dac553d9034fc9253a`.
Line 345 reported precipitation 358.200 mm, runoff 271.851 mm, effective
intensity 135.911 mm/h, and exactly `*******` for response field `PeakRO`.
No campaign evidence or manifest lifecycle transition survived the failed
transaction.

Pinned WEPP source establishes the presentation boundary. At source commit
`c3a082e`, `src/sedout.for:482-493` writes
`peakro(iplane) * 3.6e06` as element numeric index 3, while the grouped FORMAT
at lines 532-533 gives the value only `F7.3`. The same state is emitted through
`hydout`: `src/sloss.for:161-162` makes the event-by-event call,
`src/hydout.for:100` performs the same conversion, and lines 149-153 use
`F8.2`. A disposable exact reproduction selected that abbreviated event
output and captured a 969,232-byte companion stream with SHA-256
`9105f309cba7888181caa88cd83eee02a3cf486571b0fd081645c0d0c751ae41`.
Its matching block reports peak runoff rate 1022.19 mm/h. A larger graphics
stream was also examined but rejected as the recovery surface because it adds
roughly an order of magnitude more I/O per run without improving the declared
response decision.

Extractor v4 adds policy
`a5b_wepp_element_peakro_f7_3_recovery_v1`. It admits exactly seven asterisks
only in the element `PeakRO` column and recovers only from the maximum matching
event-hydrology value keyed by mapped simulation year, legacy ordinal day, and
OFE. The companion parser requires the pinned header, version, labels, note,
nonnegative finite `F8.2` lexical surface, and complete block structure. It
cross-checks every companion event key against numeric or recovered element
`PeakRO` after the existing same-day maximum reduction within 0.006 mm/h, the
full `F8.2` versus `F7.3` rounding envelope. Missing recovery, unmatched keys,
changed structure, stars in the companion stream, or a larger discrepancy is
fatal. Per-execution audits bind both raw hashes, formats, rules, row/key
counts, cross-check count, recovery count, and first key; the campaign records
the exact aggregate `PeakRO` recovery count. The independent analyzer repeats
the closure checks and mutation-tests the policy, sources, rules, run counts,
and campaign total.

A direct production-path execution of the exact failed climate under v4
succeeded, recovered 1022.19 mm/h, cross-checked all 433 unique companion
event keys against 1,129 element keys, and recorded one recovery at the failed
coordinate. Because the runner, analyzer, campaign contract, and generated run
files all changed, the v3 freeze, fit evidence, climate matrix, candidate
target, and disposable diagnostic captures were invalidated and removed,
together with Python bytecode caches and every failed WEPP staging or
quarantine path. The output-absence guard is rerun against that state before
the replacement freeze and complete A5b execution.

The focused independent v4 audit then held the replacement freeze on three P2
evidence-boundary defects. The event companion parser required its header in
the first line but accepted a second exact header later in the stream, and a
numeric element `PeakRO` bypassed the declared source `F7.3` width/precision
check before the event cross-check. In addition, coherent audit mutations could
claim more cross-checked event keys than element keys and more recoveries than
element rows. The parser now requires exactly one event
header and admits numeric `PeakRO` only as at most seven characters matching
the canonical nonnegative three-decimal lexical form. Both publication validators bind event
keys and recovery counts to their already validated element key/row counts.
Direct mutations for duplicate headers and versions, a changed version,
coordinated over-width element/event values, and coherent excessive key/count
claims join the changed-header, starred/over-width event value,
missing-recovery, and cross-check mutations. A positive duplicate event-block
vector pins maximum reduction. The fixes remain pre-output and are included in
the replacement freeze.

The audit continued rather than accepting those fixes in isolation. It found
that the synthetic companion fixture omitted WEPP's real mixed-stream
preamble and ancillary erosion/annual-summary sections. A short-lived
hardening that placed the version on synthetic line 2 would therefore have
rejected real production output. The earlier exact `al015478` v4 rerun had
preceded that line-2 regression; it did not validate the later code. The
regression was never frozen. Runner self-test now executes the pinned WEPP
binary with the exact A5b run adapter, derived p326 management, common
soil/slope, and the accepted 30-year New Meadows golden climate. Its real
6,456-byte mixed `a5b.loss.dat` has SHA-256
`09458763768f5cd300bdb5e7f5b7fb8ee3213a37cf5376be7dc0b6ab82224954`.
The current parser requires its source-built 55-line preamble, parses and
phrase-binds the embedded hydrology blocks, recognizes the annual-summary
boundary, and successfully cross-checks the real element stream. An inserted
preamble line is rejected. Non-hydrology erosion and annual-summary sections
remain explicitly opaque response-wise but are bound by the raw-stream hash.

Three additional evidence bindings were closed. Canonical GNU Fortran
`F7.3`/`F8.2` numeric spellings now reject zero padding as well as over-width
tokens. The rounding comparison uses exact integer thousandths, so the
declared six-thousandth boundary is accepted without binary64 edge drift. One
exact role/SHA-256/byte-count map now connects response outputs, campaign
index, execution audit, and the parser's element/event source hashes;
`hourly_winter` is required from the trusted station/sequence coordinate, not
from a mutable response-domain claim. Mutations independently contradict the
index, response, and execution identities, remove a cold station's winter
stream while changing its station/domain claim, zero-pad both numeric
surfaces, and exercise the exact cross-check boundary. All fail closed.
