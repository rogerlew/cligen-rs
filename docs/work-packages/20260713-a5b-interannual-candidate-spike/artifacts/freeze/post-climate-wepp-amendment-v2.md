# A5b Post-Climate WEPP Amendment v2

Date: 2026-07-13
Status: **FROZEN BEFORE PUBLIC WEPP RESPONSE OUTPUT**

## Boundary and disclosure

The v5 runner, campaign, analyzer, and post-climate freeze remain immutable.
Their freeze SHA-256 is
`01b6f52a9fdb2d85ac8f05072c5e2e0131fcf74220050e28c7e5337c4d45fa8a`.
The candidate climate manifest remained at pre-WEPP SHA-256
`b52d20b6e472995491ae3d81433f54a709a2a53c65c8b4753957c0ecb0193b50`
with all 1,904 transient candidate climates present.

The v5 campaign passed both accepted-input verifiers and privately validated
556 of 2,176 WEPP response/execution pairs before one worker failed closed.
The complete private publication tree was removed; no archive, campaign
index, analysis output, manifest transition, lifecycle quarantine, or
candidate deletion survived.

Unlike amendment v1, this format discovery occurred on a candidate coordinate
and the exact failed element row was inspected. Candidate response values were
therefore inspected after climate generation but before the downstream
campaign contract was complete. This is disclosed as outcome access even
though no candidate ranking, aggregate, comparison, gate result, or threshold
was computed or changed. The only v6 change is handling and auditing the
nonresponse `EffInt` presentation overflow. Downstream results remain
exploratory for model-selection purposes because the fully prospective
boundary was crossed.

## Source-built reproduction

The exact coordinate was station `az022664`, candidate
`full_monthly_covariance`, 30 years, replicate 1 (legacy burn 17). Its
778,946-byte candidate CLI had SHA-256
`5cac86f2708a830863294f76b6321b1cd67e67eaa1190d1c969c7b64b82fecf9`.
Execution used pinned WEPP SHA-256
`dccb55f3980e287ada5541b7801f9b9fa79b4b1d65addb97d6914317bc4a4527`
and exited successfully.

The 149,749-byte element stream had SHA-256
`27d4c58fbee84ed343939e1f25846e89f6f15cef3e2ecc0cd037e4da756e360d`.
Line 52, mapped to synthetic year 2, legacy ordinal 296, OFE 1, contained
exactly `*******` in both element fields `EffInt` and `PeakRO`. The
139,966-byte event-hydrology companion had SHA-256
`ea9c1671350aa23699a0921bf3010dacb01f629c28226f24bf82cb943179e6fe`
and supplied the existing source-registered `PeakRO` recovery. Standard output
was 11,019 bytes with SHA-256
`8f75554b4ebe3354b214869cc8c55b82f13792d87673775f49c92667486a9494`;
standard error was empty with SHA-256
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
These raw diagnostic streams remain untracked and are removed after the v6
freeze is sealed.

## Pinned-source disposition

At source commit `c3a082e`, `src/sedout.for:482-486` writes
`effint(iplane) * 3.6e06` as element numeric index 2 after the four key fields.
FORMAT 1000 at `src/sedout.for:532-533` assigns `F7.3` to `EffInt`, `PeakRO`,
and `EffDur`; `src/outfil.for:708-714` labels index 2 `EffInt` in mm/h.
`EffInt` is not selected, aggregated, recovered, or reported by any registered
A5b response metric.

Extractor `a5b_wepp_p326_response_extractor_v6` adds policy
`a5b_wepp_element_effint_f7_3_overflow_v1`. It admits exactly seven asterisks
only at numeric index 2 and only under the exact `EffInt` header. Numeric
values must be canonical nonnegative `F7.3` spellings. The extractor does not
parse, censor, impute, or use an overflowing `EffInt`; it records a separate
closed audit with the source element hash, exact field/index/token/FORMAT and
nonresponse declaration, total row count, occurrence count, and first mapped
key. The campaign independently sums the field count and the v6 analyzer
reproduces it from every archived execution record.

Wrong star counts, a star in a response-bearing or undeclared field, a changed
header, zero-padded or over-width numeric spelling, inconsistent row/source
bindings, and mismatched campaign counts remain fatal. The existing `Sm`,
same-day aggregation, `PeakRO` recovery, zero-event, role/hash, and lifecycle
rules are unchanged.

## Verification requirements

The v6 runner must parse the exact retained diagnostic to 61 event records,
778 element records, one `EffInt` overflow at `(2, 296, 1)`, one `PeakRO`
recovery, and zero `Sm` overflows. Its self-test must positively exercise the
new audit and reject wrong-star, over-width, zero-padded, header/policy, count,
and source mutations. The v6 analyzer must accept a closed zero-event recovery
count of zero, validate the new per-run audit, and reproduce independent
campaign totals for both `EffInt` and `Sm`.

Both v6 sources must pass static undefined-name checks and their complete
self-tests before production restarts. Production must repeat both accepted
input verifiers and begin from an absent WEPP evidence directory with the
candidate manifest and transient climates unchanged.
