# A10M1 execution amendments

## A1 — nullable excluded-row elevation

Date: 2026-07-17
Series-access state: no Daymet, Daily01, or Subhourly01 target series accessed.

The first metadata-only inventory pass read the current official 255-row
USCRN station table and stopped because the non-operational `TN Oakridge 0 N`
test-site row represents elevation as `UN`. The prospective eligibility rule
already excludes this row (`OPERATION=Non-operational`), but the inventory
must still preserve it. The parser now maps only that documented nonnumeric
metadata token to null. It does not alter station eligibility, source frames,
roles, periods, variables, target access, or any scientific rule.
