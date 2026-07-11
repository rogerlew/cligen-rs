# The Legacy RANDN Generator: A Grounded Literature Review

Date: 2026-07-10
Author: Claude Code
Status: informational — a literature review, not a decision record.
Evidence classes used below: **[source]** = read directly from
`reference/cligen532/cligen.f` this session; **[read]** = claim
verified against a paper read this session (local copy archived);
**[lit]** = standard published result, local copy archived but not
exhaustively read; **[cited]** = known only through another source or
abstract — no local copy.

Local copies of the copyrighted sources live in
`references/copyrighted/` (gitignored — cited, never redistributed);
SHA-256 identities are in §References so the local corpus is
verifiable.

## 1. What the legacy generator actually is [source]

`RANDN` (`cligen.f:1980-2015`) carries no citation, author, or date —
uniquely among CLIGEN's numerical routines. Its state is four small
integers holding ten decimal digits in groups (3-2-3-2). Each call:

```fortran
k(4)=3*k(4)+k(2)
k(3)=3*k(3)+k(1)
k(2)=3*k(2)
k(1)=3*k(1)
```

followed by decimal carry propagation (`/1000`, `/100` splits), with
the output assembled from the digit groups as a fixed-point decimal in
[0,1) and a rejection loop excluding exact 0 and 1. On the composite
state N = k4·10^8 + k3·10^5 + k2·10^3 + k1, the digit-group update
with its cross-feeds is **exactly the multiplicative congruential
generator N' = 100003·N mod 10^10** (verified algebraically and by
10,000-state simulation against the Fortran update, R1 correction of
this document's first revision, 2026-07-10): the by-3 multiplies plus
the k2→k4 / k1→k3 cross-adds implement a = 10^5 + 3 in digit-group
arithmetic. ~33 bits of state, zero increment, composite modulus.

The structure is a fingerprint of its era: early-1980s portable
Fortran could not assume a 32-bit multiply without overflow, so
portable generators simulated wide arithmetic in small decimal chunks.
**The exotic design is a portability workaround, not a statistical
design.** The seeding scheme is equally era-bound: ten fixed
block-data seed vectors (`k1..k10`), one stream per weather parameter,
with the `-r` option a *burn count* (N discarded draws per stream),
not a seed.

