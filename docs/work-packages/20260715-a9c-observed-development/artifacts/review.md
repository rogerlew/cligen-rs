# A9c consolidated internal review

Review boundary: accepted availability-hold report revision 2 and A9c2
prospective scaffold
Report SHA-256:
`a7852d292a82cd870bb8e8db63c0b438cc6cb317d9915ba8f6bde251b83ac7b0`

Revision 1 remains an accepted historical boundary:

- report SHA-256:
  `6a4d500225f34e83c63259d566725ef79d054549a0c9b5b83e44ec8c2483032b`;
- review SHA-256:
  `89b098fdc4e2247812d16a19abd3df16d553aa20d727d02c21bc0ade8d4042f0`;
  and
- terminal: `HOLD-A9C-GATE-CALIBRATION`.

Three read-only roles independently inspected revision 2: an evidence analyst
recomputed counts, rates, thresholds, access, and the hash cascade; a methods
analyst reconstructed the grouped design and reuse boundaries; and a
consistency/public-safety analyst checked report governance, seasonal
aggregation, spatial language, specification versioning, links, LFS, naming,
and immutable predecessors. The lead author alone edited repository files.

## Accuracy lens

Verdict: ACCEPT

- Recounted 180 append-only USCRN access rows as 12 stations × 15 years.
- Rehashed and decompressed all 40 Daymet and 24 USCRN normalized objects;
  the source verifier reports zero confirmation access.
- Recounted candidate-blind calibration as seven statistical families × two
  horizons × 500 replicates = 7,000 identities and 14 thresholds.
- Recomputed AZ Yuma 27 ENE as 136 / 7 = 19.4286 and CA Stovepipe Wells 1 SW
  as 97 / 7 = 13.8571 events per station-year. Revision 2 reports 19.4 and
  13.9, rounded to one decimal, and limits the rates to those sites, period,
  event definition, and QC rules.
- Reapplied the revision-1 registry: both sites fail the 150-event time-to-
  peak and peak-ratio rules and the 200-event joint rule, yielding 0/2
  available stations in three cells. Duration remains eligible only through
  A9c's distinct frozen hierarchy.
- Confirmed no repository artifact calibrates the 150/200 counts as empirical
  hot-arid precision or power minima. A9c's 7,000 null identities calibrate
  objective-distance thresholds, not station sample-size floors.
- Revalidated all five completed fit artifacts against the official schema
  and self-hash. They have no role in the terminal or revision-2 correction.

## Scientific-validity lens

Verdict: ACCEPT

- Revision 2 preserves the prospective A9c rule and terminal while correcting
  the follow-on interpretation. It neither passes a failed cell nor changes a
  hypothesis outcome.
- The report distinguishes a registered evaluation-design mismatch from a
  climate-model failure and from a generalized claim that hot-arid
  observations are intrinsically inadequate.
- H1--H4 provenance and outcomes still match the original pre-access
  contracts. The operator disposition is post-acceptance interpretive
  evidence, not a confirmatory hypothesis amendment.
- The first failed upstream gate still stops simulation, ranking, Pareto
  selection, A9d freeze, and confirmation access.
- A9c2 is explicitly prospective: at least five metadata-selected hot-arid
  locations, equal station mass within registered aggregation cells,
  candidate-blind precision/power calibration, site-heterogeneity guards,
  symmetric fit-side rules, and a complete new campaign identity.
- A9c2 must rerun all fits, nulls, objective vectors, and selection because the
  registry, estimator, hierarchy, and campaign RNG domain change.

## Consistency and public-safety lens

Verdict: ACCEPT

- Revision 2 retains the prior accepted report/review hashes and cites the
  hash-bound operator disposition as E09.
- A9b, SPEC-A9 revision 1, A9a's objective registry, and every canonical A9c
  freeze/result/implementation artifact remain byte-immutable.
- A9c2 requires a versioned SPEC-A9 grouped-evaluation amendment and a new
  objective registry; candidate-law IDs remain independent and unchanged.
- Group formulas preserve the original seasonal aggregation for duration,
  time-to-peak, and peak ratio; joint dependence retains season in its rank
  vector. Zero-event station-seasons remain explicit.
- The A9c2 contract distinguishes confirmation partition separation from
  within-group spatial independence and requires a spatial-dependence
  uncertainty treatment.
- A9c normalized observed objects may be reused only as explicitly exposed
  inputs. No fit, threshold, result, or selection artifact is relabeled, and
  no exposed object can become confirmation evidence.
- The locked confirmation roster remains metadata-only. No confirmation URL,
  byte, hash, summary, quality result, or event count appears in A9c2.
- A9c2 uses a package-local Git LFS rule, avoiding any change to the root
  `.gitattributes` that A9c's implementation manifest hash-binds.
- Report/package/catalog links resolve, copyrighted reading copies remain
  unlinked, and no production crate or vendored Fortran path changed.

## Findings and dispositions

| ID | Severity | Finding | Disposition | Recheck |
|---|---|---|---|---|
| A9C-REV-001 | P3 | Five fits completed before the availability check interrupted the remaining fit stage. | Report exact partial count and prohibit candidate inference; retain immutable fits as exposed evidence. | Report and inventory agree; PASS. |
| A9C-REV-002 | P3 | Four pre-ranking tooling defects could otherwise be mistaken for outcome-driven amendments. | Retain the correction/access boundary in `pre-ranking-corrections.md`. | Zero candidate development scores existed; PASS. |
| A9C-POST-001 | P2 | Revision 1's conclusion treated 150/200 as successor support targets although A9 never calibrated them as hot-arid sample-size minima. | Preserve the A9c hold but revise the interpretation, claim ledger, re-entry requirements, package, report, and roadmap; bind the operator disposition as E09. | Terminal and evidence are unchanged; revision 2 no longer makes the insufficiency inference; PASS. |
| A9C-POST-002 | P2 | An early revision-2 draft called the two counts ordinary realizations, overgeneralizing from two sites and seven years. | Limit the rates to the observed sites, period, six-hour event definition, and QC rules. | Report, disposition, ledger, and contract use bounded wording; PASS. |
| A9C-POST-003 | P2 | An early A9c2 scaffold omitted seasonal cells, fit-side rule versioning, and a complete objective/specification amendment. | Require station balancing within registered season cells, explicit zero-event behavior, symmetric fit-side identifiability, a SPEC amendment, and `a9c2-objective-registry-v1`. | Package and context contract contain every boundary; PASS. |
| A9C-POST-004 | P2 | An early A9c2 draft tied power alternatives to registry floors that do not exist for all storm objectives. | Require newly justified candidate-neutral perturbations, at least 0.80 power, and a separately frozen precision limit; prohibit treating the 0.02 normalization floor as an alternative. | Context contract is explicit; PASS. |
| A9C-POST-005 | P2 | Reuse and spatial wording could have implied relabeled A9c results or independence from a distance rule. | Limit reuse to exposed normalized inputs, require new fits/nulls/results, call 75 km partition separation, publish within-group distances, and model residual spatial dependence. | Reuse and partition language agree across the scaffold; PASS. |

Residual uncertainty: A9c2 has not inventoried eligible locations or ratified
the exact candidate-neutral perturbations and precision bound. Those are
explicit pre-access design-freeze obligations with named holds, not results of
this scaffold. Neither candidate class has yet been compared on a complete
development matrix.

Final verdict: **ACCEPT**

Open P1: 0
Open P2: 0
