# A5b WEPP Campaign Contract v4

Status: **FROZEN AFTER CLIMATE OUTPUT, BEFORE WEPP RESPONSE OUTPUT**
Date: 2026-07-13

## Role

This campaign measures downstream response; it is not an observed-response
truth surface and it does not promote an A5b candidate. All station climates
drive one common reviewed hillslope so climate effects are comparable without
silently confounding station-specific soils, slopes, or management.

## Matrix

Execute the scientific faithful-off baseline and all seven A5b candidates:

`17 stations x 2 horizons x 8 replicate records x 8 climate profiles = 2,176 WEPP runs`.

The conditioned faithful comparator is not part of the downstream matrix.
The five `cold_snow` sites are `co051660`, `wy485345`, `mn214026`,
`ak505769`, and `id106388`; the other twelve have domain `general`.

## Executable authority

Build WEPP 2020.500 from the exact `wepp-forest` Git object, never from its
mutable checkout:

- source commit: `c3a082e2eee00ab010f0eb1cb33d01114bdc0216`;
- source extraction: `git archive` of that commit into a new temporary tree;
- compiler: GNU Fortran 15.2.0 (Homebrew GCC 15.2.0_1), Apple arm64;
- compile flags: `-c -fno-align-commons -O2 -ffixed-form
  -ffixed-line-length-72 -ffpe-trap=invalid,zero,overflow
  -finit-local-zero`;
- build: from `src/`, run `make -f makefile.arm64.mac` with `FFLAGS` replaced
  by the exact flags above and require its final link to fail only at the
  makefile's omitted `wepp_observe.o` seam; compile `wepp_observe.for`
  explicitly with the same flags, remove any failed-link `wepp`, then link
  the complete lexically ordered object set with the absolute Homebrew
  `gfortran` under `PATH=/usr/bin:/bin:/usr/sbin:/sbin` as
  `gfortran *.o -o wepp`. This environment is normative because GCC
  `collect2` searches `PATH` for `ld`; a Conda-prepended ld64-530 produces
  different Mach-O bytes from identical objects;
- final linker: `/usr/bin/ld`, first version line
  `@(#)PROGRAM:ld PROJECT:ld-1266.8`, SHA-256
  `12bed4523661307059b879b9b54e77a73176e9d27d27a0e40363271d8f0668ba`;
- expected executable: 818,952 bytes, SHA-256
  `dccb55f3980e287ada5541b7801f9b9fa79b4b1d65addb97d6914317bc4a4527`;
- runtime `libgfortran.5.dylib` SHA-256
  `624e083bf9ebdcd8c6713ef8adaf1aa49ec2a1756cd0dbaed553fd48fc3e6950`;
- runtime `libquadmath.0.dylib` SHA-256
  `773034db811835ca98358409e647c46a97cb9dc3f4fbb6956c858e5a31cdf580`.

The tracked `release/wepp.arm64.mac` is ineligible: its build used
`-fdefault-real-8`, lacks complete provenance, and fails on some current
output formats.

The executable and source/deck bytes are not committed here. The source repo
has no blanket license and the fixture has no per-file grant; A5b records
their Git-object and content hashes without asserting redistribution rights.

## Reviewed hillslope inputs

All source files come from
`tests/fixtures/srivas42_claustrophobic_shortcut_p326/runs/` at the pinned
commit:

| Role | Source | SHA-256 |
|---|---|---|
| management | `p326.man` | `dd5cb34c1361a2f543cc5b1a7c7de3027621a2c9437a1c023d8f96b7bbaed60b` |
| slope | `p326.slp` | `5df68111b44cbb8b8b4b9bd8086fb76d86e19cd592f9995adace2a0354f12ec2` |
| soil | `p326.sol` | `aa79cae424a79f1991c2995738b48f0367d1eea13c3f287eff7843772516ad88` |
| control | `p326.run` | `2bd5161b13b968973be9338bc23bc272faac8f58faea2ff1232a4ac72da4c929` |

The reviewed management declares six years. Adapter
`a5b_wepp_p326_management_repeat_v1` repeats its sole annual management entry
without changing operations until exactly 100 years are declared. The
expected derived management SHA-256 is
`43ae1f0df3df5d13fe6fe7892fc20792027820c45327ccf9c259d26445d4e0f6`;
both horizons use that same 100-year file. Any byte mismatch is fatal.

