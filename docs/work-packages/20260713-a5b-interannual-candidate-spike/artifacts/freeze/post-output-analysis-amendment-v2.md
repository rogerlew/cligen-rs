# A5b Post-Output Analysis Amendment v2

Date: 2026-07-13
Status: **FROZEN BEFORE REPLACEMENT CLIMATE OR WEPP ANALYSIS OUTPUT**

## Boundary and disclosure

The climate v2 analyzer, WEPP v8 analyzer, post-output analysis freeze v1,
and their amendment remain immutable. Climate v2 completed and its exact
output is retained with deterministic `gzip -n -9` compression as
`artifacts/climate/a5b-analysis-v2-incomplete.json.gz`.
Before compression it was 146,470,359 bytes with SHA-256
`9da014ec173b134508572e58d77003bd5ae8964722079a7ba8d8729d88306d03`.
WEPP v8 rejected that input before writing downstream analysis because the
climate completeness flag was false.

The completeness ledger reported 48,713 unique failures, all labeled
`embedded target differs` for Gate 3. Counts by candidate and horizon were
inspected, followed by one source evidence vector. That diagnostic viewed
candidate metric values, so `candidate_metric_values_inspected` is now true.
No candidate ranking, gate pass table, aggregate candidate score, promotion
result, or WEPP response comparison was inspected. The package remains
exploratory for model-selection purposes under the earlier post-climate
boundary as well as this additional disclosure.

## Cause

For Gate 3, the analyzer correctly requires every candidate quality report to
bind the same station-parameter-set SHA-256 as its paired faithful-off report.
It also correctly requires the embedded target value and, where registered,
the embedded normalization scale to match exactly.

The v2 condition additionally required
`candidate_row.target_counts[index] == baseline_row.target_counts[index]`.
For the `report_embedded_station_parameter` surface, the registered
`target_count_path` points to the quality report's `n` field. That field is the
number of generated samples contributing to the statistic, not part of the
station parameter identity. It is expected to change when a candidate changes
wet-day occurrence or another sampled process.

In the inspected humid-site October vector, candidate and baseline parameter
SHA-256 and all five target values were exactly equal. The wet-day mean target
was `13.970000302791595` mm in both reports, while generated wet-day sample
counts were 670 and 616. The invalid count-equality clause alone produced the
failure. All 48,713 recorded failures arose from this combined target check;
there were no station-parameter identity failures.

## Corrected analyzers

`artifacts/climate/analyze-a5b-v3.py` independently succeeds v2. Its Gate 3
identity predicate retains exact parameter SHA-256, embedded target value,
and optional target scale equality but does not compare generated sample
counts across candidate and baseline series. Existing baseline eligibility
and candidate count-sufficiency checks remain unchanged, so insufficient
samples are still unavailable/fatal according to the registered metric
contract. A new self-test proves that unequal generated counts with equal
targets are accepted and a changed target is rejected.

`artifacts/wepp/analyze-wepp-v9.py` independently succeeds v8. It changes no
WEPP evidence, response parsing, aggregation, matrix, metric, or gate rule. It
binds the v3 climate analyzer and this freeze, then independently revalidates
all 2,176 WEPP response/execution records before writing downstream analysis.

Production must retain the incomplete v2 climate analysis, begin with the
canonical climate and WEPP analysis output paths absent, and refuse to treat
the retained incomplete analysis as replacement evidence.
