# A9c observed-development availability gate

Report ID: `a9c-observed-development-availability`
Status: `ACCEPTED`
Date: 2026-07-15
Revision: 2
Authors: cligen-rs project contributors
Evidence mode: Mixed
Experiment record: [A9c work package](../work-packages/20260715-a9c-observed-development/package.md)
Evidence snapshot: [report manifest](a9c-observed-development-availability-report.manifest.json)
Review record: [consolidated internal review](../work-packages/20260715-a9c-observed-development/artifacts/review.md)

## Abstract

A9c began the frozen observed-development comparison of two successor climate-
generator classes. It materialized 40 role-separated Daymet objects and 24
USCRN logical objects from 180 exact station-year source files, calibrated
7,000 candidate-blind null replicates, and retained five valid fit artifacts
before the mandatory availability gate stopped execution. The two hot-arid
development stations contained 136 and 97 valid events. Under the frozen
150-event station minimum for time-to-peak and peak-ratio objectives and the
200-event minimum for joint dependence, this left 0/2 available hot-arid
stations in three mandatory cells. The registered terminal is
`HOLD-A9C-GATE-CALIBRATION`. No development score, Pareto comparison, candidate
Post-acceptance operator disposition identified the station-level counts as
uncalibrated design rules, not evidence that the two sites' observations are
deficient. The operator directed a prospectively expanded, station-balanced
group design for A9c2; this interpretation changes neither the A9c arithmetic
nor its terminal [E09].

## Introduction

A9a required a joint daily/event climate family to be evaluated across six
primary climate strata, with no mandatory stratum hidden by broader humid
performance. A9b supplied the candidate-blind harness and A9c handoff [E08].
Daymet V4 R1 was selected for daily precipitation and temperature fitting,
while NOAA USCRN Subhourly01 supplied five-minute event descriptors and
compound context [R01] [R02].

The question reached in this report is narrower than candidate quality: did
the frozen observed-development roles pass every registered availability rule
before model ranking? The role and campaign freezes required at least two
available stations per mandatory stratum and prohibited replacement,
threshold changes, or confirmation access after series outcomes became visible
[E01] [E07]. Revision 2 distinguishes that procedural result from an empirical
claim about the amount of information in hot-arid storms [E09].

## Hypotheses

All hypotheses were preregistered by the A9a/A9b contracts or the A9c
pre-access freezes. The availability failure ends the comparison before H3 can
be evaluated.