Run adapter `a5b_wepp_p326_run_v2` writes paths relative to an isolated run
directory, disables water-balance output (the pinned build has an invalid
legacy FORMAT path), selects output option 3 so WEPP emits abbreviated
event-by-event hydrology, and enables element output. It enables hourly winter
output only for the five cold sites. The exact generated run file and every
installed input are hashed into each response record. The four generated run
files are frozen as follows:

| Horizon | Domain | SHA-256 |
|---:|---|---|
| 30 | `general` | `46feaab6a1c3cd6153e289a68c4b47d40268481529a163245f97da6d18fb2a4f` |
| 30 | `cold_snow` | `dc8b7c661a1f4b9319bb1223f746f0b72817b6c0b0a9447459c924de01ef825c` |
| 100 | `general` | `79bf8daaa2351b8465f54c977e3502a19dfef39344f64401a373795a11e0333a` |
| 100 | `cold_snow` | `f30d5a19d00a789a05ce6bb9fbfb7bf951cc33bee3b6b964477d858fbf780ef0` |

## Climate installation and calendar adapter

`a5b_wepp_cli_install_v1` installs the exact candidate/baseline CLI bytes as
the deck's climate input. WEPP's legacy calendar treats every year divisible
by four as leap, whereas CLIGEN uses Gregorian rules. In a 100-year climate,
the adapter changes only daily-row year labels `100` to `101`; the header
continues to declare 100 simulated years. Output year label 101 maps back to
synthetic index 100. Thirty-year climates are unchanged. The adapter must
prove that all non-year fields and all other bytes are identical and that
exactly 365 rows are relabeled for a 100-year input.
Every source must end immediately after exactly one canonical CLIGEN run-end
terminator (`0x20 0x20 0x0a`). The installer rejects a missing, duplicate,
noncanonical, or followed terminator and preserves those three bytes exactly
for both horizons.
WEPP's hourly state clock still exposes internal simulation year 100 as a
fourth-year leap year and can report ordinal day 366; the extractor accepts
that internal state, maps output label 101 back to synthetic year 100, and
uses the same legacy ordinal clock for element/hourly join keys.

## Invocation and success

From the isolated run directory:

`<pinned-wepp> < a5b.run > stdout.txt 2> stderr.txt`

Success requires exit code zero, the exact banner
`WEPP COMPLETED HILLSLOPE SIMULATION SUCCESSFULLY`, every requested output,
and exactly 30 or 100 complete mapped simulation years. Warnings, missing
years, nonfinite fields, negative response magnitudes, duplicate hourly
records, or an unexpected output format outside the two source-anchored
fixed-width policies and versioned element same-day aggregation policy below
are fatal.

## Extraction adapter

Adapter ID: `a5b_wepp_p326_response_extractor_v7`.

This is an independent post-climate successor to the immutable v4 runner and
campaign bound by the pre-candidate freeze. The first v4 production attempt
failed closed on a faithful-off dry coordinate before any response or
execution record was published. The exact discovery, leakage boundary,
source-built reproduction, raw-stream identities, and v5 disposition are
recorded in
`artifacts/freeze/post-climate-wepp-amendment-v1.md`. Candidate climate
evidence remains bound to v4; WEPP response evidence is generated and bound
only to a post-climate contract and runner. The v5 successor then failed
closed before publication on a candidate coordinate whose nonresponse
`EffInt` field overflowed the same source `F7.3` surface. That discovery,
including the disclosed candidate-response inspection boundary, is recorded
in `artifacts/freeze/post-climate-wepp-amendment-v2.md`. v5 remains immutable.
The v6 runner then executed and privately staged the complete matrix but its
final archive revalidator rejected the already registered zero-event record
because that duplicate validator incorrectly required a positive event count.
No campaign evidence was published and the private tree was removed. That
validator-only disposition is frozen in
`artifacts/freeze/post-climate-wepp-amendment-v3.md`; v6 remains immutable and
WEPP evidence is generated only by this v7 runner and contract.

