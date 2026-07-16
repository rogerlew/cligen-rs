# A9c2 hot-arid roster feasibility

Report ID: `a9c2-hot-arid-roster-feasibility`
Status: `ACCEPTED`
Date: 2026-07-15
Revision: 2
Authors: cligen-rs project contributors
Evidence mode: Mixed
Experiment record: [A9c2 work package](../work-packages/20260715-a9c2-grouped-hot-arid-reentry/package.md)
Evidence snapshot: [report manifest](a9c2-hot-arid-roster-feasibility-report.manifest.json)
Review record: [consolidated internal review](../work-packages/20260715-a9c2-grouped-hot-arid-reentry/artifacts/review.md)

## Abstract

A9c2 tested whether a prospectively frozen metadata rule could expand the
hot-arid USCRN development roster from two locations to at least five without
using observed event frequency or touching the locked confirmation series.
The filter reduced a 255-row station-listing snapshot to 113 active,
operational USCRN sites commissioned by the 2010 cutoff. Three matched the
exact A8a hot-arid descriptor screen: AZ Yuma 27 ENE, CA Stovepipe Wells 1 SW,
and NV Mercury 3 SSW. Mercury is a locked confirmation site, leaving Yuma and
Stovepipe Wells as the only two accepted development locations. Because 2 is
less than the frozen minimum of 5, A9c2 returns
`HOLD-A9C2-HOT-ARID-ROSTER` [E03] [E04]. The recorded execution accessed no
daily or subdaily station series, candidate output, or confirmation series
[E02] [E10]. Grouped-estimator calibration, candidate fitting, model
comparison, and A9d confirmation were not reached.

After acceptance of revision 1, the operator retained the census and terminal
but declared the two-site hot-arid development evidence functionally adequate
for research continuation. The five-site floor is retired as a successor entry
requirement; accepted limitations must accompany the future comparison [E12].

## Introduction

A9c stopped before candidate comparison because its two hot-arid development
sites did not satisfy uncalibrated, station-level storm-event availability
floors. The historical arithmetic and terminal remain valid, but the operator
directed a prospective correction: expand spatial replication, give stations
equal weight in grouped storm objectives, and calibrate support at the actual
design rather than require each dry station to meet an uncalibrated design
count [E09].

A9c2 therefore made roster feasibility its first outcome-bearing gate. The
design required Yuma and Stovepipe Wells to remain, accepted every additional
station satisfying one frozen metadata rule, prohibited outcome-based ranking
or substitution, and required at least five accepted locations before any
station-series access [E01]. Official NOAA USCRN station listings provide the
network metadata context [R01]; the experiment result is tied to the exact
hash-pinned snapshot rather than the mutable web page [E07].

The question is deliberately narrow: can this exact active USCRN population
commissioned by the 2010-01-01 cutoff and A8a descriptor crosswalk supply five
development sites that are ID-disjoint from, and at least 75 km from, the
locked confirmation roster? The partition rule is a campaign-separation rule,
not evidence of statistical independence.

The post-acceptance operator question is different: must the campaign expand
the corpus before returning to model development? The operator answered no,
accepting the limited spatial evidence as an explicit project risk rather than
reinterpreting the failed five-site hypothesis [E12].

## Hypotheses

The substantive criteria were frozen before roster evaluation, but the H1--H3
labels were assigned afterward for this report. They are retrospective
mappings to prospective decision rules and are not confirmatory hypotheses.

