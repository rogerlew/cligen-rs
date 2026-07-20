# Scaffold review

Disposition: `ACCEPT — A10M5O1R3-COMPOSED-ADMISSION-IDENTITY-READY`

## Review focus

Review must confirm the extension is additive, ordered identities are derived
only from the authenticated current plan, prepared and promoted identities are
cross-checked under the submit lock, amendments cannot mutate the chain, and
all failures precede resource reservation. It must also confirm that generic
asset prepare/stage/remote verification already covers transport integrity and
that no historical receipt is reinterpreted.

## Independent scaffold review

The first independent review accepted the narrow toolkit direction but held
implementation readiness pending seven corrections: preserve reachable
receipt-directory allowlist/symlink checks; use one schema consistently across
specification, example, implementation, and tests; make
`admission_materialization` immutable; cross-check prepared and promoted
identities under the submit lock; state that only historical single-controller
plans may omit the chain; reject malformed `input_identities` with a typed
toolkit error; and explicitly justify executable checker members plus
materializer/checker separation. R14R2R1 remains deferred until a follow-up
review accepts those gates.

## Follow-up implementation review

The independent reviewer found no unresolved issue after correction and
independently reran the three focused composed-admission tests. The review
confirmed that all seven findings above are resolved:

- receipt-directory strict resolution, nonsymlink, and allowed-root checks are
  reachable and covered by missing/outside/symlink fixtures;
- specification, example, implementation, tests, and receipt use the same
  nested `checker_assets` schema;
- `admission_materialization` is immutable through `amend`;
- submit-lock equality covers the semantic plan, current local files, private
  prepared assets, promoted transfer receipts, and exact receipt projection;
- legacy omission is historical-only, while newly composed controllers must
  declare the chain;
- malformed `input_identities` fails with typed `PLAN_DRIFT`; and
- repository-owned executable checker members and materializer separation are
  explicit policy and directly tested.

Final finding count: zero. Final disposition: `ACCEPT`.

## Second independent review and disposition

A second reviewer initially held ratification on four points: recompute the
current semantic plan identity and reject ambiguous current revisions; recheck
transfer promotion/revalidation fields rather than projecting only three
identity fields; cover the advertised one-checker positive case; and make the
R14 successor consume its assigned chain slots rather than treating declaration
alone as the remedy.

After correction, both independent reviewers returned `ACCEPT` with no
findings. They verified exact current-revision and semantic-hash equality;
promotion, identity-SHA, remote-revalidation, and completed-state checks; the
single- and two-checker paths; and R14R2R1's explicit outer slot 0, delegate
slot 1, remote-root-relative inherited `Path(__file__)`, plan/manifest, and
ordered receipt requirements. One reviewer independently reran the focused
tests; all passed.