The v2 fixed-width change was prospective to replacement A5b output. The first WEPP matrix
attempt exposed an element record whose `Sm` token was exactly `*******`; the
runner rejected that attempt before sealing or publication, and its raw
staging was transactionally deleted. No evidence from that attempt is admitted.
This correction and its runner identity must be present in the replacement
pre-candidate freeze before execution resumes.

Element parsing is anchored to the complete pinned output preamble. The first
header row must split to exactly these 26 fields, in order:

`OFE DD MM YYYY Precip Runoff EffInt PeakRO EffDur Enrich Keff Sm LeafArea CanHgt Cancov IntCov RilCov LivBio DeadBio Ki Kr Tcrit RilWid SedLeave QRain QSnow`

The immediately following units row must split to exactly these 26 fields, in
order:

`na na na na mm mm mm/h mm/h h Ratio mm/h mm Index m % % % Kg/m^2 Kg/m^2 na na na m kg/m mm mm`

Each data row must then contain exactly 26 fields. A legacy 24-field header,
a changed or displaced units row, a repeated header, or any later row beginning
with `na` is fatal; the extractor does not search forward for a convenient
header or silently skip post-header text.

The v3 change is also prospective to replacement A5b output. An exact
reproduction of the first later duplicate-date failure produced element stream
SHA-256 `c67d50fdcf30de04e51fb78eedc6d96776962f385ff7dd1434b36c4af5d80077`.
It contained 3,516 valid event/state rows and 3,515 unique mapped
`(simulation_year, ordinal_day, OFE)` keys. Its two rows for synthetic year
100, legacy ordinal 357, OFE 1 were distinct response records: runoff was
2.548 and 5.014 mm, `PeakRO` was 11.954 and 18.967 mm/h, `SedLeave` was
0.005 and 0.015 kg/m, and `QRain` was 2.548 and 5.014 mm. Rejecting the second
row would discard a valid event response; overwriting either row would make the
result depend on file order.

Policy `a5b_wepp_element_same_day_aggregation_v1` therefore reduces all rows
sharing that mapped key by summing `Runoff`, `SedLeave`, and `QRain`, and
taking the maximum `PeakRO`. Annual and winter response accumulation consumes
every raw row with the same sum/max rules. The daily rain-on-snow join consumes
the already summed `QRain` value once per eligible mapped key. Every raw row
still undergoes the complete lexical, finite, nonnegative, and `Sm` checks;
same-day reduction is not permission to skip or overwrite a record.

The exception is fixed by the pinned WEPP source, not inferred from a candidate
response. At source commit `c3a082e`, `src/sedout.for:445-449` sums every
`soilw` layer into `watcon`, and lines 482-493 write `watcon * 1000` as the
eighth numeric element field (zero-based index 7) after the four date/OFE
keys. The corresponding FORMAT at lines 532-533 is `F7.3`;
`src/outfil.for:708-714`
labels that field `Sm` in mm. `src/cwater.inc:60-61` defines `soilw` as soil
water per layer in metres and distinguishes frozen `soilf`; the water-balance
header at `src/outfil.for:628-629` describes their profile sums as unfrozen and
frozen water. The non-event element path uses the same sum and `F7.3` position
at `src/contin.for:1330-1371` and 1814-1815. A positive value that rounds to
1,000.000 mm cannot fit `F7.3`, so GNU Fortran emits seven asterisks even
though the finite internal value and simulation remain valid. The reviewed
p326 soil is 1.8 m deep, making this display boundary physically reachable.

Policy `a5b_wepp_element_sm_f7_3_overflow_v1` therefore admits exactly token
`*******`, only at numeric index 7 after the four keys, only when header index
7 is exactly `Sm`. Numeric `Sm` tokens must remain valid `F7.3` lexical forms.
The extractor never parses, stores, censors, or imputes `Sm`; it is not an A5b
response field. Every other element numeric token remains a strict finite
number except the separately audited `EffInt` and recovered `PeakRO` cases
below. `Runoff` index
1, `SedLeave` index 19, and `QRain` index 20 always remain numeric. A different
star count, stars in any undeclared column, a changed header, or any other
malformed field is fatal.

