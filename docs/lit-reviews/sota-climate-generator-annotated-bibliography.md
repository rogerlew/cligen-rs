# Climate and Weather Generators: Annotated Bibliography

Date: 2026-07-12
Author: OpenAI Codex
Status: informational; public-repository-safe; companion to
[`sota-climate-generator-gap-analysis.md`](sota-climate-generator-gap-analysis.md)

## Reading and acquisition conventions

This is a DOI-first reading map, not an assertion that every named system is a
direct CLIGEN peer. **Archived** means an unchanged PDF is redistributed under
the terms recorded in `references/open-access/manifest.tsv`. **Link-only**
means the paper or official record is public, but this repository does not
redistribute it. **Acquisition required** means a clean checkout has no
verified reusable full text; the citation and DOI are sufficient to request or
locate a lawful copy.

Annotations distinguish documented findings from their implication for
`cligen-rs`. A paper's inclusion is not a recommendation to adopt its model.

## Foundations and the CLIGEN baseline

### AB-01 — Richardson daily generator

C. W. Richardson (1981), “Stochastic Simulation of Daily Precipitation,
Temperature, and Solar Radiation,” *Water Resources Research* 17(1), 182–190.
DOI: [`10.1029/WR017i001p00182`](https://doi.org/10.1029/WR017i001p00182).
**Access: acquisition required.** This is the canonical precipitation-state
plus conditional multivariate-residual architecture from which many daily
generators descend. It is the right baseline for judging CLIGEN's missing
fitted lag, cross-variable, and wet/dry-conditioned dependence.

### AB-02 — Precipitation overdispersion

R. W. Katz and M. B. Parlange (1998), “Overdispersion Phenomenon in Stochastic
Modeling of Precipitation,” *Journal of Climate* 11, 591–601. DOI:
`10.1175/1520-0442(1998)011<0591:OPISMO>2.0.CO;2`.
**Access: acquisition required;** [official article record](https://journals.ametsoc.org/view/journals/clim/11/4/1520-0442_1998_011_0591_opismo_2.0.co_2.xml).
The paper establishes that richer daily occurrence or amount models alone do
not generally recover observed monthly/seasonal interannual variance and
examines low-frequency conditioning. It directly supports treating CLIGEN's
year-level climate state as a structural gap.

### AB-03 — Weather-generator review

D. S. Wilks and R. L. Wilby (1999), “The Weather Generation Game: A Review of
Stochastic Weather Models,” *Progress in Physical Geography* 23(3), 329–357.
DOI: [`10.1177/030913339902300302`](https://doi.org/10.1177/030913339902300302).
**Access: acquisition required.** This remains the most useful conceptual map
of occurrence, amount, multivariate, multisite, low-frequency, and
nonparametric approaches. Its identified weaknesses—interannual variation and
spatial/multivariate coherence—still organize the CLIGEN gap analysis.

### AB-04 — Extended Richardson dependence model

M. B. Parlange and R. W. Katz (2000), “An Extended Version of the Richardson
Model for Simulating Daily Weather Variables,” *Journal of Applied
Meteorology* 39, 610–622. DOI:
[`10.1175/1520-0450-39.5.610`](https://doi.org/10.1175/1520-0450-39.5.610).
**Access: link-only;** [official record](https://journals.ametsoc.org/view/journals/apme/39/5/1520-0450-39.5.610.xml).
The model extends the daily multivariate system to wind and dew point and
allows nonlinear, heteroscedastic conditional relations. It shows that the
same broad output variables as CLIGEN can be generated with fitted dependence
rather than mostly independent monthly draws.

### AB-05 — CLIGEN random-stream quality control

C. R. Meyer, C. S. Renschler, and R. C. Vining (2008; online 2007),
“Implementing Quality Control on a Random Number Stream to Improve a
Stochastic Weather Generator,” *Hydrological Processes* 22(8), 1069–1079.
DOI: [`10.1002/hyp.6668`](https://doi.org/10.1002/hyp.6668).
**Access: acquisition required.** This is the primary explanation for the
trajectory-conditioning machinery faithfully retained in CLIGEN 5.32.3. It
must be read with the repository's Q3 evidence: batch conditioning changes
dispersion but cannot create a missing low-frequency climate process.

### AB-06 — WEPP sensitivity to station-database change

P. Srivastava et al. (2019), “Updated Climate Database and Impacts on WEPP
Model Predictions,” *Journal of Soil and Water Conservation* 74(4), 334–349.
DOI: [`10.2489/jswc.74.4.334`](https://doi.org/10.2489/jswc.74.4.334).
**Access: link-only;** [USDA full text](https://www.ars.usda.gov/ARSUserFiles/50201000/WEPP/JSWC-74-4-334-349.pdf).
The study demonstrates that changes in climate inputs propagate materially to
WEPP runoff and erosion. It supports requiring downstream WEPP response, not
weather statistics alone, when promoting a new generator profile.

### AB-07 — WGEN versus LARS-WG

M. A. Semenov, R. J. Brooks, E. M. Barrow, and C. W. Richardson (1998),
“Comparison of the WGEN and LARS-WG Stochastic Weather Generators for Diverse
Climates,” *Climate Research* 10, 95–107. DOI:
[`10.3354/cr010095`](https://doi.org/10.3354/cr010095).
**Access: DOI/link-only.** The comparison contrasts daily Markov/distribution
models with LARS-WG's semi-empirical wet/dry-series construction. For CLIGEN,
the value is as evidence that spell representation and marginal amount choice
should be evaluated separately.

### AB-08 — LARS-WG extremes

M. A. Semenov (2008), “Simulation of Extreme Weather Events by a Stochastic
Weather Generator,” *Climate Research* 35, 203–212. DOI:
[`10.3354/cr00731`](https://doi.org/10.3354/cr00731).
**Access: link-only;** [publisher PDF](https://www.int-res.com/articles/cr2007/35/c035p203.pdf).
The paper evaluates heat, frost, and precipitation extremes across diverse
sites. It is a useful validation comparator, although LARS-WG's current
software terms and point/daily scope do not make it an implementation base.

## Directly comparable modern stochastic generators

### AB-09 — Spectral correction for low-frequency variability

J. Chen, F. P. Brissette, and R. Leconte (2010), “A Daily Stochastic Weather
Generator for Preserving Low-Frequency of Climate Variability,” *Journal of
Hydrology* 388, 480–490. DOI:
[`10.1016/j.jhydrol.2010.05.032`](https://doi.org/10.1016/j.jhydrol.2010.05.032).
**Access: acquisition required;** [institutional citation](https://espace2.etsmtl.ca/id/eprint/434/).
The method applies spectral/random-phase correction to restore monthly and
annual variance and autocorrelation lost by a standard daily generator. It is
the closest published benchmark for the first CLIGEN interannual experiment,
even if a latent annual-state model is ultimately easier to parameterize.

### AB-10 — WeaGETS

J. Chen, F. P. Brissette, and R. Leconte (2012), “WeaGETS—A Matlab-Based Daily
Scale Weather Generator for Generating Precipitation and Temperature,”
*Procedia Environmental Sciences* 13, 2222–2235. DOI:
[`10.1016/j.proenv.2012.01.211`](https://doi.org/10.1016/j.proenv.2012.01.211).
**Access: [archived PDF](../../references/open-access/chen-et-al-2012-weagets.pdf),
CC BY-NC-ND 3.0.** WeaGETS combines higher-order occurrence options,
alternative precipitation distributions, conditional Tmax/Tmin, Fourier
smoothing, and spectral correction. It is the nearest low-complexity
evolutionary comparison to point-scale CLIGEN.

### AB-11 — Semiparametric KNN generator

A. Apipattanavis et al. (2007), “A Semiparametric Multivariate and Multisite
Weather Generator,” *Water Resources Research* 43. DOI:
[`10.1029/2006WR005714`](https://doi.org/10.1029/2006WR005714).
**Access: link-only;** [publisher record](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2006WR005714).
Markov precipitation states and K-nearest-neighbor resampling preserve daily
cross-variable and cross-site structure with fewer parametric assumptions.
The tradeoff is bounded historical support and a need for complete network
records; it is more useful as a design pattern than as CLIGEN's first model.

### AB-12 — Low-frequency multivariate/multisite generator

S. Steinschneider and C. Brown (2013), “A Semiparametric Multivariate,
Multisite Weather Generator with Low-Frequency Variability for Use in Climate
Risk Assessments,” *Water Resources Research* 49, 7205–7220. DOI:
[`10.1002/wrcr.20528`](https://doi.org/10.1002/wrcr.20528).
**Access: link-only;** [publisher full text](https://agupubs.onlinelibrary.wiley.com/doi/abs/10.1002/wrcr.20528).
Wavelet autoregression supplies annual low-frequency structure, while a
Markov/KNN daily model preserves multivariate and spatial dependence and
quantile mapping imposes scenarios. This is the strongest reference for a
later multi-coefficient CLIGEN annual-state model.

### AB-13 — GWEX precipitation extremes

G. Evin, A.-C. Favre, and B. Hingray (2018), “Stochastic Generation of
Multi-Site Daily Precipitation Focusing on Extreme Events,” *Hydrology and
Earth System Sciences* 22, 655–672. DOI:
[`10.5194/hess-22-655-2018`](https://doi.org/10.5194/hess-22-655-2018).
**Access: [archived PDF](../../references/open-access/evin-et-al-2018-gwex.pdf),
CC BY 3.0.** GWEX combines higher-order occurrence, an extended-GPD margin,
spatial tail dependence, temporal dependence, and disaggregation. Its key
lesson for CLIGEN is that fitting daily tails without temporal dependence can
still understate multi-day extremes.

### AB-14 — GWEX temperature

G. Evin, A.-C. Favre, and B. Hingray (2019; online 2018), “Stochastic
Generators of Multi-Site Daily Temperature: Comparison of Performances in
Various Applications,” *Theoretical and Applied Climatology* 135, 811–824.
DOI: [`10.1007/s00704-018-2404-x`](https://doi.org/10.1007/s00704-018-2404-x).
**Access: DOI/link-only.** The study separates marginal shape, seasonality,
spatial dependence, and temporal autoregression, showing the importance of
autocorrelation to heat/cold-spell duration. It motivates temperature
persistence metrics before altering CLIGEN's temperature process.

### AB-15 — BayGEN

A. Verdin, B. Rajagopalan, W. Kleiber, G. Podestá, and F. Bert (2019),
“BayGEN: A Bayesian Space-Time Stochastic Weather Generator,” *Water Resources
Research* 55, 2900–2915. DOI:
[`10.1029/2017WR022473`](https://doi.org/10.1029/2017WR022473).
**Access: link-only;** [publisher full text](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2017WR022473).
BayGEN jointly simulates daily precipitation and Tmax/Tmin on a station
network or grid and propagates posterior parameter uncertainty. Its direct
lesson is that ensemble variation should include fitted-parameter uncertainty,
not only random weather innovations.

### AB-16 — Rglimclim

R. E. Chandler (2020), “Multisite, Multivariate Weather Generation Based on
Generalised Linear Models,” *Environmental Modelling & Software* 134, 104867.
DOI: [`10.1016/j.envsoft.2020.104867`](https://doi.org/10.1016/j.envsoft.2020.104867).
**Access: [archived PDF](../../references/open-access/chandler-2020-rglimclim.pdf),
CC BY 4.0;** [UCL record](https://discovery.ucl.ac.uk/id/eprint/10106175/).
The GLM framework explicitly accommodates spatial, temporal, inter-variable,
and nonstationary covariates. It supports a modular CLIGEN design in which
dependence and forcing are declared model components rather than post-hoc
corrections.

### AB-17 — MSTWeatherGen

S. Obakrim, L. Benoit, and D. Allard (2025), “A Multivariate and Space-Time
Stochastic Weather Generator Using a Latent Gaussian Framework,” *Stochastic
Environmental Research and Risk Assessment* 39, 3677–3701. DOI:
[`10.1007/s00477-024-02897-8`](https://doi.org/10.1007/s00477-024-02897-8).
**Access: [archived PDF](../../references/open-access/obakrim-et-al-2025-mstweathergen.pdf),
CC BY 4.0.** Weather types, ordered-quantile marginals, and a multivariate
space-time latent Gaussian covariance jointly generate precipitation,
humidity, wind, radiation, and Tmax/Tmin. It defines the present statistical
frontier, but its regional covariance/calibration burden is disproportionate
for CLIGEN's first point-scale extension.

### AB-18 — swxg

A. B. Thames, A. Hadjimichael, and J. D. Quinn (2026), “swxg: A Python Library
for Generalized Multivariate, Multisite, Copula-Based Stochastic Weather
Generation,” *Journal of Open Research Software* 14, 47. DOI:
[`10.5334/jors.651`](https://doi.org/10.5334/jors.651).
**Access: [archived PDF](../../references/open-access/thames-et-al-2026-swxg.pdf),
CC BY 4.0; software MIT.** Annual Gaussian-mixture hidden states, KNN
disaggregation, monthly autoregression/copulas, and strong validation tooling
make this the best current implementation reference for CLIGEN's annual-state
study. Its present scope is precipitation and one temperature variable, daily
or monthly, rather than a complete WEPP forcing set.

### AB-19 — Scenario-neutral climatology matching

B. Groenke, J. Wessel, P. Miersch, N. Klein, and J. Zscheischler (2026),
“Stochastic Weather Generation for Scenario-Neutral Impact Assessments Using
Simulation-Based Inference,” *Journal of Geophysical Research: Machine
Learning and Computation* 3, e2025JH000902. DOI:
[`10.1029/2025JH000902`](https://doi.org/10.1029/2025JH000902).
**Access: [archived PDF](../../references/open-access/groenke-et-al-2026-sbi-weather-generator.pdf),
CC BY 4.0.** A Bayesian GAMLSS generator models daily precipitation and
mean/min/max temperature interdependently; simulation-based inference adjusts
parameters to match arbitrary summary-statistic scenarios. It is a compelling
future calibration/control layer, but its acknowledged upper-tail and
single-site/daily limits keep it behind basic CLIGEN model corrections.

### AB-20 — EGGS-WG preprint

A. Schuddeboom, C. Zammit, D. Plew, P. Verburg, and A. Jabbari (2026),
“EGGS-WG: An Open Source Global Gridded Stochastic Weather Generator Derived
from ERA5-Land,” *EGUsphere* preprint. DOI:
[`10.5194/egusphere-2026-1651`](https://doi.org/10.5194/egusphere-2026-1651).
**Access: [archived preprint](../../references/open-access/schuddeboom-et-al-2026-eggs-wg-preprint.pdf),
CC BY 4.0; under review as of 2026-07-12.** EGGS-WG provides global gridded
daily precipitation and hourly temperature/dew point using ERA5-Land-derived
parameters. It is a watchlist item for global station fitting and spatial
generation; reported extreme-precipitation problems and preprint status make
it evidence, not an adoption target.

## Subdaily rainfall and erosion-relevant extremes

### AB-21 — Hourly stochastic–physical weather generation

V. Y. Ivanov, R. L. Bras, and D. C. Curtis (2007), “A Weather Generator for
Hydrological, Ecological, and Agricultural Applications,” *Water Resources
Research* 43. DOI:
[`10.1029/2006WR005364`](https://doi.org/10.1029/2006WR005364).
**Access: link-only;** [publisher full text](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2006WR005364).
This is the point-hourly precursor to AWE-GEN, coupling precipitation,
cloudiness, radiation, temperature, humidity, wind, and pressure. It is the
right long-run feature target for erosion/ecohydrology, but it presumes
hourly multivariable calibration data far beyond the legacy `.par` contract.

### AB-22 — AWE-GEN future scenarios

S. Fatichi, V. Y. Ivanov, and E. Caporali (2011), “Simulation of Future
Climate Scenarios with a Weather Generator,” *Advances in Water Resources*
34, 448–467. DOI:
[`10.1016/j.advwatres.2010.12.013`](https://doi.org/10.1016/j.advwatres.2010.12.013).
**Access: acquisition required.** AWE-GEN combines a Neyman–Scott pulse model,
annual precipitation persistence, physically linked hourly variables, and
climate perturbations. Its annual AR concept is portable to an early CLIGEN
profile; its full coupled hourly engine is a separate major model.

### AB-23 — AWE-GEN-2d

N. Peleg et al. (2017), “An Advanced Stochastic Weather Generator for
Simulating 2-D High-Resolution Climate Variables,” *Journal of Advances in
Modeling Earth Systems* 9, 1595–1627. DOI:
[`10.1002/2016MS000854`](https://doi.org/10.1002/2016MS000854).
**Access: link-only;** [publisher record](https://agupubs.onlinelibrary.wiley.com/doi/abs/10.1002/2016MS000854).
The model produces precipitation/cloud fields at 2 km and 5 min and other
variables at finer spatial and hourly scales. It is the broadest stochastic
WEPP forcing comparator, but radar/reanalysis inputs and request-only software
make external interoperability more feasible than a Rust reimplementation.

### AB-24 — Hierarchical hourly-to-yearly rainfall

J. Park, C. Onof, and D. Kim (2019), “A Hybrid Stochastic Rainfall Model that
Reproduces Some Important Rainfall Characteristics at Hourly to Yearly
Timescales,” *Hydrology and Earth System Sciences* 23, 989–1014. DOI:
[`10.5194/hess-23-989-2019`](https://doi.org/10.5194/hess-23-989-2019).
**Access: [archived PDF](../../references/open-access/park-et-al-2019-hybrid-rainfall.pdf),
CC BY 4.0.** A monthly time-series layer conditions a modified Bartlett–Lewis
storm process, explicitly bridging low-frequency totals and high-frequency
rainfall. This is the clearest precedent for eventually coupling CLIGEN's
annual/monthly state to a subdaily precipitation profile.

### AB-25 — Bartlett–Lewis developments

C. Onof and L.-P. Wang (2020), “Modelling Rainfall with a Bartlett–Lewis
Process: New Developments,” *Hydrology and Earth System Sciences* 24,
2791–2815. DOI:
[`10.5194/hess-24-2791-2020`](https://doi.org/10.5194/hess-24-2791-2020).
**Access: [archived article](../../references/open-access/onof-wang-2020-bartlett-lewis.pdf)
and [archived corrigendum](../../references/open-access/onof-wang-2023-bartlett-lewis-corrigendum.pdf),
CC BY 4.0.** The corrigendum points to the MIT-licensed
[`pyBL` archive](https://doi.org/10.5281/zenodo.7765663).
The paper improves the point-process parameter domain and calibration of
subhourly/hourly statistics. A fitted runtime sampler is feasible in Rust,
but optimization should initially remain in an external, independently
validated fitting tool.

### AB-26 — STORM v.2

M. F. Rios Gaona, K. Michaelides, and M. B. Singer (2024), “STORM v.2: A
Simple, Stochastic Rainfall Model for Exploring the Impacts of Climate and
Climate Change at and near the Land Surface in Gauged Watersheds,”
*Geoscientific Model Development* 17, 5387–5412. DOI:
[`10.5194/gmd-17-5387-2024`](https://doi.org/10.5194/gmd-17-5387-2024).
**Access: [archived PDF](../../references/open-access/rios-gaona-et-al-2024-storm-v2.pdf),
CC BY 4.0.** The GitHub code is GPL-3.0; the Zenodo archive containing
code/data/scripts is CC BY 4.0 (DOI:
[`10.5281/zenodo.8071820`](https://doi.org/10.5281/zenodo.8071820)).
Copula-based intensity–duration dependence,
orographic/elevation structure, seasonal and diurnal timing, and climate
scaling are especially relevant to erosion. It is rainfall-only and
watershed-calibrated, so an external field interface should precede any native
spatial implementation.

### AB-27 — RainyDay stochastic storm transposition

D. B. Wright, R. Mantilla, and C. D. Peters-Lidard (2017), “A Remote
Sensing-Based Tool for Assessing Rainfall-Driven Hazards,” *Environmental
Modelling & Software* 90, 34–54. DOI:
[`10.1016/j.envsoft.2016.12.006`](https://doi.org/10.1016/j.envsoft.2016.12.006).
**Access: link-only;** [public full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC5896577/).
RainyDay resamples and transposes observed radar storms to estimate rare
rainfall hazards while retaining event space-time structure. It is valuable
as an extreme-storm benchmark, but aligns more with a later external storm
producer than CLIGEN's first continuous-profile work.

### AB-28 — Stochastic rainfall coupled to erosion

Y. Shmilovitz et al. (2021), “Frequency Analysis of Storm-Scale Soil Erosion and
Characterization of Extreme Erosive Events by Linking the DWEPP Model and a
Stochastic Rainfall Generator,” *Science of the Total Environment* 787,
147609. DOI:
[`10.1016/j.scitotenv.2021.147609`](https://doi.org/10.1016/j.scitotenv.2021.147609).
**Access: DOI/link-only.** The study couples 5-minute stochastic rainfall to
DWEPP and shows that short-duration peak intensities dominate rare soil-loss
events. It directly supports adding EI30/intensity-duration and downstream
erosion metrics before adjudicating a new CLIGEN storm model.

## Weather regimes, spatial coherence, and nonstationarity

### AB-29 — Weather-regime generator

S. Steinschneider et al. (2019), “A Weather-Regime-Based Stochastic Weather
Generator for Climate Vulnerability Assessments of Water Systems in the
Western United States,” *Water Resources Research* 55, 6923–6945. DOI:
[`10.1029/2018WR024446`](https://doi.org/10.1029/2018WR024446).
**Access: link-only;** [publisher full text](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2018WR024446).
Nonhomogeneous regime transitions, block bootstrap, copula perturbations, and
separate thermodynamic/dynamic scenario modules preserve regional daily
structure. The portable lesson for CLIGEN is explicit provenance for distinct
changes in local distributions versus large-scale regime frequency.

### AB-30 — California regime generator, evaluation

N. Najibi et al. (2024), “A Statewide, Weather-Regime Based Stochastic Weather
Generator for Process-Based Bottom-Up Climate Risk Assessments in California—
Part I: Model Evaluation,” *Climate Services* 34, 100489. DOI:
[`10.1016/j.cliser.2024.100489`](https://doi.org/10.1016/j.cliser.2024.100489).
**Access: [archived PDF](../../references/open-access/najibi-et-al-2024-california-part-1.pdf),
CC BY 4.0.** The statewide extension evaluates precipitation/temperature,
extremes, spells, droughts, heat/cold waves, and spatial aggregation. Its
validation breadth is directly reusable even though its circulation and
6-km-data requirements place the model itself late in the roadmap.

### AB-31 — California regime generator, scenarios

N. Najibi et al. (2024), “A Statewide, Weather-Regime Based Stochastic Weather
Generator for Process-Based Bottom-Up Climate Risk Assessments in California—
Part II: Thermodynamic and Dynamic Climate Change Scenarios,” *Climate
Services* 34, 100485. DOI:
[`10.1016/j.cliser.2024.100485`](https://doi.org/10.1016/j.cliser.2024.100485).
**Access: [archived PDF](../../references/open-access/najibi-et-al-2024-california-part-2.pdf),
CC BY 4.0.** Thirty 1000-year primary scenarios vary warming, mean
precipitation, and extreme scaling; two additional experimental scenarios
vary circulation frequency and were not included in the associated data
release. It is a strong
reference for declaring which mechanism a future CLIGEN scenario changes,
rather than encoding an undifferentiated `.par` delta.

### AB-32 — IMAGE

N. J. Sparks et al. (2018), “IMAGE: A Multivariate Multi-Site Stochastic
Weather Generator for European Weather and Climate,” *Stochastic
Environmental Research and Risk Assessment* 32, 771–784. DOI:
[`10.1007/s00477-017-1433-9`](https://doi.org/10.1007/s00477-017-1433-9).
**Access: [archived PDF](../../references/open-access/sparks-et-al-2018-image.pdf),
CC BY 4.0.** Latent Gaussian fields, empirical orthogonal
functions, and autoregression jointly represent daily spatial and
multivariate dependence. It is an important spatial comparator but a much
larger schema/linear-algebra project than single-site interannual variation.

### AB-33 — RMAWGEN

E. Cordano and E. Eccel (2016), “Tools for Stochastic Weather Series
Generation in R Environment,” *Italian Journal of Agrometeorology* 21(3),
31–42. DOI:
[`10.19199/2016.3.2038-5625.031`](https://doi.org/10.19199/2016.3.2038-5625.031).
**Access: DOI/link-only; software GPL.** The package Gaussianizes station
series and applies vector autoregression with monthly adjustments. It is a
useful implementation reference for covariance and VAR mechanics, but
intermittent precipitation and extremes need more specialized treatment.

## Generative ML and climate-emulator boundary

### AB-34 — GenCast

I. Price et al. (2025), “Probabilistic Weather Forecasting with Machine
Learning,” *Nature* 637, 84–90. DOI:
[`10.1038/s41586-024-08252-9`](https://doi.org/10.1038/s41586-024-08252-9).
**Access: link-only, CC BY 4.0;** [Nature article](https://www.nature.com/articles/s41586-024-08252-9).
GenCast generates global 15-day ensemble forecasts at 0.25° and 12-hour steps
with a conditional diffusion model. It is a forecast system requiring global
initial states, not an unconditional long-run station generator; at most it is
a future coarse forcing source. Its main published scorecard excluded
precipitation because of concerns about ERA5 precipitation quality, a decisive
limitation for WEPP use.

### AB-35 — NeuralGCM

D. Kochkov et al. (2024), “Neural General Circulation Models for Weather and
Climate,” *Nature* 632, 1060–1066. DOI:
[`10.1038/s41586-024-07744-y`](https://doi.org/10.1038/s41586-024-07744-y).
**Access: link-only, CC BY 4.0;** [Nature article](https://www.nature.com/articles/s41586-024-07744-y).
The hybrid differentiable dynamical core can produce ensemble forecasts and
multi-decadal atmosphere simulations efficiently, but published climate runs
need prescribed boundary conditions and degrade outside trained warming
ranges. The published system diagnoses precipitation minus evaporation rather
than precipitation and underestimates tropical P−E extremes. It should not be
embedded in `cligen-rs`.

### AB-36 — CorrDiff

M. Mardani et al. (2025), “Residual Corrective Diffusion Modeling for Km-Scale
Atmospheric Downscaling,” *Communications Earth & Environment* 6, 124. DOI:
[`10.1038/s43247-025-02042-5`](https://doi.org/10.1038/s43247-025-02042-5).
**Access: link-only, CC BY-NC-ND 4.0;** [Nature article](https://www.nature.com/articles/s43247-025-02042-5).
CorrDiff learns a deterministic conditional mean plus stochastic small-scale
residuals from 25-km inputs to 2-km fields. The paper reports realistic spatial
spectra, but continuous-sequence temporal coherence is not established and
uncertainty calibration remains challenging. The regional experiment used
radar-assimilating Taiwan WRF simulation targets rather than observations and
was geographically limited to Taiwan; the supporting target data are public
under CC BY-NC-ND 4.0 and code is Apache-2.0. The appropriate CLIGEN
relationship is an external downscaling adapter.

### AB-37 — spateGAN-ERA5

L. Glawion et al. (2025), “Global Spatio-Temporal ERA5 Precipitation
Downscaling to km and Sub-Hourly Scale Using Generative AI,” *npj Climate and
Atmospheric Science* 8, 219. DOI:
[`10.1038/s41612-025-01103-y`](https://doi.org/10.1038/s41612-025-01103-y).
**Access: link-only, CC BY 4.0;** [code and weights](https://github.com/LGlawion/spateGAN_ERA5).
The system generates 2-km, 10-minute precipitation ensembles conditioned on
hourly ERA5. Training used German radar with limited validation in the United
States and Australia; patchwise mean adjustment is not exact coarse-cell/time
conservation. Inference requires roughly 10 GB GPU memory per sample, while
reported training used four 80-GB A100s for three days. It is attractive for
historical forcing experiments but is not an arbitrary-length stationary
climate generator; GPU/data requirements favor a Python producer and
Parquet/NetCDF exchange. Code is MIT licensed; the released data have DOI
[`10.5281/zenodo.17417589`](https://doi.org/10.5281/zenodo.17417589).

### AB-38 — Scale-adaptive generative climate downscaling

P. Hess et al. (2025), “Fast, Scale-Adaptive and Uncertainty-Aware Downscaling
of Earth System Model Fields with Generative Machine Learning,” *Nature
Machine Intelligence* 7, 363–373. DOI:
[`10.1038/s42256-025-00980-5`](https://doi.org/10.1038/s42256-025-00980-5).
**Access: link-only, CC BY 4.0;** [Nature article](https://www.nature.com/articles/s42256-025-00980-5).
A consistency model performs probabilistic, controllable, zero-shot
downscaling across Earth-system models. It demonstrates the likely future
shape of climate-forcing production, but its univariate daily precipitation
experiment does not supply WEPP-ready station meteorology or storm profiles.

## Remaining source-acquisition queue

The core papers previously requested for this review are already present in a
local, Git-ignored reading corpus and have committed identities in
the work-package evidence. The remaining queue reflects value to the next two
`cligen-rs` studies, not general citation importance.

| Priority | DOI | Request this source because |
|---|---|---|
| P1 | `10.1007/s00704-018-2404-x` | Temperature-generation comparisons can sharpen the rank-3 multivariate candidate set. |
| P1 | `10.1016/j.scitotenv.2021.147609` | DWEPP connects high-resolution rainfall generation directly to erosion response. |
| P1 | `10.1029/2006WR005714` | The K-nearest-neighbor generator is a practical nonparametric daily comparator. |
| P2 | `10.1029/WR017i001p00182` | Richardson is the foundational wet/dry-conditioned multivariate daily model. |
| P2 | `10.1175/1520-0450-39.5.610` | Parlange and Katz tests whether multivariate dependence changes hydrologic behavior. |
| P2 | `10.1029/2017WR022473` | BayGEN supplies the clearest Bayesian parameter-uncertainty and multisite comparator. |
| P3 | `10.3354/cr010095` | LARS-WG documents a widely used series-based occurrence architecture. |
| P3 | `10.3354/cr00731` | Early LARS validation helps interpret later series-based claims and limitations. |

When a source is supplied, place a local reading copy under
`references/copyrighted/`, never under `open-access/`, unless its reusable
license is independently verified and added to the manifest.
