# Downstream solar architecture constraint

A10M5R11 does not train or adjudicate a solar model. The next solar-capable
candidate should decompose solar radiation into:

1. a procedural astronomical/clear-sky envelope determined by latitude and
   day of year (with explicit calendar semantics); and
2. a learned stochastic clearness/cloud residual coupled to the model's own
   generated precipitation and temperature state.

This preserves known geometry procedurally while learning weather-dependent
variability and cross-variable dependence. Observed daily precipitation or
temperature must not enter generation. The stochastic residual needs its own
monthly and annual dispersion, correlation, and support gates. This note is a
design constraint only; it must not influence A10M5R11 selection.
