# SPEC-RUNSPEC rev-1 Independent Review — Codex (gpt-5.6-sol)

Reviewer: Codex (gpt-5.6-sol), dispatched read-only via MCP by Claude
Code at operator direction, 2026-07-09.
Dispositioner: Claude Code (same day). Every disposition below was
applied in SPEC-RUNSPEC **rev 2** (and SPEC-OBSERVED-INPUT rev 2 for
finding 4). Verification notes marked Ran were checked directly
against source/goldens before accepting.

## Findings and dispositions

| # | Sev | Finding (condensed) | Disposition |
|---|---|---|---|
| 1 | High | Byte parity is impossible unspecified: the legacy binary writes the accumulated argv string into the `.cli` header (`arg_v`, cligen.f:665-683 → wxr_gen), and the goldens carry it byte-for-byte with inconsistent flag orders across cases. | **Accepted** (Ran: verified the echo in golden line 5 of mt-wilson and single-storm). Rev 2 adds §Header echo: `output.command_echo` optional verbatim field + canonical rendering default; golden runspecs pin the echo from fixture-runs.tsv. Output-byte compatibility, not interface emulation. |
| 2 | High | `output.header` promised `-H` semantics, but `dohedr` is write-only — no consumer anywhere; headers are written unconditionally. | **Accepted** (Ran: grep confirms writes at 765/962/1088, zero reads). Field removed; `-H` ratified behaviorally dead in the traps table. |
| 3 | High | Storm-mode year model contradictory: the storm date's year IS `ibyear`/`iyear` (cligen.f:3384-3419); requiring `simulation.begin_year` conflicts and the golden row omitted it; the iopt-4/7 `nt` leap test differs from the Gregorian-on-index rule; the legacy header echoes `numyr = -1`. | **Accepted.** Rev 2 adds the normative per-mode year-plan table: storm modes take the year from `date.year`, reject `simulation.begin_year`/`years`, transcribe the distinct `nt` test (wxr_gen:3758-3763), and the header writer reproduces the legacy-visible `numyr` values. |
| 4 | High | Observed `begin_year` default (`ioyr`) is not derivable through the declared observed interface — the source reads first-record columns 11-15 with `(10x,i5)` + `backspace` (usr_opt), which SPEC-OBSERVED-INPUT declared ignored. | **Accepted.** SPEC-OBSERVED-INPUT rev 2 adds the non-consuming `initial_year` open-time read with the source citation and the A3 common-interface obligation; SPEC-RUNSPEC's year-plan table references it. |
| 5 | High | Observed `years` is a cap on year loops (`ii > numyr`, wxr_gen:3800), not an ignored value. | **Accepted.** Year-plan table: cap semantics; run ends at the earlier of the cap or the stop protocol (mid-year EOF vs post-year sentinel stop). |
| 6 | Med | Live `-S`/`-s` multi-station scan neither representable nor ratified excluded. | **Accepted.** §Non-goals now excludes it explicitly, cross-referencing SPEC-PAR's deferral; no silent first-station fallback. |
| 7 | Med | No normative scalar types/domains; invalid dates could reach `jdt` assertions. | **Accepted.** §Field invariants added (types, domains, parent-block omissibility, wrong-mode-block rejection, date validity checked before `jdt`); legacy-permissive bounds ratified explicitly. |
| 8 | Med | `validate` vs `run` behavior undefined. | **Accepted.** §validate-vs-run added: both parse/resolve/open inputs and resolve defaults; `validate` never generates or touches the output path (collision checking excluded for determinism); `run` enforces overwrite. |
| 9 | Med | Acceptance did not exercise `design_storm`, linear/monthly-mean-preserving interpolation, `overwrite: true`. | **Accepted.** §Acceptance extended with fixture-unreachable-labeled vectors (the iopt-7 precedent). |
| 10 | Med | "Hash or runspec" provenance overpromised reproduction-from-provenance-alone. | **Accepted.** §Provenance now requires the canonical effective runspec itself + hash + input content identities, and weakens the claim to "identifies its inputs"; details to SPEC-PROVENANCE. |
| 11 | Med | File-relative path semantics undefined for the in-memory A6 surface. | **Accepted.** §Path resolution added: `(document, base_dir)` API boundary; PyO3 supplies resolved paths; lexical + resolved forms both retained (echo/provenance need them). |
| 12 | Low | `-v/-V`, `-h/-?`, `-t8` lacked explicit dispositions (judgment call). | **Accepted.** Traps table + §Non-goals: control/display surfaces, not run identity; the new CLI has its own `--help`/`--version`. |
| 13 | Low | Burn wording ambiguous ("N from streams" vs N per stream). | **Accepted.** Now "N draws from EACH of k1..k9 (9N total); k10 unchanged", domain ≥ 0. |

## Verdict carried forward

The reviewer's overall verdict: schema direction sound; equivalence
values otherwise correct; not implementation-ready until findings 1-5
were resolved. All 13 findings accepted and applied; rev 2 is the
implementation-ready contract for item 8. The reviewer's full verbatim
report is preserved in the dispatch thread
(threadId 019f4a1c-0a0c-7fa0-b446-44b2322ed74c).