Extractor v6 separately registers
`a5b_wepp_element_effint_f7_3_overflow_v1`. At pinned source
`src/sedout.for:482-486`, element numeric index 2 is
`effint(iplane) * 3.6e06`; FORMAT 1000 at lines 532-533 assigns it `F7.3`, and
`src/outfil.for:708-714` labels it `EffInt` in mm/h. The failed source-built
coordinate emitted exactly `*******` for `EffInt` while its companion
response-bearing `PeakRO` overflow was recovered under the existing policy.
`EffInt` is not consumed by any registered A5b response. v6 therefore admits
only seven asterisks at numeric index 2 when header index 2 is exactly
`EffInt`; numeric values require the canonical nonnegative `F7.3` lexical
surface. Each execution records a separate closed audit containing policy,
source element hash, exact field/index/token/FORMAT/nonresponse declaration,
row count, occurrence count, and first mapped key. Wrong star counts, stars in
another field, zero-padded or over-width numeric spellings, and changed
headers remain fatal.

The v4 change is prospective to a second replacement A5b freeze. After the v3
runner passed all preflight checks, the first production batch exposed one
response-bearing element token of exactly `*******`: station `al015478`,
candidate `rank_one_monthly_sd`, 30-year horizon, replicate 1/burn 17,
synthetic year 10, legacy ordinal 279 (October 6), OFE 1. The raw element
stream is 217,141 bytes with SHA-256
`726217f6e5f3f3736103097650c39338bf9889620b6f01dac553d9034fc9253a`;
its line 345 reports precipitation 358.200 mm, runoff 271.851 mm, effective
intensity 135.911 mm/h, and an overflowing `PeakRO`. That run was rejected
before campaign publication and its staging was transactionally removed.

Pinned source establishes both the cause and an independent companion value.
At commit `c3a082e`, `src/sedout.for:482-493` writes
`peakro(iplane) * 3.6e06` as element numeric index 3, and the grouped FORMAT at
lines 532-533 gives that field `F7.3`. `src/sloss.for:161-162` calls `hydout`
for event-by-event output. `src/hydout.for:100` calculates the same converted
`peakro`, lines 103-127 emit it for OFE output, and lines 149-153 format the
non-irrigation value as `F8.2`. For the failed coordinate, the companion event
stream is 969,232 bytes with SHA-256
`9105f309cba7888181caa88cd83eee02a3cf486571b0fd081645c0d0c751ae41`
and reports `peak runoff rate 1022.19` mm/h. A direct production-path rerun of
that exact climate under v4 recovered 1022.19 and closed all parser audits.

Policy `a5b_wepp_element_peakro_f7_3_recovery_v1` therefore admits exactly
token `*******`, only at element numeric index 3, only when header index 3 is
exactly `PeakRO`. It recovers that mapped `(simulation_year, ordinal_day,
OFE)` from the maximum `peak runoff rate` in the pinned abbreviated
event-hydrology blocks. The companion parser requires the exact WEPP header,
version, source-built 55-line preamble (with only the station text variable),
OFE/date/field labels, note, nonnegative finite values, and canonical source
`F8.2` lexical surface without zero padding. Duplicate event blocks for one
mapped key reduce by maximum. The pinned file interleaves hydrology blocks
with non-hydrology erosion and annual-summary sections. Those ancillary
sections are hash-bound but are not response sources; every occurrence of a
hydrology structural phrase must belong to a valid parsed block. Every
companion event key, not only a recovered key, must agree with the
same-day-reduced element `PeakRO` within six integer thousandths of a mm/h,
the exact `F8.2` versus `F7.3` rounding envelope. Numeric element `PeakRO`
also requires canonical `F7.3` spelling without zero padding. Missing
recovery, unmatched keys, a changed preamble/label/format, a larger
discrepancy, or a star in the event stream is fatal. The policy does not clip,
censor, or impute the response.

When the pinned executable produces zero runoff events, it omits the entire
seven-line hillslope/event-section suffix and places the unique
`ANNUAL AVERAGE SUMMARIES` marker immediately after the first 48 lines of the
otherwise identical preamble. Extractor v5 admits only that exact zero-record
seam. It then requires the complete companion element output to cover every
mapped simulation year and requires every reduced `Runoff` and `PeakRO` value
to be exactly zero. A displaced marker, an empty full event section, an event
block after the zero-record seam, or any nonzero companion runoff/peak is
fatal. Nonzero-event streams retain every v4 block, lexical, cross-check, and
fixed-width recovery requirement unchanged.

