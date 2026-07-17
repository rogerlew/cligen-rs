# Prospective amendment 001 — failed-attempt collectability

Timing: after private asset construction, before toolkit planning, remote write,
or allocation.

Static review found that the toolkit evidence packer requires every allowlisted
file to exist. The job's failure trap already produced `evidence.json`, but an
early failure could leave the later `benchmark.json`, `checkpoint.json`, or
`resource.json` absent and prevent collection of an exhausted attempt.

The amendment makes the failure trap atomically create explicit
`unavailable_due_to_failed_attempt` placeholders only when each later receipt
does not exist. It changes no model, corpus role, training operation,
checkpoint comparison, RNG, benchmark, gate, resource request, retry rule, or
scientific boundary. Assets and source are rehashed against the amendment
commit before staging.
