# A5d1b consolidated internal review

Status: `ACCEPTED`
Date: 2026-07-14

## Scope and independence

The report followed the scientific report authoring protocol. Three read-only
agents first extracted evidence, methods, and authority boundaries and then
applied independent accuracy, scientific-validity, and
consistency/public-safety lenses. The lead author alone changed files,
dispositioned findings, invalidated exposed runs, and refreshed evidence.

The initial review evaluated the exposed v3 run. It found that the count solver
incorrectly equated `OptimizeResult.success` with feasibility, even though
HiGHS time-limit status 1 can retain a feasible incumbent. That defect affected
published witness counts and required a post-outcome implementation correction,
not a prose-only repair. The lead preserved the v3 tools and outcomes,
registered amendment 003, froze v4, and reran the matrix. All 17 v4 station
certificates were then preserved and invalidated after an aggregate-only
missing import; amendment 004 and freeze v5 preceded the controlling complete
rerun. Reviewers rechecked that controlling evidence.

## Lens outcomes

| Lens | Initial verdict | Final verdict | Open P1/P2/P3 |
|---|---|---|---|
| Accuracy | ACCEPT WITH CORRECTIONS | ACCEPT | 0/0/0 |
| Scientific validity | ACCEPT WITH CORRECTIONS | ACCEPT | 0/0/0 |
| Consistency and public safety | REJECT pending corrections | ACCEPT | 0/0/0 |

## Findings and dispositions

| Finding | Severity | Required correction | Lead disposition | Independent recheck |
|---|---:|---|---|---|
| ACC-001 / SCI-001 | P2 | Stop treating solver optimality as feasibility; retain and independently validate time-limit incumbents; rerun the matrix | V3 was preserved and invalidated. Amendment 003 records the material post-outcome implementation correction. V5 validates integrality, bounds, and primal constraints for any retained incumbent, then performs exact replay. Four status-1 fixtures cover valid, fractional, constraint-violating, and absent incumbents. | ACCEPT — controlling counts distinguish status, raw incumbent, accepted incumbent, and exact witness. |
| ACC-002 / SCI-002 | P2 | Independently closure-replay every separate-horizon witness, not only joint witnesses | Added `verify-count-witnesses.py` and the bound replay audit. It replays the one joint and all 14 separate-100 exact witnesses, recomputes aggregates, and rejects a count mutation. | ACCEPT — all 15 exact witnesses independently pass. |
| ACC-003 | P2 | Correct resource claims, enforce station scheduling, and measure memory | The report now calls three seconds a HiGHS option rather than a hard wall. V5 checks station scheduling and total wall; resource evidence records 52 calls, maximum call wall 3.009906 seconds, maximum station wall 11.638102 seconds, total 138.488182 seconds, and peak RSS 562,397,184 bytes. | ACCEPT — every number independently reproduced; all registered resource checks pass. |
| ACC-004 / CON-001 | P2 | Propagate the terminal state through package, roadmap, and catalogs | Package and artifact inventory close `EXECUTED-HOLD-COUNT-SEARCH-BOUNDED`; A5d1b moved to the catalog; A5d1c is the active structural successor. | ACCEPT — repository-facing states agree. |
| SCI-003 | P3 | Do not say H1 is unsupported as though bounded failure disproved existence | H1 now says global feasibility was not demonstrated under the registered bound and reports the positive 1/17 witness. | ACCEPT — no infeasibility implication remains. |
| SCI-004 | P3 | Prioritize linear scaling, incumbent retention, and work allocation before nonlinear localization | `next-action-disposition-v1.json`, report, package, and roadmap refine the successor action accordingly. | ACCEPT — ordering and confirmation remain blocked. |
| CON-002 | P2 | Include intermediate freeze v2 in the public chronology | Report and manifest bind v1, amendment 001, v2, amendment 002, v3, amendment 003, v4, amendment 004, and v5. | ACCEPT — the append-only chain is complete. |
| CON-003 | P2 | Cite the predecessor advisory and direct A5d1 machine authorities | Evidence E20–E23 bind A5d1 marginal/path results, decision, and advisory; the report labels its narrative contextual. | ACCEPT — machine authority is explicit. |
| CON-004 | P2 | Complete the report, review, gate, and closure records | Report and manifest are accepted after the bounded rechecks; terminal gates and closure identities are recorded in this package. | ACCEPT — final verifiers pass. |
| CON-005 | P2 | Stage all A5d1b archives through Git LFS and verify pointers | The controlling, invalidated-v3, and invalidated-v4 archives stage as LFS pointers with OIDs `24ba4de1…`, `8e9020d0…`, and `a1c96742…` and sizes 11,451, 6,959, and 11,440 bytes. | ACCEPT — `git lfs fsck` passes. |
| CON-006 | P3 | Qualify the unreplayable cause of the predecessor report-hash mismatch without rewriting locked evidence | The locked advisory was restored byte-for-byte; an append-only addendum calls whitespace normalization the recorded staging disposition and states that unavailable old bytes prevent replay of the exact textual delta. | ACCEPT — the noncontrolling authority disposition remains sound and the root evidence lock passes. |
| Accuracy wording recheck | P3 | Clarify that the 15/1 and 9/6/1 status splits describe initial separate-horizon calls | The Results wording now says “initial” for both splits; total 52-call statuses remain separately reported as 10/40/2. | ACCEPT — accepted report SHA-256 `892f6553eba495921644ef737dbe99ebd9a766157915704963c9054996fbe439` matches the manifest. |
| Compiled-cache hygiene | P3 | Remove transient Python bytecode trees before closure | Both A5d1 and A5d1b `__pycache__` trees were removed and excluded from staging. | ACCEPT — no `.pyc` file remains in scope. |

## Recheck coverage

Accuracy independently reconciled the 17-station matrix, 52 solver calls,
10/40/2 all-call statuses, 19 raw and 18 independently accepted incumbent
calls, one exact joint witness, 14 exact separate-100 witnesses, resource
totals, 25 report evidence bindings, three governance bindings, and every
archive member. The count values for the one joint and all 14 separate exact
witnesses were replayed independently.

Scientific validity verified hypothesis provenance and bounded language,
post-outcome amendment disclosure, independent acceptance semantics, nonlinear
replay, ordering barriers, solver-option wording, and limitations. The one
joint witness does not lift the 17/17 gate and does not authorize a candidate.

Consistency/public safety verified all v3, v4, and v5 frozen tool hashes, the
complete amendment chain, local links, report-manifest identities, package and
roadmap state, three deterministic archives, Git LFS attributes and staged
pointers, zero confirmation exposure, zero production/public interface change,
and absence of secrets, operator-specific absolute paths, compiled caches, or
copyrighted reading copies.

## Residual uncertainty

No review finding remains open. Scientific uncertainty remains intentionally
bounded: 16 joint branches and all 16 separate 30-year branches ended without
an accepted incumbent, so the study neither proves their infeasibility nor
evaluates ordering for the one exact joint count witness. The A5d1c successor
must be prospective and must not relax the climate contract or inspect
confirmation data.

Final verdict: **ACCEPT**
Open P1: 0
Open P2: 0