By the selection criteria already standard when it was written (Knuth
vol. 2's spectral-test guidance), the parameters are textbook-poor:
a = 100003 sits essentially **at √m** (√10^10 = 10^5), the classic
bad-lattice zone where consecutive pairs concentrate on a coarse 2-D
lattice; the modulus is composite (2^10·5^10), so the multiplicative
zero-increment form caps the period at λ(10^10) = 5·10^8 and imposes
seed-divisibility structure; and the output is quantized to the
10-decimal-digit state. No modern battery
result exists for this exact generator — see §5 for the cheap
executable question this repository is now uniquely positioned to
answer — but its class fails TestU01's SmallCrush categorically
[cited: L'Ecuyer & Simard 2007].

## 2. Honest limitations — three layers

Conflating these layers is the standard mistake in discussing legacy
CLIGEN; they have different owners, different fixes, and different
consequences.

### Layer 1 — the RNG itself is defective [read]

Meyer, Renschler & Vining (2008 — online 2007; p. 1) report: *"None of the many
RNGs we tested satisfactorily produced the target distribution…
distributions whose means do not even match the mean they were
generated from, regardless of the length of run."* Persistent bias
independent of run length is a generator defect, not sampling noise —
a correct generator's sample means converge at the CLT rate.

Two framing cautions when reading that paper today:

- Its generalization to "any model that employs an RNG" overreaches
  by modern standards. BigCrush-clean generators (§3) do not exhibit
  mean bias; what every generator exhibits is *sampling variability*
  at n = 31, which is a property of sampling, not of the generator.
  The paper's evidence of genuine defect and its evidence of ordinary
  small-sample variation are not fully separated.
- The generators "tested" are not identified with parameters, so the
  finding cannot be checked against the modern literature
  generator-by-generator.

### Layer 2 — the QC is a patch with real tradeoffs, applied more carefully than folklore suggests [read]

CLIGEN 5.x's response (Meyer et al. 2007) was not to replace the
generator but to reject its output: Kolmogorov-Smirnov tests on
uniform batches, confidence-interval tests on normal-deviate means and
SDs, regenerate on failure. Two details from the paper deserve more
credit than they usually get:

- The QC tests **cumulatively from run start**, not per-month
  independently, deliberately: *"this permits relaxing the constraints
  as the run progresses so that we preclude fewer extreme events than
  if we controlled each month independently."* Meyer understood that
  rejection clips variability and mitigated it.
- The acceptance threshold is disclosed as unprincipled: *"We
  arbitrarily selected a probability threshold of 50%."*

The costs, some documented in the source and some measured in this
repository:

- **Conditioning**: post-QC output is no longer a random sample of the
  fitted process; it is a sample conditioned on looking typical. The
  motivation was real — Baffaut et al. (1996, via Meyer et al. 2007)
  found 30-year runs insufficient for stable WEPP soil-loss averages
  (50-100+ years needed), and QC makes short runs converge to their
  inputs. That is variance reduction purchased with distributional
  honesty, and it was never labeled as a modeling choice.
- **Seed-dependent retry storms** [source + measured]: the QC loop's
  cost varies wildly with seed state. Historically it produced
  outright infinite loops (Yuma and Wupatki, AZ — the `iredo = 10,000`
  escape hatch inserted by Meyer in v5.105, 04/2001; its
  10,000th-retry bug was fixed in v5.220 — cligen.f header).
  This repository measured the same machinery as the burn-17
  pathology: 6.2× runtime versus burn-0 on one host
  (`docs/work-packages/20260710-cli-runtime-profile/`).
- **A false-precision aura**: QC on the batch does not and cannot fix
  the layer-3 issues below, but its presence invites the assumption
  that "the statistics are controlled."

### Layer 3 — model-structure limits no RNG can fix [read]

- **Parameter independence**: Meyer's own history notes concede
  *"Experience and common sense tell us that these parameters are NOT
  independent"* — only Tmax/Tmin/Tdew were coupled (2004); radiation
  and precipitation remain independent of each other.
- **Two-state Markov memory**: wet/dry persistence is one day deep;
  persistent spells and drought clustering are structurally absent.
- **Overdispersion / missing interannual variance**: the canonical
  WGEN-family defect. Katz & Parlange (1998, abstract): *"Simple
  stochastic models fit to time series of daily precipitation amount
  have a marked tendency to underestimate the observed (or
  interannual) variance of monthly (or seasonal) total
  precipitation."* Wilks & Wilby (1999, p. 341): *"It seems to be a
  general characteristic of weather generator models that their
  interannual variability is smaller than that of the corresponding
  observed data"* — and richer submodels (higher-order chains, better
  amount distributions) *"could be increased but still fell short of
  observed climatic variability on average."* Their preferred
  explanation: real climate statistics drift year to year; a
  generator whose parameters follow a fixed annual cycle cannot
  express that.

The irony worth recording: the headline complaint that motivated the
QC era — Johnson et al. (1996, via Meyer et al. 2007): CLIGEN *"poorly
reproduced year-to-year variance… did a dismal job of reproducing the
monthly SDs, failing all 72 tests"* — is substantially a layer-3
symptom. Batch-level QC does not create low-frequency variability; by
suppressing anomalous months it plausibly reinforces underdispersion,
subject to the cumulative-testing mitigation above. No study we
located quantifies the QC's net effect on CLIGEN's interannual
variance — an open question, and a cheap one for this repository
(§5).

### The record of the search — what the changelog preserves [source; readings tagged individually]

The version header of `cligen.f` is a lab notebook of the QC's whole
life, and it deserves to be read as one narrative — with the
chronology the source actually records:

- **2000 — the QC is born, not arrived at.** The 5.1-era header block
  states that the 11/11/99 CLIGEN release "does not include the
  RNG-QC code," and that this version adds "a feedback loop … to
  apply 'quality control' to the distributions as they are being
  produced," testing "both the mean and the variance of the standard
  normal deviates … using a prescribed value for each (`thresh` &
  `thres2`) set here at 50 percent … on the population of numbers
  generated to the current point in the simulation." Conditioning —
  including the 50% thresholds *and* the cumulative-from-run-start
  design — is the opening move of the 5.x line, motivated by
  "statistical testing demonstrat[ing] that more often than chance
  would dictate, the starting distributions were doing a poor job of
  reproducing the numbers they originated from."
- **5.105 (04/2001) — the escape cap, and a road not taken.** Yuma AZ
  and Wupatki AZ hung the QC loop ("The only exit was production of a
  distribution meeting the acceptance criteria. Not guaranteed!");
  Meyer inserted the `iredo` 10,000-retry escape himself. The same
  entry records an alternative he tried and declined: "It was
  possible to greatly improve the situation for WV by changing the
  random seed k8(4) from 31 to 41, but this is not the solution
  pursued." Reseeding was on the table and rejected. (Yuma is also
  the station that dominates the Q3 dissection's retry pathology,
  25 years later.)
- **5.200 (03/2003)** — a parameter guard: monthly precipitation skew
  clamped to ±4.5, because high skew made "90+ percent of the
  generated values" negative under Pearson Type-III.
- **5.212 (07/2003)** — a structural fix: Tpeak regenerated only on
  wet days after chi-square tests "revealed [it] was _not_ uniformly
  distributed." The same entry contains the era's thesis, describing
  the generic rejection sampler in `DSTG`: it "requires a uniform
  random number generator which functions correctly. Without using a
  quality control filter, we have not found one which does" — a
  retrospective justification of the 2000 decision, written three
  years into living with it.
- **5.213 (08/2003)** — an analytical fix: the `DSTG` upper limit
  corrected from `ai` to 5.795 by integrating the density in Maple
  (chi-square on 5 cases improved from P ≥ 0.98 to P < 0.625). The
  entry cites Zhang & Garbrecht's storm-characteristics critique.
- **5.220 (08/2003)** — a chi-square uniformity test (up to 20 bins)
  is added to the existing QC, and a "long-standing minor coding bug
  in [the] 10,000th (unsuccessful) retry" — Meyer's own 5.105
  mechanism — is fixed.
- **5.221 (09/2003)** — an external verification harness (`rand_nrs`,
  a file existing "solely to verify quality of random numbers") is
  disabled; its commented `open(73,…)` survives at `cligen.f:3441`.
- **5.223–5.2253 (10/2003–01/2004)** — QC extended to `DSTG` (with
  the two-uniform gamma correction), and two successive redesigns of
  the temperature scheme (the smaller-SD anchoring, after a
  suggestion by Fred Fox). A NOTE in this era calls the QC "totally
  necessary and to date not known to be provided in any other
  stochastic model."
- **5.2255 (05/2004)** — chi-square abandoned: "Running Excel with
  varying bin sizes from 10 to 20 showed that the Chi-square test
  gave very inconsistent results… for 30 year runs at 7 stations";
  reading "articles on the Internet" pointed to K-S for continuous
  distributions. The K-S critical value was then calibrated to the
  same pre-existing 50% policy: "One problem: I could not find
  D-value for P=50%," so 0.8276 was derived "interatively" [sic]
  using a spreadsheet. (The 50% level itself dates to the 2000
  `thresh`/`thres2` design above; 5.2255 extended it to the new
  test, and the paper later disclosed the level as arbitrary —
  Layer 2.)
- **5.2256–5.22564 (07–10/2004)** — tuning: batch lot 20 → 30 after a
  Bloomington infinite loop; the `R5MONB` dry-climate fix.

Three readings, tagged:

1. **[source] The repertoire was broad and the QC was permanent.**
   Conditioning came first (2000) and was never revisited as a
   decision; what evolved for four years was everything around it —
   the tests (CI → +χ² → K-S), the escape valve, the lot size — while
   genuinely distributional defects were fixed at their proper layer
   when he could see them (parameter guard 5.200, structural fix
   5.212, analytical fix 5.213). Reseeding (5.105) and RNG
   replacement ("many RNGs … tested" — Layer 1) were both examined
   and declined. The dead `chitst` subroutine, the commented
   `"Failed Chi-square test"` writes, and the unit-73 fossil are the
   abandoned branches still visible in the source.
2. **[analysis] The acceptance criterion biased the evidence toward
   conditioning.** A 50%-level test rejects roughly half of correct
   samples by construction, so its rejection rate cannot by itself
   distinguish a defective generator from ordinary sampling
   variability — and per the history notes, replacement candidates
   were judged partly by outlier rates against that same family of
   expectations (outliers "exceeding the expected percentage", not
   any-outlier). The paper itself acknowledges the circularity
   objection. This does not make QC the *only* intervention that
   could have satisfied the criterion (moment matching or stratified
   schemes would too); it means the evidence that "no RNG works"
   was partly a property of the yardstick, and the yardstick was
   itself the QC's acceptance rule. RANDN's genuine defects (Layer 1)
   are established on independent grounds.
3. **[source + measured] No year-level degree of freedom appears
   anywhere in this record.** Every remedy in the changelog operates
   within the fixed-monthly-parameter frame; interannual dispersion
   was a known literature complaint (Johnson et al. — Layer 3) but
   no entry contemplates a mechanism for it. The Q3 dissection
   (`docs/work-packages/20260710-q3-qc-filter-dissection/`) later
   quantified both sides of the tradeoff Meyer engineered and
   disclosed — and confirmed the missing variance is structural,
   beyond any RNG or conditioning setting.

## 3. Modern generators and the actual tradeoffs

Four decades of theory and compute later, the state of the art [lit]:

| Generator | Reference | Properties relevant here |
|---|---|---|
| PCG family | O'Neill 2014 (HMC-CS-2014-0905) | LCG core + output permutation; BigCrush-clean; 2^64+ periods; streams |
| xoshiro256++/** | Blackman & Vigna 2021 (ACM TOMS 47(4)) | Scrambled linear; BigCrush-clean; jump-ahead for parallel streams |
| SplitMix64 | Steele, Lea & Flood 2014 | Splittable; the `fast_batch_v0` spike's producer |
| Philox (counter-based) | Salmon et al. 2011 (SC'11, best paper) | `value = f(key, counter)`: random access, zero carried state, perfect parallel reproducibility |
| TestU01 | L'Ecuyer & Simard 2007 (ACM TOMS 33(4)) | The acceptance instrument: SmallCrush/Crush/BigCrush batteries |

Against `RANDN`, the statistical tradeoff is zero — there is nothing
the legacy generator does better. The *real* tradeoffs are ecosystem
ones:

1. **Trajectory compatibility.** Every historical CLIGEN output, and
   any calibration performed against those outputs, is bound to the
   legacy stream. This is why faithful mode exists and why any
   replacement must be a labeled, versioned generation profile
   (ADR-0001), never a silent swap.
2. **The QC question does not disappear — it changes meaning.** A
   perfect RNG still produces 31-day batches that fail a K-S test at
   a 50% threshold at substantial rates; that is sampling. With a
   clean generator, batch QC stops being a defect mask and becomes a
   pure modeling decision: honest sampling (fuller tails, slower
   downstream convergence) versus constrained/moment-matched sampling
   (Meyer's actual goal, made explicit). Either is defensible;
   the choice must be declared in the generation profile.
3. **A clean RNG exposes layer 3 rather than fixing it.** Interannual
   variance will not improve; anyone promised otherwise will be
   disappointed. Fixing it means model changes (parameter
   conditioning, low-frequency components — the post-1999
   literature), which are tier-2 augmentations with their own
   profiles.
4. **Parallel fit.** Counter-based generation (Philox) maps exactly
   onto the wepppy subprocess-per-hillslope architecture:
   `f(key = station/run, counter = year/day/parameter)` gives random
   access and reproducibility with no stream bookkeeping — and pairs
   naturally with the A1 provenance surface.

## 4. What would the original authors likely do today?

Grounded in their records, labeled speculation:

- **Nicks** hand-built decimal digit arithmetic because 1980s
  portability demanded it. The workaround's reason for existing is
  gone; nothing in his record suggests attachment to the mechanism
  over the model. He takes a library generator.
- **Richardson** kept evolving generators throughout his career
  (WGEN → GEM lineage) and contributed code to CLIGEN as late as 1999
  [source: `fouri1` header]. He is in the modern-generator camp by
  demonstrated behavior.
- **Meyer** is the interesting case. His 2002/2007 program — empirical
  batteries run against a distrusted generator — is the TestU01 ethos
  executed by hand, five years before he could have used TestU01
  (published 2007, the year of his death; the QC paper itself appeared
  posthumously — Meyer died 4 February 2007 [read: the paper's front
  matter]). Handed the modern toolbox, the natural reconstruction:
  BigCrush on day one, adopt PCG or Philox, and then confront what his
  QC was really about — sampling variability at n = 31 against WEPP's
  convergence needs. His stated goal ("achieve the desired
  distribution at the end of the run") says he keeps constrained
  sampling — but as a declared, principled feature, not an arbitrary
  50% threshold patching a broken generator.

That is, the original authors would plausibly land where this
repository's architecture already points: clean generator, explicit
conditioning policy, versioned profiles, provenance in every output.

## 5. Implications for cligen-rs

- **`fast_batch_v0`'s real question is not RNG quality.** SplitMix64
  is BigCrush-clean; `RANDN` is not. The open questions are the QC
  conditioning semantics and the column-5/9 structural semantics
  (see `20260710-fast-batch-rng-spike/artifacts/review-claude.md`
  F3 and §Guidance).
- **The faithful port makes `RANDN` testable for the first time.**
  Running the ported `randn`/`dstn1` through TestU01-class batteries
  is now a trivial spike — it would convert §1's "its class fails"
  [cited] into a measured result for the actual generator, and give
  the parity campaign a quantitative statement of what the legacy
  stream's defects actually are. Nobody has ever published this.
- **QC as measurement, not just mechanism**: running the faithful QC
  acceptance tests over any candidate profile's batches (rejection
  rate; faithful ≈ 0 by construction — exactly 0 only up to the
  source's 10,000-retry give-up path, `cligen.f:4302-4332`, which
  leaves a failed final batch in place; cap-hit events must be
  reported separately) prices exactly what a profile changed, in the
  model's own currency — the recommended headline metric.
- **Layer-3 fixes are tier-2 augmentations** (A-series, versioned
  profiles), not RNG work, and should never be promised as
  consequences of RNG modernization.

## References

Archived locally in `references/copyrighted/` (gitignored):

| Source | Local file | SHA-256 (first 16) |
|---|---|---|
| Meyer C.R., Renschler C.S., Vining R.C. 2008. "Implementing quality control on a random number stream to improve a stochastic weather generator." *Hydrol. Process.* 22:1069-1079. doi:10.1002/hyp.6668. [PDF via USDA ARS](https://www.ars.usda.gov/ARSUserFiles/50201000/WEPP/Meyer-Renschler-Vining2007.pdf) | `meyer-renschler-vining-2007-hyp6668.pdf` | `8424ed530f046436` |
| Meyer C.R. (undated). "General Description of the CLIGEN Model and its History." USDA-ARS NSERL notes. [PDF](https://www.ars.usda.gov/ARSUserFiles/50201000/WEPP/cligen/CLIGENDescription.pdf) (US Gov work, public domain) | `meyer-cligen-description-history.pdf` | `d5d9e10985c05ba0` |
| Katz R.W., Parlange M.B. 1998. "Overdispersion Phenomenon in Stochastic Modeling of Precipitation." *J. Climate* 11:591-601. [doi:10.1175/1520-0442(1998)011<0591:OPISMO>2.0.CO;2](https://journals.ametsoc.org/view/journals/clim/11/4/1520-0442_1998_011_0591_opismo_2.0.co_2.xml) | `katz-parlange-1998-overdispersion.pdf` | `90d90edca9ae7d7b` |
| Wilks D.S., Wilby R.L. 1999. "The weather generation game: a review of stochastic weather models." *Prog. Phys. Geog.* 23(3):329-357. [doi:10.1177/030913339902300302](https://journals.sagepub.com/doi/abs/10.1177/030913339902300302) | `wilks-wilby-1999-weather-generation-game.pdf` | `a5cc0fa064068b21` |
| O'Neill M.E. 2014. "PCG: A Family of Simple Fast Space-Efficient Statistically Good Algorithms for Random Number Generation." HMC-CS-2014-0905. [PDF](https://www.cs.hmc.edu/tr/hmc-cs-2014-0905.pdf) | `oneill-2014-pcg-hmc-cs-2014-0905.pdf` | `7e516ebe5de1a2c6` |
| Blackman D., Vigna S. 2021. "Scrambled Linear Pseudorandom Number Generators." *ACM TOMS* 47(4). [arXiv:1805.01407](https://arxiv.org/abs/1805.01407) | `blackman-vigna-2021-scrambled-linear.pdf` | `3aee2f2647867428` |
| Salmon J.K., Moraes M.A., Dror R.O., Shaw D.E. 2011. "Parallel random numbers: as easy as 1, 2, 3." SC'11 (best paper). [PDF](https://www.thesalmons.org/john/random123/papers/random123sc11.pdf) | `salmon-etal-2011-random123-philox-sc11.pdf` | `841f68114b052f43` |
| Srivastava A., Flanagan D.C., Frankenberger J.R., Engel B.A. 2019. "Updated climate database and impacts on WEPP model predictions." *JSWC* 74(4):334-349. [doi:10.2489/jswc.74.4.334](https://www.ars.usda.gov/ARSUserFiles/50201000/WEPP/JSWC-74-4-334-349.pdf) | `srivastava-etal-2019-jswc-74-334.pdf` | `d0526d9a710c3483` |

Cited without local archive (acquisition failed at authoring time —
AMS download service returned 500s; the umontreal host is
bot-shielded):

- Johnson G.L., Hanson C.L., Hardegree S.P., Ballard E.B. 1996.
  "Stochastic Weather Simulation: Overview and Analysis of Two
  Commonly Used Models." *J. Appl. Meteor.* 35:1878-1896.
  Characterized here solely via Meyer et al. 2007's direct quotation.
- L'Ecuyer P., Simard R. 2007. "TestU01: A C library for empirical
  testing of random number generators." *ACM TOMS* 33(4), art. 22.
  [Project page](https://simul.iro.umontreal.ca/testu01/tu01.html).
- Steele G.L., Lea D., Flood C.H. 2014. "Fast splittable pseudorandom
  number generators." OOPSLA 2014 (SplitMix).
- Baffaut C., Nearing M.A., Nicks A.D. 1996 — via Meyer et al. 2007.
- Knuth D.E. *The Art of Computer Programming*, vol. 2 —
  spectral-test criteria for LCG multipliers.