Extractor v7 makes the final archive revalidator agree with that existing
zero-event contract. Event record, unique-key, duplicate-row, cross-check,
and recovery counts must all be zero, and the recovery observation must be
empty. Element row/key counts remain positive and complete. A nonzero or
internally inconsistent event audit remains fatal. This changes no parsed
response value, aggregation, candidate, threshold, or metric.

Each execution record carries four closed audits. The
`parser.element_same_day_aggregation` audit records its policy and exact
sum/max rules, source element SHA-256, raw row count, unique mapped-key count,
duplicate-row count, and first duplicate key. The
`parser.element_fixed_width_overflow` audit records its policy ID, source element SHA-256,
the exact allowed field/index/token/FORMAT/nonresponse status, total element
rows, and `observed`. `observed` is `{}` when no overflow occurs; otherwise it
contains the count and first mapped `(simulation_year, ordinal_day, OFE)` key.
The sibling `parser.element_effint_fixed_width_overflow` audit has the same
closed shape for the separately registered `EffInt` exception.
The `parser.element_peakro_recovery` audit records its policy, the element and
event-stream hashes, exact source/output formats and reduction/cross-check
rules, event row/key counts, cross-checked key count, recovery count, and first
recovered key. Together with the sibling validated element row/key counts,
event keys may not exceed element keys and recoveries may not exceed raw
element rows. Response outputs, campaign-index raw audits, execution raw
audits, and parser source hashes form one exact role/SHA-256/byte-count map;
the station-derived domain fixes whether `hourly_winter` is required. The
campaign index records all exact sums
across the execution records as
`execution.element_same_day_duplicate_rows = <count>`,
`execution.element_fixed_width_overflow_counts = {"EffInt": <count>, "Sm": <count>}`, and
`execution.element_response_recovery_counts = {"PeakRO": <count>}`.
Validation must reproduce all three sums from the archived execution records.

Extractor identity is cross-bound at every evidence layer. The campaign index
must name `a5b_wepp_p326_response_extractor_v7` and bind the frozen runner's
SHA-256. Every response record's `wepp_execution.extraction_adapter` must equal
that adapter ID plus runner hash, and every execution record's `parser` must
carry the same adapter ID plus runner hash. Both campaign publication and the
independent analyzer fail closed if any one of those bindings differs.

From every element-output row, by mapped simulation year:

- `annual_runoff`: sum `Runoff`;
- `annual_peak_runoff`: maximum `PeakRO`, using the source-anchored companion
  recovery above only where its element `F7.3` token overflows;
- `annual_soil_loss`: sum `SedLeave`;
- `winter_runoff`: sum `Runoff` on December/January/February records; and
- `winter_soil_loss`: sum `SedLeave` on those records.

From hourly winter output:

- `annual_max_snow_water_state`: maximum of
  `snow_depth * snow_density / 1000`, explicitly labeled the pinned WEPP
  snow-water-state analogue;
- `annual_snowmelt`: sum `melt_water`; and
- `rain_on_snow_runoff`: hourly winter rows provide eligibility only. Mark
  each unique mapped `(simulation year, ordinal day, OFE)` when any hourly
  row has `rain_fall > 0`, `snow_depth > 0`, and `snow_density > 0`; join
  that key to the daily element-output aggregate and sum its explicit,
  same-day-reduced `QRain` exactly once. The hourly output has no `QRain`, so
  none is invented. This
  is labeled a rain-on-snow response analogue, not a causal runoff
  partition.

General records carry the first three families. Cold records carry all eight.
If a frozen output lacks a cold field, emit the schema's one explicit
`unavailable` row with source audit; never substitute zero or omit the family.
Each available family reports the mean, sample SD, nearest-rank p95, and
maximum across complete simulation years with units and exact source output
hash.

## Paired downstream analysis

