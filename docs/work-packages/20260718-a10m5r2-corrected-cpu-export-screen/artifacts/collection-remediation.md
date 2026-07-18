# A10M5R2 collection remediation

The scientific matrix completed before either issue below was discovered.
Both failures occurred in fail-closed collection and did not alter job results,
candidate identities, selection scores, thresholds, or accounting.

## Missing non-invocation records

The frozen revision-2 allowlist included `recovery.json` and the two recovery
Slurm streams, but the all-clean path did not materialize them. Initial
collection returned `EVIDENCE_INCOMPLETE`. Read-only inspection proved that
these were the only missing allowlisted paths. The operator convention already
used by A10M5 and A10M5R1 was applied:

```json
{"invoked":false,"reason":"no job-local cleanup failure"}
```

Both streams contain `recovery not invoked`. Their hashes match the prior
accepted convention: `bf058467...07d0f54` for the JSON and
`6a848f0e...8e730e` for each stream. No recovery job was submitted; the ledger
released the reserved five minutes after cleanup proof.

## External-time command path

The next collection reached projection but returned `SANITIZATION_FAILED`.
Private quarantine inspection localized every forbidden value to line one of
the twelve `cpu.time-v.txt` files: GNU time had echoed the full command with
the private durable root. No scientific JSON or numerical time/RSS line
contained a forbidden value.

Because the plan had already reached `MATRIX_SETTLED`, projection rules were no
longer amendable. The exact durable-root prefix was mechanically replaced with
the non-reserved literal `REMOTE_RUN_ROOT` in only the twelve allowlisted time
witnesses. All numerical lines were retained. Fresh authenticated collection
then passed under projection revision 3; the published hashes are bound by
`toolkit/collection.json`.

Future packages must freeze both the all-clean recovery placeholders and typed
path replacement for `/usr/bin/time -v` before allocation. The agent toolkit
README and Lemhi compute guide now state both traps explicitly.
