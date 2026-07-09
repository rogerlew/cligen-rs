# Dead-Code Adjudication

Evidence mode: Ran (mechanical call extraction, `extract.py`) + Static
(source reads of the flagged sites).

Method: every `call` statement and known-function reference in
`cligen.f` was extracted per unit, split into live-code and commented
classes (`unit-extraction.md`). A unit is dead when it has zero live
references and is not a program entry point.

## Verdicts

| Unit | Lines | Live refs | Commented refs | Verdict |
|---|---|---:|---|---|
| `nrmd` | 2123–2152 | 0 | none anywhere | **DEAD** — no reference of any kind; matches the source's own comment ("does not seem to be used", line 426) |
| `chitst` | 4342–4452 | 0 | `dstg:1731`, `ranset:4225,4241,4255` | **DEAD** — all four call sites commented; K-S replaced it on the live QC path |
| `alph` | 985–1036 | 0 | `day_gen:3118,3140` (`c call alph` immediately above the live `call alphb`) | **DEAD** — Bofu Yu variant is the live path |
| `r5mon` | 1904–1979 | 0 | `cligen:877` (`C call r5mon(tp6)` above the live `call r5monb`) | **DEAD** — Yu variant is the live path |

Corroborating live-path evidence: `alphb` called at `day_gen:3119,3141`;
`r5monb` at `cligen:878`; `dstg`'s only live caller is `alphb:3882` (the
`alph:1030` reference sits inside dead code).

## Port disposition

The four units (~330 source lines) are **recorded, not ported**. Faithful
mode owes them nothing: they cannot influence any trajectory. If a future
generation profile wants the pre-Yu intensity model, it arrives as a
deliberate extension citing these line ranges.

## Entry-point note

`dstinv` and `dstzr` appear as callees but are not units: they are ENTRY
points of `dinvr` and `dzror` respectively (`cdfchi` calls `dstinv`;
`dinvr` calls `dstzr`). Both hosts are live via the
`confls → cdfchi` chain. The ENTRY-point translation rule in the coding
standard (§5) applies.
