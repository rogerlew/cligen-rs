# A10 Daymet Calendar-Contract Hardening

Status: `EXECUTED-COMPLETE`
Date: 2026-07-19
Evidence mode: Static

## Objective

Prevent A10 data consumers from treating a complete normalized Gregorian date
axis as complete Daymet observations, and remove ambiguity between official
Daymet 365-day behavior and the inherited A5 no-leap transform.

## Scope

Included: revision-2 A10 corpus and climate-statistics specifications; a
canonical Daymet calendar profile; agent and work-package preflight rules;
terminology corrections in the A10M5R8 campaign record; static verification.

Excluded: corpus-byte changes, schema-shape changes, imputation, calendar
relabeling, historical A5 transform changes, training-code changes, model
changes, resource reservations, and scientific reruns.

## Authority

The A10 study plan section 7, accepted A10M1
`daymet_official_365_v1` corpus identity, and observed A10M5R8 failure evidence
are authoritative. This package documents existing semantics; it introduces no
generation profile.

## Plan

1. Pin official Daymet source, normalized-axis, and generated-calendar
   semantics without conflating them with `noleap_365_v1`.
2. Add exact fit-period and eight-year example counts and dates.
3. Require a pre-resource calendar/missingness preflight in agent and package
   instructions.
4. Verify the profile, terminology, links, and repository gates.

## Data calendar and missingness preflight

This package defines the preflight rather than consuming training data. Its
static verifier reconstructs the 1980--2009 Gregorian axis and 1980--1987
window, confirms February 29 presence, pins absent leap-year December 31 dates,
and checks exact axis/observed counts.

## Execution & dispatch

Codex executes from `/Users/roger/src/cligen-rs`, starting from current `main`
and pushing only `main`. No external or scarce compute is used.

## Gates

- `python3 artifacts/verify_calendar_profile.py`
- specification registry and terminology inspection
- `git diff --check`
- `cargo fmt --check`
- `cargo clippy --all-targets -- -D warnings`
- `cargo test`

## Exit criteria

Complete when the profile verifier and repository gates pass and the corpus,
consumer, agent, and package-template documentation all require mask-aware
calendar preflight. Hold on contradictory accepted corpus evidence or a failed
gate.

## Artifacts

- `artifacts/verify_calendar_profile.py` — static profile and spec verifier
- `artifacts/review.md` — final documentation review
- `artifacts/gate-results.md` — executed gates

## Disposition

Complete. The canonical profile reconstructs the exact fit-period and
eight-year counts, the two A10 specs now name the official Daymet civil-date
behavior, and agent/package instructions require mask-aware preflight before
scarce-resource use. No corpus, schema, model, or historical A5 transform was
changed.
