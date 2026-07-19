# Pedigree sources

## Primary FSWEPP origin

- Elliot, W.J.; Scheele, D.L.; Hall, D.E. (1999), *Rock:Clime Rocky Mountain
  Research Station Stochastic Weather Generator Technical Documentation*:
  <https://forest.moscowfsl.wsu.edu/fswepp/docs/rockclimdoc.html>.
  It identifies Rock:Clime as the FSWEPP browser interface to CLIGEN and the
  source of the expanded 2,600-station database.
- USDA Forest Service, *Rock:Clime Beta CD Version*:
  <https://forest.moscowfsl.wsu.edu/fswepp/docs/0007RockClimCD.html>.
  It documents user station selection, PRISM 4 km precipitation/elevation
  lookup, manual wet-day edits, and temperature lapse-rate edits.
- Hall, D.E.; Elliot, W.J. (2001), *Interfacing Soil Erosion Models for the
  World Wide Web*:
  <https://forest.moscowfsl.wsu.edu/engr/library/Hall/Hall2001a/2001a.html>.
  It documents incorporating 4 km PRISM monthly precipitation into Rock:Clime
  for locations away from CLIGEN stations.
- Elliot, W.J. (2004), *WEPP Internet Interfaces for Forest Erosion
  Prediction*, JAWRA 40(2):299–309:
  <https://forest.moscowfsl.wsu.edu/engr/library/Elliot/Elliot2004k/2004k.pdf>.
  It documents access to PRISM precipitation through Rock:Clime and user
  modification of precipitation, wet days, and temperatures.

## Published later application

Brooks, E.S.; Dobre, M.; Elliot, W.J.; Wu, J.Q.; Boll, J. (2016),
*Watershed-scale evaluation of the Water Erosion Prediction Project (WEPP)
model in the Lake Tahoe basin*, Journal of Hydrology 533:389–402,
<https://doi.org/10.1016/j.jhydrol.2015.12.004>. The paper applies monthly
PRISM precipitation ratios and Tmax/Tmin differences to station weather for
individual hillslopes. It also warns that static monthly scaling can miss
event-specific temperature and precipitation structure. It is application
and limitation evidence, not the source of cligen-rs's `.par` equations.

## WEPPcloud implementation lineage

Static git review used `/Users/roger/src/wepppy` at commit
`3ee74d02df445a30968ef92975e5e3e2f6084669`. The reviewed
`wepppy/climates/cligen/cligen.py` has SHA-256
`4071cc72165d174851316349c0d96a3f4fa06fcf0b2d91e5b67de439f39a42c1`.
History attributes the automated PRISM build/selector to 2018, the first
`par_mod` path to 2019, the rule-of-thumb wet-day/P(W/W)/P(W/D) correction to
2020, and optional `MX .5 P` adjustment to 2026. This establishes source
lineage without assigning those later formulas to FSWEPP or Brooks et al.

## cligen-rs boundary

The cligen-rs implementation is independently specified. It reuses the
FSWEPP-descended `us-2015` station collection and reviewed `wepppy` algebra,
but replaces live unversioned queries with two immutable PRISM bundles,
changes the station selector, makes intensity adjustment mandatory, tightens
numeric and fixed-width failure behavior, and emits complete provenance.