| ID | Provenance | Scope and comparison | Decision rule | Outcome | Result |
|---|---|---|---|---|---|
| H1 | retrospective mapping | Frozen metadata rule supplies the A9c2 hot-arid development roster | Accept at least five distinct stations | Not supported; 2 of 5 required stations accepted | [Results](#roster-terminal) |
| H2 | retrospective mapping | Required exposed hot-arid sites remain eligible | Yuma and Stovepipe Wells both pass the same complete rule | Supported; Yuma and Stovepipe Wells accepted | [Results](#descriptor-matches) |
| H3 | retrospective mapping | Roster execution preserves the access firewall | Record zero station-series, candidate-output, and confirmation-series access | Supported; zero station-series, candidate-output, and confirmation-series access recorded | [Results](#access-boundary) |

## Methods

### Study identity

| Fact | Registered value |
|---|---|
| Source commit | 493f8c4cb66f3db2b4eb227d615f33e31b2b5cf7 |
| Station listing rows | 255 |
| Metadata base stations | 113 |
| Descriptor inventory stations | 2,765 |
| Locked confirmation stations | 18 |
| Locked confirmation stations in metadata base | 17 |
| Hot arid descriptor matches | 3 |
| Accepted stations | 2 |
| Required accepted stations | 5 |
| Roster deficit | 3 |
| Retained required stations | AZ Yuma 27 ENE, CA Stovepipe Wells 1 SW |
| Accepted pair distance km | 498.859 |
| Distance method | haversine sphere radius 6371.0088 km |
| Station series accessed | false |
| Candidate outputs accessed | false |
| Confirmation series accessed | false |
| Terminal | HOLD-A9C2-HOT-ARID-ROSTER |
| Operator disposition | TWO-SITE-HOT-ARID-EVIDENCE-FUNCTIONALLY-ADEQUATE |
| Successor roster requirement | two fixed sites; five-site floor retired |
| A9c3 execution authorized | false |

### Population and access order

The execution was dispatched from commit
`493f8c4cb66f3db2b4eb227d615f33e31b2b5cf7` on `main` [E02]. Before
evaluating eligibility, it froze four permitted metadata inputs and prohibited
daily and subdaily station data, candidate results, and confirmation target
data [E03]. The inputs were:

- the committed 255-row NOAA station-listing snapshot [E07];
- the A8a hot-arid selection contract [E05];
- the 2,765-station A8a legacy parameter/catalog inventory, whose own boundary
  says no daily observation was read [E06]; and
- the 18-site locked metadata-only confirmation roster [E08].

The population retained rows with country `US`, network `USCRN`, status
`Commissioned`, operation `Operational`, and commissioning on or before
2010-01-01 00:00:00 UTC. The 2010 date is only a commissioning cutoff for the
intended fit role. No 2010--2017 fit series or 2018--2024 development series
was evaluated in A9c2.

### Descriptor crosswalk and partition

For each metadata-base site, the program selected the nearest A8a `us-2015`
legacy parameter/catalog station by haversine distance on a sphere of radius
6,371.0088 km; exact distance ties resolve by ascending descriptor station ID.
The crosswalk required that nearest descriptor to be no farther than 75 km.
A site matched `hot_arid` when its USCRN longitude was at most -108 degrees,
the nearest descriptor's annual expected precipitation was at most 220 mm,
and its annual mean temperature was at least 17 degrees C. These inclusive
bounds exactly reproduce the A8a selection contract [E03] [E05].

The disposition order first excluded any exact locked confirmation ID, then
any remaining site less than 75 km from a locked confirmation location, then
an out-of-range descriptor crosswalk, and finally a site outside the hot-arid
screen. Every passing site was accepted; there was no rank or roster cap. Both
required retained stations had to pass, and fewer than five accepted stations
returned the registered roster hold [E03]. The deterministic program and all
of its metadata-only inputs are hash-bound [E10].

## Analysis

The analysis assigned one disposition reason to every one of the 113
metadata-base rows. It also counted hot-arid descriptor matches independently
of disposition, so a locked confirmation site could remain visible as a
descriptor match without entering development. Reason arithmetic was checked
as 17 locked confirmation IDs in the metadata base, 94 nonmatches, and 2
accepted sites, totaling 113 [E04]. The eighteenth locked station, AK
Fairbanks 11 NE, was commissioned after the cutoff and therefore never entered
the 113-row base [E07] [E08].

H1 compared the accepted count with the frozen minimum. H2 checked that both
required retained IDs appeared in the accepted set. H3 inspected the dispatch,
freeze, deterministic program boundary, and result access flags. These records
support what the execution records; they are not an operating-system forensic
audit of all possible external access [E02] [E03] [E04] [E10].

Distances were rounded to three decimals after calculation. The sole accepted
pair, Yuma--Stovepipe Wells, is 498.859 km apart under the same haversine method
[E11]. This distance is descriptive and does not establish climatic or
statistical independence.

## Results

### Descriptor matches

Only three metadata-base sites matched the frozen screen. Values in the table
are the nearest legacy descriptor's climatology; distances are from the USCRN
site. Precipitation is annual expected millimeters, temperature is annual mean
degrees C, and distances are kilometers. Descriptor values are rounded to six
decimals and distances to three [E04].

| USCRN site | Nearest descriptor | Precipitation (mm) | Temperature (degrees C) | Descriptor distance (km) | Nearest confirmation distance (km) | Disposition |
|---|---|---:|---:|---:|---:|---|
| AZ Yuma 27 ENE | az029654 | 90.707905 | 23.601857 | 20.556 | 367.017 | accepted |
| CA Stovepipe Wells 1 SW | ca042319 | 61.186260 | 24.975289 | 28.123 | 99.993 | accepted |
| NV Mercury 3 SSW | nv262243 | 119.665850 | 17.318433 | 61.804 | 0.000 | locked confirmation ID |

H2 is supported: Yuma and Stovepipe Wells both pass the complete rule. Mercury
is itself a locked confirmation station and cannot be relabeled as development
[E04] [E08]. Other A9a stations carrying a historical `hot_arid` primary label
are not implied to satisfy this distinct A8a descriptor screen.

### Roster terminal

The complete rule accepts 2 stations against a minimum of 5, a deficit of 3.
There were no descriptor-distance or non-ID partition-distance exclusions;
changing those bounds inside A9c2 would therefore not create the three missing
sites. H1 is not supported, and the first registered terminal is
`HOLD-A9C2-HOT-ARID-ROSTER` [E03] [E04].

The stop is procedural and scientific: the package prohibited station-series
access and downstream grouped-design work when fewer than five sites passed.
It did not write the complete A9c2 objective registry or versioned SPEC-A9
grouped-evaluation amendment, acquire added station years, calibrate estimator
power, refit either candidate class, generate new null thresholds, compare
candidates, or authorize A9d [E01].

### Access boundary

The dispatch, pre-inventory freeze, deterministic roster program, and output
all record metadata-only execution. The output flags station-series access,
candidate development-output access, and confirmation-series access as false.
H3 is supported as recorded [E02] [E03] [E04] [E10]. The locked confirmation
roster remains metadata-only. Its station IDs and coordinates were read solely
to enforce disjointness and the 75 km partition; no confirmation daily or
subdaily target series was read or summarized, and the roster was not
replaced.

### Post-acceptance disposition

The operator subsequently accepted Yuma and Stovepipe Wells as functionally
adequate hot-arid development evidence for continuation. This retires the
five-site floor for a successor package and removes the proposed corpus-
expansion detour. It does not change H1, the A9c2 hold, or any census row
[E12].

A future A9c3 comparison must retain both sites, give each equal total weight,
publish pooled and site-specific uncertainty, and preserve actual event
frequencies. Candidate-blind precision and power remain diagnostics rather
than a new roster-construction gate. Nonfinite estimators and candidate/model
failures remain legitimate holds. A9c3 execution, A9d confirmation, and runtime
work are not authorized by this disposition [E12].

## Limitations and validity

Internal validity is strong for the deterministic result under the registered
inputs: every input, the program, the freeze, and the output are hash-bound;
the complete reason arithmetic reproduces; and the output embeds the freeze
hash. Chronology is recorded by the pre-evaluation freeze and its embedded
identity, not by an external timestamp authority.

Construct validity is narrower. The A8a screen uses legacy CLIGEN
parameter/catalog precipitation and temperature climatology plus longitude. It
is not a potential-evapotranspiration index or a physical classification of
aridity. A nearest legacy descriptor may not represent the exact USCRN point,
even within 75 km. The 75 km crosswalk radius was prospectively fixed but was
not sensitivity-tested; it was nonbinding because all 113 metadata-base sites
had a descriptor within the radius [E04] [E05] [E06].

External validity is limited to active and operational USCRN stations in the
frozen listing that were commissioned by the cutoff. Later-commissioned,
inactive, non-USCRN, and other subhourly-network locations were not evaluated.
The result is therefore not a census of all hot-arid climates or all sources
capable of measuring storms.

The package did not test whether five sites are scientifically necessary,
whether two sites could support a calibrated grouped estimator, or whether
either candidate model is adequate. Those downstream questions were blocked
by the prospectively registered roster gate. Access nonoccurrence is supported
by the repository's declared boundaries and program inputs, not independent
system-call monitoring.

The operator accepts these unresolved precision and generalization limits for
research continuation. That governance decision should not be reported as a
statistical demonstration that two sites equal five or that users at other
hot-arid locations can expect local calibration [E12].

## Conclusions

The exact A9c2 roster design cannot supply its required five hot-arid
development locations: only Yuma and Stovepipe Wells pass, while the only
other descriptor match is locked confirmation site Mercury. A9c2 closes at
`HOLD-A9C2-HOT-ARID-ROSTER` before any station-series or candidate access. It
neither validates nor rejects station-balanced grouping or either successor
model class.

The operator has accepted the two locations as functionally adequate for the
next research stage. The next action is therefore to scaffold a separate A9c3
two-site grouped observed-development comparison, not conduct another corpus
search. A9c3 must preserve the A9c2 outcome, expose the limited spatial
support, and return to testing both successor model classes. A9c3 execution,
A9d, and runtime work remain unauthorized until separately dispatched [E12].

## Reproducibility and data availability

The work package retains the exact metadata freeze, 113-row census, complete
disposition ledger, deterministic inventory program, accepted-site distance,
claim ledger, review, and verifier. Rerunning the program without `--write`
recomputes the census and requires byte-identical output [E10]. The accepted
pairwise-distance ledger binds its source-inventory hash [E11].

No new large artifact or station-series object was created, so A9c2 adds no
Git LFS object. The package-local LFS rule remains available if a later,
separately authorized package acquires large evidence. The report contains no
operator-specific path, credential, confirmation target object, or
nonredistributable reading-copy link.

Revision 2 retains the accepted revision-1 report, manifest, review, and gate
hashes in the post-acceptance disposition. It changes no machine evidence,
hypothesis outcome, or A9c2 terminal; it records the operator's accepted risk
and successor direction [E12].

## References

- [R01] NOAA National Centers for Environmental Information. *U.S. Climate
  Reference Network Station Listings*. No DOI.
  [Official station-listing page](https://www.ncei.noaa.gov/access/crn/station-listing),
  metadata snapshot accessed 2026-07-15.
- [E01] A9c2 prospective context and design contract.
- [E02] A9c2 execution dispatch and exact source commit.
- [E03] A9c2 prospective metadata-roster freeze.
- [E04] A9c2 complete hot-arid metadata census and terminal.
- [E05] A8a hot-arid descriptor-stratum selection contract.
- [E06] A8a legacy parameter/catalog metadata inventory.
- [E07] A9c hash-pinned official USCRN station-listing snapshot.
- [E08] A9a locked metadata-only confirmation roster.
- [E09] A9c post-acceptance operator disposition and A9c2 rationale.
- [E10] A9c2 deterministic metadata-census implementation.
- [E11] A9c2 complete accepted-site pairwise-distance ledger.
- [E12] A9c2 post-acceptance operator disposition retaining the terminal and
  accepting two-site evidence for research continuation.
