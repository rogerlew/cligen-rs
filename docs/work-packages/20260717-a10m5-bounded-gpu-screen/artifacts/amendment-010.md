# Operational amendment 010 — projection policy label

R7 collection executed with evidence projection revision 3 after amendments
007--009, but the live adapter's collection metadata still emitted its older
literal label `lemhi-evidence-projection-2`. The collected file hashes and
projection behavior are correct; the label is stale controller metadata.

The adapter now emits `lemhi-evidence-projection-3`, and its live-command-path
test asserts the value. The immutable R7 collection receipt is not rewritten;
the package records this discrepancy explicitly, and future collections carry
the corrected label.
