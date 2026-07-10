# R1 Review — Codex (Q3/Q4 adjudications)

Date: 2026-07-10
Reviewer: openai codex (read-only sandbox, dispatched via MCP by
Claude Code at operator direction: "before deciding on ADR-0003 and
fast-batch let's have codex review and weigh in an opinion")
Scope: commit range 58d5963..a5e3cac + raw campaign sidecars.
Findings and OPINION reproduced verbatim below.

---

## Findings

1. **HIGH — The decisive group-A aggregation rule was not pre-registered, and reasonable alternatives change the adjudication.**

   Verbatim finding: "B1's threshold was pinned, but its estimator was not. The pre-registration says 'corpus-median group A |rel_err|' without defining the order of aggregation across months, parameters, and stations (pre-registration.md:129). The analysis later defines a station scalar as the mean across months and parameters, followed by a corpus median (analyze-matrix.py:5-7, :33-36, :71-74, :102-103). That choice is not estimator-invariant."

   Independent recomputation from the 102 raw sidecars produced:

   - Published 100-year B1: ratio of medians = 1.120, not material.
   - Median over all parameter-month cells: 1.409, material.
   - Median of station-level cell medians: 1.431, material.
   - At 30 years, the median-of-station-medians ratio is 1.187, just below the 1.2 threshold, reversing the published material verdict.
   - For Q4 leg (a), a station-median aggregation gives 1.104 at 30 years, narrowly failing the 1.1 bound instead of passing.

   All relevant `rel_err` cells were non-null, so null filtering is not the cause. The problem is solely the unpinned aggregation hierarchy.

   Recommended disposition: Do not cite B1's "material only at 30 years" conclusion as pre-registered. Either pre-register an aggregation rule and rerun/reanalyze, or report the estimator sensitivity and treat the horizon distinction as unresolved. Q4 quality leg (a) should likewise be called aggregation-sensitive, although this does not by itself rescue promotion because leg (c) remains unresolved separately below.

2. **HIGH — Q4 leg (c) did not measure the pre-pinned quantity and lacks the required production-host methodology.**

   Verbatim finding: "The pre-registration requires a 'measured refill-path performance gain' at both horizons (pre-registration.md:146-153). The adjudication substitutes whole-run wall time: a sidecar-bearing whole run at 30 years and a generation-only whole run at 100 years (q4 package.md:31-41). Neither isolates the refill path. The 30- and 100-year legs do not even use the same measurement configuration."

   The governing draft further requires material performance on FMA-capable `wepp1` with pinned-core repeated samples before proceeding (SPEC-FAST-BATCH-V1.md:194-207). Instead, the record contains aggregate best-of-three values from an unnamed Linux host (timing-no-sidecar.json:1-13) and expressly says `wepp1` was not measured (gate-results.md:34-35). The assertion that FMA "could not plausibly bridge" 1.32× to 1.5× is speculation, not evidence (promotion-adjudication.md:55-59).

   Recommended disposition: Change leg (c) from **FAIL** to **NOT EVALUATED AS PRE-REGISTERED**. Do not claim that the 1.32× whole-generation proxy proves refill performance is below 1.5×. A valid adjudication would directly benchmark refills and/or use consistent end-to-end production workloads on `wepp1`, with pinned cores and retained raw repetitions.

3. **MEDIUM — The 52% counterfactual is sound as a diagnostic verdict rate but is repeatedly over-described as the conditioner's actual discard rate.**

   Verbatim finding: "`process.counterfactual` answers: 'Would this one batch fail the faithful QC expressions when accumulated along the unconditioned trajectory?' It does not replay faithful retries, shared `iredo`, or cap acceptance. Therefore 'the conditioner rejects half of everything' and 'discards every second batch' are not literal descriptions of faithful execution (frontier-analysis.md:23-27; 0003-qc-filter-exposure.md:15-16)."

   The implementation correctly maintains cumulative diagnostic state and mirrors the K-S/mean/variance expressions (rng.rs:417-457). But faithful `iredo` is shared across all nine parameters within a refill and accepts after the cap (cligen.f:4120-4127, :4269-4332); the counterfactual has no corresponding cap state.

   The distinction is empirically large. At Yuma, the committed record shows 2,538,348 faithful failed attempts versus 10,800 shipped parameter-month batches, while the off-trajectory counterfactual rate is 50.5% (matrix-analysis.json:564-583). Across the corpus, the independently computed faithful failed-attempt fraction has a 100-year median of about 96.9%, not 52.7%, because repeated failures cascade.

   Recommended disposition: Rename the headline metric to "raw QC-verdict failure rate along the off trajectory." State explicitly that it is non-causal after the first hypothetical rejection and has no shared-cap analogue. Retain the 7.7 million actual failed-attempt count as the faithful discard-cost measurement.

4. **MEDIUM — The claimed station-by-station GHCN confirmation is false and is not produced by the committed analysis.**

   Verbatim finding: "The frontier says the GHCN secondary 'does not change the direction on any of its stations' (frontier-analysis.md:54-58), but `analyze-matrix.py` joins only Daymet (analyze-matrix.py:94-108)."

   Independently joining `observed-stats.json` to `matrix-analysis.json` shows that at 100 years `off` is closer to GHCN on 6/8 stations, but GHCN reverses the Daymet direction for Saucier (`ms227840`) and New Meadows (`id106388`). At 30 years, three of the eight station-level directions differ. Thus the aggregate direction remains supportive, but the stated station-by-station invariance does not.

   Recommended disposition: Replace the sentence with: "The GHCN secondary favors `off` on 6/8 stations at both horizons, but changes individual-station direction relative to Daymet." Add that computation to the committed analysis output.

5. **MEDIUM — The 15/17 result is persuasive descriptive evidence, not a robust stochastic estimate.**

   Verbatim finding: "Every station/configuration uses one deterministic trajectory, `rng.burn: 0` (pre-registration.md:23-29). Stations provide climate-regime breadth, but they are not RNG replicates. Consequently, '15/17' supports a campaign-specific directional finding; it does not quantify the probability that `off` will be closer for a new run or station."

   The direction is reasonably stable to detrending: independently using Daymet detrended SD changes the 100-year count from 15/17 to 14/17. GHCN remains 6/8. Those are useful sensitivities, but no multi-burn or independent-seed interval exists.

   Recommended disposition: Qualify ADR-0003's evidence as "in this single-burn, 17-station campaign." Before changing a production default, collect repeated, explicitly non-independent burn strata or introduce a versioned backend with genuinely independent seeds and report uncertainty across trajectories.

6. **MEDIUM — The campaign record is insufficiently durable and reproducible for a decisive performance adjudication.**

   Verbatim finding: "`run-matrix.py` deletes every `.cli` immediately after hashing it (run-matrix.py:65-77), while the 102 full sidecars and runspecs live only under ignored `target/q3-matrix/`. The committed analysis preserves selected derived fields, not the complete measurement inputs. The generation-only timing file preserves only three aggregates per configuration, with no raw repetitions, timing script, host identity, binary hash, compiler flags, or core-affinity record."

   Spot verification was otherwise clean: all 102 present sidecars match the CLI hashes in committed `runs.json`, provenance is consistent, and committed `runs.json` equals the target copy.

   Recommended disposition: Archive the full sidecars and resolved runspecs in a content-addressed package artifact, or publish an immutable archive with a committed hash. Retain raw timing samples and host/binary/compiler/core-affinity metadata. Until then, describe the result as locally reproducible only while the current target tree survives.

7. **LOW — SPEC-QUALITY-REPORT retains contradictory revision text.**

   Verbatim finding: "The rev-5 status correctly says `fast_batch_v0` counterfactuals remain null (SPEC-QUALITY-REPORT.md:3-11), but group P still says fast-v0 counterfactuals land with Q3 (:140-146). The envelope sketch also still says `metrics_version: 1` (:151-168) despite rev 5 defining version 2."

   Recommended disposition: Remove the superseded fast-v0 promise or label it explicitly historical, and update the sketch to version 2.

8. **LOW — The GHCN completeness implementation is stricter than the registered screen.**

   Verbatim finding: "`ghcn()` admits years with at least 347 precipitation days, matching the stated 95% screen (acquire-observed.py:143-150), but `yearly_stats()` subsequently keeps only years with at least 360 precipitation records (:62-66). The effective screen is therefore approximately 98.6%, not 95%."

   This did not reduce any published GHCN station below 30 retained years; the minimum reported count is 38.

   Recommended disposition: Make the screen single-sourced and state the effective threshold. No rerun is necessary unless strict adherence to the registered 95% rule is required.

## Clean dimensions

- **Implementation fidelity is clean apart from the counterfactual interpretation above.** The `off` path preserves source RNG streams, masks, `ell`, and rolling predecessors while skipping generation-state QC accumulation and retry (rng.rs:348-374). `DiagnosticQc` owns separate cumulative arrays and its own `AcmState` (process.rs:30-53), so counterfactual evaluation cannot mutate generator `Crandom3State` or generator ACM state. `ks_verdict` mirrors the live `ks_tst` expressions (qc.rs:48-108). A focused equivalence regression test would be useful, but I found no current math divergence.
- **Faithful-default identity is adequately gated.** The 12-golden suite explicitly exercises `QcFilter::Faithful` (cli_parity.rs:192-242), and the runspec resolver defaults an omitted field to `Faithful` (runspec.rs:471-484). The CLI-level default test confirms faithful process provenance (quality_report.rs:444-467).
- **Campaign chronology is clean in the repository record.** Commit `3ed1c33` contains the bounds before observed acquisition (`85fd742`), implementation (`03dd1af`), and campaign results (`a5e3cac`). This establishes committed pre-registration, though naturally it cannot prove that no uncommitted exploratory output existed.
- **B2 and B3 arithmetic is clean.** B2 uses the registered median of per-station SD ratios, and B3 correctly compares decade-0 faithful/off against whole-run faithful/off (analyze-matrix.py:104-116). The published 0.806/0.888 and 10/17 reproduce. B3 is fairly characterized as a bare majority, not a universal mechanism.
- **Ran/Static labeling is generally disciplined.** Executed gates and campaigns are labeled Ran, prior faithful equivalence is identified as previously run rather than rerun, and the Daymet grid/point, period, no-detrend, and wet-day-threshold caveats are substantially honest. The exceptions are the GHCN overclaim and missing durable evidence noted above.

## OPINION

### D1 — ADR-0003

**Do not ratify ADR-0003 exactly as drafted. Ratify its core decision with amendments.**

I agree with these rulings:

1. `qc_filter` should remain user-facing.
2. The default should remain `faithful`.
3. `off` should be recommended for explicitly variance-priority 100-year runs as an opt-in practice.
4. A production default change should require a later operator decision.

I do **not** recommend `off` as the global default yet. Faithful defaulting protects byte compatibility and prevents an existing runspec from silently changing meaning. The evidence for `off` is directionally strong—lower clipping, materially improved annual-precipitation CV against Daymet on 15/17 stations, 14/17 under the detrended sensitivity, and 6/8 against GHCN—but it remains one burn per station and uses imperfect observed proxies.

I would amend ADR-0003 as follows:

- Replace "conditioning buys nothing material at 100 years" with: "Under the campaign's recorded mean-month/mean-parameter/median-station estimator, the 100-year convergence ratio was 1.12; alternative reasonable aggregations cross the 1.2 threshold, so the magnitude of the remaining convergence benefit is estimator-sensitive."
- Replace "discards ~52% of all batches" with "about 52% of off-trajectory batches fail the raw counterfactual QC verdict; faithful execution performs repeated retries and discards substantially more attempts on pathological stations."
- Qualify "moves output away from observed climate on 15/17 stations" with "in the single-burn Daymet comparison"; add the detrended 14/17 and GHCN 6/8 sensitivities.
- Phrase the recommendation as: "For 100-year variance-priority hydrology runs, consider `qc_filter: off` and inspect the emitted quality report." Avoid calling this universally correct for every rangeland/forest run.
- Clarify that "native" describes the use class here, not the future `native-f64-v1` generation profile.

Thus my D1 answer is: **ratify amended; keep faithful-by-default; recommend, but do not mandate or default to, `off` for 100-year variance-priority runs.**

### D2 — Fast-batch line

**Do not promote fast-batch. Retire/hold the present line with a narrow evidence-based reopening condition.**

I agree with the practical retirement recommendation: v0 has known column-5/9 support divergences, a proper v1 would add implementation and maintenance cost, its measured quality is merely comparable rather than better, and the current roadmap has more scientifically valuable work. A 1.32× end-to-end generation improvement on one host is useful but not compelling enough, in my judgment, to maintain a second RNG lineage when `qc_filter: off` already removes the dominant pathology.

However, **I do not agree that "1.32× < 1.5×" is a valid executed failure of the pre-pinned performance gate.** The campaign measured whole-run generation time, not refill-path gain; used inconsistent 30/100-year configurations; did not run the new `qc_off` baseline on the required `wepp1` production host; and retained no raw timing record. The proper verdict for leg (c) is "not evaluated as specified," not "failed."

I would therefore amend the retirement record to say:

- Retirement is a portfolio and maintenance decision based on the observed modest end-to-end gain, v0's semantic defects, and the likely added cost of a source-support-preserving v1.
- It is not proof that a refill backend cannot exceed 1.5× on production hardware.
- Reopen only if production profiling shows the unconditioned refill/RNG path is a material bottleneck; any reopening must begin with direct refill benchmarks and consistent pinned-core end-to-end measurements on `wepp1`.

My D2 answer is: **retire the current line and do not promote or immediately re-scope it, but correct the adjudication rationale—the 1.32× proxy alone does not justify or technically prove retirement.**
