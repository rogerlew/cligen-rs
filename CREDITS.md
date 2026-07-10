# Credits

cligen-rs is a source-code-authority Rust port of CLIGEN 5.32.3
([ADR-0001](docs/decisions/0001-source-code-authority-port.md)). A
faithful port reproduces other people's work bit-for-bit — so the
credit surface of this repository is, first and foremost, the credit
surface of CLIGEN itself: roughly four decades of model development,
maintenance, and numerical craftsmanship. This file records that
lineage as documented in the vendored source's own changelog
(`reference/cligen532/cligen.f`), the USDA-ARS [CLIGEN
page](https://www.ars.usda.gov/midwest-area/west-lafayette-in/national-soil-erosion-research/docs/wepp/cligen/),
and C. R. Meyer's ["General Description of the CLIGEN Model and its
History"](https://www.ars.usda.gov/ARSUserFiles/50201000/WEPP/cligen/CLIGENDescription.pdf).

## The CLIGEN model

- **Arlin D. Nicks** and **Gene A. Gander** (USDA-ARS, Durant,
  Oklahoma) — original authors of CLIGEN, developed as the weather
  generator for the Water Erosion Prediction Project (WEPP). Their
  last significant changes date to the mid-1990s; Dr. Nicks passed
  away in July 1997. Every distributional mechanism this port
  reproduces — the per-station monthly parameterization, the
  wet/dry-chain precipitation model, the storm-shape outputs (time to
  peak, peak intensity, duration) that distinguish CLIGEN from other
  weather generators — is their design.
- **Clarence W. Richardson** (USDA-ARS, Temple, Texas) — author of
  WGEN, the foundational stochastic weather generator of this model
  family, and direct contributor of the Fourier interpolation code
  (`fouri1`/`fouri2`, received January 1999 per the source comments).
- **David Hall** and **Dayna Scheele** (USDA Forest Service, Moscow,
  Idaho) — recovered the code and data from Dr. Nicks' computer,
  cleaned the station data files, and substantially expanded the U.S.
  station database. Hall also supplied many of the variable
  definitions that made the 1999 recode possible.
- **Bofu Yu** (Griffith University, Australia) — identified the
  rainfall-intensity unit-conversion error in 1999 and supplied
  corrected code. His replacement routines are the live intensity
  path in CLIGEN 5.x, and therefore in this port (`alphb`, `r5monb`).
- **Charles R. (Chuck) Meyer** (USDA-ARS National Soil Erosion
  Research Laboratory, West Lafayette, Indiana) — radically recoded
  the source in Fall 1999 for clarity and maintainability,
  incorporated Yu's corrections, and — after discovering the random
  number generator was not performing correctly — introduced the
  statistical quality control on the RNG stream (Kolmogorov-Smirnov
  and confidence-interval acceptance with regeneration) that is
  CLIGEN 5's signature feature. The QC-regeneration draws are
  trajectory-load-bearing; this port replicates them draw-for-draw.
  Chuck Meyer passed away on 4 February 2007; the journal paper
  formalizing his quality-control method appeared posthumously
  (Meyer, Renschler & Vining, below).
- **Maintainers, per the source changelog**: **Jim Frankenberger**
  (USDA-ARS NSERL) — versions 5.3 through 5.32 (dew point, solar
  radiation, observed-mode tpeak fixes) and host of the canonical
  source repositories ([cligen5](https://github.com/jfrankenberger/cligen5),
  [cligen4](https://github.com/jfrankenberger/cligen4));
  **Bill Rust** — 5.30001 (wet/wet & wet/dry interpolation-order
  fix); **Fred Fox** (USDA-ARS Wind Erosion Research Unit) — 5.30002
  and 5.322, with bug reports alongside **Larry Wagner** (WERU);
  **Roger Lew** (University of Idaho) — 5.32.1 (leap-year rule) and
  5.323 (observed-mode end-of-file fix), the pinned port baseline.
- **Institutions**: the USDA Agricultural Research Service —
  above all the **National Soil Erosion Research Laboratory** (West
  Lafayette, Indiana) — the USDA Forest Service (Moscow, Idaho), and
  Griffith University.

## Numerical code embedded in CLIGEN (ported in `acm.rs`)

The last ~2,400 lines of `cligen.f` embed a public-domain
special-function library that the quality-control chain depends on
(chi-square CDF inversion). Its own comment headers credit:

- **DCDFLIB** — "ACM Chi-square code from Anderson Cancer Center in
  Texas": Barry W. Brown, James Lovato, and Kathy Russell, University
  of Texas M.D. Anderson Cancer Center. Chosen by Meyer specifically
  because it is public domain — the copyrighted Numerical Recipes
  chi-square it replaced could not be redistributed as source.
- **Alfred H. Morris, Jr.** (Naval Surface Warfare Center, Dahlgren,
  Virginia) — the underlying gamma/error special functions, and
  `ipmpar`, his adaptation of `I1MACH` by P. A. Fox, A. D. Hall, and
  N. L. Schryer (Bell Laboratories).
- **J. C. P. Bus and T. J. Dekker** — the guaranteed-convergence
  zero-finder (ACM Transactions on Mathematical Software) used for
  CDF inversion.
- **Abramowitz & Stegun**, *Handbook of Mathematical Functions*
  (1965), and N. T. Kottegoda, *Stochastic Water Resources
  Technology* (1980) — the cited mathematical sources for the
  generic deviate-generation approach.

## Numerical routines adopted by the Rust port

Bit-identity with the pinned reference build required reproducing the
reference platform's transcendental math exactly. Where the Rust
`libm` crate diverged (adjudicated empirically, per the repository's
coding standard §1.3), `libm_pinned.rs` transcribes published
implementations:

- **Arm Limited, optimized-routines** (pinned commit `e17e9860…`,
  MIT OR Apache-2.0 WITH LLVM-exception) — `logf`, `cosf`, `sinf`,
  `exp`, `expf`. These are the algorithms glibc ships for these
  functions.
- **Sun Microsystems ("SunPro") fdlibm**, with float conversions by
  **Ian Lance Taylor** (Cygnus) as carried in **NetBSD** and
  **glibc** — `atanf`, `tanf`, `acosf`. Full license provenance,
  including the per-file analysis and license texts, lives in the
  work-package record
  ([libm-pinned-provenance](docs/work-packages/20260709-rng-deviates-port/artifacts/libm-pinned-provenance.md),
  [atanf-pinned-provenance](docs/work-packages/20260709-par-monthlies-port/artifacts/atanf-pinned-provenance.md)).

There is a pleasing symmetry here: in 2000, CLIGEN swapped Numerical
Recipes for public-domain ACM code so the source could be freely
distributed; this port made the same style of decision when it
transcribed permissively licensed reference implementations instead
of copying the LGPL glibc carrier.

## Station and climate data

- The station parameter (`.par`) databases descend from the climate
  records compiled by Nicks et al. for WEPP (1995 database), expanded
  by the USDA Forest Service, and updated by USDA-ARS from 1974-2013
  records (Srivastava et al. 2019). The fixture `.par` files in this
  repository come from that lineage, via WEPPcloud.
- The observed-mode fixture series derive from **DAYMET**
  (mt-wilson-ca) and **gridMET** (fish-springs-ut) gridded daily
  data, prepared through WEPPcloud; the underlying station
  observations trace to NOAA/NWS cooperative networks.

## Publications

- Nicks, A. D., L. J. Lane, and G. A. Gander. 1995. "Weather
  Generator." Chapter 2 in *USDA-Water Erosion Prediction Project:
  Hillslope Profile and Watershed Model Documentation*, NSERL Report
  No. 10, USDA-ARS-NSERL, West Lafayette, Indiana.
- Richardson, C. W., and D. A. Wright. 1984. *WGEN: A Model for
  Generating Daily Weather Variables*. USDA-ARS, ARS-8.
- Meyer, C. R., C. S. Renschler, and R. C. Vining. 2008.
  "Implementing quality control on a random number stream to improve
  a stochastic weather generator." *Hydrological Processes*
  22(8):1069-1079. doi:10.1002/hyp.6668 (online 2007; published
  posthumously for Meyer).
- "Implementing Quality Control Techniques for Random Number
  Generators to Improve Stochastic Weather Generators: The Cligen
  Experience." 2002 (Applied Climatology conference; as listed on the
  ARS CLIGEN page).
- "Evaluation of CLIGEN Precipitation Parameters and their
  Implication on WEPP Runoff and Erosion Prediction." 2003 (as listed
  on the ARS CLIGEN page).
- Srivastava, A., D. C. Flanagan, J. R. Frankenberger, and
  B. A. Engel. 2019. "Updated climate database and impacts on WEPP
  model predictions." *Journal of Soil and Water Conservation*
  74(4):334-349. doi:10.2489/jswc.74.4.334.
- Meyer, C. R. (undated). "General Description of the CLIGEN Model
  and its History." USDA-ARS NSERL notes.

## The Rust port

- **Roger Lew** (University of Idaho) — project direction and
  operation: the port posture (ADR-0001), the fixture cohort, the
  `inp.yaml` contract decision, and every ratification in the
  work-package record; also maintainer of the upstream 5.32.1/5.323
  fixes and of WEPPcloud, the production context this port serves.
- **Claude** (Anthropic; Claude Code) and **Codex** (OpenAI) — the
  two AI executors of the staged work-package model: Claude authored
  the design-setting spines, contracts, and adjudications; Codex
  completed, gated, and cross-reviewed each package; each reviewed
  the other. The full execution record — every stage, review,
  finding, and gate — lives in
  [`docs/work-packages/`](docs/work-packages/README.md).

## Licensing

CLIGEN is a work of the United States Government (USDA-ARS) and is in
the public domain; the pinned copy and its lineage are documented in
[`reference/cligen532/PROVENANCE.md`](reference/cligen532/PROVENANCE.md).
The Rust code is licensed under [Apache-2.0](LICENSE); adopted
numerical routines carry their upstream notices in
`crates/cligen/src/libm_pinned.rs` and the license texts vendored in
the work-package artifacts.
