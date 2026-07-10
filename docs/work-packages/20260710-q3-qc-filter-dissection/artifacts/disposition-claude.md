# R1 Dispositions — Claude Code (Q3/Q4 adjudications)

Date: 2026-07-10
Evidence mode: Ran for every verification and remediation. All eight
findings **ACCEPTED**. The two HIGH findings were independently
verified before acceptance (my recomputation reproduces Codex's
numbers; `estimator-sensitivity.json`).

| # | Sev | Disposition | Applied fix |
|---|---|---|---|
| 1 | HIGH | **ACCEPTED — verified independently.** I pinned B1's threshold but not its aggregation hierarchy; the verdict is estimator-sensitive (Ran: all-cells 1.44/1.41; station-medians 1.19/1.43 — both recorded verdicts flip under some reasonable estimator). | `estimator-sensitivity.json` committed (all estimators, both horizons, plus the Q4-leg-(a) sensitivity); frontier-analysis B1 row and headline 2 corrected to "horizon distinction unresolved; the buy never vanishes"; ADR-0003 context amended; ROADMAP note corrected. The B1 horizon claim is no longer cited as pre-registered. |
| 2 | HIGH | **ACCEPTED.** Leg (c) measured a whole-run proxy, not the pinned refill-path quantity, on the wrong host class, without raw samples. | Q4 verdict changed FAIL → **NOT EVALUATED AS PRE-REGISTERED**; retirement rationale reframed as a portfolio/maintenance decision with a pinned reopening condition (production profiling showing the refill/RNG path is a material bottleneck; direct refill benchmarks + pinned-core wepp1 measurements); the FMA "could not plausibly bridge" speculation removed. |
| 3 | MEDIUM | **ACCEPTED.** The 52% is the raw QC-verdict failure rate along the off trajectory — non-causal after the first hypothetical rejection, no shared-cap analogue; faithful's actual failed-attempt fraction is far larger (~97% corpus median at 100 yr). | Frontier headline 1, ADR-0003 context, and the ROADMAP note reworded; the 7.7M failed-attempt count retained as the faithful discard-cost measurement. |
| 4 | MEDIUM | **ACCEPTED — my claim was false.** GHCN favors `off` on 6/8 with station-level direction reversals vs Daymet (Ran: fl083909, id106388, ms227840 at 100 yr); I had asserted invariance without committing the computation. | Sentence corrected in frontier-analysis; the GHCN join is now a committed computation (`estimator-sensitivity.json`). |
| 5 | MEDIUM | **ACCEPTED.** Single-burn design: 15/17 is descriptive of this campaign, not a stochastic interval. | Qualifier added to frontier sensitivities and ADR-0003 ("in this single-burn Daymet comparison"); multi-trajectory uncertainty named as a precondition for any future default change. |
| 6 | MEDIUM | **ACCEPTED.** Campaign evidence lived only under `target/`. | Full evidence archive (102 sidecars + resolved runspecs + runs.json) published as release `q3-evidence-2026.07`, asset `q3-matrix-evidence.tar.gz`, SHA-256 `cc42e65e7ad798c774d27fdbb9c525c8ed1abcc2bc5dc204756516f8508e072a`. Raw timing repetitions were not retained (accepted limitation — moot for the record since leg (c) is now "not evaluated"; the reopening condition pins the required methodology). |
| 7 | LOW | **ACCEPTED.** | SPEC-QUALITY-REPORT group P superseded sentence replaced with the rev-5 ruling + historical note; envelope sketch bumped to `metrics_version: 2`. |
| 8 | LOW | **ACCEPTED.** Effective GHCN screen is ~98.6%, not the registered 95% (the yearly-stats ≥360-day filter stacks on the ≥347 screen). | Documented in the acquisition script at the screen site; no station fell below 30 retained years (minimum 38), so no rerun. |

## On the reviewer's OPINION

Codex's independent recommendations — **ratify ADR-0003 with its five
amendments** (all applied) and **retire the fast-batch line on
portfolio grounds with a narrow reopening condition** (applied) — are
now what the record proposes. My original bottom lines survive; my
original *arguments* needed the corrections above, most seriously the
unpinned B1 estimator and the false GHCN sentence. Both decisions
remain the operator's.