Frozen analyzer `analyze-wepp.py` independently revalidates all 2,176 response
and execution records and their canonical archive bindings before comparing a
candidate. The climate analyzer runs after the sole candidate-manifest
lifecycle transition. Its `inputs.candidate_manifest_sha256` must equal the
campaign's exact `candidate.lifecycle.post_manifest.sha256`, and its
`evidence_completeness.climate_evidence_complete` value must be `true` before
any climate gate can enter the downstream table. Each candidate value is
paired with `faithful_off` by exact station, horizon, replicate, metric, and
statistic. Signed difference is candidate minus faithful-off. Ratio is
candidate divided by faithful-off and is JSON `null` whenever the
faithful-off value is zero, including zero divided by zero.

Aggregation contract `a5b-wepp-paired-hierarchical-median-v1` first reports
each replicate pair and a station summary using conventional median,
nearest-rank p05 and p95, minimum, and maximum across the eight replicates.
Domain and corpus summaries apply those same statistics to station medians,
so every applicable station has equal weight. `general` and `cold_snow` are
separate domain summaries; corpus summaries span every station where the
metric/statistic is available. Unavailable families remain explicit counts
and never become zero. This comparison is descriptive: revision 1 registers
no downstream numeric pass bound.

The final candidate-by-horizon gate table copies climate Gates 1--6 unchanged.
Gate 7 is true exactly when the complete 2,176-record WEPP campaign validates;
it does not judge the magnitude or direction of a response difference.

## Evidence and interpretation

Every response uses `a5-wepp-response-v1.schema.json` and the pinned semantic
validator. For candidate climates, the schema field `climate.provenance_sha256`
binds the strict `a5b_run_record_v1` bytes; for faithful-off baseline climates
it binds provenance v1. This usage is fixed by the prospective A5b lineage
amendment and is never represented as embedded quality-report provenance.
The accepted A5a faithful-off manifest and archive must match both their
fixed content/byte pins and the corresponding `a5a_pinned_artifacts` entries
in the prospective pre-candidate freeze. The WEPP runner invokes the frozen
A5b historical-evidence wrapper, not the checkout-relative original A5a
verifier; the wrapper replays that unchanged verifier after proving the exact
accepted source/evaluation identities and the sole declared A5b extension.
Its own artifact identity and stdout hash are retained in campaign evidence.

The public WEPP archives contain only canonical validated `response.json`
and `execution.json` records. Each execution record binds the hash and byte
count of element, event-by-event hydrology/soil-loss, optional hourly-winter,
stdout, and stderr streams, marks each `retained: false`, and records the
removal audit. The event stream is a hash-bound companion for `PeakRO`
recovery and is not substituted for element `SedLeave`. Raw or gzip-compressed
WEPP streams are not redistributed; isolated run directories are deleted
after their response records are sealed.

A5b reports response differences, station failures, and intervention counts.
The response surface has no independently observed truth and revision 1 does
not invent a numeric pass bound after seeing values. Climate Gates 1--6 and
complete valid response evidence determine A5c eligibility; A5c applies
ADR-0002 to the downstream tradeoffs before any promotion.

After the complete response archives and campaign index validate in a staging
directory, the runner atomically renames the exact 1,904-file candidate CLI
root to a reversible quarantine and performs the sole manifest transition
allowed by SPEC-A5B-CANDIDATES: it atomically changes
`candidate_cli_bytes_removed_after_wepp` from `false` to `true`, proves all
other manifest values and bytes unchanged, and records the pre/post hashes in
the staged campaign index. It then verifies the candidate evidence under true
semantics, revalidates the lifecycle and staged campaign, and atomically
publishes the campaign. Any failure before publication restores the original
manifest and CLI root. Only after publication succeeds is the quarantine
deleted. The repository-containment, regular-entry, exact-file-inventory, and
manifest-transition checks run as a nonmutating preflight before WEPP is built
or any response job starts, then repeat immediately before activation. The
campaign index binds the post-removal verifier output. If recursive quarantine
deletion is interrupted after publication, a
same-command rerun validates the sealed campaign, true manifest, absent CLI
root, and every remaining quarantine file against the sealed inventory before
deleting that strict remainder. An already finalized rerun is idempotent.
Baseline regenerations and all raw WEPP outputs are removed after their hashes
and response records are sealed.
