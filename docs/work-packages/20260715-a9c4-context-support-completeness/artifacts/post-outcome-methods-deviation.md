# Post-outcome availability-label deviation

Date: 2026-07-15
Detected by: independent evidence extraction
Outcome boundary: after the canonical audit and mask; before report drafting

The A9c4 audit recomputes 522 non-storm historical A9c3 mandatory-cell
**statuses** exactly: 408 available, 114 unavailable, and zero mismatches. It
copies the 144 storm-descriptor statuses from A9c3 under the inherited grouped
policy rather than independently recomputing them. All 666 stored values
therefore match A9c3, but only 522 are recomputation evidence. In addition, 96
stored historical storm-descriptor contributor **counts** do not reproduce
A9c3's `available_station_count`. For six configurations, four storm objectives,
and four strata having four generated contributors, the audit records four
while A9c3 records two.

The cause is bounded. Storm rows are policy-retained under A9c3's grouped rule.
The audit implementation stores the number of frozen generated contributors
for those rows, while A9c3's objective row stores the grouped observed-station
count. The affected field name, `historical_a9c3_joint_available_station_count`,
therefore overstates what those 96 storm values represent. Non-storm counts
use the historical A9c3 any-burn station-union semantics.

This discrepancy changes no stored A9c3 status, A9c4 retained/excluded cell,
breadth combination, or terminal. The public report must distinguish 522
recomputed non-storm statuses from 144 inherited storm statuses, disclose the
96 count-label discrepancies, and describe storm retention as an inherited
policy exception rather than the non-storm common-support rule. The mask field
`candidate_inputs_used: false` means that
historical candidate diagnostics did not select mask cells; it does not mean
the audit generated no historical candidate data.
