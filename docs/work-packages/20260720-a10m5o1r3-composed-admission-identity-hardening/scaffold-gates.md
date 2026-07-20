# Scaffold gates

- optional, backward-compatible `checker_assets` field
- exact protocol `ordered-plan-assets-v1`
- non-empty ordered duplicate-free logical-name roster
- every checker is an executable frozen plan asset
- exact plan/prepared/transfer/receipt identity equality
- exactly one current semantic revision and recomputed `plan_id` equality
- promoted, identity-matched, remotely revalidated transfer state
- order changes alter plan identity and fail stale receipts
- local or staged byte drift fails before submission
- admission contract immutable across amendments
- historical contracts without `checker_assets` remain accepted unchanged
- no ledger reservation or adapter submit call on any adverse fixture
- full toolkit tests and standard repository gates
- independent review with no unresolved finding

Coverage/CRAP is not triggered because no production function under `crates/`
changes.
