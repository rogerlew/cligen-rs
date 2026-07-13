# A5a Design Decisions

Date: 2026-07-12
Status: fixed before implementation

1. **Only the metric vector advances.** Quality envelope 2, provenance 1,
   runspec 1, station schema/model, generation profiles, and output schemas do
   not change. The combination schema is named
   `quality-report-s2-m3.schema.json`; historical schemas remain immutable.
2. **Observed targets remain external.** They are neither station parameters
   nor embedded comparisons in the quality sidecar. The report remains
   network-free and measures rendered `.cli` bytes.
3. **Group A/P semantics remain unchanged.** Group A retains the legacy
   `precip > 0` contract. V3 adds a separately named R1mm surface for direct
   observed comparison.
4. **Quality terminology is corrected at the version boundary.** `.cli ip`
   is `peak_intensity_ratio`; a positive-precipitation row is a
   `wet_event_day`, not proof of multiple storms or a physical intensity.
5. **Interannual cells use complete periods.** Complete months and years are
   explicit; a contiguous EOF-truncated observed tail remains measurable but
   cannot bias annual/monthly dispersion.
6. **Spells cross boundaries.** Whole-stream spell summaries cross month and
   year boundaries. Per-year longest-spell fields remain explicitly clipped
   diagnostics.
7. **Low frequency is pinned.** The diagnostic is the fraction of two-sided
   demeaned periodogram power at nonzero Fourier periods of at least four
   years. It uses the complete annual sequence and pinned `libm` sine/cosine.
8. **Winter climate is not winter physics.** Mean-air `<= 0 °C`, cold-day
   precipitation fraction, DJF R1mm precipitation/temperature dependence,
   and air-state transitions are climate proxies. Physical WEPP response is a
   separate versioned record.
9. **Burn honesty.** Eight fixed burn offsets measure trajectory sensitivity;
   independent extension seeds are separate. Across-burn ranges are not IID
   confidence intervals.
10. **Public DTOs validate against the full combination schema.** Parsing and
    serialization both fail closed, including unknown fields and post-
    construction mutation; no host/network schema lookup is allowed.