| ID | Provenance | Scope and comparison | Decision rule | Outcome | Result |
|---|---|---|---|---|---|
| H1 | preregistered | Observed development passes the registered mandatory-objective availability rules in all six strata | At least two available stations per mandatory stratum and objective | Not supported under the registered station-floor design; no data-deficiency inference | [Results](#availability-terminal) |
| H2 | preregistered | Candidate-blind numeric gates and availability can both be frozen | 500 paired null identities per family/horizon plus complete mandatory availability | Partially supported; numeric thresholds complete but availability gate failed | [Results](#null-calibration) |
| H3 | preregistered | At most one candidate can survive the frozen selector | Execute ranking only after all upstream gates pass | Not evaluated; upstream hold prohibited ranking | [Results](#candidate-boundary) |
| H4 | preregistered | Confirmation targets remain untouched throughout A9c | Zero confirmation station-year series access | Supported; zero confirmation series access | [Results](#confirmation-firewall) |

## Methods

### Study identity

| Fact | Registered value |
|---|---|
| Source commit | 4e918ecd5d2b37eaa99ae365677f423080069480 |
| Daymet stations | 20 |
| Uscrn development stations | 12 |
| Uscrn source station years | 180 |
| Normalized observed objects | 64 |
| Fit period | 1980--2009 Daymet; 2010--2017 USCRN |
| Development period | 2010--2025 Daymet; 2018--2024 USCRN |
| Null replicates | 7,000 |
| Complete fit artifacts | 5 |
| Development scores accessed | false |
| Confirmation series accessed | false |
| Hot arid event counts | 136, 97 |
| Hot arid available stations | 0 |
| Hot arid required stations | 2 |
| Failed mandatory cells | 3 |
| Terminal | HOLD-A9C-GATE-CALIBRATION |

### Role freeze and sources

Before station-series access, A9c froze 20 exposed A8a Daymet sites and 12
USCRN event sites, two in each primary stratum. Daymet was normalized into
1980--2009 coefficient-fit and 2010--2025 development objects using the
official 365-value mapping: leap years retain February 29 and omit December
31. USCRN sites were disjoint from the locked 18-site confirmation roster and
were split into 2010--2017 fit and 2018--2024 development periods [E01] [E02].

USCRN events used 72 consecutive valid zero five-minute intervals as the dry
separator. A missing separator invalidated the event. Raw annual files were
hashed and discarded after normalization; the ledger retains URL, year,
station, byte count, and SHA-256 identity. Daymet and USCRN product identities,
documentation, and logical-object hashes are bound in the source manifest
[E02]. These archived products correspond to Daymet V4 R1 and USCRN processed
Subhourly01 data [R01] [R02].

### Availability rules

The objective registry made storm duration available with 150 station events
or with at least 50 station events plus a frozen group containing at least
1,000 events from five sites. Time-to-peak and peak ratio each require 150
station events. Joint dependence requires 200 valid events plus deep-event
support. Every mandatory stratum requires two available stations. Unavailable
is not a zero or a pass [E03] [E08]. These were prospective A9 rules. A9a did
not derive the 150/200 values from a power or precision study for these hot-
arid stations [E09].

## Analysis

The analysis counted valid normalized events per station and mechanically
applied each objective's registered support rule before any candidate
development evaluation. It then
aggregated Boolean station availability by objective and primary stratum. The
global development hierarchy contained 6,835 events across 12 sites, so the
duration borrowing rule was available. That rule does not replace the explicit
station minima for the other three storm objectives [E03].

Numeric gate calibration independently resampled observed year or event blocks
within stratum. For each of seven statistical families and each 30- and
100-year horizon, 500 paired same-observed-law replicates supplied the 95th-
percentile maximum statistic. No fit artifact existed when thresholds were
written, and no candidate input entered calibration [E04].

## Results

### Availability terminal

The hot-arid stations AZ Yuma 27 ENE and CA Stovepipe Wells 1 SW supplied 136
and 97 development events, or 19.4 and 13.9 events per station-year over the
seven-year development window. Consequently, under the frozen rules hot-arid
availability was 0/2 for
`storm_time_to_peak`, 0/2 for `storm_peak_ratio`, and 0/2 for
`storm_joint_dependence`. These are three failed mandatory stratum/objective
cells. Duration remained available through the frozen global borrowing rule.
The first failed upstream gate returns `HOLD-A9C-GATE-CALIBRATION` [E03]. The
operator's later design disposition does not retroactively turn any failed
cell into a pass [E09].

### Null calibration

Numeric calibration itself completed: seven families × two horizons × 500
replicates produced 7,000 hash-bound identities and 14 thresholds. H2 is only
partially supported because the A9 gate includes availability as well as
numeric thresholds [E04].

### Candidate boundary

Four alternating-renewal configurations and one three-state latent-regime
configuration had produced valid, official-schema fit artifacts when the
availability terminal was applied. The remaining fit run was interrupted
because no ranking could legally follow. No generated development climate,
objective distance, Pareto frontier, lexicographic selection trace, or A9d
freeze exists. H3 is therefore not evaluated, and the evidence says nothing
about which candidate class is better [E05] [E06].

### Confirmation firewall

The exact A9a 18-site roster remains `metadata_only`. The A9c role manifest,
source manifest, and access ledger record no confirmation object or logical
hash, and the availability analysis records `confirmation_series_accessed:
false`. H4 is supported [E02] [E03] [E07].

## Limitations and validity

Internal validity is strong for the narrow count-based terminal because every
USCRN source object is hash-bound and the rule is deterministic. The first
acquisition finalizer, null dry run, and early fit construction exposed four
pre-ranking implementation defects; each correction is recorded, and none
used a candidate development score [E06]. The interrupted fit means A9c did
not complete the structural cross-fit or monthly reconciliation campaign.

Construct validity is limited by the selected 2018--2024 development window,
the six-hour event separator, strict missingness, and the registry's
uncalibrated station-level minima. Global borrowing legitimately supports
duration under A9c's rules but cannot be retroactively generalized to
time-to-peak, peak ratio, or joint dependence. The terminal is a mismatch
between the registered evaluation design and observed hot-arid event
frequency, not a climate-model failure or proof of intrinsically inadequate
observations [E09].

External validity is limited to these 12 USCRN development sites, the exact
station-year bytes, and the frozen objective registry. An expanded hot-arid
roster and station-balanced group estimator may use sparse events more
appropriately, but its precision, power, and sensitivity to site heterogeneity
remain future A9c2 questions. Confirmation sites, production Rust, openWEPP,
and WEPPcloud were not evaluated.

## Conclusions

A9c cannot legally rank the successor candidates because its frozen hot-arid
development roles do not pass the registered station-level availability
rules. The historical outcome remains `HOLD-A9C-GATE-CALIBRATION`; revision 2
does not relax an A9c threshold or substitute an A9c station. It corrects the
follow-on interpretation: the 150/200 counts were not calibrated facts about
hot-arid sufficiency. A9c2 should freeze more hot-arid locations, equalize
station influence in grouped event objectives, and calibrate availability
candidate-blind at the actual design before a fresh full comparison. Existing
A9c observations and fits remain exposed, and the confirmation roster remains
untouched [E09].

## Reproducibility and data availability

The work package retains the role/source/access manifests, deterministic
normalizers, null replicates and thresholds, fit inventory, availability
matrix, correction log, and verifier. Normalized observed objects and null
replicates are managed through Git LFS; their compressed and logical SHA-256
identities are checked independently. Raw USCRN annual bytes are identified in
the access ledger but are not redistributed. Public NOAA and ORNL records
retain their source citations. Copyrighted reading copies are not linked.

Revision 2 retains the revision-1 accepted report hash and post-acceptance
operator disposition in the experiment package. All original machine evidence
is unchanged; the revised report and consolidated review are rehashed and
reverified [E09].

## References

- [R01] Thornton, M. M., et al. (2022). *Daymet: Daily Surface Weather Data on
  a 1-km Grid for North America, Version 4 R1*. DOI
  [10.3334/ORNLDAAC/2129](https://doi.org/10.3334/ORNLDAAC/2129).
- [R02] Palecki, M. A., et al. (2015). *U.S. Climate Reference Network
  Processed Data from USCRN Database Version 2*. DOI
  [10.7289/V5MS3QR9](https://doi.org/10.7289/V5MS3QR9).
- [E01] A9c pre-access role freeze and station/period selection.
- [E02] A9c exact observed source and normalized-object manifest.
- [E03] A9c mandatory gate-calibration availability analysis.
- [E04] A9c candidate-blind numeric null thresholds.
- [E05] A9c immutable fit-attempt inventory.
- [E06] A9c pre-ranking correction record.
- [E07] A9c strict data-role manifest and confirmation firewall.
- [E08] A9c predecessor handoff and objective boundary.
- [E09] A9c post-acceptance operator disposition and immutable-boundary record.
